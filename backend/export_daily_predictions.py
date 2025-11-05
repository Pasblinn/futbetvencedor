#!/usr/bin/env python3
"""
📊 EXPORTADOR DE PREDIÇÕES DIÁRIAS
Salva predictions em arquivos separados por dia para treinar ML
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import json
import csv
from datetime import datetime, timedelta
from app.core.database import SessionLocal
from app.models import Match, Prediction, Odds

class DailyPredictionExporter:
    """Exporta predictions diárias para arquivos CSV e JSON"""

    def __init__(self):
        self.db = SessionLocal()
        self.export_dir = Path("ml_training_data")
        self.export_dir.mkdir(exist_ok=True)

    def export_today_predictions(self):
        """Exportar predictions de hoje"""
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)

        # Buscar matches de hoje
        matches = self.db.query(Match).filter(
            Match.match_date >= datetime.combine(today, datetime.min.time()),
            Match.match_date < datetime.combine(tomorrow, datetime.min.time())
        ).all()

        predictions_data = []

        for match in matches:
            # Buscar prediction
            prediction = self.db.query(Prediction).filter(
                Prediction.match_id == match.id,
                Prediction.market_type == '1X2'
            ).first()

            # Buscar odds
            odds = self.db.query(Odds).filter(
                Odds.match_id == match.id,
                Odds.market == '1X2'
            ).first()

            if prediction:
                data = {
                    'date': today.isoformat(),
                    'match_id': match.id,
                    'external_id': match.external_id,
                    'home_team': match.home_team.name,
                    'away_team': match.away_team.name,
                    'league': match.league,
                    'match_date': match.match_date.isoformat(),
                    'status': match.status,
                    'home_score': match.home_score,
                    'away_score': match.away_score,
                    # Prediction
                    'predicted_outcome': prediction.predicted_outcome,
                    'confidence_score': float(prediction.confidence_score) if prediction.confidence_score else None,
                    'probability_home': float(prediction.probability_home) if hasattr(prediction, 'probability_home') and prediction.probability_home else None,
                    'probability_draw': float(prediction.probability_draw) if hasattr(prediction, 'probability_draw') and prediction.probability_draw else None,
                    'probability_away': float(prediction.probability_away) if hasattr(prediction, 'probability_away') and prediction.probability_away else None,
                    'model_version': prediction.model_version if hasattr(prediction, 'model_version') else None,
                    # Odds
                    'odds_home': float(odds.home_win) if odds else None,
                    'odds_draw': float(odds.draw) if odds else None,
                    'odds_away': float(odds.away_win) if odds else None,
                    'bookmaker': odds.bookmaker if odds else None,
                    # Actual outcome (to be filled after match)
                    'actual_outcome': None,
                    'is_correct': None
                }

                # Determinar actual outcome se o jogo já terminou
                if match.status in ['FT', 'FINISHED'] and match.home_score is not None and match.away_score is not None:
                    if match.home_score > match.away_score:
                        data['actual_outcome'] = '1'
                    elif match.home_score < match.away_score:
                        data['actual_outcome'] = '2'
                    else:
                        data['actual_outcome'] = 'X'

                    data['is_correct'] = (data['predicted_outcome'] == data['actual_outcome'])

                predictions_data.append(data)

        # Salvar em JSON
        json_file = self.export_dir / f"predictions_{today.isoformat()}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(predictions_data, f, indent=2, ensure_ascii=False)

        print(f"✅ JSON salvo: {json_file}")

        # Salvar em CSV
        if predictions_data:
            csv_file = self.export_dir / f"predictions_{today.isoformat()}.csv"
            fieldnames = predictions_data[0].keys()

            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(predictions_data)

            print(f"✅ CSV salvo: {csv_file}")

        return len(predictions_data)

    def export_historical_predictions(self, days_back=30):
        """Exportar predictions dos últimos N dias"""
        print(f"\n📅 Exportando predictions dos últimos {days_back} dias...")

        today = datetime.now().date()

        for i in range(days_back):
            target_date = today - timedelta(days=i)
            next_date = target_date + timedelta(days=1)

            # Buscar matches da data
            matches = self.db.query(Match).filter(
                Match.match_date >= datetime.combine(target_date, datetime.min.time()),
                Match.match_date < datetime.combine(next_date, datetime.min.time())
            ).all()

            predictions_data = []

            for match in matches:
                prediction = self.db.query(Prediction).filter(
                    Prediction.match_id == match.id,
                    Prediction.market_type == '1X2'
                ).first()

                odds = self.db.query(Odds).filter(
                    Odds.match_id == match.id,
                    Odds.market == '1X2'
                ).first()

                if prediction:
                    data = {
                        'date': target_date.isoformat(),
                        'match_id': match.id,
                        'external_id': match.external_id,
                        'home_team': match.home_team.name,
                        'away_team': match.away_team.name,
                        'league': match.league,
                        'match_date': match.match_date.isoformat(),
                        'status': match.status,
                        'home_score': match.home_score,
                        'away_score': match.away_score,
                        'predicted_outcome': prediction.predicted_outcome,
                        'confidence_score': float(prediction.confidence_score) if prediction.confidence_score else None,
                        'probability_home': float(prediction.probability_home) if hasattr(prediction, 'probability_home') and prediction.probability_home else None,
                        'probability_draw': float(prediction.probability_draw) if hasattr(prediction, 'probability_draw') and prediction.probability_draw else None,
                        'probability_away': float(prediction.probability_away) if hasattr(prediction, 'probability_away') and prediction.probability_away else None,
                        'odds_home': float(odds.home_win) if odds else None,
                        'odds_draw': float(odds.draw) if odds else None,
                        'odds_away': float(odds.away_win) if odds else None,
                        'actual_outcome': None,
                        'is_correct': None
                    }

                    # Determinar resultado real
                    if match.status in ['FT', 'FINISHED'] and match.home_score is not None and match.away_score is not None:
                        if match.home_score > match.away_score:
                            data['actual_outcome'] = '1'
                        elif match.home_score < match.away_score:
                            data['actual_outcome'] = '2'
                        else:
                            data['actual_outcome'] = 'X'

                        data['is_correct'] = (data['predicted_outcome'] == data['actual_outcome'])

                    predictions_data.append(data)

            if predictions_data:
                # Salvar JSON
                json_file = self.export_dir / f"predictions_{target_date.isoformat()}.json"
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(predictions_data, f, indent=2, ensure_ascii=False)

                # Salvar CSV
                csv_file = self.export_dir / f"predictions_{target_date.isoformat()}.csv"
                with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=predictions_data[0].keys())
                    writer.writeheader()
                    writer.writerows(predictions_data)

                print(f"   ✅ {target_date}: {len(predictions_data)} predictions exportadas")

        print(f"\n✅ Exportação histórica concluída!")

    def generate_training_summary(self):
        """Gerar resumo de dados de treinamento"""
        files = list(self.export_dir.glob("predictions_*.json"))

        total_predictions = 0
        total_correct = 0
        total_with_results = 0

        for file in files:
            with open(file, 'r') as f:
                data = json.load(f)
                total_predictions += len(data)

                for pred in data:
                    if pred.get('actual_outcome'):
                        total_with_results += 1
                        if pred.get('is_correct'):
                            total_correct += 1

        accuracy = (total_correct / total_with_results * 100) if total_with_results > 0 else 0

        summary = {
            'total_files': len(files),
            'total_predictions': total_predictions,
            'predictions_with_results': total_with_results,
            'correct_predictions': total_correct,
            'accuracy_percentage': round(accuracy, 2),
            'generated_at': datetime.now().isoformat()
        }

        summary_file = self.export_dir / "training_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"\n📊 RESUMO DE DADOS DE TREINAMENTO:")
        print(f"   📁 Arquivos: {summary['total_files']}")
        print(f"   🎯 Total predictions: {summary['total_predictions']}")
        print(f"   ✅ Com resultados: {summary['predictions_with_results']}")
        print(f"   🎉 Corretas: {summary['correct_predictions']}")
        print(f"   📈 Acurácia: {summary['accuracy_percentage']}%")
        print(f"\n💾 Resumo salvo em: {summary_file}")


if __name__ == "__main__":
    print("🚀 EXPORTADOR DE PREDIÇÕES DIÁRIAS\n")
    print("="*70)

    exporter = DailyPredictionExporter()

    # Exportar predictions de hoje
    count_today = exporter.export_today_predictions()
    print(f"\n✅ {count_today} predictions de hoje exportadas")

    # Exportar histórico (últimos 7 dias)
    exporter.export_historical_predictions(days_back=7)

    # Gerar resumo
    exporter.generate_training_summary()

    print("\n" + "="*70)
    print("✅ EXPORTAÇÃO CONCLUÍDA!")
    print("="*70)
