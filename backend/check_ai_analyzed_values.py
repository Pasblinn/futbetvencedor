#!/usr/bin/env python3
"""
Check ai_analyzed field values
"""
from app.core.database import get_db_session
from app.models import Prediction

db = get_db_session()

# Get all high confidence predictions
high_conf = db.query(Prediction).filter(Prediction.confidence_score >= 0.60).all()

print("=" * 70)
print("🔍 AI_ANALYZED FIELD VALUES")
print("=" * 70)
print(f"Total high confidence predictions: {len(high_conf)}")

values = {}
for pred in high_conf:
    val = repr(pred.ai_analyzed)
    values[val] = values.get(val, 0) + 1

print("\nValues found:")
for val, count in values.items():
    print(f"  {val}: {count}")

# Show samples
print("\n📋 Sample predictions:")
for i, pred in enumerate(high_conf[:5], 1):
    print(f"\n  {i}. Match ID: {pred.match_id}")
    print(f"     ai_analyzed: {repr(pred.ai_analyzed)}")
    print(f"     Type: {type(pred.ai_analyzed).__name__}")
    print(f"     ai_analyzed == True: {pred.ai_analyzed == True}")
    print(f"     ai_analyzed != True: {pred.ai_analyzed != True}")
    print(f"     ai_analyzed is None: {pred.ai_analyzed is None}")
    print(f"     ai_analyzed is False: {pred.ai_analyzed is False}")
    print(f"     not ai_analyzed: {not pred.ai_analyzed}")

db.close()
print("\n" + "=" * 70)
