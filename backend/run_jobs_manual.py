#!/usr/bin/env python3
"""
🔧 EXECUÇÃO MANUAL DE JOBS

Script para rodar jobs automáticos manualmente e popular o DB com dados
"""
import asyncio
import logging
from app.core.database import get_db_session
from app.services.automated_pipeline import (
    run_import_upcoming_matches,
    run_update_live_matches,
    run_generate_predictions,
    run_cleanup_finished,
    run_normalize_leagues
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Executa todos os jobs principais"""

    print("\n" + "="*80)
    print("🤖 EXECUTANDO JOBS AUTOMÁTICOS MANUALMENTE")
    print("="*80 + "\n")

    # Job 1: Importar jogos dos próximos 7 dias
    print("\n📥 [1/5] IMPORTANDO JOGOS DOS PRÓXIMOS 7 DIAS...")
    print("-" * 80)
    try:
        stats = run_import_upcoming_matches(days=7)
        print(f"""
✅ IMPORTAÇÃO CONCLUÍDA:
   - Dias processados: {stats['days_processed']}
   - Jogos importados: {stats['total_imported']}
   - Jogos atualizados: {stats['total_updated']}
   - Erros: {stats['errors']}
        """)
    except Exception as e:
        print(f"❌ Erro na importação: {e}")

    # Job 2: Atualizar jogos ao vivo
    print("\n🔴 [2/5] ATUALIZANDO JOGOS AO VIVO...")
    print("-" * 80)
    try:
        stats = run_update_live_matches()
        print(f"""
✅ ATUALIZAÇÃO LIVE CONCLUÍDA:
   - Jogos ao vivo encontrados: {stats['live_matches_found']}
   - Jogos atualizados: {stats['updated']}
   - Jogos finalizados: {stats['finished']}
   - Erros: {stats['errors']}
        """)
    except Exception as e:
        print(f"❌ Erro na atualização: {e}")

    # Job 3: Limpar jogos finalizados
    print("\n🧹 [3/5] LIMPANDO JOGOS FINALIZADOS...")
    print("-" * 80)
    try:
        stats = run_cleanup_finished()
        print(f"""
✅ LIMPEZA CONCLUÍDA:
   - Jogos limpos: {stats['matches_cleaned']}
   - Predictions resolvidas: {stats['predictions_resolved']}
        """)
    except Exception as e:
        print(f"❌ Erro na limpeza: {e}")

    # Job 4: Normalizar nomes de ligas
    print("\n🏆 [4/5] NORMALIZANDO NOMES DE LIGAS...")
    print("-" * 80)
    try:
        stats = run_normalize_leagues()
        print(f"""
✅ NORMALIZAÇÃO CONCLUÍDA:
   - Ligas normalizadas: {stats['leagues_normalized']}
        """)
    except Exception as e:
        print(f"❌ Erro na normalização: {e}")

    # Job 5: Gerar predictions para novos jogos
    print("\n🧠 [5/5] GERANDO PREDICTIONS PARA NOVOS JOGOS...")
    print("-" * 80)
    try:
        stats = run_generate_predictions()
        print(f"""
✅ PREDICTIONS GERADAS:
   - Jogos processados: {stats['matches_processed']}
   - Predictions criadas: {stats['predictions_created']}
   - Erros: {stats['errors']}
        """)
    except Exception as e:
        print(f"❌ Erro ao gerar predictions: {e}")

    print("\n" + "="*80)
    print("✅ TODOS OS JOBS EXECUTADOS!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
