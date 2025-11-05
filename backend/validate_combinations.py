#!/usr/bin/env python3
"""
Script para validar combinações (doubles, trebles, multiples)
"""

from app.core.database import SessionLocal
from app.models.prediction import Prediction
import json

def main():
    db = SessionLocal()

    print('🎯 VALIDANDO COMBINAÇÕES:')
    print('=' * 80)
    print()

    # Buscar todas as combinações v3_combo não validadas
    combinations = db.query(Prediction).filter(
        Prediction.model_version == 'ml_generator_v3_combo',
        Prediction.is_validated == False
    ).all()

    # Buscar todas as predictions singles já validadas
    singles = db.query(Prediction).filter(
        Prediction.model_version == 'ml_generator_v3',
        Prediction.prediction_type == 'SINGLE',
        Prediction.is_validated == True
    ).all()

    # Criar dicionário de resultados por match_id
    singles_results = {}
    for single in singles:
        singles_results[single.match_id] = single.is_winner

    print(f'📊 Singles validados: {len(singles)}')
    print(f'📦 Combinações a validar: {len(combinations)}')
    print()

    stats_by_type = {
        'DOUBLE': {'total': 0, 'wins': 0, 'losses': 0},
        'TREBLE': {'total': 0, 'wins': 0, 'losses': 0},
        'MULTIPLE': {'total': 0, 'wins': 0, 'losses': 0}
    }

    for combo in combinations:
        # Parse analysis_summary para extrair match_ids
        summary = combo.analysis_summary
        match_ids = []

        # Extrair match_ids do summary
        if 'Double: Match' in summary:
            parts = summary.split('Match ')[1].split(' + ')
            match_ids = [int(p.strip()) for p in parts]
        elif 'Treble: Matches' in summary:
            parts = summary.split('Matches ')[1].split(', ')
            match_ids = [int(p.strip()) for p in parts]
        elif 'Quad: Matches' in summary:
            parts = summary.split('Matches ')[1].split(', ')
            match_ids = [int(p.strip()) for p in parts]

        # Verificar se TODOS os singles acertaram
        all_wins = True
        combo_details = []

        for match_id in match_ids:
            is_winner = singles_results.get(match_id, False)
            combo_details.append((match_id, is_winner))
            if not is_winner:
                all_wins = False

        # Atualizar combinação
        combo.is_validated = True
        combo.is_winner = all_wins

        combo_type = combo.prediction_type
        stats_by_type[combo_type]['total'] += 1

        if all_wins:
            stats_by_type[combo_type]['wins'] += 1
            result_icon = '✅ GREEN'
        else:
            stats_by_type[combo_type]['losses'] += 1
            result_icon = '❌ RED'

        print(f'{result_icon} | {combo_type} (ID: {combo.id})')
        print(f'       Prob: {combo.predicted_probability:.1%} | Conf: {combo.confidence_score:.1%}')
        print(f'       Matches: {match_ids}')
        for match_id, is_winner in combo_details:
            icon = '✓' if is_winner else '✗'
            print(f'         {icon} Match {match_id}')
        print()

    db.commit()

    # Relatório final
    print('=' * 80)
    print('📊 RESUMO POR TIPO:')
    print()

    total_all = sum(s['total'] for s in stats_by_type.values())
    wins_all = sum(s['wins'] for s in stats_by_type.values())
    losses_all = sum(s['losses'] for s in stats_by_type.values())

    for combo_type, stats in stats_by_type.items():
        if stats['total'] > 0:
            acc = (stats['wins'] / stats['total'] * 100)
            print(f'{combo_type}:')
            print(f'  Total: {stats["total"]}')
            print(f'  Wins: {stats["wins"]}')
            print(f'  Losses: {stats["losses"]}')
            print(f'  Accuracy: {acc:.1f}%')
            print()

    print('=' * 80)
    print('🎯 RESULTADO GERAL DAS COMBINAÇÕES:')
    print(f'Total: {total_all}')
    print(f'Wins: {wins_all}')
    print(f'Losses: {losses_all}')

    if total_all > 0:
        acc_total = (wins_all / total_all * 100)
        print(f'Accuracy: {acc_total:.1f}%')

        if acc_total >= 10:
            print('✅ Resultado dentro do esperado para combinações!')
        else:
            print('⚠️  Accuracy muito baixa para combinações')

    db.close()

if __name__ == '__main__':
    main()
