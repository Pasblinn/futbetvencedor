#!/usr/bin/env python3
"""
🔄 RESET DE PREDICTIONS - Começo Zero com AI Agent

Remove predictions antigas (pré-AI) e mantém apenas:
- Predictions futuras (ainda não aconteceram)
- Sistema limpo para começar do zero com AI Agent
"""
from app.core.database import get_db_session
from app.models import Match, Prediction
from datetime import datetime
from sqlalchemy import and_

db = get_db_session()

print("=" * 80)
print("🔄 RESET DE PREDICTIONS - COMEÇANDO DO ZERO COM AI AGENT")
print("=" * 80)

# 1. Contar predictions atuais
total_predictions = db.query(Prediction).count()
print(f"\n📊 Total de predictions no DB: {total_predictions}")

# 2. Identificar predictions de jogos passados (já finalizados)
past_predictions = db.query(Prediction).join(Match).filter(
    Match.match_date < datetime.now()
).all()

print(f"🗑️  Predictions de jogos passados: {len(past_predictions)}")

# 3. Identificar predictions resolvidas (com resultado)
resolved_predictions = db.query(Prediction).filter(
    Prediction.actual_outcome.isnot(None)
).all()

print(f"✅ Predictions resolvidas (com resultado): {len(resolved_predictions)}")

# Contar GREENS e REDS que serão removidos
greens = sum(1 for p in resolved_predictions if p.is_winner)
reds = sum(1 for p in resolved_predictions if p.is_winner == False)

print(f"   🟢 GREENS: {greens}")
print(f"   🔴 REDS: {reds}")

# 4. Remover predictions antigas
print(f"\n🗑️  Removendo {len(resolved_predictions)} predictions antigas...")

for pred in resolved_predictions:
    db.delete(pred)

db.commit()

# 5. Verificar estado final
remaining = db.query(Prediction).count()
future = db.query(Prediction).join(Match).filter(
    and_(
        Match.match_date >= datetime.now(),
        Match.status.in_(['NS', 'TBD', 'SCHEDULED'])
    )
).count()

print(f"\n✅ LIMPEZA CONCLUÍDA!")
print(f"   📊 Predictions restantes: {remaining}")
print(f"   📅 Predictions futuras: {future}")

# 6. Mostrar próximas predictions
next_predictions = db.query(Prediction).join(Match).filter(
    Match.match_date >= datetime.now()
).order_by(Match.match_date).limit(5).all()

if next_predictions:
    print(f"\n🎯 PRÓXIMAS PREDICTIONS (TOP 5):")
    for i, pred in enumerate(next_predictions, 1):
        match = pred.match
        print(f"\n   {i}. {match.home_team.name if match.home_team else '?'} vs {match.away_team.name if match.away_team else '?'}")
        print(f"      📅 {match.match_date.strftime('%d/%m %H:%M')}")
        print(f"      🎲 {pred.predicted_outcome} - {pred.confidence_score:.1%}")
        if pred.ai_analyzed:
            print(f"      🤖 AI: {pred.ai_recommendation} ({pred.ai_risk_level})")

print("\n" + "=" * 80)
print("🚀 SISTEMA PRONTO PARA COMEÇAR DO ZERO COM AI AGENT!")
print("=" * 80)

db.close()
