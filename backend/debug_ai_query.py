#!/usr/bin/env python3
"""
Debug AI query directly
"""
from app.core.database import get_db_session
from app.models import Prediction, Match
from datetime import datetime
from sqlalchemy import and_

db = get_db_session()

print("=" * 70)
print("🔍 DEBUGGING AI QUERY")
print("=" * 70)

# Test the exact query from run_ai_batch_analysis
top_predictions = db.query(Prediction).join(Match).filter(
    and_(
        Prediction.confidence_score >= 0.60,
        Prediction.match_id.isnot(None),
        Prediction.ai_analyzed != True,
        Match.match_date >= datetime.now(),
        Match.status.in_(['NS', 'TBD', 'SCHEDULED'])
    )
).order_by(Prediction.confidence_score.desc()).limit(100).all()

print(f"\nQuery result: {len(top_predictions)} predictions found")

if len(top_predictions) > 0:
    print("\n📋 Predictions to be analyzed:")
    for i, pred in enumerate(top_predictions, 1):
        match = pred.match
        print(f"\n  {i}. Match ID: {pred.match_id}")
        print(f"     {match.home_team.name if match.home_team else '?'} vs {match.away_team.name if match.away_team else '?'}")
        print(f"     Match Date: {match.match_date}")
        print(f"     Match Status: {match.status}")
        print(f"     Confidence: {pred.confidence_score:.1%}")
        print(f"     ai_analyzed value: {repr(pred.ai_analyzed)} (type: {type(pred.ai_analyzed).__name__})")
        print(f"     Passes filter (ai_analyzed != True): {pred.ai_analyzed != True}")
else:
    print("\n⚠️ NO predictions found!")
    print("\nLet's check each filter individually:")

    # Check 1: High confidence
    high_conf = db.query(Prediction).filter(Prediction.confidence_score >= 0.60).all()
    print(f"\n1. Confidence >= 60%: {len(high_conf)}")

    # Check 2: Has match_id
    with_match = db.query(Prediction).filter(
        and_(
            Prediction.confidence_score >= 0.60,
            Prediction.match_id.isnot(None)
        )
    ).all()
    print(f"2. + has match_id: {len(with_match)}")

    # Check 3: Not AI analyzed
    not_analyzed = db.query(Prediction).filter(
        and_(
            Prediction.confidence_score >= 0.60,
            Prediction.match_id.isnot(None),
            Prediction.ai_analyzed != True
        )
    ).all()
    print(f"3. + not AI analyzed: {len(not_analyzed)}")

    # Check 4: Join with Match
    with_match_join = db.query(Prediction).join(Match).filter(
        and_(
            Prediction.confidence_score >= 0.60,
            Prediction.match_id.isnot(None),
            Prediction.ai_analyzed != True
        )
    ).all()
    print(f"4. + join Match: {len(with_match_join)}")

    # Check 5: Future matches
    future = db.query(Prediction).join(Match).filter(
        and_(
            Prediction.confidence_score >= 0.60,
            Prediction.match_id.isnot(None),
            Prediction.ai_analyzed != True,
            Match.match_date >= datetime.now()
        )
    ).all()
    print(f"5. + future matches: {len(future)}")

    # Check 6: Status
    with_status = db.query(Prediction).join(Match).filter(
        and_(
            Prediction.confidence_score >= 0.60,
            Prediction.match_id.isnot(None),
            Prediction.ai_analyzed != True,
            Match.match_date >= datetime.now(),
            Match.status.in_(['NS', 'TBD', 'SCHEDULED'])
        )
    ).all()
    print(f"6. + status filter: {len(with_status)}")

db.close()
print("\n" + "=" * 70)
