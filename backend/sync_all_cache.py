#!/usr/bin/env python3
"""
🔄 SINCRONIZAR TODO O CACHE
Processa todo o cache pendente em lotes
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.services.data_pipeline import DataPipeline
from app.models.api_tracking import FixtureCache

async def main():
    print("🔄 SINCRONIZAÇÃO COMPLETA DO CACHE")
    print("="*60)

    db = SessionLocal()
    pipeline = DataPipeline(db)

    # Contar total
    total = db.query(FixtureCache).filter(
        FixtureCache.has_basic_data == True,
        FixtureCache.match_id == None
    ).count()

    print(f"\n📊 Total pendente: {total} fixtures")

    if total == 0:
        print("✅ Nada para sincronizar!")
        db.close()
        return

    # Sincronizar em lotes
    synced_total = 0
    batch = 1

    while True:
        pending = db.query(FixtureCache).filter(
            FixtureCache.has_basic_data == True,
            FixtureCache.match_id == None
        ).count()

        if pending == 0:
            break

        print(f"\n[Batch {batch}] Pendentes: {pending}")

        result = await pipeline.sync_cache_to_database(limit=500)

        synced = result.get('synced', 0)
        synced_total += synced

        print(f"   ✅ Sincronizados: {synced}")
        print(f"   📊 Total processado: {synced_total}/{total}")

        if synced == 0:
            break

        batch += 1

    print(f"\n{'='*60}")
    print("🎉 SINCRONIZAÇÃO COMPLETA!")
    print(f"{'='*60}")
    print(f"📊 Total sincronizado: {synced_total}")

    db.close()

if __name__ == "__main__":
    asyncio.run(main())
