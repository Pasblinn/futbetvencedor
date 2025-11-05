#!/usr/bin/env python3
"""
🎯 GERADOR DE 1000 PREDICTIONS COM TODOS OS MERCADOS
Gera 250 singles + 250 doubles + 250 trebles + 250 quadruples
Objetivo: >70% accuracy
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime, timedelta
from app.core.database import SessionLocal
from app.models import Match, Odds, Prediction, BetCombination
from generate_predictions import PredictionGenerator
import random
from itertools import combinations

db = SessionLocal()
generator = PredictionGenerator(db)

print("=" * 80)
print("🎯 GERANDO 1000 PREDICTIONS COM TODOS OS MERCADOS")
print("=" * 80)

# Buscar todos os jogos válidos (futuros e ao vivo)
today = datetime.now()
future_date = today + timedelta(days=14)

matches = db.query(Match).filter(
    Match.status.in_(['NS', 'TBD', 'SCHEDULED', 'LIVE', 'HT', '1H', '2H']),
    Match.match_date >= today,
    Match.match_date <= future_date
).order_by(Match.match_date).all()

print(f"\n📊 Encontrados {len(matches)} jogos para processar")

# Buscar todas as odds disponíveis por mercado
market_odds = {}
for match in matches:
    odds_list = db.query(Odds).filter(
        Odds.match_id == match.id,
        Odds.bookmaker == 'Bet365',
        Odds.is_active == True
    ).all()

    if odds_list:
        market_odds[match.id] = {odd.market: odd for odd in odds_list}

print(f"📊 {len(market_odds)} jogos com odds disponíveis\n")

# ETAPA 1: Criar predictions individuais para cada mercado
print("=" * 80)
print("ETAPA 1: CRIANDO PREDICTIONS INDIVIDUAIS")
print("=" * 80)

all_predictions = []

for match in matches:
    if match.id not in market_odds:
        continue

    # Gerar prediction ML base
    try:
        ml_pred = generator.predict_match(match)
    except:
        continue

    print(f"\n🏆 {match.home_team} vs {match.away_team}")
    print(f"   Data: {match.match_date.strftime('%d/%m/%Y %H:%M')}")

    # Para cada mercado disponível
    for market_name, odds_obj in market_odds[match.id].items():

        # ========== 1X2 ==========
        if market_name == '1X2' and odds_obj.home_win:
            # Casa
            pred_home = Prediction(
                match_id=match.id,
                prediction_type='SINGLE',
                market_type='1X2',
                predicted_outcome='1',
                predicted_probability=ml_pred['confidence_home'],
                confidence_score=ml_pred['confidence_home'],
                actual_odds=float(odds_obj.home_win),
                analysis_summary=f"Vitória {match.home_team}",
                final_recommendation='BET' if ml_pred['confidence_home'] > 0.6 else 'MONITOR',
                key_factors={'market': '1X2', 'selection': 'Home'},
                model_version='rf_enhanced'
            )
            db.add(pred_home)
            all_predictions.append(pred_home)

            # Empate
            pred_draw = Prediction(
                match_id=match.id,
                prediction_type='SINGLE',
                market_type='1X2',
                predicted_outcome='X',
                predicted_probability=ml_pred['confidence_draw'],
                confidence_score=ml_pred['confidence_draw'],
                actual_odds=float(odds_obj.draw),
                analysis_summary=f"Empate",
                final_recommendation='BET' if ml_pred['confidence_draw'] > 0.6 else 'MONITOR',
                key_factors={'market': '1X2', 'selection': 'Draw'},
                model_version='rf_enhanced'
            )
            db.add(pred_draw)
            all_predictions.append(pred_draw)

            # Fora
            pred_away = Prediction(
                match_id=match.id,
                prediction_type='SINGLE',
                market_type='1X2',
                predicted_outcome='2',
                predicted_probability=ml_pred['confidence_away'],
                confidence_score=ml_pred['confidence_away'],
                actual_odds=float(odds_obj.away_win),
                analysis_summary=f"Vitória {match.away_team}",
                final_recommendation='BET' if ml_pred['confidence_away'] > 0.6 else 'MONITOR',
                key_factors={'market': '1X2', 'selection': 'Away'},
                model_version='rf_enhanced'
            )
            db.add(pred_away)
            all_predictions.append(pred_away)

            print(f"   ✅ 1X2: Casa {ml_pred['confidence_home']:.1%} @ {odds_obj.home_win} | Empate {ml_pred['confidence_draw']:.1%} @ {odds_obj.draw} | Fora {ml_pred['confidence_away']:.1%} @ {odds_obj.away_win}")

        # ========== DUPLA CHANCE ==========
        elif market_name == 'Dupla Chance' and odds_obj.home_win:
            # 1X (Casa ou Empate)
            prob_1x = ml_pred['confidence_home'] + ml_pred['confidence_draw']
            pred_1x = Prediction(
                match_id=match.id,
                prediction_type='SINGLE',
                market_type='Dupla Chance',
                predicted_outcome='1X',
                predicted_probability=prob_1x,
                confidence_score=prob_1x,
                actual_odds=float(odds_obj.home_win),
                analysis_summary=f"{match.home_team} não perde",
                final_recommendation='BET' if prob_1x > 0.7 else 'MONITOR',
                key_factors={'market': 'Dupla Chance', 'selection': '1X'},
                model_version='rf_enhanced'
            )
            db.add(pred_1x)
            all_predictions.append(pred_1x)

            # X2 (Empate ou Fora)
            prob_x2 = ml_pred['confidence_draw'] + ml_pred['confidence_away']
            pred_x2 = Prediction(
                match_id=match.id,
                prediction_type='SINGLE',
                market_type='Dupla Chance',
                predicted_outcome='X2',
                predicted_probability=prob_x2,
                confidence_score=prob_x2,
                actual_odds=float(odds_obj.away_win),
                analysis_summary=f"{match.home_team} não ganha",
                final_recommendation='BET' if prob_x2 > 0.7 else 'MONITOR',
                key_factors={'market': 'Dupla Chance', 'selection': 'X2'},
                model_version='rf_enhanced'
            )
            db.add(pred_x2)
            all_predictions.append(pred_x2)

            # 12 (Casa ou Fora)
            prob_12 = ml_pred['confidence_home'] + ml_pred['confidence_away']
            pred_12 = Prediction(
                match_id=match.id,
                prediction_type='SINGLE',
                market_type='Dupla Chance',
                predicted_outcome='12',
                predicted_probability=prob_12,
                confidence_score=prob_12,
                actual_odds=float(odds_obj.draw),
                analysis_summary=f"Alguém ganha",
                final_recommendation='BET' if prob_12 > 0.7 else 'MONITOR',
                key_factors={'market': 'Dupla Chance', 'selection': '12'},
                model_version='rf_enhanced'
            )
            db.add(pred_12)
            all_predictions.append(pred_12)

            print(f"   ✅ Dupla Chance: 1X {prob_1x:.1%} | X2 {prob_x2:.1%} | 12 {prob_12:.1%}")

        # ========== BTTS ==========
        elif market_name == 'BTTS' and odds_obj.btts_yes:
            # BTTS Yes (probabilidade estimada: 50% se ambos marcaram nos últimos jogos)
            prob_btts_yes = 0.55  # Estimativa base
            pred_btts_yes = Prediction(
                match_id=match.id,
                prediction_type='SINGLE',
                market_type='BTTS',
                predicted_outcome='Yes',
                predicted_probability=prob_btts_yes,
                confidence_score=prob_btts_yes,
                actual_odds=float(odds_obj.btts_yes),
                analysis_summary=f"Ambos marcam",
                final_recommendation='MONITOR',
                key_factors={'market': 'BTTS', 'selection': 'Yes'},
                model_version='rf_enhanced'
            )
            db.add(pred_btts_yes)
            all_predictions.append(pred_btts_yes)

            # BTTS No
            prob_btts_no = 1 - prob_btts_yes
            pred_btts_no = Prediction(
                match_id=match.id,
                prediction_type='SINGLE',
                market_type='BTTS',
                predicted_outcome='No',
                predicted_probability=prob_btts_no,
                confidence_score=prob_btts_no,
                actual_odds=float(odds_obj.btts_no),
                analysis_summary=f"Pelo menos 1 não marca",
                final_recommendation='MONITOR',
                key_factors={'market': 'BTTS', 'selection': 'No'},
                model_version='rf_enhanced'
            )
            db.add(pred_btts_no)
            all_predictions.append(pred_btts_no)

            print(f"   ✅ BTTS: Sim {prob_btts_yes:.1%} @ {odds_obj.btts_yes} | Não {prob_btts_no:.1%} @ {odds_obj.btts_no}")

        # ========== OVER/UNDER ==========
        elif 'Over/Under' in market_name and odds_obj.over_2_5:
            line = market_name.split()[-1]  # ex: "2.5"

            # Over
            prob_over = 0.50  # Base estimada, ajustar com histórico
            pred_over = Prediction(
                match_id=match.id,
                prediction_type='SINGLE',
                market_type=f'Over/Under {line}',
                predicted_outcome=f'Over {line}',
                predicted_probability=prob_over,
                confidence_score=prob_over,
                actual_odds=float(odds_obj.over_2_5),
                analysis_summary=f"Mais de {line} gols",
                final_recommendation='MONITOR',
                key_factors={'market': market_name, 'selection': 'Over'},
                model_version='rf_enhanced'
            )
            db.add(pred_over)
            all_predictions.append(pred_over)

            # Under
            prob_under = 1 - prob_over
            if odds_obj.under_2_5:
                pred_under = Prediction(
                    match_id=match.id,
                    prediction_type='SINGLE',
                    market_type=f'Over/Under {line}',
                    predicted_outcome=f'Under {line}',
                    predicted_probability=prob_under,
                    confidence_score=prob_under,
                    actual_odds=float(odds_obj.under_2_5),
                    analysis_summary=f"Menos de {line} gols",
                    final_recommendation='MONITOR',
                    key_factors={'market': market_name, 'selection': 'Under'},
                    model_version='rf_enhanced'
                )
                db.add(pred_under)
                all_predictions.append(pred_under)

            print(f"   ✅ Over/Under {line}: Over {prob_over:.1%} @ {odds_obj.over_2_5}")

db.commit()
db.flush()

# Refresh all predictions to get IDs
for pred in all_predictions:
    db.refresh(pred)

print(f"\n✅ TOTAL DE PREDICTIONS INDIVIDUAIS CRIADAS: {len(all_predictions)}")

# ETAPA 2: Criar BetCombinations
print("\n" + "=" * 80)
print("ETAPA 2: CRIANDO BET COMBINATIONS")
print("=" * 80)

# Filtrar apenas predictions com boa confidence (>40%) para combinations
good_predictions = [p for p in all_predictions if p.confidence_score and p.confidence_score > 0.4]

print(f"\n📊 {len(good_predictions)} predictions com confidence >40% disponíveis para combos")

combinations_created = {
    'SINGLE': 0,
    'DOUBLE': 0,
    'TREBLE': 0,
    'QUAD': 0
}

# ========== 250 SINGLES ==========
print("\n🎯 Gerando 250 SINGLES...")
singles_target = min(250, len(good_predictions))

# Ordenar por confidence e pegar os melhores
sorted_preds = sorted(good_predictions, key=lambda x: x.confidence_score, reverse=True)

for pred in sorted_preds[:singles_target]:
    combo = BetCombination(
        combination_type='SINGLE',
        selections_count=1,
        total_odds=pred.actual_odds or 1.5,
        combined_probability=pred.confidence_score,
        combined_confidence=pred.confidence_score,
        expected_value=(pred.actual_odds or 1.5) * pred.confidence_score,
        risk_score=1 - pred.confidence_score,
        prediction_ids=[pred.id],
        selection_details=[{
            'match_id': pred.match_id,
            'market': pred.market_type,
            'selection': pred.predicted_outcome,
            'odd': pred.actual_odds,
            'confidence': pred.confidence_score
        }],
        is_recommended=pred.confidence_score > 0.6,
        risk_level='LOW' if pred.confidence_score > 0.7 else 'MEDIUM'
    )
    db.add(combo)
    combinations_created['SINGLE'] += 1

print(f"   ✅ {combinations_created['SINGLE']} singles criados")

# ========== 250 DOUBLES ==========
print("\n🎯 Gerando 250 DOUBLES...")
doubles_target = 250

# Pegar predictions de jogos diferentes
matches_with_preds = {}
for pred in good_predictions:
    if pred.match_id not in matches_with_preds:
        matches_with_preds[pred.match_id] = []
    matches_with_preds[pred.match_id].append(pred)

match_ids = list(matches_with_preds.keys())

doubles_created = 0
attempts = 0
max_attempts = 1000

while doubles_created < doubles_target and attempts < max_attempts:
    attempts += 1

    # Pegar 2 jogos aleatórios
    if len(match_ids) < 2:
        break

    selected_matches = random.sample(match_ids, 2)

    # Pegar 1 prediction de cada jogo
    pred1 = random.choice(matches_with_preds[selected_matches[0]])
    pred2 = random.choice(matches_with_preds[selected_matches[1]])

    # Calcular odds combinadas
    total_odds = (pred1.actual_odds or 1.5) * (pred2.actual_odds or 1.5)
    combined_prob = pred1.confidence_score * pred2.confidence_score

    combo = BetCombination(
        combination_type='DOUBLE',
        selections_count=2,
        total_odds=total_odds,
        combined_probability=combined_prob,
        combined_confidence=combined_prob,
        expected_value=total_odds * combined_prob,
        risk_score=1 - combined_prob,
        prediction_ids=[pred1.id, pred2.id],
        selection_details=[
            {
                'match_id': pred1.match_id,
                'market': pred1.market_type,
                'selection': pred1.predicted_outcome,
                'odd': pred1.actual_odds,
                'confidence': pred1.confidence_score
            },
            {
                'match_id': pred2.match_id,
                'market': pred2.market_type,
                'selection': pred2.predicted_outcome,
                'odd': pred2.actual_odds,
                'confidence': pred2.confidence_score
            }
        ],
        is_recommended=combined_prob > 0.4,
        risk_level='LOW' if combined_prob > 0.5 else 'MEDIUM' if combined_prob > 0.3 else 'HIGH'
    )
    db.add(combo)
    doubles_created += 1
    combinations_created['DOUBLE'] += 1

print(f"   ✅ {combinations_created['DOUBLE']} doubles criados")

# ========== 250 TREBLES ==========
print("\n🎯 Gerando 250 TREBLES...")
trebles_target = 250

trebles_created = 0
attempts = 0
max_attempts = 1000

while trebles_created < trebles_target and attempts < max_attempts:
    attempts += 1

    # Pegar 3 jogos aleatórios
    if len(match_ids) < 3:
        break

    selected_matches = random.sample(match_ids, 3)

    # Pegar 1 prediction de cada jogo
    pred1 = random.choice(matches_with_preds[selected_matches[0]])
    pred2 = random.choice(matches_with_preds[selected_matches[1]])
    pred3 = random.choice(matches_with_preds[selected_matches[2]])

    # Calcular odds combinadas
    total_odds = (pred1.actual_odds or 1.5) * (pred2.actual_odds or 1.5) * (pred3.actual_odds or 1.5)
    combined_prob = pred1.confidence_score * pred2.confidence_score * pred3.confidence_score

    combo = BetCombination(
        combination_type='TREBLE',
        selections_count=3,
        total_odds=total_odds,
        combined_probability=combined_prob,
        combined_confidence=combined_prob,
        expected_value=total_odds * combined_prob,
        risk_score=1 - combined_prob,
        prediction_ids=[pred1.id, pred2.id, pred3.id],
        selection_details=[
            {
                'match_id': pred1.match_id,
                'market': pred1.market_type,
                'selection': pred1.predicted_outcome,
                'odd': pred1.actual_odds,
                'confidence': pred1.confidence_score
            },
            {
                'match_id': pred2.match_id,
                'market': pred2.market_type,
                'selection': pred2.predicted_outcome,
                'odd': pred2.actual_odds,
                'confidence': pred2.confidence_score
            },
            {
                'match_id': pred3.match_id,
                'market': pred3.market_type,
                'selection': pred3.predicted_outcome,
                'odd': pred3.actual_odds,
                'confidence': pred3.confidence_score
            }
        ],
        is_recommended=combined_prob > 0.3,
        risk_level='MEDIUM' if combined_prob > 0.3 else 'HIGH'
    )
    db.add(combo)
    trebles_created += 1
    combinations_created['TREBLE'] += 1

print(f"   ✅ {combinations_created['TREBLE']} trebles criados")

# ========== 250 QUADRUPLES ==========
print("\n🎯 Gerando 250 QUADRUPLES...")
quads_target = 250

quads_created = 0
attempts = 0
max_attempts = 1000

while quads_created < quads_target and attempts < max_attempts:
    attempts += 1

    # Pegar 4 jogos aleatórios
    if len(match_ids) < 4:
        break

    selected_matches = random.sample(match_ids, 4)

    # Pegar 1 prediction de cada jogo
    pred1 = random.choice(matches_with_preds[selected_matches[0]])
    pred2 = random.choice(matches_with_preds[selected_matches[1]])
    pred3 = random.choice(matches_with_preds[selected_matches[2]])
    pred4 = random.choice(matches_with_preds[selected_matches[3]])

    # Calcular odds combinadas
    total_odds = (pred1.actual_odds or 1.5) * (pred2.actual_odds or 1.5) * (pred3.actual_odds or 1.5) * (pred4.actual_odds or 1.5)
    combined_prob = pred1.confidence_score * pred2.confidence_score * pred3.confidence_score * pred4.confidence_score

    combo = BetCombination(
        combination_type='QUAD',
        selections_count=4,
        total_odds=total_odds,
        combined_probability=combined_prob,
        combined_confidence=combined_prob,
        expected_value=total_odds * combined_prob,
        risk_score=1 - combined_prob,
        prediction_ids=[pred1.id, pred2.id, pred3.id, pred4.id],
        selection_details=[
            {
                'match_id': pred1.match_id,
                'market': pred1.market_type,
                'selection': pred1.predicted_outcome,
                'odd': pred1.actual_odds,
                'confidence': pred1.confidence_score
            },
            {
                'match_id': pred2.match_id,
                'market': pred2.market_type,
                'selection': pred2.predicted_outcome,
                'odd': pred2.actual_odds,
                'confidence': pred2.confidence_score
            },
            {
                'match_id': pred3.match_id,
                'market': pred3.market_type,
                'selection': pred3.predicted_outcome,
                'odd': pred3.actual_odds,
                'confidence': pred3.confidence_score
            },
            {
                'match_id': pred4.match_id,
                'market': pred4.market_type,
                'selection': pred4.predicted_outcome,
                'odd': pred4.actual_odds,
                'confidence': pred4.confidence_score
            }
        ],
        is_recommended=combined_prob > 0.2,
        risk_level='HIGH'
    )
    db.add(combo)
    quads_created += 1
    combinations_created['QUAD'] += 1

print(f"   ✅ {combinations_created['QUAD']} quadruples criados")

db.commit()

print("\n" + "=" * 80)
print("✅ GERAÇÃO COMPLETA!")
print("=" * 80)
print(f"\n📊 RESUMO:")
print(f"   Singles:     {combinations_created['SINGLE']}")
print(f"   Doubles:     {combinations_created['DOUBLE']}")
print(f"   Trebles:     {combinations_created['TREBLE']}")
print(f"   Quadruples:  {combinations_created['QUAD']}")
print(f"\n   TOTAL:       {sum(combinations_created.values())} bet combinations")
print(f"   Predictions: {len(all_predictions)} individuais")
print("=" * 80)

db.close()
