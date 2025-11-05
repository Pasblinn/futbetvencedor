#!/usr/bin/env python3
"""
🔄 SCRIPT DE VALIDAÇÃO HISTÓRICA DE PREDICTIONS

Valida todas as predictions que têm jogos finalizados
e alimenta o sistema de ML com feedback loop GREEN/RED
"""
import sys
import logging
from app.core.database import get_db_session
from app.services.results_updater import run_historical_validation

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Executa validação histórica"""
    logger.info("=" * 80)
    logger.info("🚀 INICIANDO VALIDAÇÃO HISTÓRICA DE PREDICTIONS")
    logger.info("=" * 80)

    db = get_db_session()

    try:
        stats = run_historical_validation(db)

        logger.info("=" * 80)
        logger.info("✅ VALIDAÇÃO CONCLUÍDA COM SUCESSO!")
        logger.info("=" * 80)
        logger.info(f"📊 Resumo:")
        logger.info(f"   • Matches processados: {stats['matches_processed']}")
        logger.info(f"   • Predictions validadas: {stats['predictions_validated']}")
        logger.info(f"   • 🟢 GREENS: {stats['greens']}")
        logger.info(f"   • 🔴 REDS: {stats['reds']}")

        if stats['predictions_validated'] > 0:
            accuracy = (stats['greens'] / stats['predictions_validated']) * 100
            logger.info(f"   • 🎯 Acurácia: {accuracy:.1f}%")

        if stats['errors']:
            logger.warning(f"   • ⚠️ Erros: {len(stats['errors'])}")
            for error in stats['errors'][:5]:  # Mostrar primeiros 5 erros
                logger.warning(f"      - {error}")

        logger.info("=" * 80)
        logger.info("💾 Dados salvos em: retraining_data/")
        logger.info("🧠 Sistema de ML pronto para retreinar!")
        logger.info("=" * 80)

        return 0

    except Exception as e:
        logger.error(f"❌ ERRO na validação: {e}", exc_info=True)
        return 1

    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
