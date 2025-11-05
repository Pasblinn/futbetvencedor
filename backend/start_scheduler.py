"""
⏰ START SCHEDULER - Iniciar o scheduler automático
Script para iniciar o sistema de coleta automática respeitando rate limits
"""

import asyncio
import sys
import os
import signal
from datetime import datetime

sys.path.append(os.getcwd())

from app.services.intelligent_scheduler import intelligent_scheduler
from app.core.database import get_db_session
from app.models.match import Match

def signal_handler(sig, frame):
    """Parar scheduler graciosamente"""
    print("\n🛑 Parando scheduler...")
    intelligent_scheduler.stop_scheduler()
    print("✅ Scheduler parado com sucesso")
    sys.exit(0)

async def show_current_database_status():
    """Mostrar status atual do banco"""
    print("📊 STATUS ATUAL DO BANCO:")
    print("=" * 50)

    with get_db_session() as session:
        total_matches = session.query(Match).count()
        print(f"⚽ Total de jogos: {total_matches}")

        if total_matches > 0:
            # Ligas no banco
            leagues = session.query(Match.league).distinct().all()
            print(f"🏆 Ligas ativas: {len(leagues)}")

            for league in leagues[:10]:  # Mostrar top 10
                if league[0]:
                    count = session.query(Match).filter(Match.league == league[0]).count()
                    print(f"  • {league[0]}: {count} jogos")

            # Jogos recentes
            print(f"\n⚽ Jogos mais recentes:")
            recent_matches = session.query(Match).order_by(Match.created_at.desc()).limit(5).all()

            from app.models.team import Team
            for match in recent_matches:
                home_team = session.query(Team).filter(Team.id == match.home_team_id).first()
                away_team = session.query(Team).filter(Team.id == match.away_team_id).first()
                print(f"  • {home_team.name} vs {away_team.name} ({match.league})")

    print("=" * 50)

def main():
    """Função principal"""
    print("⏰ SISTEMA DE SCHEDULER AUTOMÁTICO")
    print("🔒 Rate Limiting Rigoroso")
    print("🇧🇷 Prioridade: Brasil e Espanha")
    print("=" * 60)

    try:
        # Mostrar status inicial
        asyncio.run(show_current_database_status())
        print()

        # Configurar handler para CTRL+C
        signal.signal(signal.SIGINT, signal_handler)

        print("🚀 INICIANDO SCHEDULER AUTOMÁTICO...")
        print()
        print("📅 AGENDA CONFIGURADA:")
        print("  ⚡ Jogos ao vivo: a cada 15 minutos")
        print("  🔄 População gradual: a cada 2 horas")
        print("  🇧🇷 Brasileirão: 8h, 14h, 20h")
        print("  🇪🇸 La Liga: 12h, 18h")
        print("  🧹 Reset rate limits: a cada hora")
        print("  📊 Relatório diário: 23:30")
        print()

        # Iniciar scheduler
        intelligent_scheduler.start_scheduler()

        print("✅ Scheduler iniciado com sucesso!")
        print("⏰ Sistema rodando automaticamente...")
        print("🔒 Rate limits sendo respeitados")
        print()
        print("💡 Para parar o scheduler, pressione Ctrl+C")
        print("📊 Para ver status, verifique os logs")
        print()

        # Mostrar status inicial
        status = intelligent_scheduler.get_status()
        print("📊 STATUS INICIAL:")
        print(f"  • Rodando: {status['is_running']}")
        print(f"  • Jobs agendados: {len(status['next_scheduled_jobs'])}")
        print()

        # Loop para manter o programa rodando
        try:
            while True:
                # Mostrar status a cada 5 minutos
                import time
                time.sleep(300)  # 5 minutos

                print(f"⏰ {datetime.now().strftime('%H:%M:%S')} - Scheduler ativo")
                status = intelligent_scheduler.get_status()

                if status['last_execution']['last_run']:
                    print(f"  📊 Última execução: {status['last_execution']['last_run']}")
                    print(f"  ⚽ Jogos adicionados: {status['last_execution']['matches_added']}")

        except KeyboardInterrupt:
            signal_handler(None, None)

    except Exception as e:
        print(f"❌ Erro no scheduler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()