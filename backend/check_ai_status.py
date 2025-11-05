#!/usr/bin/env python3
"""
Check AI analysis status
"""
from app.core.database import get_db_session
from app.models import Prediction
from datetime import datetime, timedelta

db = get_db_session()

# Total predictions
total = db.query(Prediction).count()

# AI analyzed
ai_analyzed = db.query(Prediction).filter(Prediction.ai_analyzed == True).count()

# High confidence predictions (>= 60%) from last 24h
high_conf = db.query(Prediction).filter(
    Prediction.confidence_score >= 0.60,
    Prediction.created_at >= datetime.now() - timedelta(hours=24)
).count()

# High confidence NOT analyzed
high_conf_not_analyzed = db.query(Prediction).filter(
    Prediction.confidence_score >= 0.60,
    Prediction.created_at >= datetime.now() - timedelta(hours=24),
    Prediction.ai_analyzed != True
).count()

print("=" * 60)
print("🧠 AI ANALYSIS STATUS")
print("=" * 60)
print(f"Total predictions: {total}")
print(f"AI analyzed: {ai_analyzed}")
print(f"High confidence (>= 60%) last 24h: {high_conf}")
print(f"High confidence NOT analyzed: {high_conf_not_analyzed}")
print("=" * 60)

# Show some predictions
if high_conf > 0:
    print("\n📊 Sample high confidence predictions:")
    samples = db.query(Prediction).filter(
        Prediction.confidence_score >= 0.60
    ).limit(5).all()

    for i, pred in enumerate(samples, 1):
        print(f"\n  {i}. Match ID: {pred.match_id}")
        print(f"     Confidence: {pred.confidence_score:.1%}")
        print(f"     AI Analyzed: {pred.ai_analyzed}")
        print(f"     Recommendation: {pred.final_recommendation}")
        if pred.ai_analyzed:
            print(f"     AI Recommendation: {pred.ai_recommendation}")
            print(f"     AI Risk: {pred.ai_risk_level}")

db.close()
