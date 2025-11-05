"""
🧹 SERVIÇO DE LIMPEZA DE PREDICTIONS

Funções para limpar e manter predictions organizadas:
- Remove predictions de jogos cancelados/adiados
- Valida predictions pendentes de jogos já finalizados
- Remove predictions antigas sem jogo correspondente

Criado em: 2025-10-20
Parte da Fase 1 de correções críticas
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models import Match, Prediction
from app.services.results_updater import run_historical_validation

logger = logging.getLogger(__name__)


def cleanup_invalid_predictions(db: Session) -> dict:
    """
    Remove predictions de jogos cancelados, adiados ou muito antigos

    Returns:
        Dict com estatísticas da limpeza
    """
    logger.info("🧹 Iniciando limpeza de predictions inválidas...")

    stats = {
        'cancelled_removed': 0,
        'old_removed': 0,
        'orphaned_removed': 0,
        'total_removed': 0
    }

    try:
        # 1. Remover predictions de jogos CANCELADOS/ADIADOS
        cancelled_statuses = ['CANC', 'PST', 'ABD', 'AWD', 'WO', 'SUSP']

        cancelled_matches = db.query(Match).filter(
            Match.status.in_(cancelled_statuses)
        ).all()

        for match in cancelled_matches:
            count = db.query(Prediction).filter(
                Prediction.match_id == match.id
            ).delete(synchronize_session=False)

            stats['cancelled_removed'] += count

        logger.info(f"   Removidas {stats['cancelled_removed']} predictions de jogos cancelados")

        # 2. Remover predictions ANTIGAS (>30 dias) de jogos não finalizados
        cutoff_date = datetime.now() - timedelta(days=30)

        old_matches_not_finished = db.query(Match).filter(
            and_(
                Match.match_date < cutoff_date,
                Match.status.in_(['NS', 'TBD', 'SCHEDULED'])
            )
        ).all()

        for match in old_matches_not_finished:
            count = db.query(Prediction).filter(
                and_(
                    Prediction.match_id == match.id,
                    Prediction.is_validated == False
                )
            ).delete(synchronize_session=False)

            stats['old_removed'] += count

        logger.info(f"   Removidas {stats['old_removed']} predictions antigas (>30 dias)")

        # 3. Remover predictions ÓRFÃS (sem match correspondente)
        # Buscar todas predictions
        all_predictions = db.query(Prediction.id, Prediction.match_id).all()

        # Verificar quais tem match
        for pred in all_predictions:
            match_exists = db.query(Match).filter(Match.id == pred.match_id).first()

            if not match_exists:
                db.query(Prediction).filter(Prediction.id == pred.id).delete(synchronize_session=False)
                stats['orphaned_removed'] += 1

        if stats['orphaned_removed'] > 0:
            logger.info(f"   Removidas {stats['orphaned_removed']} predictions órfãs")

        # Commit todas as deleções
        db.commit()

        stats['total_removed'] = (
            stats['cancelled_removed'] +
            stats['old_removed'] +
            stats['orphaned_removed']
        )

        logger.info(f"""
        ✅ Limpeza concluída:
        - Predictions de jogos cancelados: {stats['cancelled_removed']}
        - Predictions antigas: {stats['old_removed']}
        - Predictions órfãs: {stats['orphaned_removed']}
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        TOTAL REMOVIDO: {stats['total_removed']}
        """)

        return stats

    except Exception as e:
        logger.error(f"❌ Erro na limpeza de predictions: {e}")
        db.rollback()
        return stats


def validate_pending_predictions_batch(db: Session) -> dict:
    """
    Valida todas predictions pendentes de jogos já finalizados

    Returns:
        Dict com estatísticas da validação
    """
    logger.info("🔄 Validando predictions pendentes de jogos finalizados...")

    try:
        # Contar predictions pendentes com jogo finalizado
        pending_count = db.query(Prediction).join(Match).filter(
            and_(
                Prediction.is_validated == False,
                Match.status == 'FT',
                Match.home_score.isnot(None),
                Match.away_score.isnot(None)
            )
        ).count()

        if pending_count == 0:
            logger.info("   Nenhuma prediction pendente para validar")
            return {'validated': 0, 'greens': 0, 'reds': 0}

        logger.info(f"   Encontradas {pending_count} predictions para validar")

        # Executar validação histórica
        result = run_historical_validation(db)

        logger.info(f"""
        ✅ Validação concluída:
        - Predictions validadas: {result['predictions_validated']}
        - 🟢 GREENS: {result['greens']}
        - 🔴 REDS: {result['reds']}
        """)

        return result

    except Exception as e:
        logger.error(f"❌ Erro na validação de predictions: {e}")
        return {'validated': 0, 'greens': 0, 'reds': 0}


def run_full_cleanup_job(db: Session) -> dict:
    """
    Job completo: Limpeza + Validação

    Returns:
        Dict com estatísticas completas
    """
    logger.info("🧹 Iniciando job completo de limpeza e validação...")

    stats = {
        'cleanup': {},
        'validation': {},
        'timestamp': datetime.now().isoformat()
    }

    try:
        # 1. Limpar predictions inválidas
        stats['cleanup'] = cleanup_invalid_predictions(db)

        # 2. Validar predictions pendentes
        stats['validation'] = validate_pending_predictions_batch(db)

        logger.info(f"""
        ✅ JOB COMPLETO FINALIZADO:

        🧹 LIMPEZA:
        - Total removido: {stats['cleanup']['total_removed']}

        🔄 VALIDAÇÃO:
        - Total validado: {stats['validation'].get('predictions_validated', 0)}
        - 🟢 GREENS: {stats['validation'].get('greens', 0)}
        - 🔴 REDS: {stats['validation'].get('reds', 0)}
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """)

        return stats

    except Exception as e:
        logger.error(f"❌ Erro no job de limpeza completo: {e}")
        return stats


# Função helper para uso no scheduler
def run_cleanup_job_for_scheduler():
    """
    Wrapper para executar job de limpeza pelo scheduler
    """
    from app.core.database import get_db_session

    db = get_db_session()
    try:
        return run_full_cleanup_job(db)
    finally:
        db.close()
