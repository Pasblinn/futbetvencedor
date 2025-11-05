"""
🤖 PIPELINE AUTOMÁTICO COMPLETO
Sistema 100% automático para Docker/hospedagem

Jobs:
- Importar jogos dos próximos 7 dias (4x por dia)
- Atualizar placares ao vivo (a cada 2 min)
- Gerar predictions para novos jogos (a cada 6h)
- Limpar jogos finalizados das predictions (a cada 1h)
- Normalizar nomes de ligas
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.core.database import get_db_session
from app.models import Match, Prediction
from app.services.api_football_service import APIFootballService
from app.ml.ensemble_model import generate_match_predictions

logger = logging.getLogger(__name__)


class AutomatedPipeline:
    """Pipeline completo automatizado"""

    def __init__(self):
        self.api_service = APIFootballService()


    def import_upcoming_matches(self, db: Session, days: int = 7) -> dict:
        """
        Importa jogos dos próximos N dias

        Args:
            days: Número de dias futuros para importar

        Returns:
            Estatísticas da importação
        """
        logger.info(f"📥 Importando jogos dos próximos {days} dias...")

        stats = {
            'days_processed': 0,
            'total_imported': 0,
            'total_updated': 0,
            'errors': 0
        }

        # 🌍 LIGAS PRINCIPAIS MUNDIAIS
        target_leagues = [
            # 🇧🇷 BRASIL
            71,   # Brasileirão Série A
            72,   # Brasileirão Série B
            73,   # Brasileirão Série C
            1322, # Copa do Brasil
            531,  # Campeonato Paulista

            # 🇪🇺 EUROPA - TOP 5
            39,   # Premier League (Inglaterra)
            140,  # La Liga (Espanha)
            135,  # Serie A (Itália)
            78,   # Bundesliga (Alemanha)
            61,   # Ligue 1 (França)

            # 🌎 AMÉRICA DO SUL
            128,  # Liga Profesional (Argentina)
            281,  # Campeonato Uruguaio
            265,  # Primera División (Chile)
            239,  # Categoría Primera A (Colômbia)
            250,  # División Profesional (Paraguai)

            # 🏆 TORNEIOS CONTINENTAIS
            2,    # UEFA Champions League
            3,    # UEFA Europa League
            848,  # UEFA Conference League
            13,   # Copa Libertadores
            11,   # Copa Sul-Americana
        ]

        logger.info(f"🎯 Monitorando {len(target_leagues)} ligas principais")

        # Criar event loop reutilizável
        import asyncio

        async def fetch_all_fixtures():
            """Busca fixtures para todos os dias em uma única sessão async"""
            all_fixtures_by_date = {}
            for day_offset in range(days):
                target_date = datetime.now() + timedelta(days=day_offset)
                date_str = target_date.strftime('%Y-%m-%d')

                try:
                    fixtures = await self.api_service.get_fixtures_by_date(
                        date=date_str,
                        league_ids=target_leagues
                    )
                    all_fixtures_by_date[date_str] = fixtures
                except Exception as e:
                    logger.error(f"Erro ao buscar jogos para {date_str}: {e}")
                    all_fixtures_by_date[date_str] = []

            return all_fixtures_by_date

        # Executar busca async de uma vez
        try:
            all_fixtures_by_date = asyncio.run(fetch_all_fixtures())
        except Exception as e:
            logger.error(f"Erro no event loop: {e}")
            all_fixtures_by_date = {}

        # Processar fixtures de cada dia
        for date_str, fixtures in all_fixtures_by_date.items():
            logger.info(f"📅 Processando data: {date_str}")
            logger.info(f"📥 {len(fixtures)} fixtures encontrados para {date_str}")

            if not fixtures:
                stats['days_processed'] += 1
                continue

            for fixture in fixtures:
                try:
                    # Pegar league_id do fixture
                    league_id = fixture.get('league', {}).get('id')

                    # Verificar se já existe
                    existing = db.query(Match).filter(
                        Match.external_id == str(fixture['fixture']['id'])
                    ).first()

                    if existing:
                        # Atualizar se mudou algo
                        if existing.status != fixture['fixture']['status']['short']:
                            existing.status = fixture['fixture']['status']['short']
                            stats['total_updated'] += 1
                    else:
                        # Criar novo jogo
                        self._create_match_from_fixture(db, fixture, league_id)
                        stats['total_imported'] += 1

                except Exception as e:
                    logger.error(f"Erro ao processar fixture {fixture.get('fixture', {}).get('id')}: {e}")
                    stats['errors'] += 1

            db.commit()
            stats['days_processed'] += 1

        logger.info(f"""
        ✅ Importação concluída:
        - Dias processados: {stats['days_processed']}
        - Jogos importados: {stats['total_imported']}
        - Jogos atualizados: {stats['total_updated']}
        - Erros: {stats['errors']}
        """)

        return stats


    def _create_match_from_fixture(self, db: Session, fixture: dict, league_id: int):
        """Cria um jogo no DB a partir de fixture da API"""
        from app.models.team import Team

        # Buscar ou criar times
        home_team = self._get_or_create_team(
            db,
            fixture['teams']['home']['id'],
            fixture['teams']['home']['name']
        )

        away_team = self._get_or_create_team(
            db,
            fixture['teams']['away']['id'],
            fixture['teams']['away']['name']
        )

        # Criar jogo
        match = Match(
            external_id=str(fixture['fixture']['id']),
            league=fixture.get('league', {}).get('name', 'Unknown'),
            home_team_id=home_team.id,
            away_team_id=away_team.id,
            match_date=datetime.fromisoformat(fixture['fixture']['date'].replace('Z', '+00:00')),
            status=fixture['fixture']['status']['short'],
            home_score=fixture['goals']['home'],
            away_score=fixture['goals']['away']
        )

        db.add(match)


    def _get_or_create_team(self, db: Session, api_id: int, name: str):
        """Busca ou cria um time"""
        from app.models.team import Team

        team = db.query(Team).filter(Team.external_id == str(api_id)).first()

        if not team:
            team = Team(
                external_id=str(api_id),
                name=name
            )
            db.add(team)
            db.flush()

        return team


    def update_live_matches(self, db: Session) -> dict:
        """
        Atualiza placares de jogos ao vivo

        Returns:
            Estatísticas da atualização
        """
        logger.info("🔴 Atualizando jogos ao vivo...")

        stats = {
            'live_matches_found': 0,
            'updated': 0,
            'finished': 0,
            'errors': 0
        }

        # Buscar jogos que deveriam estar ao vivo (entre 2h antes e 3h depois do horário)
        now = datetime.utcnow()
        window_start = now - timedelta(hours=2)
        window_end = now + timedelta(hours=3)

        potential_live = db.query(Match).filter(
            and_(
                Match.match_date.between(window_start, window_end),
                Match.status.in_(['NS', '1H', '2H', 'HT', 'LIVE'])
            )
        ).all()

        logger.info(f"🔍 {len(potential_live)} jogos potencialmente ao vivo")

        for match in potential_live:
            try:
                # Buscar status atualizado da API
                import asyncio
                fixture_data = asyncio.run(self.api_service.get_fixture_by_id(int(match.external_id)))

                if not fixture_data:
                    continue

                old_status = match.status
                new_status = fixture_data['fixture']['status']['short']

                # Atualizar status
                match.status = new_status

                # Atualizar placar
                if fixture_data['goals']['home'] is not None:
                    match.home_score = fixture_data['goals']['home']
                if fixture_data['goals']['away'] is not None:
                    match.away_score = fixture_data['goals']['away']

                # Marcar tempo decorrido
                if 'elapsed' in fixture_data['fixture']['status']:
                    match.elapsed_time = fixture_data['fixture']['status']['elapsed']

                if new_status in ['1H', '2H', 'HT']:
                    stats['live_matches_found'] += 1
                    stats['updated'] += 1
                    logger.info(f"🔴 LIVE: {match.home_team.name if match.home_team else '?'} {match.home_score}-{match.away_score} {match.away_team.name if match.away_team else '?'} [{new_status}]")

                elif new_status == 'FT' and old_status != 'FT':
                    stats['finished'] += 1
                    logger.info(f"✅ FINALIZADO: {match.home_team.name if match.home_team else '?'} {match.home_score}-{match.away_score} {match.away_team.name if match.away_team else '?'}")

                db.commit()

            except Exception as e:
                logger.error(f"Erro ao atualizar jogo {match.id}: {e}")
                stats['errors'] += 1
                db.rollback()

        logger.info(f"✅ Atualização live concluída: {stats['live_matches_found']} ao vivo, {stats['finished']} finalizados")

        return stats


    def generate_predictions_for_new_matches(self, db: Session) -> dict:
        """
        Gera predictions para jogos que ainda não têm - V3 CORRIGIDA (2025-10-20)
        Usa MLPredictionGenerator com seleção inteligente de outcomes

        Returns:
            Estatísticas da geração
        """
        logger.info("🧠 Gerando predictions ML v3 para novos jogos...")

        stats = {
            'matches_processed': 0,
            'predictions_created': 0,
            'errors': 0
        }

        # Buscar jogos futuros sem prediction
        future_matches = db.query(Match).filter(
            and_(
                Match.match_date > datetime.utcnow(),
                Match.status.in_(['NS', 'TBD', 'SCHEDULED']),
                ~Match.predictions.any()  # Não tem predictions
            )
        ).limit(50).all()  # Processar em lotes de 50

        logger.info(f"📊 {len(future_matches)} jogos sem predictions")

        for match in future_matches:
            try:
                # Gerar predictions usando ML v3
                prediction_data = generate_match_predictions(db, match.id)

                if prediction_data:
                    # ML v3 retorna múltiplas predictions (all_predictions)
                    all_preds = prediction_data.get('all_predictions', [])

                    if all_preds:
                        # Criar uma Prediction no DB para CADA market que passou nos thresholds
                        for pred_dict in all_preds:
                            market_type = pred_dict.get('market_type')
                            probs = pred_dict.get('probabilities', {})

                            # Criar Prediction no DB
                            prediction = Prediction(
                                match_id=match.id,
                                prediction_type='SINGLE',
                                market_type=market_type,  # HOME_WIN, DRAW, AWAY_WIN, BTTS_YES, etc
                                predicted_outcome=market_type,  # Usar market_type como outcome
                                predicted_probability=pred_dict.get('predicted_probability', 0.5),  # 🔥 BUG FIX (2025-10-21)
                                confidence_score=pred_dict.get('confidence_score', 0.5),
                                probability_home=probs.get('home_win', 0.33),
                                probability_draw=probs.get('draw', 0.33),
                                probability_away=probs.get('away_win', 0.33),
                                model_version='ml_generator_v3',
                                analysis_summary=f"ML v3: {market_type} - Edge: {pred_dict.get('value_edge', 0):.1%}",
                                key_factors=[f"Confidence: {pred_dict.get('confidence_score', 0)*100:.1f}%"]
                            )

                            db.add(prediction)
                            stats['predictions_created'] += 1

                        logger.info(f"✅ {len(all_preds)} predictions criadas para: {match.home_team.name if match.home_team else '?'} vs {match.away_team.name if match.away_team else '?'}")
                    else:
                        logger.debug(f"Match {match.id}: Nenhuma prediction passou nos thresholds v3")

                stats['matches_processed'] += 1

            except Exception as e:
                logger.error(f"Erro ao gerar prediction para jogo {match.id}: {e}")
                import traceback
                traceback.print_exc()
                stats['errors'] += 1

        db.commit()

        logger.info(f"✅ Predictions ML v3 geradas: {stats['predictions_created']} para {stats['matches_processed']} jogos")

        # 🎯 CRIAR COMBINAÇÕES INTELIGENTES (Doubles, Trebles, Multiples)
        if stats['predictions_created'] > 0:
            combo_stats = self._create_intelligent_combinations(db)
            stats['combinations_created'] = combo_stats
            logger.info(f"✅ Combinações criadas: {combo_stats['total']} (Doubles: {combo_stats['doubles']}, Trebles: {combo_stats['trebles']}, Multiples: {combo_stats['multiples']})")

        return stats


    def _create_intelligent_combinations(self, db: Session) -> dict:
        """
        🎯 CRIAR COMBINAÇÕES INTELIGENTES A PARTIR DOS SINGLES V3

        Proporção alvo:
        - 5% Singles
        - 80% Doubles/Trebles
        - 15% Multiples (4+)

        Estratégia:
        1. Manter apenas melhores singles (confidence > 70%)
        2. Criar doubles com jogos diferentes (evitar correlação)
        3. Criar trebles balanceados (high + medium confidence)
        4. Criar multiples selecionados (4-5 jogos, confidence médio > 65%)
        """
        import itertools
        from datetime import timedelta

        logger.info("🎯 Criando combinações inteligentes a partir dos singles v3...")

        stats = {
            'doubles': 0,
            'trebles': 0,
            'multiples': 0,
            'total': 0
        }

        # Buscar singles v3 não validados COM MATCHES FUTUROS (NS)
        from app.models import Match

        singles = db.query(Prediction).join(Match).filter(
            and_(
                Prediction.model_version == 'ml_generator_v3',
                Prediction.prediction_type == 'SINGLE',
                Prediction.is_validated == False,
                Match.status == 'NS'  # 🔥 APENAS JOGOS FUTUROS
            )
        ).all()

        if len(singles) < 2:
            logger.info("⚠️ Menos de 2 singles - não é possível criar combinações")
            return stats

        logger.info(f"📊 {len(singles)} singles disponíveis para combinações")

        # Filtrar por confidence para combinações (> 55%)
        good_singles = [s for s in singles if s.confidence_score and s.confidence_score > 0.55]

        if len(good_singles) < 2:
            logger.info("⚠️ Menos de 2 singles com confidence > 55%")
            return stats

        # 🎯 ESTRATÉGIA: Criar proporção correta
        # v6.0: Ajustado para funcionar com poucos singles
        total_singles = len(singles)

        # Se temos < 10 singles, manter todos e criar máximo de combinações
        # Se temos >= 10 singles, aplicar proporção 5%/80%/15%
        if total_singles < 10:
            keep_singles = total_singles  # Manter todos
            # Calcular targets baseado em combinações possíveis
            # Para N singles, podemos criar C(N,2) doubles, C(N,3) trebles, etc
            import math
            max_doubles = math.comb(len(good_singles), 2) if len(good_singles) >= 2 else 0
            max_trebles = math.comb(len(good_singles), 3) if len(good_singles) >= 3 else 0
            max_multiples = math.comb(len(good_singles), 4) if len(good_singles) >= 4 else 0

            # Target: criar todas as combinações possíveis (ou limitar a 3x o número de singles)
            target_doubles = min(max_doubles, total_singles * 3)
            logger.info(f"   Poucos singles ({total_singles}) - mantendo todos e criando máximo de combos")
        else:
            # Proporção normal: 5% singles, 80% doubles+trebles, 15% multiples
            keep_singles = max(1, int(total_singles * 0.05))
            target_doubles = int(total_singles * 0.65)  # 65% do total
            logger.info(f"   Aplicando proporção 5%/80%/15%")

        # Ordenar por confidence e manter apenas os melhores
        singles_sorted = sorted(good_singles, key=lambda x: x.confidence_score, reverse=True)
        combo_pool = good_singles  # Usar todos para combinações

        logger.info(f"   Singles finais: {total_singles}")
        logger.info(f"   Pool para combinações: {len(combo_pool)}")
        logger.info(f"   Target doubles: {target_doubles}")

        # 🎲 CRIAR DOUBLES (2 jogos)

        doubles_created = 0
        for combo in itertools.combinations(combo_pool, 2):
            if doubles_created >= target_doubles:
                break

            pred1, pred2 = combo

            # Evitar mesmo jogo
            if pred1.match_id == pred2.match_id:
                continue

            # Calcular probabilidade combinada
            combined_prob = pred1.predicted_probability * pred2.predicted_probability if (pred1.predicted_probability and pred2.predicted_probability) else 0.5
            combined_conf = (pred1.confidence_score + pred2.confidence_score) / 2

            # Criar double
            double = Prediction(
                match_id=pred1.match_id,  # Usar primeiro jogo como referência
                prediction_type='DOUBLE',
                market_type=f"{pred1.market_type} + {pred2.market_type}",
                predicted_outcome=f"{pred1.predicted_outcome} + {pred2.predicted_outcome}",
                predicted_probability=combined_prob,
                confidence_score=combined_conf,
                model_version='ml_generator_v3_combo',
                analysis_summary=f"Double: Match {pred1.match_id} + {pred2.match_id}",
                key_factors=[
                    f"Pred1: {pred1.market_type} ({pred1.confidence_score*100:.1f}%)",
                    f"Pred2: {pred2.market_type} ({pred2.confidence_score*100:.1f}%)"
                ]
            )

            db.add(double)
            doubles_created += 1

        stats['doubles'] = doubles_created

        # 🎲 CRIAR TREBLES (3 jogos)
        # v6.0: Ajustado para poucos singles
        if total_singles < 10:
            target_trebles = min(max_trebles, max(1, total_singles // 2)) if total_singles >= 3 else 0
        else:
            target_trebles = max(1, int(total_singles * 0.15))  # 15% do total

        logger.info(f"   Target trebles: {target_trebles}")

        trebles_created = 0
        for combo in itertools.combinations(combo_pool, 3):
            if trebles_created >= target_trebles:
                break

            pred1, pred2, pred3 = combo

            # Evitar jogos repetidos
            match_ids = {pred1.match_id, pred2.match_id, pred3.match_id}
            if len(match_ids) < 3:
                continue

            # Calcular probabilidade e confidence combinados
            combined_prob = (pred1.predicted_probability * pred2.predicted_probability * pred3.predicted_probability) if all([pred1.predicted_probability, pred2.predicted_probability, pred3.predicted_probability]) else 0.4
            combined_conf = (pred1.confidence_score + pred2.confidence_score + pred3.confidence_score) / 3

            # Filtrar: confidence médio > 60%
            if combined_conf < 0.60:
                continue

            # Criar treble
            treble = Prediction(
                match_id=pred1.match_id,
                prediction_type='TREBLE',
                market_type=f"{pred1.market_type} + {pred2.market_type} + {pred3.market_type}",
                predicted_outcome=f"{pred1.predicted_outcome} + {pred2.predicted_outcome} + {pred3.predicted_outcome}",
                predicted_probability=combined_prob,
                confidence_score=combined_conf,
                model_version='ml_generator_v3_combo',
                analysis_summary=f"Treble: Matches {pred1.match_id}, {pred2.match_id}, {pred3.match_id}",
                key_factors=[
                    f"Avg confidence: {combined_conf*100:.1f}%",
                    f"Combined prob: {combined_prob*100:.1f}%"
                ]
            )

            db.add(treble)
            trebles_created += 1

        stats['trebles'] = trebles_created

        # 🎲 CRIAR MULTIPLES (4+ jogos)
        # v6.0: Ajustado para poucos singles
        if total_singles < 10:
            target_multiples = min(max_multiples, max(1, total_singles // 3)) if total_singles >= 4 else 0
        else:
            target_multiples = max(1, int(total_singles * 0.15))  # 15% do total

        logger.info(f"   Target multiples: {target_multiples}")

        multiples_created = 0

        # Só criar multiples se tiver pelo menos 4 singles bons
        if len(combo_pool) >= 4:
            for combo in itertools.combinations(combo_pool, 4):
                if multiples_created >= target_multiples:
                    break

                # Verificar jogos únicos
                match_ids = {p.match_id for p in combo}
                if len(match_ids) < 4:
                    continue

                # Calcular métricas
                combined_prob = 1.0
                for p in combo:
                    if p.predicted_probability:
                        combined_prob *= p.predicted_probability

                combined_conf = sum(p.confidence_score for p in combo) / len(combo)

                # Filtrar: confidence médio > 65% para quads
                if combined_conf < 0.65:
                    continue

                # Criar multiple
                markets_str = " + ".join(p.market_type for p in combo)
                outcomes_str = " + ".join(p.predicted_outcome for p in combo)
                matches_str = ", ".join(str(p.match_id) for p in combo)

                multiple = Prediction(
                    match_id=combo[0].match_id,
                    prediction_type='MULTIPLE',
                    market_type=markets_str[:200] if len(markets_str) > 200 else markets_str,
                    predicted_outcome=outcomes_str[:200] if len(outcomes_str) > 200 else outcomes_str,
                    predicted_probability=combined_prob,
                    confidence_score=combined_conf,
                    model_version='ml_generator_v3_combo',
                    analysis_summary=f"Quad: Matches {matches_str}",
                    key_factors=[
                        f"4 games combined",
                        f"Avg confidence: {combined_conf*100:.1f}%"
                    ]
                )

                db.add(multiple)
                multiples_created += 1

        stats['multiples'] = multiples_created

        # Commit combinations
        db.commit()

        stats['total'] = doubles_created + trebles_created + multiples_created

        logger.info(f"✅ Combinações criadas: {stats['total']} total")
        logger.info(f"   - Doubles: {doubles_created}")
        logger.info(f"   - Trebles: {trebles_created}")
        logger.info(f"   - Multiples: {multiples_created}")

        return stats


    def cleanup_finished_matches_from_predictions(self, db: Session) -> dict:
        """
        Remove jogos finalizados da lista de upcoming predictions
        Marca predictions como resolvidas

        Returns:
            Estatísticas da limpeza
        """
        logger.info("🧹 Limpando jogos finalizados...")

        stats = {
            'matches_cleaned': 0,
            'predictions_resolved': 0
        }

        # Buscar jogos finalizados com predictions não resolvidas
        finished_with_predictions = db.query(Match).join(Prediction).filter(
            and_(
                Match.status.in_(['FT', 'AET', 'PEN', 'FINISHED']),
                Match.home_score.isnot(None),
                Match.away_score.isnot(None),
                Prediction.actual_outcome.is_(None)  # Ainda não resolvida
            )
        ).all()

        logger.info(f"🔍 {len(finished_with_predictions)} jogos finalizados para resolver")

        for match in finished_with_predictions:
            try:
                # Determinar resultado real
                if match.home_score > match.away_score:
                    actual = '1'
                elif match.home_score < match.away_score:
                    actual = '2'
                else:
                    actual = 'X'

                # Atualizar todas predictions desse jogo
                for prediction in match.predictions:
                    if prediction.actual_outcome is None:
                        prediction.actual_outcome = actual
                        prediction.is_winner = (prediction.predicted_outcome == actual)
                        stats['predictions_resolved'] += 1

                stats['matches_cleaned'] += 1

                logger.info(f"✅ Resolvido: {match.home_team.name if match.home_team else '?'} {match.home_score}-{match.away_score} {match.away_team.name if match.away_team else '?'} = {actual}")

            except Exception as e:
                logger.error(f"Erro ao limpar jogo {match.id}: {e}")

        db.commit()

        logger.info(f"✅ Limpeza concluída: {stats['matches_cleaned']} jogos, {stats['predictions_resolved']} predictions resolvidas")

        return stats


    def normalize_league_names(self, db: Session) -> dict:
        """
        Normaliza nomes de ligas para padronização

        Returns:
            Estatísticas da normalização
        """
        logger.info("🏆 Normalizando nomes de ligas...")

        stats = {
            'leagues_normalized': 0
        }

        # Mapeamento de nomes para normalizar
        normalizations = {
            'Serie A': 'Brasileirão Serie A',
            'Série A': 'Brasileirão Serie A',
            'Brasileirao Serie A': 'Brasileirão Serie A',
            'Serie B': 'Brasileirão Serie B',
            'Série B': 'Brasileirão Serie B',
            'Brasileirao Serie B': 'Brasileirão Serie B',
        }

        for old_name, new_name in normalizations.items():
            # Atualizar jogos com o nome antigo da liga
            matches = db.query(Match).filter(Match.league == old_name).all()

            for match in matches:
                match.league = new_name
                stats['leagues_normalized'] += 1
                logger.info(f"✅ {old_name} → {new_name}")

        db.commit()

        logger.info(f"✅ Normalização concluída: {stats['leagues_normalized']} jogos atualizados")

        return stats


# Instância global
automated_pipeline = AutomatedPipeline()


# Funções helper para uso nos jobs
def run_import_upcoming_matches(days: int = 7):
    """Job: Importar jogos futuros"""
    db = get_db_session()
    try:
        return automated_pipeline.import_upcoming_matches(db, days)
    finally:
        db.close()


def run_update_live_matches():
    """Job: Atualizar jogos ao vivo"""
    db = get_db_session()
    try:
        return automated_pipeline.update_live_matches(db)
    finally:
        db.close()


def run_generate_predictions():
    """Job: Gerar predictions"""
    db = get_db_session()
    try:
        return automated_pipeline.generate_predictions_for_new_matches(db)
    finally:
        db.close()


def run_cleanup_finished():
    """Job: Limpar finalizados"""
    db = get_db_session()
    try:
        return automated_pipeline.cleanup_finished_matches_from_predictions(db)
    finally:
        db.close()


def run_normalize_leagues():
    """Job: Normalizar ligas"""
    db = get_db_session()
    try:
        return automated_pipeline.normalize_league_names(db)
    finally:
        db.close()


def run_ai_batch_analysis():
    """
    🧠 Job: Análise AI em Lote

    Analisa TOP predictions do ML com AI Agent para refinamento contextual
    Executa a cada 12 horas
    """
    from app.services.ai_agent_service import AIAgentService
    from app.services.context_analyzer import get_context_analyzer
    from app.services.few_shot_memory import get_few_shot_memory

    logger.info("🧠 Iniciando análise AI em lote das predictions...")

    db = get_db_session()
    ai_agent = AIAgentService()

    try:
        # Verificar se AI Agent está disponível
        if not ai_agent.is_available():
            logger.warning("⚠️ AI Agent não disponível (Ollama offline). Pulando análise AI.")
            return {
                'analyzed': 0,
                'skipped': 0,
                'errors': 0,
                'ai_available': False
            }

        context_analyzer = get_context_analyzer(db)
        memory = get_few_shot_memory(db)

        # Buscar TOP 100 predictions com maior confidence que ainda não foram analisadas por AI
        # IMPORTANTE: Apenas para jogos FUTUROS (não finalizados)
        from datetime import datetime, timedelta

        # Buscar predictions de QUALQUER fonte (ML ou usuário) que atendem os critérios:
        # 1. Alta confidence (>= 60%)
        # 2. Ainda não analisadas por AI (None ou False)
        # 3. Jogos futuros (não finalizados)
        from sqlalchemy import or_

        top_predictions = db.query(Prediction).join(Match).filter(
            and_(
                Prediction.confidence_score >= 0.60,  # Mínimo 60% de confidence
                Prediction.match_id.isnot(None),
                or_(  # Aceita None ou False (não True)
                    Prediction.ai_analyzed.is_(None),
                    Prediction.ai_analyzed == False
                ),
                Match.match_date >= datetime.now(),  # Jogos FUTUROS apenas
                Match.status.in_(['NS', 'TBD', 'SCHEDULED'])  # Jogos não iniciados
            )
        ).order_by(Prediction.confidence_score.desc()).limit(100).all()

        if not top_predictions:
            logger.info("ℹ️ Nenhuma prediction pendente para análise AI")
            return {
                'analyzed': 0,
                'skipped': 0,
                'errors': 0,
                'ai_available': True
            }

        logger.info(f"📊 {len(top_predictions)} predictions selecionadas para análise AI")

        stats = {
            'analyzed': 0,
            'upgraded': 0,  # Confidence aumentada
            'downgraded': 0,  # Confidence reduzida
            'skipped': 0,
            'errors': 0,
            'ai_available': True
        }

        for prediction in top_predictions:
            try:
                match = prediction.match
                if not match:
                    stats['skipped'] += 1
                    continue

                # Preparar dados do jogo
                match_data = {
                    'match_id': match.id,
                    'home_team': match.home_team.name if match.home_team else 'Unknown',
                    'away_team': match.away_team.name if match.away_team else 'Unknown',
                    'league': match.league,
                    'match_date': match.match_date.isoformat() if match.match_date else None,
                }

                # Preparar prediction ML
                ml_pred = {
                    'predicted_outcome': prediction.predicted_outcome,
                    'confidence': prediction.confidence_score,
                    'probability_home': prediction.probability_home,
                    'probability_draw': prediction.probability_draw,
                    'probability_away': prediction.probability_away,
                    'markets': [prediction.market_type] if prediction.market_type else ['1X2']
                }

                # Análise de contexto
                context_data = context_analyzer.analyze_match_context(match)

                # Few-shot examples
                few_shot_examples = memory.get_learning_examples(limit=10)

                # Executar análise AI
                ai_analysis = ai_agent.analyze_prediction(
                    match_data=match_data,
                    ml_prediction=ml_pred,
                    context_data=context_data,
                    few_shot_examples=few_shot_examples
                )

                # Atualizar prediction com análise AI
                old_confidence = prediction.confidence_score
                new_confidence = ai_analysis.get('adjusted_confidence', old_confidence)

                prediction.confidence_score = new_confidence
                prediction.ai_analysis = ai_analysis.get('explanation', '')
                prediction.ai_recommendation = ai_analysis.get('recommendation', 'MONITOR')
                prediction.ai_risk_level = ai_analysis.get('risk_level', 'MEDIUM')
                prediction.ai_analyzed = True
                prediction.ai_analyzed_at = datetime.now()

                # Estatísticas
                stats['analyzed'] += 1
                if new_confidence > old_confidence:
                    stats['upgraded'] += 1
                elif new_confidence < old_confidence:
                    stats['downgraded'] += 1

                # Commit a cada 10 predictions para evitar perder progresso
                if stats['analyzed'] % 10 == 0:
                    db.commit()
                    logger.info(f"✅ {stats['analyzed']} predictions analisadas...")

            except Exception as e:
                logger.error(f"❌ Erro ao analisar prediction {prediction.id}: {e}")
                stats['errors'] += 1
                continue

        # Commit final
        db.commit()

        logger.info(f"""
        ✅ Análise AI em lote concluída:
        - Analisadas: {stats['analyzed']}
        - Confidence aumentada: {stats['upgraded']}
        - Confidence reduzida: {stats['downgraded']}
        - Puladas: {stats['skipped']}
        - Erros: {stats['errors']}
        """)

        return stats

    except Exception as e:
        logger.error(f"❌ Erro na análise AI em lote: {e}")
        return {
            'analyzed': 0,
            'skipped': 0,
            'errors': 1,
            'ai_available': False,
            'error': str(e)
        }
    finally:
        db.close()


async def run_ml_retraining():
    """
    🤖 Job: ML Retraining Automático

    Retreina modelos ML com resultados GREEN/RED acumulados
    Executa diariamente às 2h da manhã
    """
    from app.services.automated_ml_retraining import AutomatedMLRetraining
    import asyncio

    logger.info("🤖 Iniciando ML Retraining automático...")

    db = get_db_session()

    try:
        # Verificar se há dados suficientes
        results_count = db.query(Prediction).filter(
            Prediction.is_winner.isnot(None)
        ).count()

        min_samples = 20

        if results_count < min_samples:
            logger.info(f"ℹ️ Dados insuficientes para retraining: {results_count}/{min_samples}")
            return {
                'retrained': False,
                'reason': 'insufficient_data',
                'samples_available': results_count,
                'samples_required': min_samples
            }

        logger.info(f"📊 {results_count} resultados disponíveis para treino")

        # Inicializar retraining service
        retraining_service = AutomatedMLRetraining()

        # Retreinar cada modelo
        models_to_train = ['1x2_classifier', 'over_under_classifier', 'btts_classifier']

        stats = {
            'retrained': True,
            'models': {},
            'total_improved': 0,
            'total_samples': results_count
        }

        for model_name in models_to_train:
            try:
                from app.services.automated_ml_retraining import RetrainingTrigger
                from datetime import datetime

                trigger = RetrainingTrigger(
                    trigger_type='schedule',
                    threshold_value=0.0,
                    current_value=0.0,
                    triggered_at=datetime.now(),
                    reason='Daily scheduled retraining'
                )

                # Executar com await (função é async)
                result = await retraining_service.retrain_model(model_name, trigger)

                if result and result.success:
                    improvement = result.improvement * 100
                    logger.info(f"✅ {model_name}: {result.old_accuracy:.1%} → {result.new_accuracy:.1%} ({improvement:+.1f}%)")

                    stats['models'][model_name] = {
                        'improved': result.improvement > 0,
                        'old_accuracy': result.old_accuracy,
                        'new_accuracy': result.new_accuracy,
                        'improvement': result.improvement
                    }

                    if result.improvement > 0:
                        stats['total_improved'] += 1
                else:
                    logger.warning(f"⚠️ {model_name}: Retraining não melhorou performance")
                    stats['models'][model_name] = {
                        'improved': False,
                        'reason': 'no_improvement'
                    }

            except Exception as e:
                logger.error(f"❌ Erro ao retreinar {model_name}: {e}")
                stats['models'][model_name] = {
                    'improved': False,
                    'error': str(e)
                }

        logger.info(f"""
        ✅ ML Retraining concluído:
        - Modelos treinados: {len(models_to_train)}
        - Modelos melhorados: {stats['total_improved']}
        - Samples usados: {results_count}
        """)

        return stats

    except Exception as e:
        logger.error(f"❌ Erro crítico no ML retraining: {e}")
        return {
            'retrained': False,
            'error': str(e)
        }
    finally:
        db.close()


def run_ml_retraining_sync():
    """
    Wrapper síncrono para run_ml_retraining (para uso no scheduler)
    """
    import asyncio
    return asyncio.run(run_ml_retraining())
