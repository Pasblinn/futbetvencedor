"""
🔍 SCRIPT DE DIAGNÓSTICO COMPLETO DO PIPELINE ML

Verifica:
1. Predictions geradas vs esperadas
2. Resultados GREEN/RED disponíveis
3. Sistema de retraining funcionando
4. Odds disponíveis vs odds mock
5. Força geração de predictions para teste
6. Analisa logs e estatísticas

Uso:
    python test_ml_pipeline.py
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from sqlalchemy import create_engine, func, and_, or_
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from app.models import Prediction, Match, Odds, BetCombination
from app.services.ml_prediction_generator import MLPredictionGenerator, run_daily_ml_prediction_generation
from app.services.automated_ml_retraining import automated_ml_retraining
import json

# Database connection
DATABASE_URL = f"sqlite:///{backend_path}/football_analytics.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def print_section(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def check_predictions_generated():
    """Verifica quantas predictions foram geradas"""
    print_section("📊 ANÁLISE DE PREDICTIONS GERADAS")

    db = SessionLocal()

    # Total de predictions
    total = db.query(Prediction).count()
    print(f"✅ Total de predictions no banco: {total}")

    # Por tipo
    by_type = db.query(
        Prediction.prediction_type,
        func.count(Prediction.id)
    ).group_by(Prediction.prediction_type).all()

    print("\n📈 Distribuição por tipo:")
    for pred_type, count in by_type:
        percentage = (count / total * 100) if total > 0 else 0
        print(f"  - {pred_type}: {count} ({percentage:.1f}%)")

    # Predictions dos últimos 7 dias
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent = db.query(Prediction).filter(
        Prediction.created_at >= week_ago
    ).count()
    print(f"\n📅 Predictions dos últimos 7 dias: {recent}")

    # Meta diária (4500)
    daily_average = recent / 7 if recent > 0 else 0
    print(f"📊 Média diária: {daily_average:.0f} (meta: 4500)")

    if daily_average < 4500:
        print(f"⚠️  ALERTA: Gerando apenas {(daily_average/4500*100):.1f}% da meta!")

    db.close()
    return total, recent

def check_green_red_results():
    """Verifica quantas predictions têm resultados GREEN/RED"""
    print_section("🎯 ANÁLISE DE RESULTADOS GREEN/RED")

    db = SessionLocal()

    # Total com resultado (is_winner não é None)
    with_result = db.query(Prediction).filter(
        Prediction.is_winner.isnot(None)
    ).count()

    total = db.query(Prediction).count()
    percentage = (with_result / total * 100) if total > 0 else 0

    print(f"✅ Predictions com resultado: {with_result} de {total} ({percentage:.1f}%)")

    # Distribuição GREEN vs RED
    green_count = db.query(Prediction).filter(Prediction.is_winner == True).count()
    red_count = db.query(Prediction).filter(Prediction.is_winner == False).count()

    if with_result > 0:
        green_pct = (green_count / with_result * 100)
        red_pct = (red_count / with_result * 100)
        print(f"\n🟢 GREEN: {green_count} ({green_pct:.1f}%)")
        print(f"🔴 RED: {red_count} ({red_pct:.1f}%)")
        print(f"\n📊 Taxa de acerto: {green_pct:.1f}%")
    else:
        print("\n⚠️  NENHUMA PREDICTION COM RESULTADO!")
        print("   O sistema não pode aprender sem resultados!")

    # Predictions pendentes (sem resultado)
    pending = db.query(Prediction).filter(
        Prediction.is_winner.is_(None)
    ).count()
    print(f"\n⏳ Predictions pendentes (aguardando resultado): {pending}")

    db.close()
    return with_result, green_count, red_count

def check_odds_quality():
    """Verifica qualidade das odds (detecta mocks)"""
    print_section("💰 ANÁLISE DE QUALIDADE DAS ODDS")

    db = SessionLocal()

    total_odds = db.query(Odds).count()
    print(f"✅ Total de odds no banco: {total_odds}")

    # Buscar odds suspeitas (valores muito próximos de 2.91, 3.33, 2.81)
    suspicious = db.query(Odds).filter(
        Odds.market_type == '1X2'
    ).limit(100).all()

    mock_count = 0
    valid_count = 0

    for odd in suspicious:
        try:
            odds_data = odd.odds_data
            if isinstance(odds_data, str):
                odds_data = json.loads(odds_data)

            home = float(odds_data.get('home', 0))
            draw = float(odds_data.get('draw', 0))
            away = float(odds_data.get('away', 0))

            # Detectar padrões mock
            if (abs(home - 2.91) < 0.1 and abs(draw - 3.33) < 0.1 and abs(away - 2.81) < 0.1):
                mock_count += 1
            else:
                valid_count += 1
        except:
            pass

    total_checked = mock_count + valid_count
    if total_checked > 0:
        mock_pct = (mock_count / total_checked * 100)
        print(f"\n🔍 Amostra analisada: {total_checked} odds")
        print(f"⚠️  Odds MOCK detectadas: {mock_count} ({mock_pct:.1f}%)")
        print(f"✅ Odds VÁLIDAS: {valid_count} ({(100-mock_pct):.1f}%)")

        if mock_pct > 20:
            print(f"\n❌ PROBLEMA: {mock_pct:.1f}% das odds são MOCK!")
            print("   Isso indica que a API de odds não está funcionando corretamente.")
    else:
        print("\n⚠️  Não foi possível analisar as odds")

    db.close()
    return mock_count, valid_count

def check_retraining_status():
    """Verifica status do sistema de retraining"""
    print_section("🧠 ANÁLISE DO SISTEMA DE RETRAINING ML")

    # Verificar configuração
    config = automated_ml_retraining.config
    print(f"✅ Configuração do retrainer:")
    print(f"  - Mínimo de samples: {config.get('min_data_samples', 'N/A')}")
    print(f"  - Auto retrain: {config.get('auto_retrain_schedule', 'disabled')}")
    if hasattr(automated_ml_retraining, 'last_check'):
        print(f"  - Última verificação: {automated_ml_retraining.last_check or 'Nunca'}")

    # Verificar se há dados suficientes
    db = SessionLocal()
    ready_for_training = db.query(Prediction).filter(
        Prediction.is_winner.isnot(None)
    ).count()
    db.close()

    print(f"\n📊 Dados disponíveis para treino: {ready_for_training}")
    print(f"   Mínimo necessário: {config['min_data_samples']}")

    if ready_for_training >= config['min_data_samples']:
        print("✅ SISTEMA PRONTO PARA RETRAINING")
    else:
        needed = config['min_data_samples'] - ready_for_training
        print(f"⚠️  Faltam {needed} predictions com resultado para iniciar retraining")

    return ready_for_training

def force_generate_predictions():
    """Força geração de predictions para teste"""
    print_section("🚀 FORÇANDO GERAÇÃO DE PREDICTIONS (TESTE)")

    print("Iniciando geração forçada de predictions...")
    print("Meta: 100 predictions de teste\n")

    try:
        result = run_daily_ml_prediction_generation(target=100)

        print(f"\n✅ Geração concluída:")
        print(f"  - Singles: {result.get('singles', 0)}")
        print(f"  - Doubles (mesmo jogo): {result.get('doubles_same_match', 0)}")
        print(f"  - Trebles (mesmo jogo): {result.get('trebles_same_match', 0)}")
        print(f"  - Quads (mesmo jogo): {result.get('quads_same_match', 0)}")
        print(f"  - Doubles (multi): {result.get('doubles_multi', 0)}")
        print(f"  - Trebles (multi): {result.get('trebles_multi', 0)}")
        print(f"  - Quads (multi): {result.get('quads_multi', 0)}")
        print(f"\n🎯 TOTAL GERADO: {result.get('total', 0)}")

        if result.get('errors', 0) > 0:
            print(f"\n⚠️  Erros encontrados: {result['errors']}")

        return result
    except Exception as e:
        print(f"\n❌ ERRO ao gerar predictions: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_logs():
    """Analisa logs do backend"""
    print_section("📋 ANÁLISE DE LOGS")

    log_file = Path(__file__).parent / "backend.log"

    if not log_file.exists():
        print("⚠️  Arquivo de log não encontrado")
        return

    try:
        with open(log_file, 'r') as f:
            lines = f.readlines()
            last_100 = lines[-100:]

        # Contar eventos importantes
        prediction_generated = sum(1 for line in last_100 if 'prediction' in line.lower() and 'generated' in line.lower())
        errors = sum(1 for line in last_100 if 'ERROR' in line)
        warnings = sum(1 for line in last_100 if 'WARNING' in line or 'WARN' in line)
        retraining = sum(1 for line in last_100 if 'retraining' in line.lower() or 'retrain' in line.lower())

        print(f"📊 Últimas 100 linhas do log:")
        print(f"  - Predictions geradas: {prediction_generated} menções")
        print(f"  - Retraining: {retraining} menções")
        print(f"  - Erros: {errors}")
        print(f"  - Avisos: {warnings}")

        if errors > 10:
            print(f"\n⚠️  MUITOS ERROS NO LOG ({errors})!")
            print("   Últimos erros:")
            error_lines = [line for line in last_100 if 'ERROR' in line]
            for line in error_lines[-5:]:
                print(f"     {line.strip()}")

    except Exception as e:
        print(f"❌ Erro ao ler log: {e}")

def main():
    print("\n🔍 INICIANDO DIAGNÓSTICO COMPLETO DO PIPELINE ML")
    print("="*80)

    # 1. Verificar predictions geradas
    total_preds, recent_preds = check_predictions_generated()

    # 2. Verificar resultados GREEN/RED
    with_result, green, red = check_green_red_results()

    # 3. Verificar qualidade das odds
    mock_odds, valid_odds = check_odds_quality()

    # 4. Verificar sistema de retraining
    ready_samples = check_retraining_status()

    # 5. Analisar logs
    analyze_logs()

    # 6. Forçar geração (opcional - comentar se não quiser)
    # force_result = force_generate_predictions()

    # RESUMO FINAL
    print_section("📋 RESUMO DO DIAGNÓSTICO")

    issues = []

    if recent_preds < (4500 * 7):
        issues.append(f"⚠️  Meta diária não está sendo atingida ({recent_preds/7:.0f}/4500)")

    if with_result == 0:
        issues.append("❌ CRÍTICO: Nenhuma prediction com resultado GREEN/RED!")
    elif with_result < 50:
        issues.append(f"⚠️  Poucos resultados disponíveis ({with_result})")

    if mock_odds > (mock_odds + valid_odds) * 0.2:
        issues.append("❌ Muitas odds MOCK detectadas (>20%)")

    if ready_samples < 20:
        issues.append(f"⚠️  Dados insuficientes para retraining ({ready_samples}/20)")

    if issues:
        print("\n🚨 PROBLEMAS ENCONTRADOS:\n")
        for issue in issues:
            print(f"  {issue}")

        print("\n💡 RECOMENDAÇÕES:")
        if with_result == 0:
            print("  1. Verificar se o results_updater está rodando")
            print("  2. Verificar se há jogos finalizados no banco")
            print("  3. Executar update de resultados manualmente")

        if recent_preds < (4500 * 7):
            print("  1. Verificar se o scheduler está ativo")
            print("  2. Executar geração manual: python test_ml_pipeline.py")
            print("  3. Verificar logs do DataScheduler")

        if mock_odds > 0:
            print("  1. Verificar API de odds (Bet365/API-Football)")
            print("  2. Verificar credenciais da API")
            print("  3. Verificar rate limits")
    else:
        print("\n✅ TUDO FUNCIONANDO PERFEITAMENTE!")
        print(f"  - {total_preds} predictions no banco")
        print(f"  - {with_result} com resultado GREEN/RED")
        print(f"  - {green} GREEN ({green/(with_result or 1)*100:.1f}% de acerto)")
        print(f"  - Sistema de retraining pronto")

    print("\n" + "="*80)
    print("✅ DIAGNÓSTICO COMPLETO!")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
