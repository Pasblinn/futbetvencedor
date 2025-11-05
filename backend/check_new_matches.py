#!/usr/bin/env python3
"""
Verifica os novos matches e odds no banco
"""

from app.core.database import SessionLocal
from app.models import Match, Team, Odds, Prediction
from sqlalchemy import desc

db = SessionLocal()

print("=" * 80)
print("📊 MATCHES RECENTES NO BANCO")
print("=" * 80)

# Buscar últimos 10 matches
recent_matches = db.query(Match).order_by(desc(Match.id)).limit(10).all()

for match in recent_matches:
    home_team = db.query(Team).filter(Team.id == match.home_team_id).first()
    away_team = db.query(Team).filter(Team.id == match.away_team_id).first()

    # Buscar odds
    odds = db.query(Odds).filter(
        Odds.match_id == match.id,
        Odds.market == '1X2'
    ).first()

    # Buscar prediction
    prediction = db.query(Prediction).filter(
        Prediction.match_id == match.id,
        Prediction.market_type == '1X2'
    ).first()

    print(f"\n{'=' * 80}")
    print(f"Match ID: {match.id} | External ID: {match.external_id}")
    print(f"🏆 {home_team.name if home_team else 'Unknown'} vs {away_team.name if away_team else 'Unknown'}")
    print(f"📅 {match.match_date} | Status: {match.status}")
    print(f"Liga: {match.league} | Season: {match.season}")

    if match.home_score is not None and match.away_score is not None:
        print(f"⚽ Placar: {match.home_score} x {match.away_score}")

    if odds:
        print(f"💰 ODDS ({odds.bookmaker}): {odds.home_win} / {odds.draw} / {odds.away_win}")
        print(f"   Source: DATABASE | Timestamp: {odds.odds_timestamp}")
    else:
        print(f"❌ SEM ODDS")

    if prediction:
        print(f"🤖 PREDICTION: {prediction.predicted_outcome} | Confidence: {prediction.confidence_score:.2%}")
    else:
        print(f"⚠️  SEM PREDICTION")

print(f"\n{'=' * 80}")
print(f"✅ Total de matches no banco: {db.query(Match).count()}")
print(f"✅ Total com odds: {db.query(Odds).count()}")
print(f"✅ Total com predictions: {db.query(Prediction).count()}")
print(f"{'=' * 80}\n")

db.close()
