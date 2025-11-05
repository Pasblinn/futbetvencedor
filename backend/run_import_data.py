#!/usr/bin/env python3
"""
🧠 PIPELINE COMPLETO - IMPORTAÇÃO + ML

Script para rodar TODOS os jobs automáticos incluindo o ML (cérebro do projeto)
"""
import logging
from app.core.database import get_db_session
from app.services.automated_pipeline import automated_pipeline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Executa pipeline completo: importação, atualização e ML"""

    print("\n" + "="*80)
    print("🧠 PIPELINE COMPLETO - DADOS + MACHINE LEARNING")
    print("="*80 + "\n")

    db = get_db_session()

    try:
        # Job 1: Importar jogos dos próximos 7 dias
        print("\n📥 [1/5] IMPORTANDO JOGOS DOS PRÓXIMOS 7 DIAS...")
        print("-" * 80)
        stats = automated_pipeline.import_upcoming_matches(db, days=7)
        print(f"""
✅ IMPORTAÇÃO CONCLUÍDA:
   - Dias processados: {stats['days_processed']}
   - Jogos importados: {stats['total_imported']}
   - Jogos atualizados: {stats['total_updated']}
   - Erros: {stats['errors']}
        """)

        # Job 2: Atualizar jogos ao vivo
        print("\n🔴 [2/5] ATUALIZANDO JOGOS AO VIVO...")
        print("-" * 80)
        stats = automated_pipeline.update_live_matches(db)
        print(f"""
✅ ATUALIZAÇÃO LIVE CONCLUÍDA:
   - Jogos ao vivo encontrados: {stats['live_matches_found']}
   - Jogos atualizados: {stats['updated']}
   - Jogos finalizados: {stats['finished']}
   - Erros: {stats['errors']}
        """)

        # Job 3: Limpar jogos finalizados
        print("\n🧹 [3/5] LIMPANDO JOGOS FINALIZADOS...")
        print("-" * 80)
        stats = automated_pipeline.cleanup_finished_matches_from_predictions(db)
        print(f"""
✅ LIMPEZA CONCLUÍDA:
   - Jogos limpos: {stats['matches_cleaned']}
   - Predictions resolvidas: {stats['predictions_resolved']}
        """)

        # Job 4: Normalizar nomes de ligas
        print("\n🏆 [4/5] NORMALIZANDO NOMES DE LIGAS...")
        print("-" * 80)
        stats = automated_pipeline.normalize_league_names(db)
        print(f"""
✅ NORMALIZAÇÃO CONCLUÍDA:
   - Jogos normalizados: {stats['leagues_normalized']}
        """)

        # Job 5: GERAR PREDICTIONS COM ML (CÉREBRO DO PROJETO!)
        print("\n🧠 [5/5] GERANDO PREDICTIONS COM MACHINE LEARNING...")
        print("-" * 80)
        print("⚡ Ativando modelos de ML para análise preditiva...")
        stats = automated_pipeline.generate_predictions_for_new_matches(db)
        print(f"""
✅ PREDICTIONS ML GERADAS:
   - Jogos processados: {stats['matches_processed']}
   - Predictions criadas: {stats['predictions_created']}
   - Erros: {stats['errors']}
        """)

    except Exception as e:
        print(f"\n❌ ERRO NO PIPELINE: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

    print("\n" + "="*80)
    print("✅ PIPELINE COMPLETO EXECUTADO!")
    print("🧠 Machine Learning processou todos os novos jogos")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
