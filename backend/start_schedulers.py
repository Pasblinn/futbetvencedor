#!/usr/bin/env python3
"""
🤖 START ALL SCHEDULERS - Sistema 100% Automatizado

Inicia todos os schedulers em background:
- Importação de jogos (4x/dia)
- Atualização de jogos ao vivo (2 min)
- Geração de predictions ML (6h)
- Análise AI Agent (12h)
- Limpeza de jogos finalizados (1h)
- Normalização de ligas (diária)
- Atualização de resultados (1h)
"""
import time
import logging
from app.core.scheduler import start_scheduler, scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    print("=" * 80)
    print("🤖 INICIANDO SISTEMA AUTOMATIZADO COMPLETO")
    print("=" * 80)

    # Start scheduler
    start_scheduler()

    print("\n✅ Scheduler iniciado com sucesso!")
    print("\n📋 Jobs ativos:")
    for job in scheduler.get_jobs():
        print(f"   - {job.name} (ID: {job.id})")
        if hasattr(job.trigger, 'interval'):
            print(f"     Intervalo: {job.trigger.interval}")
        elif hasattr(job.trigger, 'fields'):
            hour = job.trigger.fields[5]
            minute = job.trigger.fields[6]
            print(f"     Horário: {hour}:{minute}")

    print("\n" + "=" * 80)
    print("🚀 SISTEMA RODANDO EM BACKGROUND")
    print("=" * 80)
    print("\nPressione Ctrl+C para parar...")
    print()

    try:
        # Keep running
        while True:
            time.sleep(60)
            # Show heartbeat every minute
            logger.info("💚 Sistema ativo - Todos os schedulers rodando")

    except KeyboardInterrupt:
        print("\n\n⏹️  Parando schedulers...")
        from app.core.scheduler import stop_scheduler
        stop_scheduler()
        print("✅ Schedulers parados com sucesso!")
