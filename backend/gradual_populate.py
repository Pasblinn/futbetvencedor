"""
🔄 GRADUAL POPULATE - População gradual priorizando Brasil e Espanha
Script para popular o banco gradualmente respeitando rate limits
"""

import asyncio
import sys
import os
from datetime import datetime

sys.path.append(os.getcwd())

from app.services.gradual_population_service import gradual_population_service
from app.core.database import get_db_session
from app.models.team import Team
from app.models.match import Match

async def show_current_status():
    """Mostrar status atual do banco"""
    print("📊 STATUS ATUAL DO BANCO:")
    print("=" * 50)

    with get_db_session() as session:
        teams_count = session.query(Team).count()
        matches_count = session.query(Match).count()

        print(f"👥 Times no banco: {teams_count}")
        print(f"⚽ Jogos no banco: {matches_count}")

        if matches_count > 0:
            print(f"\n🏆 Ligas no banco:")
            leagues = session.query(Match.league).distinct().all()
            for league in leagues:
                if league[0]:
                    count = session.query(Match).filter(Match.league == league[0]).count()
                    print(f"  • {league[0]}: {count} jogos")

            print(f"\n⚽ Últimos jogos adicionados:")
            recent_matches = session.query(Match).order_by(Match.created_at.desc()).limit(5).all()
            for match in recent_matches:
                home_team = session.query(Team).filter(Team.id == match.home_team_id).first()
                away_team = session.query(Team).filter(Team.id == match.away_team_id).first()
                print(f"  • {home_team.name} vs {away_team.name} ({match.league})")

    print("=" * 50)

async def main():
    """Função principal"""
    print("🔄 SISTEMA DE POPULAÇÃO GRADUAL")
    print("🇧🇷 Prioridade 1: Brasileirão")
    print("🇪🇸 Prioridade 2: La Liga")
    print("⚡ Jogos ao vivo incluídos")
    print("=" * 60)

    try:
        # 1. Mostrar status atual
        await show_current_status()
        print()

        # 2. Executar população gradual
        print("🚀 INICIANDO POPULAÇÃO GRADUAL...")
        print("🎯 Meta: 100 jogos totais no banco")
        print()

        result = await gradual_population_service.populate_gradually(target_matches=150)

        # 3. Mostrar resultados
        print("\n" + "=" * 60)
        print("📊 RESULTADOS DA POPULAÇÃO:")
        print(f"✅ Sucesso: {result['success']}")
        print(f"⚽ Jogos adicionados nesta execução: {result['matches_added']}")
        print(f"👥 Times adicionados: {result['teams_added']}")
        print(f"⚡ Jogos ao vivo coletados: {result['live_matches']}")

        if result['leagues_processed']:
            print(f"\n🏆 Ligas processadas:")
            for league, data in result['leagues_processed'].items():
                print(f"  • {league}: {data['matches_added']} jogos, {data['teams_added']} times")

        if result['errors']:
            print(f"\n❌ Erros encontrados:")
            for error in result['errors']:
                print(f"  • {error}")

        # 4. Mostrar status final
        print("\n" + "=" * 60)
        print("📊 STATUS FINAL:")
        await show_current_status()

        print("\n🎉 POPULAÇÃO GRADUAL CONCLUÍDA!")
        print("🔄 Execute novamente para adicionar mais jogos")

    except Exception as e:
        print(f"❌ Erro na população gradual: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())