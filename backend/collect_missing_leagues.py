#!/usr/bin/env python3
"""
📚 COLETAR LIGAS FALTANTES
Coleta histórico das ligas que ainda não temos dados
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.services.data_pipeline import DataPipeline
from app.services.api_quota_manager import APIQuotaManager

# Ligas e temporadas que precisamos coletar
MISSING_DATA = [
    # Brasileirão Série B
    {'league_id': 72, 'league_name': 'Brasileirão Série B', 'season': 2023},
    {'league_id': 72, 'league_name': 'Brasileirão Série B', 'season': 2024},

    # Libertadores
    {'league_id': 13, 'league_name': 'Copa Libertadores', 'season': 2023},
    {'league_id': 13, 'league_name': 'Copa Libertadores', 'season': 2024},
    {'league_id': 13, 'league_name': 'Copa Libertadores', 'season': 2025},

    # Sul-Americana
    {'league_id': 11, 'league_name': 'Copa Sul-Americana', 'season': 2023},
]

async def main():
    print("📚 COLETANDO LIGAS FALTANTES")
    print("="*60)

    db = SessionLocal()
    pipeline = DataPipeline(db)
    quota_manager = APIQuotaManager(db)

    # Status inicial
    health = quota_manager.check_health()
    print(f"\n💊 Quota disponível: {health['available_requests']} requests")
    print(f"   Status: {health['status']}")

    print(f"\n🎯 {len(MISSING_DATA)} temporadas serão coletadas")
    print(f"   Estimativa: ~{len(MISSING_DATA)} requests (batch mode)")

    total_fixtures = 0
    total_stats = 0
    total_requests = 0

    for idx, item in enumerate(MISSING_DATA, 1):
        league_id = item['league_id']
        league_name = item['league_name']
        season = item['season']

        print(f"\n[{idx}/{len(MISSING_DATA)}] 🏆 {league_name} - Temporada {season}")
        print("-"*60)

        result = await pipeline.collect_historical_batch(
            league_id=league_id,
            season=season,
            force_update=False
        )

        if result['status'] == 'COMPLETED':
            fixtures = result.get('fixtures_collected', 0)
            stats = result.get('fixtures_with_stats', 0)
            requests = result.get('requests_used', 0)

            total_fixtures += fixtures
            total_stats += stats
            total_requests += requests

            print(f"✅ Coletado: {fixtures} fixtures | {stats} com stats | {requests} requests")

        elif result['status'] == 'SKIPPED':
            existing = result.get('existing_count', 0)
            print(f"⏭️  Já existe: {existing} fixtures")

        elif result['status'] == 'FAILED':
            error = result.get('error', 'Unknown')
            print(f"❌ Falhou: {error}")

        # Verificar quota
        remaining = quota_manager.get_available_requests()
        print(f"💊 Quota restante: {remaining}")

        if remaining < 100:
            print(f"\n⚠️ Quota baixa! Parando para economizar.")
            break

        # Delay entre requisições
        await asyncio.sleep(2)

    # Resumo final
    print(f"\n{'='*60}")
    print("🎉 COLETA CONCLUÍDA!")
    print(f"{'='*60}")
    print(f"📊 Total de fixtures: {total_fixtures}")
    print(f"📊 Com estatísticas: {total_stats}")
    print(f"📡 Requests usados: {total_requests}")

    final_health = quota_manager.check_health()
    print(f"\n💊 Quota final: {final_health['available_requests']} restantes")

    db.close()

if __name__ == "__main__":
    asyncio.run(main())
