"""
🔄 GRADUAL POPULATION SERVICE - População gradual e inteligente do banco
Popula o banco respeitando rate limits e priorizando ligas específicas:
- 🇧🇷 Brasileirão (prioridade 1)
- 🇪🇸 La Liga (prioridade 2)
- 🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League
- 🇮🇹 Serie A
- 🇩🇪 Bundesliga
- ⚽ Jogos ao vivo
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db_session
from app.models.team import Team
from app.models.match import Match
from app.services.free_apis_collector import free_apis_collector
from app.services.api_sports_collector import api_sports_collector

logger = logging.getLogger(__name__)

class GradualPopulationService:
    """
    🔄 Serviço de população gradual respeitando rate limits
    """

    def __init__(self):
        self.priority_leagues = {
            # 🇧🇷 Brasil (máxima prioridade)
            'brasileirao': {
                'priority': 1,
                'api_sports_id': 71,  # Série A
                'names': ['Brasileirão', 'Serie A Brasil', 'Brazilian Championship'],
                'country': 'Brazil'
            },
            # 🇪🇸 Espanha
            'la_liga': {
                'priority': 2,
                'api_sports_id': 140,
                'names': ['La Liga', 'Primera Division', 'Spanish La Liga'],
                'country': 'Spain'
            },
            # 🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra
            'premier_league': {
                'priority': 3,
                'api_sports_id': 39,
                'names': ['Premier League', 'English Premier League'],
                'country': 'England'
            },
            # 🇮🇹 Itália
            'serie_a': {
                'priority': 4,
                'api_sports_id': 135,
                'names': ['Serie A', 'Italian Serie A'],
                'country': 'Italy'
            },
            # 🇩🇪 Alemanha
            'bundesliga': {
                'priority': 5,
                'api_sports_id': 78,
                'names': ['Bundesliga', 'German Bundesliga', '1. Fußball-Bundesliga'],
                'country': 'Germany'
            }
        }

        self.rate_limits = {
            'football_data': {'max_per_minute': 10, 'calls': 0, 'reset_time': datetime.now()},
            'api_sports': {'max_per_minute': 100, 'calls': 0, 'reset_time': datetime.now()},
            'sportdb': {'max_per_minute': 30, 'calls': 0, 'reset_time': datetime.now()},
            'openliga': {'max_per_minute': 20, 'calls': 0, 'reset_time': datetime.now()}
        }

    async def populate_gradually(self, target_matches: int = 50) -> Dict:
        """
        🔄 População gradual priorizando ligas específicas
        """
        logger.info(f"🔄 INICIANDO POPULAÇÃO GRADUAL - Meta: {target_matches} jogos")

        results = {
            'start_time': datetime.now().isoformat(),
            'target_matches': target_matches,
            'leagues_processed': {},
            'teams_added': 0,
            'matches_added': 0,
            'live_matches': 0,
            'success': True,
            'errors': []
        }

        try:
            with get_db_session() as session:
                current_matches = session.query(Match).count()
                logger.info(f"📊 Jogos atuais no banco: {current_matches}")

                if current_matches >= target_matches:
                    logger.info(f"✅ Meta já atingida: {current_matches}/{target_matches}")
                    results['matches_added'] = current_matches
                    return results

                needed_matches = target_matches - current_matches
                logger.info(f"🎯 Precisamos de {needed_matches} jogos adicionais")

                # 1. Coletar jogos ao vivo primeiro (alta prioridade)
                if os.getenv('API_SPORTS_KEY'):
                    logger.info("⚡ Usando API-Sports para jogos ao vivo...")
                    api_sports_result = await api_sports_collector.collect_priority_leagues()

                    # Inserir jogos ao vivo
                    for match_data in api_sports_result['live_matches']:
                        try:
                            added = await self._insert_match_safely(session, match_data)
                            if added:
                                results['matches_added'] += 1
                                results['live_matches'] += 1
                        except Exception as e:
                            logger.warning(f"⚠️ Erro inserindo jogo ao vivo: {e}")

                    # Inserir jogos das ligas prioritárias
                    for league_key, league_data in api_sports_result['leagues'].items():
                        for match_data in league_data['matches'][:10]:  # Limite por liga
                            try:
                                added = await self._insert_match_safely(session, match_data)
                                if added:
                                    results['matches_added'] += 1
                            except Exception as e:
                                logger.warning(f"⚠️ Erro inserindo jogo {league_key}: {e}")
                else:
                    live_results = await self._collect_live_matches(session)
                    results['live_matches'] = live_results['matches_added']
                    results['matches_added'] += live_results['matches_added']

                # 2. Se ainda precisamos de mais jogos, usar APIs gratuitas
                if results['matches_added'] < target_matches:
                    logger.info("📡 Coletando mais dados das APIs gratuitas...")

                    # Coletar de todas as APIs gratuitas
                    free_api_result = await free_apis_collector.collect_from_all_free_apis()

                    # Inserir todos os jogos coletados
                    for match_data in free_api_result['all_matches']:
                        if results['matches_added'] >= target_matches:
                            break

                        try:
                            added = await self._insert_match_safely(session, match_data)
                            if added:
                                results['matches_added'] += 1
                        except Exception as e:
                            logger.warning(f"⚠️ Erro inserindo jogo das APIs gratuitas: {e}")

                # 3. Processar ligas por prioridade (fallback)
                for league_key, league_info in sorted(self.priority_leagues.items(),
                                                    key=lambda x: x[1]['priority']):

                    if results['matches_added'] >= target_matches:
                        break

                    logger.info(f"🏆 Processando {league_key} (prioridade {league_info['priority']})")

                    league_results = await self._populate_league(session, league_key, league_info)
                    results['leagues_processed'][league_key] = league_results
                    results['teams_added'] += league_results['teams_added']
                    results['matches_added'] += league_results['matches_added']

                    # Rate limiting entre ligas
                    await asyncio.sleep(1)

                session.commit()

        except Exception as e:
            logger.error(f"❌ Erro na população gradual: {e}")
            results['success'] = False
            results['errors'].append(str(e))

        results['end_time'] = datetime.now().isoformat()
        logger.info(f"✅ População gradual concluída: {results['matches_added']} jogos")

        return results

    async def _collect_live_matches(self, session) -> Dict:
        """
        ⚡ Coletar jogos ao vivo (máxima prioridade)
        """
        logger.info("⚡ Coletando jogos ao vivo...")

        results = {'matches_added': 0, 'teams_added': 0}

        try:
            # Usar API-Sports para jogos ao vivo (se disponível)
            if os.getenv('API_SPORTS_KEY'):
                live_matches = await self._get_live_matches_api_sports()

                for match_data in live_matches[:5]:  # Máximo 5 jogos ao vivo
                    try:
                        added = await self._insert_match_safely(session, match_data)
                        if added:
                            results['matches_added'] += 1
                            logger.info(f"⚡ Jogo ao vivo: {match_data['home_team']['name']} vs {match_data['away_team']['name']}")
                    except Exception as e:
                        logger.warning(f"⚠️ Erro inserindo jogo ao vivo: {e}")

        except Exception as e:
            logger.error(f"❌ Erro coletando jogos ao vivo: {e}")

        return results

    async def _populate_league(self, session, league_key: str, league_info: Dict) -> Dict:
        """
        🏆 Popular uma liga específica
        """
        results = {'matches_added': 0, 'teams_added': 0}

        try:
            # Coletar de múltiplas fontes
            all_matches = []

            # 1. Football-Data.org (se disponível)
            if os.getenv('FOOTBALL_DATA_API_KEY'):
                fd_matches = await self._get_league_matches_football_data(league_key)
                all_matches.extend(fd_matches)

            # 2. API-Sports (se disponível)
            if os.getenv('API_SPORTS_KEY'):
                api_matches = await self._get_league_matches_api_sports(league_info['api_sports_id'])
                all_matches.extend(api_matches)

            # 3. SportDB
            sportdb_matches = await self._get_league_matches_sportdb(league_info['country'])
            all_matches.extend(sportdb_matches)

            # Filtrar duplicatas por nomes dos times
            unique_matches = self._remove_duplicate_matches(all_matches)

            logger.info(f"📊 {league_key}: {len(unique_matches)} jogos únicos coletados")

            # Inserir no banco
            for match_data in unique_matches[:15]:  # Limite por liga
                try:
                    added = await self._insert_match_safely(session, match_data)
                    if added:
                        results['matches_added'] += 1
                except Exception as e:
                    logger.warning(f"⚠️ Erro inserindo jogo {league_key}: {e}")

        except Exception as e:
            logger.error(f"❌ Erro processando liga {league_key}: {e}")

        return results

    async def _insert_match_safely(self, session, match_data: Dict) -> bool:
        """
        🛡️ Inserir jogo no banco de forma segura (evitando duplicatas)
        """
        try:
            home_team_name = match_data['home_team']['name']
            away_team_name = match_data['away_team']['name']
            league = match_data.get('tournament', 'Unknown')

            # 1. Garantir que os times existem
            home_team = await self._get_or_create_team(session, home_team_name)
            away_team = await self._get_or_create_team(session, away_team_name)

            # 2. Verificar se jogo já existe
            existing_match = session.query(Match).filter(
                Match.home_team_id == home_team.id,
                Match.away_team_id == away_team.id,
                Match.league == league
            ).first()

            if existing_match:
                return False  # Jogo já existe

            # 3. Criar external_id único
            external_id = f"{home_team.id}_{away_team.id}_{league}_{datetime.now().timestamp()}"

            # 4. Inserir jogo
            match = Match(
                external_id=external_id,
                home_team_id=home_team.id,
                away_team_id=away_team.id,
                league=league,
                season="2023/24",
                match_date=self._parse_match_date(match_data.get('match_date')),
                status=match_data.get('status', 'SCHEDULED'),
                home_score=match_data.get('home_score'),
                away_score=match_data.get('away_score')
            )

            session.add(match)
            session.flush()  # Para verificar se inserção funcionou

            logger.info(f"✅ Jogo inserido: {home_team_name} vs {away_team_name} ({league})")
            return True

        except IntegrityError as e:
            session.rollback()
            logger.warning(f"⚠️ Jogo duplicado ignorado: {match_data}")
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Erro inserindo jogo: {e}")
            return False

    async def _get_or_create_team(self, session, team_name: str) -> Team:
        """
        👥 Obter ou criar time no banco
        """
        # Buscar time existente
        team = session.query(Team).filter(Team.name == team_name).first()

        if team:
            return team

        # Criar novo time
        team = Team(
            name=team_name,
            country=self._detect_country_from_name(team_name),
            external_id=f"team_{team_name.lower().replace(' ', '_')}_{datetime.now().timestamp()}"
        )

        session.add(team)
        session.flush()

        logger.info(f"👥 Time criado: {team_name}")
        return team

    async def _get_live_matches_api_sports(self) -> List[Dict]:
        """
        ⚡ Buscar jogos ao vivo via API-Sports
        """
        matches = []

        try:
            # Implementar chamada à API-Sports para jogos ao vivo
            # URL: https://api-football-v1.p.rapidapi.com/v3/fixtures?live=all
            pass
        except Exception as e:
            logger.error(f"❌ Erro API-Sports live: {e}")

        return matches

    async def _get_league_matches_football_data(self, league_key: str) -> List[Dict]:
        """
        📡 Buscar jogos via Football-Data.org
        """
        matches = []

        try:
            # Usar o free_apis_collector existente
            api_result = await free_apis_collector._collect_football_data()
            matches = api_result
        except Exception as e:
            logger.error(f"❌ Erro Football-Data {league_key}: {e}")

        return matches

    async def _get_league_matches_api_sports(self, league_id: int) -> List[Dict]:
        """
        🔑 Buscar jogos via API-Sports
        """
        matches = []

        try:
            # Implementar chamada específica para liga
            pass
        except Exception as e:
            logger.error(f"❌ Erro API-Sports liga {league_id}: {e}")

        return matches

    async def _get_league_matches_sportdb(self, country: str) -> List[Dict]:
        """
        🏟️ Buscar jogos via SportDB
        """
        matches = []

        try:
            # Usar o free_apis_collector existente
            api_result = await free_apis_collector._collect_sportdb()
            matches = api_result
        except Exception as e:
            logger.error(f"❌ Erro SportDB {country}: {e}")

        return matches

    def _remove_duplicate_matches(self, matches: List[Dict]) -> List[Dict]:
        """
        🔄 Remover jogos duplicados baseado nos nomes dos times
        """
        seen = set()
        unique_matches = []

        for match in matches:
            home_team = match['home_team']['name']
            away_team = match['away_team']['name']
            match_key = f"{home_team.lower()}_{away_team.lower()}"

            if match_key not in seen:
                seen.add(match_key)
                unique_matches.append(match)

        return unique_matches

    def _parse_match_date(self, date_str) -> datetime:
        """Parse data do jogo"""
        if not date_str:
            return datetime.now()

        try:
            formats = [
                '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d',
                '%d/%m/%Y'
            ]

            for fmt in formats:
                try:
                    return datetime.strptime(str(date_str), fmt)
                except ValueError:
                    continue

            return datetime.now()
        except:
            return datetime.now()

    def _detect_country_from_name(self, team_name: str) -> str:
        """Detectar país do time"""
        team_lower = team_name.lower()

        # Brasil
        if any(keyword in team_lower for keyword in ['flamengo', 'palmeiras', 'corinthians', 'santos', 'são paulo', 'grêmio', 'internacional', 'atlético mg', 'cruzeiro', 'vasco']):
            return 'Brazil'
        # Espanha
        elif any(keyword in team_lower for keyword in ['real madrid', 'barcelona', 'atletico', 'valencia', 'sevilla', 'villarreal', 'real sociedad', 'athletic']):
            return 'Spain'
        # Inglaterra
        elif any(keyword in team_lower for keyword in ['manchester', 'liverpool', 'arsenal', 'chelsea', 'tottenham', 'leicester', 'united', 'city']):
            return 'England'
        # Itália
        elif any(keyword in team_lower for keyword in ['juventus', 'milan', 'inter', 'roma', 'napoli', 'lazio', 'fiorentina', 'atalanta']):
            return 'Italy'
        # Alemanha
        elif any(keyword in team_lower for keyword in ['bayern', 'dortmund', 'schalke', 'leverkusen', 'wolfsburg', 'frankfurt', 'stuttgart']):
            return 'Germany'

        return 'Unknown'

# Instância global
gradual_population_service = GradualPopulationService()