#!/usr/bin/env python3
"""
📚 COLETA HISTÓRICA DE TODAS AS LIGAS
Coleta dados históricos de todas as ligas configuradas
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.services.data_pipeline import DataPipeline
from app.services.api_quota_manager import APIQuotaManager
from app.models.api_tracking import LeagueConfig

async def main():
    print("🚀 COLETA HISTÓRICA DE TODAS AS LIGAS")
    print("="*60)

    db = SessionLocal()
    pipeline = DataPipeline(db)
    quota_manager = APIQuotaManager(db)

    # Verificar quota inicial
    health = quota_manager.check_health()
    print(f"\n💊 Quota disponível: {health['available_requests']} requests")
    print(f"   Status: {health['status']}")

    # Buscar ligas ativas
    leagues = db.query(LeagueConfig).filter(
        LeagueConfig.is_active == True,
        LeagueConfig.collect_historical == True
    ).order_by(LeagueConfig.priority).all()

    print(f"\n🏆 {len(leagues)} ligas serão processadas:")
    for league in leagues:
        print(f"   {league.priority}. {league.league_name} ({len(league.seasons)} temporadas)")

    # Confirmação
    print("\n⚠️  Estimativa de requests:")
    print(f"   - Mínimo: ~{len(leagues)} requests (apenas fixtures)")
    print(f"   - Máximo: ~{len(leagues) * 150} requests (com estatísticas)")

    input("\nPressione ENTER para continuar ou Ctrl+C para cancelar...")

    # Coletar cada liga
    total_fixtures = 0
    total_requests = 0
    total_stats = 0

    for idx, league in enumerate(leagues, 1):
        print(f"\n{'='*60}")
        print(f"[{idx}/{len(leagues)}] 🏆 {league.league_name}")
        print(f"{'='*60}")

        # Coletar cada temporada
        for season in league.seasons:
            print(f"\n📅 Temporada {season}...")

            result = await pipeline.collect_historical_batch(
                league_id=league.league_id,
                season=season,
                force_update=False  # Não forçar se já existir
            )

            if result['status'] == 'COMPLETED':
                fixtures = result.get('fixtures_collected', 0)
                stats = result.get('fixtures_with_stats', 0)
                requests = result.get('requests_used', 0)

                total_fixtures += fixtures
                total_stats += stats
                total_requests += requests

                print(f"   ✅ {fixtures} fixtures | {stats} stats | {requests} requests")

            elif result['status'] == 'SKIPPED':
                existing = result.get('existing_count', 0)
                print(f"   ⏭️  Já coletada ({existing} fixtures)")

            elif result['status'] == 'FAILED':
                print(f"   ❌ Erro: {result.get('error')}")

            # Verificar quota
            remaining = quota_manager.get_available_requests()
            if remaining < 50:
                print(f"\n⚠️ Quota baixa ({remaining} requests). Parando...")
                break

            # Delay entre temporadas
            await asyncio.sleep(1)

        # Delay entre ligas
        await asyncio.sleep(2)

        # Status após cada liga
        quota_health = quota_manager.check_health()
        print(f"\n📊 Quota após {league.league_name}: {quota_health['available_requests']} restantes")

    # Resumo final
    print(f"\n{'='*60}")
    print("🎉 COLETA HISTÓRICA CONCLUÍDA!")
    print(f"{'='*60}")
    print(f"📊 Total de fixtures: {total_fixtures}")
    print(f"📊 Com estatísticas: {total_stats}")
    print(f"📡 Requests usados: {total_requests}")

    final_health = quota_manager.check_health()
    print(f"\n💊 Quota final:")
    print(f"   Status: {final_health['status']}")
    print(f"   Disponível: {final_health['available_requests']}")

    db.close()

if __name__ == "__main__":
    asyncio.run(main())
