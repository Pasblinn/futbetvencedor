#!/usr/bin/env python3
"""
🧪 TESTE SIMPLES - Executar todo o pipeline manualmente
"""
from datetime import datetime
from app.services.automated_pipeline import (
    run_import_upcoming_matches,
    run_generate_predictions,
    run_ai_batch_analysis,
    run_cleanup_finished
)
from app.services.results_updater import run_results_update
from app.core.database import get_db_session

print("=" * 80)
print("🧪 TESTE COMPLETO DO PIPELINE")
print("=" * 80)
print(f"⏰ Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")

# 1. Import upcoming matches
print("📥 PASSO 1/5: Importando jogos...")
print("-" * 80)
import_stats = run_import_upcoming_matches()
print(f"✅ Importados: {import_stats['total_imported']}")
print(f"✅ Atualizados: {import_stats['total_updated']}\n")

# 2. Generate predictions
print("🧠 PASSO 2/5: Gerando predictions ML...")
print("-" * 80)
pred_stats = run_generate_predictions()
print(f"✅ Criadas: {pred_stats['predictions_created']}\n")

# 3. AI analysis
print("🤖 PASSO 3/5: Análise AI Agent...")
print("-" * 80)
ai_stats = run_ai_batch_analysis()
print(f"✅ Analisadas: {ai_stats['analyzed']}\n")

# 4. Update results
print("🔄 PASSO 4/5: Atualizando resultados...")
print("-" * 80)
db = get_db_session()
results_stats = run_results_update(db)
db.close()
print(f"✅ Atualizados: {results_stats['results_updated']}")
print(f"🟢 GREENS: {results_stats['greens']}")
print(f"🔴 REDS: {results_stats['reds']}\n")

# 5. Cleanup
print("🧹 PASSO 5/5: Limpeza...")
print("-" * 80)
cleanup_stats = run_cleanup_finished()
print(f"✅ Resolvidas: {cleanup_stats['predictions_resolved']}\n")

print("=" * 80)
print("✅ TESTE CONCLUÍDO!")
print("=" * 80)
print(f"\n📊 RESUMO:")
print(f"   📥 Jogos: {import_stats['total_imported']} novos, {import_stats['total_updated']} atualizados")
print(f"   🧠 Predictions: {pred_stats['predictions_created']} criadas")
print(f"   🤖 AI: {ai_stats['analyzed']} analisadas")
print(f"   🟢 GREENS: {results_stats['greens']}")
print(f"   🔴 REDS: {results_stats['reds']}")
print(f"\n⏰ Fim: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
print("=" * 80)
