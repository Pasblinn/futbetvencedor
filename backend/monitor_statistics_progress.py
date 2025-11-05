#!/usr/bin/env python3
"""
📊 MONITORAR PROGRESSO DA COLETA DE ESTATÍSTICAS
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.models.api_tracking import FixtureCache, DailyAPIQuota

db = SessionLocal()

# Status atual
total_ft = db.query(FixtureCache).filter(FixtureCache.status == 'FT').count()
with_stats = db.query(FixtureCache).filter(
    FixtureCache.status == 'FT',
    FixtureCache.has_statistics == True
).count()

coverage = (with_stats / total_ft * 100) if total_ft > 0 else 0

print("📊 PROGRESSO DA COLETA DE ESTATÍSTICAS")
print("="*60)
print(f"\nFixtures finalizados: {total_ft}")
print(f"Com estatísticas: {with_stats} ({coverage:.1f}%)")
print(f"Faltam: {total_ft - with_stats}")

# Quota
quota = db.query(DailyAPIQuota).first()
if quota:
    print(f"\n💊 Quota:")
    print(f"   Usados: {quota.requests_used}/{quota.daily_limit}")
    print(f"   Restante: {quota.requests_remaining}")
    print(f"   Última estatística: {quota.statistics_requests} requests")

print("="*60)

db.close()
