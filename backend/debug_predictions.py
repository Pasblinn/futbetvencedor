#!/usr/bin/env python3
"""
Debug script to investigate why predictions aren't being generated
"""
from app.core.database import get_db_session
from app.models import Match, Prediction
from datetime import datetime, timedelta
from sqlalchemy import and_

db = get_db_session()

print("=" * 60)
print("🔍 DEBUGGING PREDICTION GENERATION")
print("=" * 60)

# Check matches
upcoming_matches = db.query(Match).filter(
    Match.match_date >= datetime.now()
).all()

print(f"\n📊 Total upcoming matches: {len(upcoming_matches)}")

# Group by status
statuses = {}
for match in upcoming_matches:
    status = match.status or 'NULL'
    statuses[status] = statuses.get(status, 0) + 1

print("\n📋 Matches by status:")
for status, count in statuses.items():
    print(f"  {status}: {count}")

# Check if matches have predictions
matches_with_predictions = 0
matches_without_predictions = 0

print("\n🎯 Sample matches (first 5):")
for i, match in enumerate(upcoming_matches[:5]):
    has_pred = db.query(Prediction).filter(Prediction.match_id == match.id).first() is not None
    print(f"\n  Match {i+1}:")
    print(f"    ID: {match.id}")
    print(f"    {match.home_team} vs {match.away_team}")
    print(f"    Date: {match.match_date}")
    print(f"    Status: {match.status}")
    print(f"    League: {match.league}")
    print(f"    Has prediction: {has_pred}")

    if has_pred:
        matches_with_predictions += 1
    else:
        matches_without_predictions += 1

# Check total predictions
total_predictions = db.query(Prediction).count()
print(f"\n📈 Total predictions in DB: {total_predictions}")
print(f"   Matches WITH predictions: {matches_with_predictions} (of 5 sampled)")
print(f"   Matches WITHOUT predictions: {matches_without_predictions} (of 5 sampled)")

# Check what the prediction service would see
print("\n🔬 Checking prediction generation criteria:")
print("   Looking for matches with status in ['NS', 'TBD', 'SCHEDULED']")

target_matches = db.query(Match).filter(
    and_(
        Match.match_date >= datetime.now(),
        Match.match_date <= datetime.now() + timedelta(days=7),
        Match.status.in_(['NS', 'TBD', 'SCHEDULED'])
    )
).all()

print(f"   Matches meeting criteria: {len(target_matches)}")

if len(target_matches) > 0:
    print("\n   Sample target match:")
    m = target_matches[0]
    print(f"     {m.home_team} vs {m.away_team}")
    print(f"     Date: {m.match_date}")
    print(f"     Status: '{m.status}'")
    print(f"     Has home_team_id: {hasattr(m, 'home_team_id') and m.home_team_id is not None}")
    print(f"     Has away_team_id: {hasattr(m, 'away_team_id') and m.away_team_id is not None}")

db.close()
print("\n" + "=" * 60)
