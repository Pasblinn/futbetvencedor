#!/usr/bin/env python3
"""
🎯 Gerar Predições para Jogos de Hoje
Usa o modelo ML melhorado para gerar predictions reais
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
from datetime import datetime, timedelta
import joblib
from sqlalchemy import and_

from app.core.database import SessionLocal
from app.models.match import Match
from app.models.prediction import Prediction
from app.models.statistics import MatchStatistics

class TodaysPredictionGenerator:
    """Gerador de predições para jogos de hoje"""

    def __init__(self):
        self.db = SessionLocal()
        self.model = None
        self.scaler = None
        self.load_model()

    def load_model(self):
        """Carregar o modelo mais recente"""
        model_dir = Path("models")

        # Buscar modelo mais recente
        model_files = list(model_dir.glob("improved_model_*.joblib"))
        if not model_files:
            # Fallback para modelo antigo
            model_files = list(model_dir.glob("random_forest_enhanced.joblib"))

        if not model_files:
            print("❌ Nenhum modelo encontrado!")
            return

        latest_model = max(model_files, key=lambda p: p.stat().st_mtime)
        print(f"📦 Carregando modelo: {latest_model.name}")

        self.model = joblib.load(str(latest_model))

        # Carregar scaler
        scaler_files = list(model_dir.glob("scaler_*.joblib"))
        if scaler_files:
            latest_scaler = max(scaler_files, key=lambda p: p.stat().st_mtime)
            self.scaler = joblib.load(str(latest_scaler))
            print(f"📊 Scaler carregado: {latest_scaler.name}")

    def get_team_form(self, team_id, match_date, n_games=5):
        """Calcular forma recente do time"""
        from sqlalchemy import or_

        recent_matches = self.db.query(Match).filter(
            or_(Match.home_team_id == team_id, Match.away_team_id == team_id),
            Match.match_date < match_date,
            Match.status == 'FT'
        ).order_by(Match.match_date.desc()).limit(n_games).all()

        wins = draws = losses = 0
        goals_for = goals_against = 0

        for m in recent_matches:
            is_home = m.home_team_id == team_id
            team_score = m.home_score if is_home else m.away_score
            opp_score = m.away_score if is_home else m.home_score

            if team_score is not None and opp_score is not None:
                goals_for += team_score
                goals_against += opp_score

                if team_score > opp_score:
                    wins += 1
                elif team_score == opp_score:
                    draws += 1
                else:
                    losses += 1

        games = len(recent_matches)
        if games == 0:
            return {
                'win_rate': 0.33, 'ppg': 1.0,
                'goals_for_avg': 1.0, 'goals_against_avg': 1.0
            }

        return {
            'win_rate': wins / games,
            'ppg': (wins * 3 + draws) / games,
            'goals_for_avg': goals_for / games,
            'goals_against_avg': goals_against / games
        }

    def extract_features(self, match):
        """Extrair features do match (mesmo formato do treinamento)"""
        features = {}

        # Stats básicas (defaults se não houver)
        stats = self.db.query(MatchStatistics).filter(
            MatchStatistics.match_id == match.id
        ).first()

        if stats:
            features['possession_home'] = stats.possession_home or 50
            features['possession_away'] = stats.possession_away or 50
            features['shots_home'] = stats.shots_home or 10
            features['shots_away'] = stats.shots_away or 10
            features['shots_on_target_home'] = stats.shots_on_target_home or 4
            features['shots_on_target_away'] = stats.shots_on_target_away or 4
            features['corners_home'] = stats.corners_home or 5
            features['corners_away'] = stats.corners_away or 5
        else:
            # Defaults baseados em médias
            features = {
                'possession_home': 50, 'possession_away': 50,
                'shots_home': 12, 'shots_away': 10,
                'shots_on_target_home': 4, 'shots_on_target_away': 3,
                'corners_home': 5, 'corners_away': 4
            }

        # Forma recente
        home_form = self.get_team_form(match.home_team_id, match.match_date, 5)
        away_form = self.get_team_form(match.away_team_id, match.match_date, 5)

        features['home_win_rate'] = home_form['win_rate']
        features['away_win_rate'] = away_form['win_rate']
        features['home_ppg'] = home_form['ppg']
        features['away_ppg'] = away_form['ppg']
        features['home_goals_scored_avg'] = home_form['goals_for_avg']
        features['away_goals_scored_avg'] = away_form['goals_for_avg']
        features['home_goals_conceded_avg'] = home_form['goals_against_avg']
        features['away_goals_conceded_avg'] = away_form['goals_against_avg']

        # Momentum (últimos 3 jogos)
        home_momentum = self.get_team_form(match.home_team_id, match.match_date, 3)
        away_momentum = self.get_team_form(match.away_team_id, match.match_date, 3)

        features['home_momentum'] = home_momentum['ppg']
        features['away_momentum'] = away_momentum['ppg']

        # Goal difference
        features['home_goal_diff_avg'] = (
            features['home_goals_scored_avg'] - features['home_goals_conceded_avg']
        )
        features['away_goal_diff_avg'] = (
            features['away_goals_scored_avg'] - features['away_goals_conceded_avg']
        )

        # Home advantage
        features['home_advantage'] = 1
        features['form_difference'] = features['home_ppg'] - features['away_ppg']

        return list(features.values())

    def generate_predictions(self):
        """Gerar predições para jogos de hoje"""
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)

        # Buscar jogos de hoje
        matches = self.db.query(Match).filter(
            Match.match_date >= datetime.combine(today, datetime.min.time()),
            Match.match_date < datetime.combine(tomorrow, datetime.min.time()),
            Match.status.in_(['NS', 'TBD', 'SCHEDULED'])
        ).all()

        print(f"\n🎯 Gerando predições para {len(matches)} jogos de hoje...")

        predictions_created = 0

        for match in matches:
            # Extrair features
            features = self.extract_features(match)
            X = np.array([features])

            # Normalizar se houver scaler
            if self.scaler:
                X = self.scaler.transform(X)

            # Fazer predição
            proba = self.model.predict_proba(X)[0]
            prediction_class = self.model.predict(X)[0]

            # Mapear classes: 0=Draw, 1=Home, 2=Away
            outcome_map = {0: 'X', 1: '1', 2: '2'}
            predicted_outcome = outcome_map[prediction_class]

            # Probabilidades
            prob_draw = proba[0]
            prob_home = proba[1]
            prob_away = proba[2]

            # Confidence score (máxima probabilidade)
            confidence = max(proba)

            # Verificar se já existe predição
            existing = self.db.query(Prediction).filter(
                Prediction.match_id == match.id,
                Prediction.market_type == '1X2'
            ).first()

            if existing:
                # Atualizar predição existente
                existing.predicted_outcome = predicted_outcome
                existing.confidence_score = float(confidence)
                existing.probability_home = float(prob_home)
                existing.probability_draw = float(prob_draw)
                existing.probability_away = float(prob_away)
                existing.model_version = 'improved_ensemble_v1'
                existing.predicted_at = datetime.now()
                print(f"   ✅ Atualizado: {match.home_team.name} vs {match.away_team.name}")
            else:
                # Criar nova predição
                new_prediction = Prediction(
                    match_id=match.id,
                    market_type='1X2',
                    predicted_outcome=predicted_outcome,
                    confidence_score=float(confidence),
                    probability_home=float(prob_home),
                    probability_draw=float(prob_draw),
                    probability_away=float(prob_away),
                    model_version='improved_ensemble_v1',
                    predicted_at=datetime.now()
                )
                self.db.add(new_prediction)
                print(f"   ✅ Criado: {match.home_team.name} vs {match.away_team.name}")

            # Mostrar predição
            print(f"      Predição: {predicted_outcome} (Conf: {confidence:.1%})")
            print(f"      Probs: H:{prob_home:.1%} D:{prob_draw:.1%} A:{prob_away:.1%}")

            predictions_created += 1

        self.db.commit()
        print(f"\n✅ {predictions_created} predições geradas/atualizadas!")

        return predictions_created


if __name__ == "__main__":
    print("🚀 GERADOR DE PREDIÇÕES PARA HOJE\n")

    generator = TodaysPredictionGenerator()

    if generator.model is None:
        print("❌ Erro ao carregar modelo. Abortando.")
        sys.exit(1)

    count = generator.generate_predictions()

    print(f"\n{'='*60}")
    print(f"✅ CONCLUÍDO! {count} predições prontas")
    print(f"{'='*60}")
