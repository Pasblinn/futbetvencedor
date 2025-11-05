#!/usr/bin/env python3
"""
🎯 SCRIPT DE GERAÇÃO EM MASSA DE PREDICTIONS

Este script gera predictions para todos os jogos futuros usando:
1. Poisson Distribution (50+ mercados)
2. AI Validation (modo automático)
3. Salvamento no banco de dados

Uso:
    python generate_predictions_batch.py [--days 7] [--leagues "Liga1,Liga2"]

Exemplos:
    python generate_predictions_batch.py                          # Próximos 7 dias, todas as ligas
    python generate_predictions_batch.py --days 14                # Próximos 14 dias
    python generate_predictions_batch.py --leagues "Premier League,La Liga"  # Ligas específicas
"""

import sys
import argparse
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import logging

# Setup paths
sys.path.append('/home/pablintadini/mododeus/football-analytics/backend')

from app.core.database import SessionLocal
from app.models import Match, Team, Prediction
from app.services.poisson_service import poisson_service
from app.services.ai_prediction_validator import AIPredictionValidator

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ligas prioritárias (focar apenas nessas)
PRIORITY_LEAGUES = [
    "Brasileirão Série A",
    "Brasileirão Série B",
    "Premier League",
    "La Liga",
    "Serie A",
    "Bundesliga",
    "Ligue 1",
    "UEFA Champions League",
    "UEFA Europa League",
    "Copa Libertadores",
    "Copa Sul-Americana",
    "Copa do Brasil",
    "MLS",
    "World Cup - Qualification South America",  # Eliminatórias
]

# Status de jogos finalizados
FINISHED_STATUSES = ['FT', 'PEN', 'AET']


def get_upcoming_matches(
    db: Session,
    days: int = 7,
    leagues: list = None
) -> list[Match]:
    """
    Busca jogos futuros dos próximos N dias.

    Args:
        db: Database session
        days: Número de dias para buscar (default: 7)
        leagues: Lista de ligas específicas (default: todas as prioritárias)

    Returns:
        Lista de Match objects
    """
    now = datetime.now(timezone.utc)
    future_date = now + timedelta(days=days)

    logger.info(f"🔍 Buscando jogos entre {now.date()} e {future_date.date()}")

    # Filtrar por ligas
    if leagues is None:
        leagues = PRIORITY_LEAGUES

    # Query
    query = db.query(Match).filter(
        and_(
            Match.match_date >= now,
            Match.match_date <= future_date,
            Match.status.in_(['SCHEDULED', 'NS', 'TBD']),  # Não iniciados
            Match.league.in_(leagues)
        )
    ).order_by(Match.match_date.asc())

    matches = query.all()
    logger.info(f"✅ {len(matches)} jogos encontrados")

    return matches


def calculate_team_stats(db: Session, team_id: int, is_home: bool, last_n: int = 10) -> dict:
    """
    Calcula estatísticas de um time (últimos N jogos).

    Args:
        db: Database session
        team_id: ID do time
        is_home: True se calcular jogos em casa, False se fora
        last_n: Número de jogos recentes (default: 10)

    Returns:
        Dict com goals_avg e conceded_avg
    """
    if is_home:
        # Jogos em casa
        matches = db.query(Match).filter(
            Match.home_team_id == team_id,
            Match.status.in_(FINISHED_STATUSES),
            Match.home_score.isnot(None),
            Match.away_score.isnot(None)
        ).order_by(Match.match_date.desc()).limit(last_n).all()

        if not matches:
            return None

        goals_avg = sum(m.home_score for m in matches) / len(matches)
        conceded_avg = sum(m.away_score for m in matches) / len(matches)
    else:
        # Jogos fora
        matches = db.query(Match).filter(
            Match.away_team_id == team_id,
            Match.status.in_(FINISHED_STATUSES),
            Match.home_score.isnot(None),
            Match.away_score.isnot(None)
        ).order_by(Match.match_date.desc()).limit(last_n).all()

        if not matches:
            return None

        goals_avg = sum(m.away_score for m in matches) / len(matches)
        conceded_avg = sum(m.home_score for m in matches) / len(matches)

    return {
        'goals_avg': goals_avg,
        'conceded_avg': conceded_avg,
        'games_count': len(matches)
    }


def generate_predictions_for_match(
    db: Session,
    match: Match,
    ai_validator: AIPredictionValidator = None
) -> dict:
    """
    Gera predictions para uma partida específica.

    Args:
        db: Database session
        match: Match object
        ai_validator: AI Validator instance (opcional)

    Returns:
        Dict com resultado da geração
    """
    try:
        # 1. Buscar times
        home_team = db.query(Team).filter(Team.id == match.home_team_id).first()
        away_team = db.query(Team).filter(Team.id == match.away_team_id).first()

        if not home_team or not away_team:
            return {
                'success': False,
                'error': 'Times não encontrados',
                'match_id': match.id
            }

        # 2. Calcular estatísticas
        home_stats = calculate_team_stats(db, home_team.id, is_home=True, last_n=10)
        away_stats = calculate_team_stats(db, away_team.id, is_home=False, last_n=10)

        if not home_stats or not away_stats:
            return {
                'success': False,
                'error': f'Dados insuficientes (Home: {home_stats is not None}, Away: {away_stats is not None})',
                'match_id': match.id
            }

        # 3. Calcular com Poisson (TODOS os mercados)
        poisson_result = poisson_service.analyze_match(
            home_goals_avg=home_stats['goals_avg'],
            away_goals_avg=away_stats['goals_avg'],
            home_conceded_avg=home_stats['conceded_avg'],
            away_conceded_avg=away_stats['conceded_avg'],
            market_odds=None,
            league_avg=2.7
        )

        # 4. Focar no mercado 1X2 para salvar no banco (por enquanto)
        prob_home = poisson_result.probabilities.get('HOME_WIN', 0)
        prob_draw = poisson_result.probabilities.get('DRAW', 0)
        prob_away = poisson_result.probabilities.get('AWAY_WIN', 0)

        # Determinar resultado mais provável
        max_prob = max(prob_home, prob_draw, prob_away)
        if max_prob == prob_home:
            predicted_outcome = '1'
            confidence = prob_home
        elif max_prob == prob_draw:
            predicted_outcome = 'X'
            confidence = prob_draw
        else:
            predicted_outcome = '2'
            confidence = prob_away

        # 5. AI Validation (se disponível)
        ai_validated = False
        ai_confidence = None
        ai_reasoning = None

        if ai_validator and confidence >= 0.5:  # Só validar se confiança mínima
            try:
                validation_result = ai_validator.validate_prediction(
                    match_id=match.id,
                    home_team=home_team.name,
                    away_team=away_team.name,
                    league=match.league,
                    market_type='1X2',
                    predicted_outcome=predicted_outcome,
                    ml_confidence=confidence,
                    ml_reasoning=f"Poisson: λ_home={poisson_result.home_lambda:.2f}, λ_away={poisson_result.away_lambda:.2f}",
                    historical_performance={'home_stats': home_stats, 'away_stats': away_stats}
                )

                ai_validated = validation_result['validated']
                ai_confidence = validation_result.get('ai_confidence')
                ai_reasoning = validation_result.get('reasoning')

            except Exception as e:
                logger.warning(f"AI validation failed for match {match.id}: {e}")

        # 6. Salvar prediction no banco
        # Verificar se já existe
        existing = db.query(Prediction).filter(
            Prediction.match_id == match.id,
            Prediction.market_type == '1X2'
        ).first()

        if existing:
            # Atualizar
            existing.predicted_outcome = predicted_outcome
            existing.confidence = confidence
            existing.ai_validated = ai_validated
            existing.ai_confidence = ai_confidence
            existing.reasoning = ai_reasoning or f"Poisson λ_h={poisson_result.home_lambda:.2f} λ_a={poisson_result.away_lambda:.2f}"
            existing.updated_at = datetime.now(timezone.utc)
        else:
            # Criar nova
            new_prediction = Prediction(
                match_id=match.id,
                market_type='1X2',
                predicted_outcome=predicted_outcome,
                confidence=confidence,
                ai_validated=ai_validated,
                ai_confidence=ai_confidence,
                reasoning=ai_reasoning or f"Poisson λ_h={poisson_result.home_lambda:.2f} λ_a={poisson_result.away_lambda:.2f}",
                status='pending',
                created_at=datetime.now(timezone.utc)
            )
            db.add(new_prediction)

        db.commit()

        return {
            'success': True,
            'match_id': match.id,
            'prediction': predicted_outcome,
            'confidence': confidence,
            'ai_validated': ai_validated,
            'total_markets_calculated': len(poisson_result.probabilities)
        }

    except Exception as e:
        logger.error(f"Error generating prediction for match {match.id}: {e}")
        db.rollback()
        return {
            'success': False,
            'error': str(e),
            'match_id': match.id
        }


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Geração em massa de predictions')
    parser.add_argument('--days', type=int, default=7, help='Número de dias futuros (default: 7)')
    parser.add_argument('--leagues', type=str, default=None, help='Ligas específicas separadas por vírgula')
    parser.add_argument('--no-ai', action='store_true', help='Desabilitar validação AI')

    args = parser.parse_args()

    # Processar ligas
    leagues = None
    if args.leagues:
        leagues = [l.strip() for l in args.leagues.split(',')]
    else:
        leagues = PRIORITY_LEAGUES

    logger.info("=" * 80)
    logger.info("🚀 GERAÇÃO EM MASSA DE PREDICTIONS")
    logger.info("=" * 80)
    logger.info(f"📅 Período: Próximos {args.days} dias")
    logger.info(f"🏆 Ligas: {', '.join(leagues[:5])}{'...' if len(leagues) > 5 else ''}")
    logger.info(f"🤖 AI Validation: {'Desabilitada' if args.no_ai else 'Habilitada'}")
    logger.info("=" * 80)

    # Database session
    db = SessionLocal()

    # AI Validator (se habilitado)
    ai_validator = None
    if not args.no_ai:
        try:
            ai_validator = AIPredictionValidator()
            logger.info("✅ AI Validator inicializado")
        except Exception as e:
            logger.warning(f"⚠️ Não foi possível inicializar AI Validator: {e}")

    # Buscar jogos
    matches = get_upcoming_matches(db, days=args.days, leagues=leagues)

    if not matches:
        logger.warning("⚠️ Nenhum jogo encontrado no período especificado")
        db.close()
        return

    # Gerar predictions
    results = {
        'total': len(matches),
        'success': 0,
        'failed': 0,
        'ai_validated': 0
    }

    logger.info(f"\n🎯 Gerando predictions para {len(matches)} jogos...\n")

    for i, match in enumerate(matches, 1):
        logger.info(f"[{i}/{len(matches)}] {match.home_team.name} vs {match.away_team.name} ({match.league})")

        result = generate_predictions_for_match(db, match, ai_validator)

        if result['success']:
            results['success'] += 1
            if result.get('ai_validated'):
                results['ai_validated'] += 1

            logger.info(f"  ✅ Prediction: {result['prediction']} | Conf: {result['confidence']:.2%} | AI: {result.get('ai_validated', False)}")
        else:
            results['failed'] += 1
            logger.error(f"  ❌ Erro: {result.get('error', 'Unknown')}")

    # Resumo final
    logger.info("\n" + "=" * 80)
    logger.info("📊 RESUMO DA GERAÇÃO")
    logger.info("=" * 80)
    logger.info(f"Total de jogos: {results['total']}")
    logger.info(f"✅ Sucesso: {results['success']}")
    logger.info(f"❌ Falhas: {results['failed']}")
    logger.info(f"🤖 Validadas pela AI: {results['ai_validated']}")
    logger.info(f"📈 Taxa de sucesso: {results['success']/results['total']*100:.1f}%")
    logger.info("=" * 80)

    db.close()
    logger.info("\n✅ Script finalizado!")


if __name__ == '__main__':
    main()
