#!/usr/bin/env python3
"""
⚡ GERADOR DE PREDICTIONS PARA JOGOS AO VIVO
Gera predictions para jogos com status LIVE, HT, 1H, 2H
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime
from app.core.database import SessionLocal
from app.models import Match, Prediction
from generate_predictions import PredictionGenerator

db = SessionLocal()

print("=" * 80)
print("⚡ GERANDO PREDICTIONS PARA JOGOS AO VIVO/RECENTES")
print("=" * 80)

# Buscar jogos futuros e ao vivo (por data, não por ID)
from datetime import datetime, timedelta
today = datetime.now()
future_date = today + timedelta(days=14)  # Próximos 14 dias

live_matches = db.query(Match).filter(
    Match.status.in_(['LIVE', 'HT', '1H', '2H', 'NS', 'TBD', 'SCHEDULED']),
    Match.match_date >= today,
    Match.match_date <= future_date
).order_by(Match.match_date).all()

print(f"\n📊 Encontrados {len(live_matches)} jogos para processar\n")

# Criar gerador
generator = PredictionGenerator(db)

created = 0
updated = 0
skipped = 0

for match in live_matches:
    try:
        # Verificar se já tem prediction
        existing = db.query(Prediction).filter(
            Prediction.match_id == match.id,
            Prediction.market_type == '1X2'
        ).first()

        if existing:
            print(f"⏭️  Match {match.id} já tem prediction - pulando")
            skipped += 1
            continue

        # Gerar prediction
        pred_data = generator.predict_match(match)

        # Mapear outcome
        outcome_map = {'H': '1', 'D': 'X', 'A': '2'}
        predicted_outcome = outcome_map.get(pred_data['predicted_result'], pred_data['predicted_result'])

        # Calcular confidence score (maior probabilidade)
        confidence_score = max(
            pred_data['confidence_home'],
            pred_data['confidence_draw'],
            pred_data['confidence_away']
        )

        # Probabilidade do resultado predito
        prob_map = {
            'H': pred_data['confidence_home'],
            'D': pred_data['confidence_draw'],
            'A': pred_data['confidence_away']
        }
        predicted_probability = prob_map.get(pred_data['predicted_result'], 0.33)

        # Criar prediction
        prediction = Prediction(
            match_id=match.id,
            prediction_type='SINGLE',
            market_type='1X2',
            predicted_outcome=predicted_outcome,
            predicted_probability=predicted_probability,
            confidence_score=confidence_score,
            analysis_summary=f"Análise ML: {pred_data['predicted_result']} com {confidence_score:.1%} de confiança",
            final_recommendation='BET' if confidence_score > 0.6 else 'CONSIDER',
            key_factors={
                'confidence_home': pred_data['confidence_home'],
                'confidence_draw': pred_data['confidence_draw'],
                'confidence_away': pred_data['confidence_away'],
                'model': 'random_forest_enhanced'
            }
        )

        db.add(prediction)
        db.commit()

        print(f"✨ Match {match.id}: {pred_data['home_team']} vs {pred_data['away_team']}")
        print(f"   Prediction: {predicted_outcome} | Confidence: {confidence_score:.1%}")

        created += 1

    except Exception as e:
        print(f"❌ Erro no match {match.id}: {e}")
        continue

print(f"\n{'=' * 80}")
print(f"✅ CONCLUÍDO!")
print(f"   Criadas: {created}")
print(f"   Puladas: {skipped}")
print(f"{'=' * 80}\n")

db.close()
