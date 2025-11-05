"""
🔄 DATA PIPELINE - COLETA OTIMIZADA
Pipeline completo de coleta de dados para ML

Estratégias:
1. Histórico inicial em batch (temporadas completas)
2. Incremental diário (novos jogos)
3. Zero redundância (nunca reconsultar dados salvos)
4. Otimização de requests (batch sempre que possível)
"""

import asyncio
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
import logging

from app.services.api_football_service import APIFootballService
from app.services.api_quota_manager import APIQuotaManager
from app.models.api_tracking import FixtureCache, DataCollectionJob, LeagueConfig
from app.models.match import Match
from app.models.team import Team
from app.models.statistics import MatchStatistics

logger = logging.getLogger(__name__)

class DataPipeline:
    """Pipeline otimizado de coleta de dados"""

    def __init__(self, db: Session):
        self.db = db
        self.api_service = APIFootballService()
        self.quota_manager = APIQuotaManager(db)

    async def collect_historical_batch(
        self,
        league_id: int,
        season: int,
        force_update: bool = False
    ) -> Dict:
        """
        HISTÓRICO INICIAL - Coletar temporada completa em batch

        Esta é a forma mais eficiente: 1 request = temporada inteira!

        Args:
            league_id: ID da liga
            season: Ano da temporada
            force_update: Forçar atualização mesmo se já existir

        Returns:
            Resultado da coleta
        """
        logger.info(f"📦 Coletando histórico batch: Liga {league_id}, Temporada {season}")

        # Verificar se já foi coletado
        if not force_update:
            existing_count = self.db.query(FixtureCache).filter(
                FixtureCache.league_id == league_id,
                FixtureCache.season == season,
                FixtureCache.has_basic_data == True
            ).count()

            if existing_count > 0:
                logger.info(f"✅ Já existem {existing_count} fixtures no cache. Pulando...")
                return {
                    'status': 'SKIPPED',
                    'reason': 'already_exists',
                    'existing_count': existing_count
                }

        # Verificar quota
        if not self.quota_manager.can_make_request(1):
            logger.warning("⚠️ Quota insuficiente para coletar histórico")
            return {'status': 'FAILED', 'reason': 'insufficient_quota'}

        # Criar job
        job = DataCollectionJob(
            job_type='INITIAL_HISTORICAL',
            job_name=f'Historical Liga {league_id} Season {season}',
            league_ids=[league_id],
            season=season,
            status='RUNNING',
            started_at=datetime.now()
        )
        self.db.add(job)
        self.db.commit()

        try:
            # 1. COLETAR TEMPORADA COMPLETA (1 request!)
            start_time = datetime.now()

            fixtures = await self.api_service.get_fixtures_by_league(
                league_id=league_id,
                season=season
            )

            response_time = (datetime.now() - start_time).total_seconds() * 1000

            # Registrar request
            self.quota_manager.record_request(
                endpoint='fixtures_by_season',
                success=True,
                results_count=len(fixtures),
                response_time_ms=response_time,
                params={'league': league_id, 'season': season}
            )

            job.requests_used += 1
            job.fixtures_collected = len(fixtures)

            logger.info(f"✅ {len(fixtures)} fixtures coletados em batch")

            # 2. SALVAR NO CACHE (evitar reprocessamento)
            saved_count = 0
            for fixture in fixtures:
                saved = await self._save_fixture_to_cache(fixture, league_id, season)
                if saved:
                    saved_count += 1

            logger.info(f"💾 {saved_count} fixtures salvos no cache")

            # 3. COLETAR ESTATÍSTICAS (apenas para finalizados)
            finished_fixtures = [
                f for f in fixtures
                if f.get('fixture', {}).get('status', {}).get('short') == 'FT'
            ]

            stats_collected = await self._collect_statistics_batch(
                finished_fixtures,
                job,
                max_stats=100  # Limitar estatísticas para economizar requests
            )

            # Finalizar job
            job.status = 'COMPLETED'
            job.completed_at = datetime.now()
            job.fixtures_with_stats = stats_collected
            job.progress = 100.0

            self.db.commit()

            logger.info(f"🎉 Coleta histórica concluída!")
            logger.info(f"   - Fixtures: {saved_count}")
            logger.info(f"   - Com estatísticas: {stats_collected}")
            logger.info(f"   - Requests usados: {job.requests_used}")

            return {
                'status': 'COMPLETED',
                'job_id': job.id,
                'fixtures_collected': saved_count,
                'fixtures_with_stats': stats_collected,
                'requests_used': job.requests_used
            }

        except Exception as e:
            logger.error(f"❌ Erro na coleta histórica: {e}")
            job.status = 'FAILED'
            job.error_details = {'error': str(e)}
            job.completed_at = datetime.now()
            self.db.commit()

            return {'status': 'FAILED', 'error': str(e)}

    async def _save_fixture_to_cache(
        self,
        fixture_data: Dict,
        league_id: int,
        season: int
    ) -> bool:
        """Salvar fixture no cache (evitar redundância)"""
        try:
            fixture_info = fixture_data.get('fixture', {})
            fixture_id = fixture_info.get('id')

            if not fixture_id:
                return False

            # Verificar se já existe
            existing = self.db.query(FixtureCache).filter(
                FixtureCache.fixture_id == fixture_id
            ).first()

            if existing:
                # Atualizar se necessário
                existing.raw_fixture_data = fixture_data
                existing.status = fixture_info.get('status', {}).get('short', 'NS')
                existing.last_synced = datetime.now()
            else:
                # Criar novo
                cache = FixtureCache(
                    fixture_id=fixture_id,
                    league_id=league_id,
                    season=season,
                    fixture_date=datetime.fromisoformat(fixture_info.get('date', '').replace('Z', '+00:00')),
                    status=fixture_info.get('status', {}).get('short', 'NS'),
                    has_basic_data=True,
                    raw_fixture_data=fixture_data
                )
                self.db.add(cache)

            self.db.commit()
            return True

        except Exception as e:
            logger.error(f"Erro ao salvar fixture {fixture_data.get('fixture', {}).get('id')}: {e}")
            return False

    async def _collect_statistics_batch(
        self,
        fixtures: List[Dict],
        job: DataCollectionJob,
        max_stats: int = 100
    ) -> int:
        """
        Coletar estatísticas em batch (otimizado)

        Args:
            fixtures: Lista de fixtures
            job: Job de coleta
            max_stats: Máximo de estatísticas para coletar

        Returns:
            Quantidade coletada
        """
        collected = 0
        delay = self.quota_manager.get_recommended_delay()

        for idx, fixture in enumerate(fixtures[:max_stats]):
            fixture_id = fixture.get('fixture', {}).get('id')

            if not fixture_id:
                continue

            # Verificar se já tem estatísticas
            cache = self.db.query(FixtureCache).filter(
                FixtureCache.fixture_id == fixture_id
            ).first()

            if cache and cache.has_statistics:
                continue  # Já tem, pular

            # Verificar quota
            if not self.quota_manager.can_make_request(1):
                logger.warning(f"⚠️ Quota esgotada. Parando coleta de estatísticas em {idx}/{max_stats}")
                break

            try:
                # Coletar estatísticas
                stats = await self.api_service.get_fixture_statistics(fixture_id)

                # Registrar request
                self.quota_manager.record_request(
                    endpoint='fixture_statistics',
                    success=True,
                    results_count=len(stats) if stats else 0,
                    params={'fixture': fixture_id}
                )

                job.requests_used += 1

                # Salvar no cache
                if cache and stats:
                    cache.raw_statistics_data = stats
                    cache.has_statistics = True
                    cache.last_synced = datetime.now()
                    self.db.commit()
                    collected += 1

                # Delay adaptativo
                await asyncio.sleep(delay)

                # Atualizar progresso
                if idx % 10 == 0:
                    job.progress = min(99, (idx / max_stats) * 100)
                    self.db.commit()
                    logger.info(f"   📊 Estatísticas: {idx}/{max_stats}")

            except Exception as e:
                logger.error(f"Erro ao coletar stats da fixture {fixture_id}: {e}")
                job.errors_count += 1

        return collected

    async def collect_daily_incremental(self, target_date: Optional[str] = None) -> Dict:
        """
        ROTINA INCREMENTAL DIÁRIA

        Coleta otimizada de:
        1. Novos jogos agendados
        2. Resultados de jogos finalizados
        3. Atualizações de jogos em andamento

        Args:
            target_date: Data alvo (YYYY-MM-DD), None = hoje

        Returns:
            Resultado da coleta
        """
        if target_date is None:
            target_date = date.today().isoformat()

        logger.info(f"📅 Coleta incremental diária: {target_date}")

        # Criar job
        job = DataCollectionJob(
            job_type='DAILY_INCREMENTAL',
            job_name=f'Daily Update {target_date}',
            date_from=target_date,
            date_to=target_date,
            status='RUNNING',
            started_at=datetime.now()
        )
        self.db.add(job)
        self.db.commit()

        try:
            # Obter ligas ativas
            active_leagues = self.db.query(LeagueConfig).filter(
                LeagueConfig.is_active == True,
                LeagueConfig.collect_daily == True
            ).order_by(LeagueConfig.priority).all()

            if not active_leagues:
                logger.warning("⚠️ Nenhuma liga ativa configurada")
                job.status = 'COMPLETED'
                job.completed_at = datetime.now()
                self.db.commit()
                return {'status': 'COMPLETED', 'message': 'no_active_leagues'}

            logger.info(f"🏆 {len(active_leagues)} ligas ativas")

            total_new = 0
            total_updated = 0

            # Para cada liga, coletar fixtures do dia
            for league_config in active_leagues:
                # Verificar quota
                if not self.quota_manager.can_make_request(1):
                    logger.warning("⚠️ Quota insuficiente. Parando coleta diária.")
                    break

                result = await self._collect_league_daily(
                    league_config,
                    target_date,
                    job
                )

                total_new += result.get('new_fixtures', 0)
                total_updated += result.get('updated_fixtures', 0)

                # Delay entre ligas
                await asyncio.sleep(self.quota_manager.get_recommended_delay())

            # Finalizar job
            job.status = 'COMPLETED'
            job.completed_at = datetime.now()
            job.fixtures_collected = total_new + total_updated
            job.progress = 100.0

            self.db.commit()

            logger.info(f"✅ Coleta diária concluída!")
            logger.info(f"   - Novos: {total_new}")
            logger.info(f"   - Atualizados: {total_updated}")
            logger.info(f"   - Requests: {job.requests_used}")

            return {
                'status': 'COMPLETED',
                'job_id': job.id,
                'new_fixtures': total_new,
                'updated_fixtures': total_updated,
                'requests_used': job.requests_used
            }

        except Exception as e:
            logger.error(f"❌ Erro na coleta diária: {e}")
            job.status = 'FAILED'
            job.error_details = {'error': str(e)}
            job.completed_at = datetime.now()
            self.db.commit()

            return {'status': 'FAILED', 'error': str(e)}

    async def _collect_league_daily(
        self,
        league_config: LeagueConfig,
        target_date: str,
        job: DataCollectionJob
    ) -> Dict:
        """Coletar dados diários de uma liga"""
        try:
            # Buscar fixtures do dia (1 request por liga)
            fixtures = await self.api_service.get_fixtures_by_league(
                league_id=league_config.league_id,
                season=league_config.current_season or datetime.now().year,
                date_from=target_date,
                date_to=target_date
            )

            self.quota_manager.record_request(
                endpoint='fixtures_daily',
                success=True,
                results_count=len(fixtures),
                params={'league': league_config.league_id, 'date': target_date}
            )

            job.requests_used += 1

            new_count = 0
            updated_count = 0

            # Processar fixtures
            for fixture in fixtures:
                fixture_id = fixture.get('fixture', {}).get('id')
                status = fixture.get('fixture', {}).get('status', {}).get('short')

                # Verificar se já existe
                cache = self.db.query(FixtureCache).filter(
                    FixtureCache.fixture_id == fixture_id
                ).first()

                if cache:
                    # Atualizar se mudou o status
                    if cache.status != status:
                        cache.status = status
                        cache.raw_fixture_data = fixture
                        cache.last_synced = datetime.now()

                        # Se finalizou, marcar para coletar estatísticas
                        if status == 'FT' and not cache.has_statistics:
                            cache.needs_update = True

                        updated_count += 1
                else:
                    # Novo fixture
                    new_cache = FixtureCache(
                        fixture_id=fixture_id,
                        league_id=league_config.league_id,
                        season=league_config.current_season,
                        fixture_date=datetime.fromisoformat(
                            fixture.get('fixture', {}).get('date', '').replace('Z', '+00:00')
                        ),
                        status=status,
                        has_basic_data=True,
                        raw_fixture_data=fixture,
                        needs_update=(status == 'FT')  # Se já finalizou, coletar stats
                    )
                    self.db.add(new_cache)
                    new_count += 1

            self.db.commit()

            # Coletar estatísticas de jogos finalizados
            finished_fixtures = [
                f for f in fixtures
                if f.get('fixture', {}).get('status', {}).get('short') == 'FT'
            ]

            if finished_fixtures and league_config.collect_statistics:
                stats_count = await self._collect_statistics_batch(
                    finished_fixtures,
                    job,
                    max_stats=20  # Limite menor para coleta diária
                )
                logger.info(f"   📊 {league_config.league_name}: {stats_count} estatísticas coletadas")

            # Atualizar config da liga
            league_config.last_collection_date = datetime.now()
            self.db.commit()

            return {
                'new_fixtures': new_count,
                'updated_fixtures': updated_count
            }

        except Exception as e:
            logger.error(f"Erro ao coletar liga {league_config.league_name}: {e}")
            return {'new_fixtures': 0, 'updated_fixtures': 0}

    async def sync_cache_to_database(self, limit: int = 100) -> Dict:
        """
        Sincronizar fixtures do cache para o banco principal

        Converte dados brutos do cache em modelos estruturados

        Args:
            limit: Limite de fixtures para processar por vez

        Returns:
            Resultado da sincronização
        """
        logger.info(f"🔄 Sincronizando cache para banco (limite: {limit})")

        # Buscar fixtures que precisam ser sincronizados
        fixtures_to_sync = self.db.query(FixtureCache).filter(
            FixtureCache.has_basic_data == True,
            FixtureCache.match_id == None  # Ainda não sincronizado
        ).limit(limit).all()

        if not fixtures_to_sync:
            logger.info("✅ Cache já está sincronizado")
            return {'status': 'COMPLETED', 'synced': 0}

        synced = 0

        for cache in fixtures_to_sync:
            try:
                # Criar/atualizar Match
                match = await self._create_match_from_cache(cache)

                if match:
                    cache.match_id = match.id
                    synced += 1

                    # Criar estatísticas se disponíveis
                    if cache.has_statistics and cache.raw_statistics_data:
                        await self._create_statistics_from_cache(match, cache)

            except Exception as e:
                logger.error(f"Erro ao sincronizar fixture {cache.fixture_id}: {e}")

        self.db.commit()

        logger.info(f"✅ {synced} fixtures sincronizados")

        return {
            'status': 'COMPLETED',
            'synced': synced,
            'total_pending': len(fixtures_to_sync) - synced
        }

    async def _create_match_from_cache(self, cache: FixtureCache) -> Optional[Match]:
        """Criar Match a partir do cache"""
        try:
            fixture_data = cache.raw_fixture_data
            if not fixture_data:
                return None

            fixture_info = fixture_data.get('fixture', {})
            teams = fixture_data.get('teams', {})
            goals = fixture_data.get('goals', {})

            # Buscar ou criar times
            home_team = await self._get_or_create_team(teams.get('home', {}))
            away_team = await self._get_or_create_team(teams.get('away', {}))

            if not home_team or not away_team:
                return None

            # Verificar se match já existe
            existing_match = self.db.query(Match).filter(
                Match.home_team_id == home_team.id,
                Match.away_team_id == away_team.id,
                Match.match_date == cache.fixture_date
            ).first()

            if existing_match:
                return existing_match

            # Criar novo Match
            match = Match(
                home_team_id=home_team.id,
                away_team_id=away_team.id,
                match_date=cache.fixture_date,
                home_score=goals.get('home'),
                away_score=goals.get('away'),
                status=cache.status,
                league=str(cache.league_id),  # Usar league_id
                season=str(cache.season),
                external_id=str(cache.fixture_id)
            )

            self.db.add(match)
            self.db.commit()
            self.db.refresh(match)

            return match

        except Exception as e:
            logger.error(f"Erro ao criar match do cache {cache.id}: {e}")
            return None

    async def _get_or_create_team(self, team_data: Dict) -> Optional[Team]:
        """Buscar ou criar time"""
        if not team_data:
            return None

        team_name = team_data.get('name')
        if not team_name:
            return None

        # Buscar time existente
        team = self.db.query(Team).filter(Team.name == team_name).first()

        if team:
            return team

        # Criar novo time
        team = Team(name=team_name)
        self.db.add(team)
        self.db.commit()
        self.db.refresh(team)

        return team

    async def _create_statistics_from_cache(self, match: Match, cache: FixtureCache):
        """Criar MatchStatistics a partir do cache"""
        try:
            stats_data = cache.raw_statistics_data
            if not stats_data or len(stats_data) < 2:
                return

            # Verificar se já existe estatística para este match
            existing = self.db.query(MatchStatistics).filter(
                MatchStatistics.match_id == match.id
            ).first()

            if existing:
                return

            # Stats vêm como lista de 2 times [home, away]
            home_stats_dict = {}
            away_stats_dict = {}

            for team_stats in stats_data:
                team_info = team_stats.get('team', {})
                statistics = team_stats.get('statistics', [])

                # Determinar se é home ou away
                is_home = team_info.get('id') == cache.raw_fixture_data.get('teams', {}).get('home', {}).get('id')

                # Extrair estatísticas
                stats_dict = {}
                for stat in statistics:
                    stat_type = stat.get('type')
                    stat_value = stat.get('value')
                    if stat_type and stat_value is not None:
                        stats_dict[stat_type] = stat_value

                if is_home:
                    home_stats_dict = stats_dict
                else:
                    away_stats_dict = stats_dict

            # Criar MatchStatistics com dados de ambos os times
            match_stat = MatchStatistics(
                match_id=match.id,
                possession_home=self._extract_possession(home_stats_dict.get('Ball Possession')),
                possession_away=self._extract_possession(away_stats_dict.get('Ball Possession')),
                shots_home=self._extract_int(home_stats_dict.get('Total Shots')),
                shots_away=self._extract_int(away_stats_dict.get('Total Shots')),
                shots_on_target_home=self._extract_int(home_stats_dict.get('Shots on Goal')),
                shots_on_target_away=self._extract_int(away_stats_dict.get('Shots on Goal')),
                corners_home=self._extract_int(home_stats_dict.get('Corner Kicks')),
                corners_away=self._extract_int(away_stats_dict.get('Corner Kicks')),
                fouls_home=self._extract_int(home_stats_dict.get('Fouls')),
                fouls_away=self._extract_int(away_stats_dict.get('Fouls')),
                yellow_cards_home=self._extract_int(home_stats_dict.get('Yellow Cards')),
                yellow_cards_away=self._extract_int(away_stats_dict.get('Yellow Cards')),
                red_cards_home=self._extract_int(home_stats_dict.get('Red Cards')),
                red_cards_away=self._extract_int(away_stats_dict.get('Red Cards')),
                passes_home=self._extract_int(home_stats_dict.get('Total passes')),
                passes_away=self._extract_int(away_stats_dict.get('Total passes')),
                pass_accuracy_home=self._extract_pass_accuracy(home_stats_dict.get('Passes accurate'), home_stats_dict.get('Total passes')),
                pass_accuracy_away=self._extract_pass_accuracy(away_stats_dict.get('Passes accurate'), away_stats_dict.get('Total passes'))
            )

            self.db.add(match_stat)
            self.db.commit()

        except Exception as e:
            logger.error(f"Erro ao criar estatísticas do cache {cache.id}: {e}")

    def _extract_possession(self, value) -> Optional[float]:
        """Extrair posse de bola (ex: '60%' -> 60.0)"""
        if not value:
            return None
        if isinstance(value, str) and '%' in value:
            return float(value.replace('%', ''))
        return float(value) if value else None

    def _extract_int(self, value) -> Optional[int]:
        """Extrair valor inteiro"""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    def _extract_pass_accuracy(self, accurate, total) -> Optional[float]:
        """Calcular precisão de passes"""
        if not accurate or not total:
            return None
        try:
            acc = int(accurate) if isinstance(accurate, str) else accurate
            tot = int(total) if isinstance(total, str) else total
            if tot > 0:
                return (acc / tot) * 100
            return None
        except (ValueError, TypeError):
            return None
