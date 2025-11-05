#!/usr/bin/env python3
"""
📊 STATUS COMPLETO DO SISTEMA
"""
from app.core.database import get_db_session
from app.models import Match, Prediction
from datetime import datetime, timedelta
from sqlalchemy import and_, func

db = get_db_session()

print("=" * 80)
print("📊 SISTEMA FOOTBALL ANALYTICS - STATUS COMPLETO")
print("=" * 80)

# Ligas únicas nos jogos
leagues = db.query(Match.league).distinct().all()
print(f"\n🏆 LIGAS NO SISTEMA: {len(leagues)}")
for league_tuple in leagues[:10]:
    print(f"   - {league_tuple[0]}")

# Matches
total_matches = db.query(Match).count()
upcoming_matches = db.query(Match).filter(
    and_(
        Match.match_date >= datetime.now(),
        Match.status.in_(['NS', 'TBD', 'SCHEDULED'])
    )
).count()

finished_matches = db.query(Match).filter(
    Match.status.in_(['FT', 'AET', 'PEN'])
).count()

live_matches = db.query(Match).filter(
    Match.status.in_(['1H', '2H', 'HT', 'ET', 'P', 'LIVE'])
).count()

print(f"\n⚽ JOGOS:")
print(f"   Total: {total_matches}")
print(f"   📅 Próximos: {upcoming_matches}")
print(f"   🔴 Ao vivo: {live_matches}")
print(f"   ✅ Finalizados: {finished_matches}")

# Predictions
total_predictions = db.query(Prediction).count()
future_predictions = db.query(Prediction).join(Match).filter(
    and_(
        Match.match_date >= datetime.now(),
        Match.status.in_(['NS', 'TBD', 'SCHEDULED'])
    )
).count()

high_conf = db.query(Prediction).join(Match).filter(
    and_(
        Prediction.confidence_score >= 0.60,
        Match.match_date >= datetime.now(),
        Match.status.in_(['NS', 'TBD', 'SCHEDULED'])
    )
).count()

ai_analyzed = db.query(Prediction).filter(
    Prediction.ai_analyzed == True
).count()

greens = db.query(Prediction).filter(
    Prediction.is_winner == True
).count()

reds = db.query(Prediction).filter(
    and_(
        Prediction.is_winner == False,
        Prediction.actual_outcome.isnot(None)
    )
).count()

print(f"\n🧠 PREDICTIONS:")
print(f"   Total: {total_predictions}")
print(f"   📅 Futuras: {future_predictions}")
print(f"   ⭐ Alta confidence (>=60%): {high_conf}")
print(f"   🤖 Analisadas por AI: {ai_analyzed}")
print(f"   🟢 GREENS: {greens}")
print(f"   🔴 REDS: {reds}")
if greens + reds > 0:
    win_rate = (greens / (greens + reds)) * 100
    print(f"   📈 Taxa de acerto: {win_rate:.1f}%")

# Próximos jogos com predictions
next_matches = db.query(Match).join(Prediction).filter(
    and_(
        Match.match_date >= datetime.now(),
        Match.status.in_(['NS', 'TBD', 'SCHEDULED']),
        Prediction.confidence_score >= 0.60
    )
).order_by(Match.match_date).limit(5).all()

if next_matches:
    print(f"\n🎯 PRÓXIMAS PREDICTIONS DE ALTA CONFIANÇA:")
    for match in next_matches:
        pred = [p for p in match.predictions if p.confidence_score >= 0.60][0]
        print(f"\n   {match.home_team.name if match.home_team else '?'} vs {match.away_team.name if match.away_team else '?'}")
        print(f"   📅 {match.match_date.strftime('%d/%m %H:%M')}")
        print(f"   🎲 {pred.predicted_outcome} - {pred.confidence_score:.1%}")
        if pred.ai_analyzed:
            print(f"   🤖 AI: {pred.ai_recommendation} ({pred.ai_risk_level})")

print("\n" + "=" * 80)
print("✅ API: http://localhost:8000")
print("📚 Docs: http://localhost:8000/docs")
print("🤖 AI Agent: ATIVO (Ollama + Llama 3.1:8b)")
print("=" * 80)

db.close()
