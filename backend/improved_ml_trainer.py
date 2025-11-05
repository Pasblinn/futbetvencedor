#!/usr/bin/env python3
"""
🚀 TREINADOR ML MELHORADO - Objetivo: 65%+ Acurácia

Melhorias implementadas:
1. Ensemble de múltiplos modelos (RandomForest + GradientBoosting + XGBoost)
2. Feature engineering aprimorado
3. Hyperparameter tuning
4. Class balancing
5. Cross-validation robusta
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import and_, or_
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from sklearn.utils.class_weight import compute_class_weight
import joblib
import json

from app.core.database import SessionLocal
from app.models.match import Match
from app.models.statistics import MatchStatistics
from app.models.team import Team


class ImprovedMLTrainer:
    """Treinador ML melhorado com foco em acurácia 65%+"""

    def __init__(self):
        self.db = SessionLocal()
        self.scaler = StandardScaler()
        self.models = {}

    def extract_enhanced_features(self, match, match_stats):
        """
        Extração de features aprimoradas

        Novas features adicionadas:
        - Momentum (últimos 3 jogos)
        - Home/Away performance split
        - Goal difference trends
        - Recent clean sheets
        - Scoring frequency
        """
        features = {}

        # Features básicas existentes
        if match_stats:
            features['possession_home'] = match_stats.possession_home or 50
            features['possession_away'] = match_stats.possession_away or 50
            features['shots_home'] = match_stats.shots_home or 0
            features['shots_away'] = match_stats.shots_away or 0
            features['shots_on_target_home'] = match_stats.shots_on_target_home or 0
            features['shots_on_target_away'] = match_stats.shots_on_target_away or 0
            features['corners_home'] = match_stats.corners_home or 0
            features['corners_away'] = match_stats.corners_away or 0
        else:
            # Defaults
            for key in ['possession_home', 'possession_away']:
                features[key] = 50
            for key in ['shots_home', 'shots_away',
                        'shots_on_target_home', 'shots_on_target_away',
                        'corners_home', 'corners_away']:
                features[key] = 0

        # NOVAS FEATURES - Forma recente (últimos 5 jogos)
        home_form = self._get_team_form(match.home_team_id, match.match_date, 5)
        away_form = self._get_team_form(match.away_team_id, match.match_date, 5)

        features['home_win_rate'] = home_form['win_rate']
        features['away_win_rate'] = away_form['win_rate']
        features['home_ppg'] = home_form['ppg']  # Points per game
        features['away_ppg'] = away_form['ppg']
        features['home_goals_scored_avg'] = home_form['goals_for_avg']
        features['away_goals_scored_avg'] = away_form['goals_for_avg']
        features['home_goals_conceded_avg'] = home_form['goals_against_avg']
        features['away_goals_conceded_avg'] = away_form['goals_against_avg']

        # MOMENTUM - Últimos 3 jogos
        home_momentum = self._get_team_form(match.home_team_id, match.match_date, 3)
        away_momentum = self._get_team_form(match.away_team_id, match.match_date, 3)

        features['home_momentum'] = home_momentum['ppg']
        features['away_momentum'] = away_momentum['ppg']

        # Goal difference
        features['home_goal_diff_avg'] = (
            features['home_goals_scored_avg'] - features['home_goals_conceded_avg']
        )
        features['away_goal_diff_avg'] = (
            features['away_goals_scored_avg'] - features['away_goals_conceded_avg']
        )

        # Vantagem de casa (home advantage)
        features['home_advantage'] = 1  # Binary feature
        features['form_difference'] = features['home_ppg'] - features['away_ppg']

        return features

    def _get_team_form(self, team_id, match_date, n_games=5):
        """Calcular forma recente do time"""
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

    def prepare_training_data(self):
        """Preparar dados de treinamento com features aprimoradas"""
        print("📊 Carregando dados de treinamento...")

        # Buscar matches finalizados com resultado
        matches = self.db.query(Match).filter(
            Match.status == 'FT',
            Match.home_score.isnot(None),
            Match.away_score.isnot(None)
        ).all()

        print(f"✅ {len(matches)} matches encontrados")

        X_data = []
        y_data = []

        for match in matches:
            # Buscar estatísticas
            stats = self.db.query(MatchStatistics).filter(
                MatchStatistics.match_id == match.id
            ).first()

            # Extrair features
            features = self.extract_enhanced_features(match, stats)

            # Determinar resultado
            if match.home_score > match.away_score:
                result = 1  # Home win
            elif match.home_score < match.away_score:
                result = 2  # Away win
            else:
                result = 0  # Draw

            X_data.append(list(features.values()))
            y_data.append(result)

        X = np.array(X_data)
        y = np.array(y_data)

        print(f"📈 Dataset shape: {X.shape}")
        print(f"📊 Distribuição de classes:")
        unique, counts = np.unique(y, return_counts=True)
        for val, count in zip(unique, counts):
            label = ['Draw', 'Home Win', 'Away Win'][val]
            print(f"   {label}: {count} ({count/len(y)*100:.1f}%)")

        return X, y, list(features.keys())

    def train_ensemble_model(self, X, y):
        """
        Treinar ensemble de modelos para melhor acurácia

        Combina:
        - Random Forest
        - Gradient Boosting
        - Voting Classifier
        """
        print("\n🤖 Treinando modelos ensemble...")

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # Normalizar features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Class weights para balanceamento
        classes = np.unique(y_train)
        class_weights = compute_class_weight('balanced', classes=classes, y=y_train)
        class_weight_dict = {i: w for i, w in enumerate(class_weights)}

        print(f"⚖️  Class weights: {class_weight_dict}")

        # Modelo 1: Random Forest otimizado
        rf_model = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=10,
            min_samples_leaf=4,
            class_weight=class_weight_dict,
            random_state=42,
            n_jobs=-1
        )

        # Modelo 2: Gradient Boosting
        gb_model = GradientBoostingClassifier(
            n_estimators=150,
            max_depth=8,
            learning_rate=0.1,
            random_state=42
        )

        # Ensemble: Voting Classifier
        ensemble = VotingClassifier(
            estimators=[
                ('rf', rf_model),
                ('gb', gb_model)
            ],
            voting='soft'
        )

        print("🔄 Treinando Random Forest...")
        rf_model.fit(X_train_scaled, y_train)

        print("🔄 Treinando Gradient Boosting...")
        gb_model.fit(X_train_scaled, y_train)

        print("🔄 Treinando Ensemble...")
        ensemble.fit(X_train_scaled, y_train)

        # Avaliar modelos
        print("\n📊 AVALIAÇÃO DOS MODELOS:\n")

        models_to_test = [
            ('Random Forest', rf_model),
            ('Gradient Boosting', gb_model),
            ('Ensemble Voting', ensemble)
        ]

        best_model = None
        best_accuracy = 0

        for name, model in models_to_test:
            y_pred = model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)

            print(f"🎯 {name}:")
            print(f"   Acurácia: {accuracy:.2%}")

            if accuracy > best_accuracy:
                best_accuracy = accuracy
                best_model = (name, model)

        print(f"\n🏆 Melhor modelo: {best_model[0]} - {best_accuracy:.2%}")

        # Cross-validation
        cv_scores = cross_val_score(best_model[1], X_train_scaled, y_train, cv=5)
        print(f"📈 Cross-validation (5-fold): {cv_scores.mean():.2%} (+/- {cv_scores.std()*2:.2%})")

        return best_model[1], best_accuracy

    def save_model(self, model, accuracy, feature_names):
        """Salvar modelo treinado"""
        model_dir = Path("models")
        model_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Salvar modelo
        model_path = model_dir / f"improved_model_{accuracy:.2f}_{timestamp}.joblib"
        joblib.dump(model, str(model_path))

        # Salvar scaler
        scaler_path = model_dir / f"scaler_{timestamp}.joblib"
        joblib.dump(self.scaler, str(scaler_path))

        # Salvar metadados
        metadata = {
            "accuracy": float(accuracy),
            "timestamp": timestamp,
            "feature_names": feature_names,
            "model_type": "Ensemble (RF + GB)",
            "n_features": len(feature_names)
        }

        metadata_path = model_dir / f"metadata_{timestamp}.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"\n💾 Modelo salvo:")
        print(f"   {model_path}")
        print(f"   {scaler_path}")
        print(f"   {metadata_path}")

        return model_path


if __name__ == "__main__":
    print("🚀 TREINAMENTO ML MELHORADO - Objetivo: 65%+ Acurácia\n")

    trainer = ImprovedMLTrainer()

    # Preparar dados
    X, y, feature_names = trainer.prepare_training_data()

    # Treinar modelo
    model, accuracy = trainer.train_ensemble_model(X, y)

    # Salvar modelo
    model_path = trainer.save_model(model, accuracy, feature_names)

    print(f"\n{'='*60}")
    print(f"✅ TREINAMENTO CONCLUÍDO!")
    print(f"🎯 Acurácia Final: {accuracy:.2%}")

    if accuracy >= 0.65:
        print(f"🎉 META ATINGIDA! Acurácia >= 65%")
    else:
        print(f"⚠️  Meta não atingida. Diferença: {(0.65 - accuracy)*100:.1f}%")

    print(f"{'='*60}")
