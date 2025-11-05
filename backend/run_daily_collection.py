#!/usr/bin/env python3
"""
📅 COLETA DIÁRIA INCREMENTAL
Executa coleta incremental para hoje
"""
import asyncio
import sys
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.services.data_pipeline import DataPipeline
from app.services.api_quota_manager import APIQuotaManager

async def main():
    print("📅 COLETA DIÁRIA INCREMENTAL")
    print("="*60)

    db = SessionLocal()
    pipeline = DataPipeline(db)
    quota_manager = APIQuotaManager(db)

    # Status inicial
    health = quota_manager.check_health()
    print(f"\n💊 Quota disponível: {health['available_requests']} requests")

    # Executar coleta de hoje
    today = date.today().isoformat()
    print(f"\n📅 Coletando fixtures de: {today}")
    print("-"*60)

    result = await pipeline.collect_daily_incremental(target_date=today)

    print(f"\n📊 Resultado:")
    print(f"   Status: {result['status']}")

    if result['status'] == 'COMPLETED':
        print(f"   Novos fixtures: {result.get('new_fixtures', 0)}")
        print(f"   Atualizados: {result.get('updated_fixtures', 0)}")
        print(f"   Requests usados: {result.get('requests_used', 0)}")

    # Status final
    final_health = quota_manager.check_health()
    print(f"\n💊 Quota restante: {final_health['available_requests']}")
    print("="*60)

    db.close()

if __name__ == "__main__":
    asyncio.run(main())
