#!/usr/bin/env python3
"""
Show AI analysis results
"""
from app.core.database import get_db_session
from app.models import Prediction, Match
from datetime import datetime
from sqlalchemy import and_

db = get_db_session()

# Get AI analyzed predictions
ai_analyzed = db.query(Prediction).join(Match).filter(
    and_(
        Prediction.ai_analyzed == True,
        Match.match_date >= datetime.now()
    )
).order_by(Prediction.confidence_score.desc()).all()

print("=" * 80)
print("🧠 AI AGENT ANALYSIS RESULTS")
print("=" * 80)
print(f"Total predictions analyzed by AI: {len(ai_analyzed)}")

for i, pred in enumerate(ai_analyzed, 1):
    match = pred.match
    print(f"\n{'=' * 80}")
    print(f"🎯 PREDICTION #{i}")
    print(f"{'=' * 80}")
    print(f"⚽ Match: {match.home_team.name if match.home_team else '?'} vs {match.away_team.name if match.away_team else '?'}")
    print(f"📅 Date: {match.match_date}")
    print(f"🏆 League: {match.league}")
    print(f"\n📊 ML PREDICTION:")
    print(f"   Outcome: {pred.predicted_outcome}")
    print(f"   ML Confidence: {pred.confidence_score:.1%}")

    print(f"\n🧠 AI ANALYSIS:")
    print(f"   AI Recommendation: {pred.ai_recommendation}")
    print(f"   AI Risk Level: {pred.ai_risk_level}")
    if pred.ai_confidence_delta:
        delta_sign = "+" if pred.ai_confidence_delta > 0 else ""
        print(f"   Confidence Adjustment: {delta_sign}{pred.ai_confidence_delta:.1%}")
        adjusted = pred.confidence_score + (pred.ai_confidence_delta or 0)
        print(f"   Final Confidence: {adjusted:.1%}")

    if pred.ai_analysis:
        print(f"\n💭 AI Explanation:")
        # Limit to first 300 chars
        analysis = pred.ai_analysis[:300]
        if len(pred.ai_analysis) > 300:
            analysis += "..."
        print(f"   {analysis}")

db.close()
print("\n" + "=" * 80)
