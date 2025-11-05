#!/usr/bin/env python3
"""
Script para validar predictions manualmente após jogos terminarem
"""

from app.core.database import SessionLocal
from app.models.prediction import Prediction
from app.models.match import Match
from app.models.team import Team

def main():
    db = SessionLocal()

    print('🎯 VALIDANDO PREDICTIONS:')
    print('=' * 60)
    print()

    # Buscar singles v3 não validados
    predictions = db.query(Prediction).filter(
        Prediction.model_version == 'ml_generator_v3',
        Prediction.prediction_type == 'SINGLE',
        Prediction.is_validated == False
    ).all()

    total = len(predictions)
    wins = 0
    losses = 0

    for pred in predictions:
        match = db.query(Match).filter(Match.id == pred.match_id).first()

        if not match or match.status != 'FINISHED':
            continue

        home = db.query(Team).filter(Team.id == match.home_team_id).first()
        away = db.query(Team).filter(Team.id == match.away_team_id).first()

        # Verificar resultado
        is_winner = False

        if pred.market_type == 'HOME_WIN':
            is_winner = match.home_score > match.away_score
        elif pred.market_type == 'AWAY_WIN':
            is_winner = match.away_score > match.home_score
        elif pred.market_type == 'DRAW':
            is_winner = match.home_score == match.away_score
        elif pred.market_type == 'BTTS_YES':
            is_winner = match.home_score > 0 and match.away_score > 0
        elif pred.market_type == 'BTTS_NO':
            is_winner = match.home_score == 0 or match.away_score == 0

        # Atualizar prediction
        pred.is_validated = True
        pred.is_winner = is_winner
        pred.actual_outcome = f'{match.home_score}x{match.away_score}'

        if is_winner:
            wins += 1
            result_icon = '✅ GREEN'
        else:
            losses += 1
            result_icon = '❌ RED'

        home_name = home.name if home else '?'
        away_name = away.name if away else '?'

        print(f'{result_icon} | {home_name} {match.home_score} x {match.away_score} {away_name}')
        print(f'       Pred: {pred.market_type} | Prob: {pred.predicted_probability:.1%} | Conf: {pred.confidence_score:.1%}')
        print()

    db.commit()

    accuracy = (wins / total * 100) if total > 0 else 0

    print('=' * 60)
    print(f'📊 RESULTADOS FINAIS:')
    print(f'Total: {total}')
    print(f'Wins (GREEN): {wins}')
    print(f'Losses (RED): {losses}')
    print(f'Accuracy: {accuracy:.1f}%')
    print(f'Accuracy esperada: 58.9%')
    print()

    if accuracy >= 50:
        print('🎉 SUCESSO! Accuracy acima de 50%!')
    else:
        print('⚠️  ATENÇÃO: Accuracy abaixo de 50%')

    db.close()

if __name__ == '__main__':
    main()
