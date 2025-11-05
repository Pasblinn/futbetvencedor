import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import cross_val_score, GridSearchCV
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import xgboost as xgb
import lightgbm as lgb
from typing import Dict, List, Tuple, Optional
import joblib
import logging
from datetime import datetime
from .poisson_predictor import PoissonPredictor, integrate_poisson_with_ensemble

logger = logging.getLogger(__name__)

class EnsemblePredictor:
    """Advanced Ensemble Model combining multiple algorithms"""

    def __init__(self, model_path: str = "models/", use_poisson: bool = True):
        self.model_path = model_path
        self.models = {}
        self.scalers = {}
        self.feature_selectors = {}
        self.use_poisson = use_poisson

        # Initialize Poisson predictor
        if use_poisson:
            self.poisson_predictor = PoissonPredictor(home_advantage=1.3)
            logger.info("Poisson predictor initialized with home advantage factor 1.3")

        # Individual model configurations
        self.base_models = {
            'random_forest': RandomForestClassifier(
                n_estimators=200,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            ),
            'gradient_boosting': GradientBoostingClassifier(
                n_estimators=150,
                learning_rate=0.1,
                max_depth=8,
                random_state=42
            ),
            'xgboost': xgb.XGBClassifier(
                n_estimators=200,
                learning_rate=0.1,
                max_depth=8,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                eval_metric='logloss'
            ),
            'lightgbm': lgb.LGBMClassifier(
                n_estimators=200,
                learning_rate=0.1,
                max_depth=8,
                num_leaves=31,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                verbose=-1
            ),
            'logistic_regression': LogisticRegression(
                random_state=42,
                max_iter=1000,
                solver='liblinear'
            ),
            'svm': SVC(
                kernel='rbf',
                probability=True,
                random_state=42
            )
        }

    def _prepare_advanced_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create advanced features for ensemble models"""
        features = data.copy()

        # Team strength features
        features['team_strength_diff'] = features['home_elo_rating'] - features['away_elo_rating']
        features['form_diff'] = features['home_recent_form'] - features['away_recent_form']
        features['attack_vs_defense'] = features['home_goals_scored_avg'] - features['away_goals_conceded_avg']
        features['defense_vs_attack'] = features['home_goals_conceded_avg'] - features['away_goals_scored_avg']

        # xG features
        if all(col in features.columns for col in ['home_xg_for_avg', 'away_xg_for_avg']):
            features['xg_diff'] = features['home_xg_for_avg'] - features['away_xg_for_avg']
            features['xg_efficiency_home'] = features['home_goals_scored_avg'] / (features['home_xg_for_avg'] + 0.1)
            features['xg_efficiency_away'] = features['away_goals_scored_avg'] / (features['away_xg_for_avg'] + 0.1)

        # Possession and style features
        if 'home_possession_avg' in features.columns:
            features['possession_diff'] = features['home_possession_avg'] - features['away_possession_avg']
            features['high_possession_home'] = (features['home_possession_avg'] > 55).astype(int)
            features['high_possession_away'] = (features['away_possession_avg'] > 55).astype(int)

        # Head-to-head derived features
        if 'h2h_home_wins' in features.columns:
            features['h2h_home_dominance'] = features['h2h_home_wins'] / (features['h2h_home_wins'] + features['h2h_draws'] + features['h2h_away_wins'] + 0.1)
            features['h2h_away_dominance'] = features['h2h_away_wins'] / (features['h2h_home_wins'] + features['h2h_draws'] + features['h2h_away_wins'] + 0.1)
            features['h2h_competitive'] = (features['h2h_draws'] / (features['h2h_home_wins'] + features['h2h_draws'] + features['h2h_away_wins'] + 0.1) > 0.3).astype(int)

        # Motivation and context features
        features['pressure_match'] = ((features['importance_factor'] > 1.2) |
                                     (features['is_derby'] == 1) |
                                     (features['is_rivalry'] == 1)).astype(int)

        # Market expectation features
        if 'home_win_odds' in features.columns:
            features['market_home_prob'] = 1 / features['home_win_odds']
            features['market_draw_prob'] = 1 / features['draw_odds']
            features['market_away_prob'] = 1 / features['away_win_odds']
            features['market_total_prob'] = features['market_home_prob'] + features['market_draw_prob'] + features['market_away_prob']
            features['market_efficiency'] = abs(1 - features['market_total_prob'])

        # Time-based features
        if 'match_date' in features.columns:
            match_dates = pd.to_datetime(features['match_date'])
            features['month'] = match_dates.dt.month
            features['is_weekend'] = match_dates.dt.dayofweek.isin([5, 6]).astype(int)
            features['is_holiday_period'] = match_dates.dt.month.isin([12, 1, 6, 7]).astype(int)

        # Weather impact categories
        if 'weather_impact_score' in features.columns:
            features['severe_weather'] = (features['weather_impact_score'] > 0.6).astype(int)
            features['mild_weather_impact'] = ((features['weather_impact_score'] > 0.2) &
                                              (features['weather_impact_score'] <= 0.6)).astype(int)

        # Injury impact categories
        if 'home_injury_impact' in features.columns:
            features['significant_injuries_home'] = (features['home_injury_impact'] > 0.3).astype(int)
            features['significant_injuries_away'] = (features['away_injury_impact'] > 0.3).astype(int)
            features['injury_advantage'] = features['away_injury_impact'] - features['home_injury_impact']

        # Rest and fatigue features
        if 'rest_days_home' in features.columns:
            features['rest_advantage'] = features['rest_days_home'] - features['rest_days_away']
            features['both_rested'] = ((features['rest_days_home'] >= 5) & (features['rest_days_away'] >= 5)).astype(int)
            features['both_tired'] = ((features['rest_days_home'] <= 3) & (features['rest_days_away'] <= 3)).astype(int)

        return features

    def train_ensemble(self, training_data: pd.DataFrame, target_column: str, prediction_type: str) -> Dict:
        """Train ensemble model for specific prediction"""
        logger.info(f"Training ensemble model for {prediction_type}...")

        # Prepare features
        features_df = self._prepare_advanced_features(training_data)

        # Select relevant features
        feature_columns = [col for col in features_df.columns
                          if col not in ['match_id', 'outcome', 'total_goals', 'both_teams_scored', 'total_corners']]

        X = features_df[feature_columns].fillna(0)
        y = training_data[target_column]

        # Encode labels if necessary
        label_encoder = None
        if y.dtype == 'object':
            label_encoder = LabelEncoder()
            y = label_encoder.fit_transform(y)

        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Train individual models
        trained_models = {}
        model_scores = {}

        for name, model in self.base_models.items():
            try:
                logger.info(f"Training {name}...")

                if name in ['logistic_regression', 'svm']:
                    # Use scaled features for linear models
                    model.fit(X_scaled, y)
                else:
                    # Use original features for tree-based models
                    model.fit(X, y)

                # Cross-validation score
                if name in ['logistic_regression', 'svm']:
                    cv_scores = cross_val_score(model, X_scaled, y, cv=5, scoring='accuracy')
                else:
                    cv_scores = cross_val_score(model, X, y, cv=5, scoring='accuracy')

                trained_models[name] = model
                model_scores[name] = cv_scores.mean()

                logger.info(f"{name} CV Score: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")

            except Exception as e:
                logger.error(f"Error training {name}: {e}")

        # Create voting classifier with best performing models
        best_models = sorted(model_scores.items(), key=lambda x: x[1], reverse=True)[:4]
        ensemble_estimators = [(name, trained_models[name]) for name, score in best_models]

        voting_classifier = VotingClassifier(
            estimators=ensemble_estimators,
            voting='soft'
        )

        # Train voting classifier
        voting_classifier.fit(X, y)

        # Calculate ensemble score
        ensemble_cv_scores = cross_val_score(voting_classifier, X, y, cv=5, scoring='accuracy')
        ensemble_score = ensemble_cv_scores.mean()

        logger.info(f"Ensemble CV Score: {ensemble_score:.4f} (+/- {ensemble_cv_scores.std() * 2:.4f})")

        # Save models
        model_data = {
            'ensemble_model': voting_classifier,
            'individual_models': trained_models,
            'scaler': scaler,
            'label_encoder': label_encoder,
            'feature_columns': feature_columns,
            'model_scores': model_scores,
            'ensemble_score': ensemble_score
        }

        # Save to disk
        joblib.dump(model_data, f"{self.model_path}ensemble_{prediction_type}.pkl")

        # Store in memory
        self.models[prediction_type] = model_data

        return {
            'ensemble_score': ensemble_score,
            'individual_scores': model_scores,
            'best_models': best_models,
            'feature_count': len(feature_columns)
        }

    def predict_ensemble(self, data: pd.DataFrame, prediction_type: str, league_avg_goals: float = 2.7) -> Dict:
        """Make predictions using ensemble model with Poisson integration"""
        if prediction_type not in self.models:
            try:
                model_data = joblib.load(f"{self.model_path}ensemble_{prediction_type}.pkl")
                self.models[prediction_type] = model_data
            except FileNotFoundError:
                raise ValueError(f"Ensemble model for {prediction_type} not found")

        model_data = self.models[prediction_type]
        ensemble_model = model_data['ensemble_model']
        scaler = model_data['scaler']
        feature_columns = model_data['feature_columns']
        label_encoder = model_data['label_encoder']

        # Prepare features
        features_df = self._prepare_advanced_features(data)
        X = features_df[feature_columns].fillna(0)

        # Make predictions
        predictions = ensemble_model.predict(X)
        probabilities = ensemble_model.predict_proba(X)

        # Get individual model predictions for confidence calculation
        individual_predictions = {}
        for name, model in model_data['individual_models'].items():
            try:
                if name in ['logistic_regression', 'svm']:
                    X_scaled = scaler.transform(X)
                    pred_proba = model.predict_proba(X_scaled)
                else:
                    pred_proba = model.predict_proba(X)
                individual_predictions[name] = pred_proba
            except Exception as e:
                logger.warning(f"Error getting prediction from {name}: {e}")

        # Integrate Poisson predictions if enabled
        poisson_predictions = []
        if self.use_poisson and hasattr(self, 'poisson_predictor'):
            for idx in range(len(data)):
                try:
                    home_team_data = {
                        'goals_scored_avg': data.iloc[idx].get('home_goals_scored_avg', 1.5),
                        'goals_conceded_avg': data.iloc[idx].get('home_goals_conceded_avg', 1.5)
                    }
                    away_team_data = {
                        'goals_scored_avg': data.iloc[idx].get('away_goals_scored_avg', 1.5),
                        'goals_conceded_avg': data.iloc[idx].get('away_goals_conceded_avg', 1.5)
                    }

                    poisson_result = self.poisson_predictor.predict_match(
                        home_team_data,
                        away_team_data,
                        league_avg_goals
                    )
                    poisson_predictions.append(poisson_result)

                    # Integrate with ensemble prediction
                    ensemble_probs = {
                        'home': probabilities[idx][0] if probabilities.shape[1] > 0 else 0.33,
                        'draw': probabilities[idx][1] if probabilities.shape[1] > 1 else 0.33,
                        'away': probabilities[idx][2] if probabilities.shape[1] > 2 else 0.33
                    }

                    combined_probs = integrate_poisson_with_ensemble(
                        ensemble_probs,
                        poisson_result,
                        poisson_weight=0.3  # 30% Poisson, 70% ensemble
                    )

                    # Update probabilities with combined values
                    probabilities[idx] = [
                        combined_probs['home'],
                        combined_probs['draw'],
                        combined_probs['away']
                    ]

                except Exception as e:
                    logger.warning(f"Error integrating Poisson for row {idx}: {e}")
                    poisson_predictions.append(None)

        # Calculate prediction confidence
        confidence_scores = self._calculate_ensemble_confidence(individual_predictions, probabilities)

        # Decode labels if necessary
        if label_encoder:
            predictions = label_encoder.inverse_transform(predictions)

        result = {
            'predictions': predictions.tolist(),
            'probabilities': probabilities.tolist(),
            'confidence_scores': confidence_scores,
            'individual_predictions': individual_predictions,
            'ensemble_agreement': self._calculate_agreement(individual_predictions)
        }

        # Add Poisson predictions if available
        if poisson_predictions:
            result['poisson_predictions'] = poisson_predictions
            result['poisson_integrated'] = True

        return result

    def _calculate_ensemble_confidence(self, individual_predictions: Dict, ensemble_probabilities: np.ndarray) -> List[float]:
        """Calculate confidence based on model agreement"""
        if not individual_predictions:
            return [0.5] * len(ensemble_probabilities)

        confidence_scores = []

        for i in range(len(ensemble_probabilities)):
            # Calculate variance in predictions across models
            model_probs = []
            for model_proba in individual_predictions.values():
                model_probs.append(model_proba[i])

            if model_probs:
                # Standard deviation of max probabilities
                max_probs = [np.max(proba) for proba in model_probs]
                agreement = 1 - np.std(max_probs)

                # Ensemble max probability
                ensemble_max = np.max(ensemble_probabilities[i])

                # Combined confidence
                confidence = (agreement + ensemble_max) / 2
                confidence_scores.append(max(0.0, min(1.0, confidence)))
            else:
                confidence_scores.append(0.5)

        return confidence_scores

    def _calculate_agreement(self, individual_predictions: Dict) -> Dict:
        """Calculate agreement metrics between individual models"""
        if not individual_predictions:
            return {}

        agreements = {}
        model_names = list(individual_predictions.keys())

        for i in range(len(model_names)):
            for j in range(i + 1, len(model_names)):
                model1, model2 = model_names[i], model_names[j]
                pred1 = np.argmax(individual_predictions[model1], axis=1)
                pred2 = np.argmax(individual_predictions[model2], axis=1)

                agreement = np.mean(pred1 == pred2)
                agreements[f"{model1}_vs_{model2}"] = agreement

        # Overall agreement
        all_predictions = [np.argmax(pred, axis=1) for pred in individual_predictions.values()]
        if len(all_predictions) > 1:
            # Calculate mode and its frequency
            overall_agreement = []
            for i in range(len(all_predictions[0])):
                sample_preds = [pred[i] for pred in all_predictions]
                mode_count = max([sample_preds.count(val) for val in set(sample_preds)])
                agreement_ratio = mode_count / len(sample_preds)
                overall_agreement.append(agreement_ratio)

            agreements['overall'] = np.mean(overall_agreement)

        return agreements

    def get_feature_importance(self, prediction_type: str) -> Dict:
        """Get feature importance from ensemble models"""
        if prediction_type not in self.models:
            return {}

        model_data = self.models[prediction_type]
        importance_dict = {}

        for name, model in model_data['individual_models'].items():
            if hasattr(model, 'feature_importances_'):
                # Tree-based models
                importances = model.feature_importances_
                importance_dict[name] = dict(zip(model_data['feature_columns'], importances))
            elif hasattr(model, 'coef_'):
                # Linear models
                importances = np.abs(model.coef_[0]) if len(model.coef_.shape) > 1 else np.abs(model.coef_)
                importance_dict[name] = dict(zip(model_data['feature_columns'], importances))

        # Average importance across models
        if importance_dict:
            feature_names = model_data['feature_columns']
            avg_importance = {}

            for feature in feature_names:
                importances = [importance_dict[model].get(feature, 0)
                             for model in importance_dict.keys()]
                avg_importance[feature] = np.mean(importances)

            # Normalize
            total_importance = sum(avg_importance.values())
            if total_importance > 0:
                avg_importance = {k: v/total_importance for k, v in avg_importance.items()}

            return avg_importance

        return {}

    def hyperparameter_tuning(self, training_data: pd.DataFrame, target_column: str, prediction_type: str) -> Dict:
        """Perform hyperparameter tuning for ensemble models"""
        logger.info(f"Performing hyperparameter tuning for {prediction_type}...")

        features_df = self._prepare_advanced_features(training_data)
        feature_columns = [col for col in features_df.columns
                          if col not in ['match_id', 'outcome', 'total_goals', 'both_teams_scored', 'total_corners']]

        X = features_df[feature_columns].fillna(0)
        y = training_data[target_column]

        # Encode labels if necessary
        if y.dtype == 'object':
            label_encoder = LabelEncoder()
            y = label_encoder.fit_transform(y)

        # Hyperparameter grids
        param_grids = {
            'random_forest': {
                'n_estimators': [100, 200, 300],
                'max_depth': [10, 15, 20],
                'min_samples_split': [2, 5, 10]
            },
            'xgboost': {
                'n_estimators': [100, 200],
                'learning_rate': [0.05, 0.1, 0.2],
                'max_depth': [6, 8, 10]
            }
        }

        best_params = {}

        for model_name, param_grid in param_grids.items():
            if model_name in self.base_models:
                logger.info(f"Tuning {model_name}...")

                grid_search = GridSearchCV(
                    self.base_models[model_name],
                    param_grid,
                    cv=3,
                    scoring='accuracy',
                    n_jobs=-1,
                    verbose=1
                )

                grid_search.fit(X, y)
                best_params[model_name] = grid_search.best_params_

                logger.info(f"Best params for {model_name}: {grid_search.best_params_}")
                logger.info(f"Best score for {model_name}: {grid_search.best_score_:.4f}")

        return best_params


def generate_match_predictions(db, match_id: int) -> Optional[Dict]:
    """
    🧠 Gera predictions ML para um jogo específico - V3 CORRIGIDA (2025-10-20)
    Usa MLPredictionGenerator com seleção inteligente de outcomes e confidence calibrado

    Args:
        db: SQLAlchemy Session
        match_id: ID do jogo

    Returns:
        List[Dict] com predictions (pode ser múltiplas para diferentes markets) ou None se falhar
    """
    try:
        from app.services.ml_prediction_generator import MLPredictionGenerator
        from app.models import Match

        # Buscar jogo
        match = db.query(Match).filter(Match.id == match_id).first()
        if not match:
            logger.warning(f"Match {match_id} não encontrado")
            return None

        # Verificar se é jogo futuro
        if match.match_date <= datetime.now():
            logger.warning(f"Match {match_id} já passou ou está ao vivo")
            return None

        # Inicializar gerador ML v3 (com correções)
        ml_generator = MLPredictionGenerator(db)

        # Gerar predictions para TODOS markets (1X2, BTTS, O/U)
        # Retorna apenas outcomes que passam nos thresholds
        predictions = ml_generator.generate_predictions_for_single_match(match)

        if not predictions or len(predictions) == 0:
            logger.debug(f"Match {match_id}: Nenhuma prediction passou nos thresholds")
            return None

        # Para compatibilidade com automated_pipeline, retornar a primeira prediction
        # (que será a melhor do 1X2 se houver, ou a melhor de outro market)
        first_pred = predictions[0]

        # Extrair probabilidades do prediction dict
        probs = first_pred.get('probabilities', {})

        # Mapear market_type para predicted_outcome no formato esperado
        market = first_pred.get('market_type', 'HOME_WIN')
        if market == 'HOME_WIN':
            predicted_outcome = '1'
        elif market == 'DRAW':
            predicted_outcome = 'X'
        elif market == 'AWAY_WIN':
            predicted_outcome = '2'
        elif market in ['BTTS_YES', 'BTTS_NO']:
            predicted_outcome = market
        else:
            predicted_outcome = market

        # Retornar no formato esperado pelo automated_pipeline
        return {
            'predicted_outcome': predicted_outcome,
            'confidence': first_pred.get('confidence_score', 0.5),
            'probabilities': {
                'home': probs.get('home_win', 0.33),
                'draw': probs.get('draw', 0.33),
                'away': probs.get('away_win', 0.33)
            },
            'analysis_summary': f"ML v3: {market} ({first_pred.get('confidence_score', 0)*100:.1f}% confidence)",
            'key_factors': [f"Edge: {first_pred.get('value_edge', 0):.1%}", f"Model: v3_corrected"],
            'model_version': 'ml_generator_v3',
            'generated_at': datetime.now().isoformat(),
            'all_predictions': predictions  # Incluir todas para referência
        }

    except Exception as e:
        logger.error(f"Erro ao gerar predição ML v3 para match {match_id}: {e}")
        import traceback
        traceback.print_exc()
        return None