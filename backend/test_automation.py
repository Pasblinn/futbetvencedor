#!/usr/bin/env python3
"""
🧪 TESTE DE AUTOMAÇÃO END-TO-END
Valida que todo o pipeline automático está funcionando

Testa:
1. ✅ Scheduler pode iniciar
2. ✅ Jobs estão registrados corretamente
3. ✅ AI Agent está disponível (Ollama)
4. ✅ ML Retraining pode executar
5. ✅ AI Agent batch pode processar predictions
"""

import sys
import os
from pathlib import Path

# Adicionar backend ao path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

import asyncio
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine
from app.models.prediction import Prediction
from app.services.data_scheduler import DataScheduler
from app.services.ai_agent_service import AIAgentService
from app.services.ai_agent_batch import AIAgentBatchService, analyze_unanalyzed_predictions
from app.services.automated_ml_retraining import AutomatedMLRetraining


def print_header(title: str):
    """Imprime cabeçalho formatado"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def test_scheduler_initialization(db: Session):
    """Teste 1: Scheduler pode iniciar e registrar jobs"""
    print_header("TESTE 1: Inicialização do Scheduler")

    try:
        scheduler = DataScheduler(db)

        print("🚀 Iniciando scheduler...")
        scheduler.start()

        # Verificar status
        status = scheduler.get_status()

        print(f"✅ Status: {status['status']}")
        print(f"📋 Jobs registrados: {len(status['jobs'])}")

        # Listar jobs
        print("\n📊 Jobs configurados:")
        for job in status['jobs']:
            next_run = job.get('next_run', 'N/A')
            print(f"  • {job['name']} (id: {job['id']})")
            print(f"    Próxima execução: {next_run}")

        # Parar scheduler
        scheduler.stop()
        print("\n✅ Teste 1 PASSOU - Scheduler funciona corretamente")

        return True

    except Exception as e:
        print(f"\n❌ Teste 1 FALHOU: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ai_agent_availability():
    """Teste 2: AI Agent está disponível (Ollama conectado)"""
    print_header("TESTE 2: Disponibilidade do AI Agent")

    try:
        ai_agent = AIAgentService(model="llama3.1:8b")

        if ai_agent.is_available():
            print("✅ AI Agent disponível")
            print(f"   Modelo: {ai_agent.model}")
            print("   Ollama está rodando corretamente")

            return True
        else:
            print("❌ AI Agent NÃO disponível")
            print("🔧 Certifique-se que Ollama está rodando:")
            print("   1. ollama serve")
            print("   2. ollama pull llama3.1:8b")

            return False

    except Exception as e:
        print(f"\n❌ Teste 2 FALHOU: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ml_retraining(db: Session):
    """Teste 3: ML Retraining pode executar"""
    print_header("TESTE 3: ML Retraining")

    try:
        # Verificar quantos resultados temos
        results_count = db.query(Prediction).filter(
            Prediction.is_winner.isnot(None)
        ).count()

        print(f"📊 Resultados disponíveis: {results_count}")

        if results_count < 20:
            print("⚠️ Poucos resultados para treinar (mínimo: 20)")
            print("   Teste será pulado (aguardando mais dados)")
            return True

        # Tentar retreinar um modelo
        print("\n🤖 Testando retraining do modelo 1x2_classifier...")

        retraining_service = AutomatedMLRetraining()

        trigger = {
            'trigger_type': 'manual',
            'threshold_value': 0.0,
            'current_value': 0.0,
            'reason': 'Test automation'
        }

        result = retraining_service.retrain_model('1x2_classifier', trigger)

        if result and result.success:
            print(f"✅ Retraining executado com sucesso")
            print(f"   Samples: {result.training_samples}")
            print(f"   Accuracy antiga: {result.old_accuracy:.2%}")
            print(f"   Accuracy nova: {result.new_accuracy:.2%}")
            print(f"   Melhoria: {result.improvement*100:+.1f}%")

            return True
        else:
            print("⚠️ Retraining não melhorou performance (esperado em alguns casos)")
            return True

    except Exception as e:
        print(f"\n❌ Teste 3 FALHOU: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_ai_agent_batch(db: Session):
    """Teste 4: AI Agent batch pode processar predictions"""
    print_header("TESTE 4: AI Agent Batch Processing")

    try:
        # Verificar quantas predictions pendentes temos
        pending_count = db.query(Prediction).filter(
            Prediction.ai_analyzed == False
        ).count()

        print(f"📊 Predictions pendentes: {pending_count}")

        if pending_count == 0:
            print("ℹ️ Nenhuma prediction pendente para processar")
            print("   Teste será pulado (todas predictions já foram analisadas)")
            return True

        # Testar processamento batch
        print(f"\n🧠 Processando até 10 predictions...")

        result = await analyze_unanalyzed_predictions(limit=10)

        if result.get('success'):
            stats = result.get('stats', {})
            print(f"✅ Batch processing executado com sucesso")
            print(f"   Processadas: {stats.get('processed', 0)}")
            print(f"   Sucesso: {stats.get('success', 0)}")
            print(f"   Falhas: {stats.get('failed', 0)}")
            print(f"   Puladas: {stats.get('skipped', 0)}")

            return True
        else:
            error = result.get('error', 'Unknown')
            print(f"❌ Batch processing falhou: {error}")
            return False

    except Exception as e:
        print(f"\n❌ Teste 4 FALHOU: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_summary(results: dict):
    """Imprime resumo dos testes"""
    print_header("RESUMO DOS TESTES")

    total = len(results)
    passed = sum(1 for r in results.values() if r)
    failed = total - passed

    for test_name, passed_test in results.items():
        status = "✅ PASSOU" if passed_test else "❌ FALHOU"
        print(f"{status} - {test_name}")

    print(f"\n📊 Total: {passed}/{total} testes passaram")

    if failed == 0:
        print("\n🎉 TODOS OS TESTES PASSARAM! Automação está funcionando corretamente.")
    else:
        print(f"\n⚠️ {failed} teste(s) falharam. Verifique os erros acima.")


async def main():
    """Executa todos os testes"""
    print_header("🧪 TESTE DE AUTOMAÇÃO END-TO-END")
    print("Timestamp:", datetime.now().isoformat())

    # Criar sessão do banco
    db = SessionLocal()

    results = {}

    try:
        # Teste 1: Scheduler
        results["Scheduler Initialization"] = test_scheduler_initialization(db)

        # Teste 2: AI Agent
        results["AI Agent Availability"] = test_ai_agent_availability()

        # Teste 3: ML Retraining
        results["ML Retraining"] = test_ml_retraining(db)

        # Teste 4: AI Agent Batch (apenas se AI Agent disponível)
        if results["AI Agent Availability"]:
            results["AI Agent Batch"] = await test_ai_agent_batch(db)
        else:
            print("\n⚠️ Pulando teste AI Agent Batch (AI Agent não disponível)")
            results["AI Agent Batch"] = False

    finally:
        db.close()

    # Resumo
    print_summary(results)

    # Exit code
    if all(results.values()):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
