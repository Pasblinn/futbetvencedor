#!/usr/bin/env python3
"""
🔄 ATUALIZAÇÃO MANUAL COMPLETA DO SISTEMA

Executa todos os processos em sequência:
1. Importação de jogos dos próximos 7 dias
2. Geração de predictions ML
3. Análise AI Agent
4. Atualização de resultados finalizados
"""
from app.services.automated_pipeline import (
    run_import_upcoming_matches,
    run_generate_predictions,
    run_ai_batch_analysis,
    run_cleanup_finished
)
from app.services.results_updater import run_results_update
from app.core.database import get_db_session

print("=" * 80)
print("🔄 ATUALIZAÇÃO MANUAL COMPLETA DO SISTEMA")
print("=" * 80)

# Step 1: Import matches
print("\n📥 PASSO 1/5: Importando jogos dos próximos 7 dias...")
print("-" * 80)
import_stats = run_import_upcoming_matches()
print(f"""
✅ Importação concluída:
   - Dias processados: {import_stats['days_processed']}
   - Jogos importados: {import_stats['total_imported']}
   - Jogos atualizados: {import_stats['total_updated']}
   - Erros: {import_stats['errors']}
""")

# Step 2: Generate predictions
print("\n🧠 PASSO 2/5: Gerando predictions ML...")
print("-" * 80)
pred_stats = run_generate_predictions()
print(f"""
✅ Predictions geradas:
   - Jogos processados: {pred_stats['matches_processed']}
   - Predictions criadas: {pred_stats['predictions_created']}
   - Erros: {pred_stats['errors']}
""")

# Step 3: AI Agent analysis
print("\n🤖 PASSO 3/5: Análise AI Agent...")
print("-" * 80)
ai_stats = run_ai_batch_analysis()
print(f"""
✅ Análise AI concluída:
   - Predictions analisadas: {ai_stats['analyzed']}
   - Puladas: {ai_stats['skipped']}
   - Erros: {ai_stats['errors']}
   - AI disponível: {ai_stats['ai_available']}
""")

# Step 4: Update results
print("\n🔄 PASSO 4/5: Atualizando resultados de jogos finalizados...")
print("-" * 80)
db = get_db_session()
try:
    results_stats = run_results_update(db)
    print(f"""
✅ Resultados atualizados:
   - Jogos verificados: {results_stats['total_matches_checked']}
   - Resultados atualizados: {results_stats['results_updated']}
   - 🟢 GREENS: {results_stats['greens']}
   - 🔴 REDS: {results_stats['reds']}
""")
finally:
    db.close()

# Step 5: Cleanup finished
print("\n🧹 PASSO 5/5: Limpando jogos finalizados...")
print("-" * 80)
cleanup_stats = run_cleanup_finished()
print(f"""
✅ Limpeza concluída:
   - Jogos limpos: {cleanup_stats['matches_cleaned']}
   - Predictions resolvidas: {cleanup_stats['predictions_resolved']}
""")

print("\n" + "=" * 80)
print("✅ ATUALIZAÇÃO COMPLETA FINALIZADA!")
print("=" * 80)
print("\n📊 RESUMO GERAL:")
print(f"   📥 Jogos importados: {import_stats['total_imported']}")
print(f"   🧠 Predictions criadas: {pred_stats['predictions_created']}")
print(f"   🤖 Análises AI: {ai_stats['analyzed']}")
print(f"   🟢 GREENS: {results_stats['greens']}")
print(f"   🔴 REDS: {results_stats['reds']}")
print("=" * 80)
