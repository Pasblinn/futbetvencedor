#!/usr/bin/env python3
"""
Check predictions confidence scores
"""
from app.core.database import get_db_session
from app.models import Prediction, Match
from datetime import datetime
from sqlalchemy import and_

db = get_db_session()

# All predictions for future matches
future_predictions = db.query(Prediction).join(Match).filter(
    and_(
        Match.match_date >= datetime.now(),
        Match.status.in_(['NS', 'TBD', 'SCHEDULED'])
    )
).all()

print("=" * 70)
print("📊 PREDICTIONS CONFIDENCE ANALYSIS")
print("=" * 70)
print(f"Total future predictions: {len(future_predictions)}")

if len(future_predictions) > 0:
    # Group by confidence ranges
    ranges = {
        '90-100%': 0,
        '80-90%': 0,
        '70-80%': 0,
        '60-70%': 0,
        '50-60%': 0,
        '40-50%': 0,
        '<40%': 0,
        'None': 0
    }

    for pred in future_predictions:
        conf = pred.confidence_score
        if conf is None:
            ranges['None'] += 1
        elif conf >= 0.90:
            ranges['90-100%'] += 1
        elif conf >= 0.80:
            ranges['80-90%'] += 1
        elif conf >= 0.70:
            ranges['70-80%'] += 1
        elif conf >= 0.60:
            ranges['60-70%'] += 1
        elif conf >= 0.50:
            ranges['50-60%'] += 1
        elif conf >= 0.40:
            ranges['40-50%'] += 1
        else:
            ranges['<40%'] += 1

    print("\nConfidence distribution:")
    for range_name, count in ranges.items():
        if count > 0:
            print(f"  {range_name}: {count}")

    # High confidence (>= 60%)
    high_conf = [p for p in future_predictions if p.confidence_score and p.confidence_score >= 0.60]
    print(f"\n✅ High confidence (>= 60%): {len(high_conf)}")

    # AI analyzed
    ai_analyzed = [p for p in high_conf if p.ai_analyzed]
    print(f"   Already AI analyzed: {len(ai_analyzed)}")
    print(f"   Pending AI analysis: {len(high_conf) - len(ai_analyzed)}")

    # Show samples
    if len(high_conf) > 0:
        print("\n📋 Sample high confidence predictions:")
        for i, pred in enumerate(high_conf[:5], 1):
            match = pred.match
            print(f"\n  {i}. {match.home_team.name if match.home_team else '?'} vs {match.away_team.name if match.away_team else '?'}")
            print(f"     Date: {match.match_date}")
            print(f"     Confidence: {pred.confidence_score:.1%}")
            print(f"     Predicted: {pred.predicted_outcome}")
            print(f"     AI Analyzed: {pred.ai_analyzed}")

db.close()
print("=" * 70)
