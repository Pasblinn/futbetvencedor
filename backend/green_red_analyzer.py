#!/usr/bin/env python3
"""
🟢🔴 ANALISADOR GREEN/RED AUTOMÁTICO
Verifica jogos finalizados e marca predictions como GREEN (acerto) ou RED (erro)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime
from sqlalchemy import and_
from app.core.database import SessionLocal
from app.models import Match, Prediction, Odds

class GreenRedAnalyzer:
    """Analisa predictions e marca GREEN ou RED"""

    def __init__(self):
        self.db = SessionLocal()
        self.greens = 0
        self.reds = 0
        self.total = 0

    def analyze_finished_matches(self):
        """Analisar todos os jogos finalizados"""
        print("🎯 ANÁLISE GREEN/RED - JOGOS FINALIZADOS\n")
        print("="*70)

        # Buscar jogos finalizados
        finished_matches = self.db.query(Match).filter(
            Match.status.in_(['FT', 'FINISHED']),
            Match.home_score.isnot(None),
            Match.away_score.isnot(None)
        ).all()

        print(f"📊 {len(finished_matches)} jogos finalizados encontrados\n")

        for match in finished_matches:
            # Buscar prediction
            prediction = self.db.query(Prediction).filter(
                Prediction.match_id == match.id,
                Prediction.market_type == '1X2'
            ).first()

            if not prediction:
                continue

            # Determinar resultado real
            if match.home_score > match.away_score:
                actual_outcome = '1'
            elif match.home_score < match.away_score:
                actual_outcome = '2'
            else:
                actual_outcome = 'X'

            # Comparar com prediction
            is_correct = (prediction.predicted_outcome == actual_outcome)

            # Atualizar prediction
            prediction.actual_outcome = actual_outcome
            prediction.is_winner = is_correct

            # Calcular lucro/prejuízo se houver odds
            if hasattr(prediction, 'actual_odds') and prediction.actual_odds:
                if is_correct:
                    # GREEN: ganhou (odds - 1) * stake
                    prediction.profit_loss = (prediction.actual_odds - 1) * 100  # stake = 100
                else:
                    # RED: perdeu stake
                    prediction.profit_loss = -100

            self.total += 1
            if is_correct:
                self.greens += 1
                status = "🟢 GREEN"
            else:
                self.reds += 1
                status = "🔴 RED"

            print(f"{status} | {match.home_team.name} {match.home_score}-{match.away_score} {match.away_team.name}")
            print(f"        Prediction: {prediction.predicted_outcome} | Real: {actual_outcome}")

        self.db.commit()

        # Estatísticas
        print("\n" + "="*70)
        print("📊 ESTATÍSTICAS")
        print("="*70)
        print(f"🎯 Total analisado: {self.total}")
        print(f"🟢 GREEN (acertos): {self.greens} ({self.greens/self.total*100:.1f}%)" if self.total > 0 else "🟢 GREEN: 0")
        print(f"🔴 RED (erros): {self.reds} ({self.reds/self.total*100:.1f}%)" if self.total > 0 else "🔴 RED: 0")

        accuracy = (self.greens / self.total * 100) if self.total > 0 else 0
        print(f"\n📈 ACURÁCIA REAL: {accuracy:.1f}%")

        return {
            'total': self.total,
            'greens': self.greens,
            'reds': self.reds,
            'accuracy': accuracy
        }

    def get_statistics(self):
        """Obter estatísticas GREEN/RED"""
        total = self.db.query(Prediction).filter(
            Prediction.actual_outcome.isnot(None)
        ).count()

        greens = self.db.query(Prediction).filter(
            Prediction.is_winner == True
        ).count()

        reds = self.db.query(Prediction).filter(
            Prediction.is_winner == False
        ).count()

        return {
            'total': total,
            'greens': greens,
            'reds': reds,
            'accuracy': (greens / total * 100) if total > 0 else 0
        }

    def export_green_red_report(self):
        """Exportar relatório GREEN/RED"""
        from datetime import date
        import json

        stats = self.get_statistics()

        # Buscar todas predictions com resultado
        predictions = self.db.query(Prediction).filter(
            Prediction.actual_outcome.isnot(None)
        ).all()

        report_data = []

        for pred in predictions:
            match = self.db.query(Match).filter(Match.id == pred.match_id).first()

            if match:
                report_data.append({
                    'date': match.match_date.date().isoformat(),
                    'match': f"{match.home_team.name} vs {match.away_team.name}",
                    'score': f"{match.home_score}-{match.away_score}",
                    'predicted': pred.predicted_outcome,
                    'actual': pred.actual_outcome,
                    'result': 'GREEN' if pred.is_winner else 'RED',
                    'confidence': float(pred.confidence_score) if pred.confidence_score else None,
                    'profit_loss': float(pred.profit_loss) if pred.profit_loss else None
                })

        # Salvar relatório
        report_dir = Path("green_red_reports")
        report_dir.mkdir(exist_ok=True)

        today = date.today().isoformat()
        report_file = report_dir / f"green_red_report_{today}.json"

        with open(report_file, 'w') as f:
            json.dump({
                'generated_at': datetime.now().isoformat(),
                'statistics': stats,
                'predictions': report_data
            }, f, indent=2)

        print(f"\n💾 Relatório salvo: {report_file}")

        return report_file


if __name__ == "__main__":
    print("🟢🔴 SISTEMA DE ANÁLISE GREEN/RED\n")

    analyzer = GreenRedAnalyzer()

    # Analisar jogos finalizados
    stats = analyzer.analyze_finished_matches()

    # Exportar relatório
    if stats['total'] > 0:
        analyzer.export_green_red_report()

    print("\n" + "="*70)
    print("✅ ANÁLISE CONCLUÍDA!")
    print("="*70)
