#!/usr/bin/env python3
"""
🔄 SINCRONIZAÇÃO: Cache → Database
Converte dados brutos do cache em modelos estruturados para ML
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.services.data_pipeline import DataPipeline

async def main():
    print("🔄 SINCRONIZAÇÃO: Cache → Database")
    print("="*60)

    db = SessionLocal()
    pipeline = DataPipeline(db)

    # Verificar pendências
    from app.models.api_tracking import FixtureCache

    total_cache = db.query(FixtureCache).count()
    pending = db.query(FixtureCache).filter(
        FixtureCache.has_basic_data == True,
        FixtureCache.match_id == None
    ).count()

    print(f"\n📊 Status:")
    print(f"   Total no cache: {total_cache}")
    print(f"   Pendentes de sync: {pending}")

    if pending == 0:
        print("\n✅ Tudo sincronizado!")
        db.close()
        return

    print(f"\n🔄 Iniciando sincronização...")

    result = await pipeline.sync_cache_to_database(limit=500)

    print(f"\n📋 Resultado:")
    print(f"   Status: {result['status']}")
    print(f"   Sincronizados: {result.get('synced', 0)}")
    print(f"   Pendentes: {result.get('total_pending', 0)}")

    print("\n" + "="*60)
    print("✅ Sincronização concluída!")

    db.close()

if __name__ == "__main__":
    asyncio.run(main())
