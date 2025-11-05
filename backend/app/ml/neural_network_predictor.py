import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from typing import Dict, List, Tuple, Optional
import joblib
import os
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class NeuralNetworkPredictor:
    """Advanced Neural Network for Football Match Prediction"""

    def __init__(self, model_path: str = "models/"):
        self.model_path = model_path
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.feature_names = []

        # Model architectures for different prediction types
        self.model_configs = {
            'match_outcome': {
                'input_dim': 50,
                'hidden_layers': [128, 64, 32],
                'output_dim': 3,  # Home win, Draw, Away win
                'activation': 'softmax',
                'loss': 'categorical_crossentropy'
            },
            'goals_total': {
                'input_dim': 50,
                'hidden_layers': [64, 32, 16],
                'output_dim': 1,
                'activation': 'linear',
                'loss': 'mse'
            },
            'btts': {
                'input_dim': 50,
                'hidden_layers': [64, 32],
                'output_dim': 1,
                'activation': 'sigmoid',
                'loss': 'binary_crossentropy'
            },
            'corners': {
                'input_dim': 50,
                'hidden_layers': [32, 16],
                'output_dim': 1,
                'activation': 'linear',
                'loss': 'mse'
            }
        }

        # Create models directory if it doesn't exist
        os.makedirs(model_path, exist_ok=True)

    def _build_model(self, config: Dict) -> keras.Model:
        """Build neural network model with specified configuration"""
        model = keras.Sequential()

        # Input layer
        model.add(layers.Input(shape=(config['input_dim'],)))

        # Hidden layers with dropout and batch normalization
        for i, units in enumerate(config['hidden_layers']):
            model.add(layers.Dense(units, activation='relu'))
            model.add(layers.BatchNormalization())
            model.add(layers.Dropout(0.3))

        # Output layer
        model.add(layers.Dense(config['output_dim'], activation=config['activation']))

        # Compile model
        optimizer = keras.optimizers.Adam(learning_rate=0.001)
        model.compile(
            optimizer=optimizer,
            loss=config['loss'],
            metrics=['accuracy'] if config['activation'] in ['softmax', 'sigmoid'] else ['mae']
        )

        return model

    def _prepare_features(self, data: pd.DataFrame) -> np.ndarray:
        """Extract and engineer features from match data"""
        features = []

        # Team performance features
        for team in ['home', 'away']:
            # Recent form (weighted by recency)
            recent_form = data[f'{team}_recent_form'].fillna(0)
            features.append(recent_form)

            # Goal statistics
            features.extend([
                data[f'{team}_goals_scored_avg'].fillna(0),
                data[f'{team}_goals_conceded_avg'].fillna(0),
                data[f'{team}_xg_for_avg'].fillna(0),
                data[f'{team}_xg_against_avg'].fillna(0)
            ])

            # Possession and style
            features.extend([
                data[f'{team}_possession_avg'].fillna(50),
                data[f'{team}_shots_avg'].fillna(0),
                data[f'{team}_corners_avg'].fillna(0)
            ])

            # Defensive metrics
            features.extend([
                data[f'{team}_clean_sheets_rate'].fillna(0),
                data[f'{team}_cards_avg'].fillna(0)
            ])

        # Head-to-head features
        features.extend([
            data['h2h_home_wins'].fillna(0),
            data['h2h_draws'].fillna(0),
            data['h2h_away_wins'].fillna(0),
            data['h2h_avg_goals'].fillna(2.5),
            data['h2h_over_2_5_rate'].fillna(0.5),
            data['h2h_btts_rate'].fillna(0.5)
        ])

        # Match context features
        features.extend([
            data['importance_factor'].fillna(1.0),
            data['rest_days_home'].fillna(7),
            data['rest_days_away'].fillna(7),
            data['is_derby'].fillna(0).astype(int),
            data['is_rivalry'].fillna(0).astype(int)
        ])

        # Weather features
        features.extend([
            data['temperature'].fillna(15),
            data['wind_speed'].fillna(0),
            data['humidity'].fillna(60),
            data['weather_impact_score'].fillna(0)
        ])

        # Elo ratings and form trends
        features.extend([
            data['home_elo_rating'].fillna(1200),
            data['away_elo_rating'].fillna(1200),
            data['elo_difference'].fillna(0),
            data['home_form_trend'].fillna(0),
            data['away_form_trend'].fillna(0)
        ])

        # Market features (if available)
        features.extend([
            data['home_win_odds'].fillna(2.5),
            data['draw_odds'].fillna(3.2),
            data['away_win_odds'].fillna(2.8),
            data['over_2_5_odds'].fillna(1.8),
            data['btts_yes_odds'].fillna(1.9)
        ])

        # Injury impact
        features.extend([
            data['home_injury_impact'].fillna(0),
            data['away_injury_impact'].fillna(0),
            data['key_players_missing_home'].fillna(0),
            data['key_players_missing_away'].fillna(0)
        ])

        # Time-based features
        if 'match_date' in data.columns:
            match_dates = pd.to_datetime(data['match_date'])
            features.extend([
                match_dates.dt.month / 12.0,  # Seasonal effect
                match_dates.dt.dayofweek / 6.0,  # Day of week effect
                match_dates.dt.hour / 23.0  # Time of day effect
            ])
        else:
            features.extend([0.5, 0.5, 0.5])  # Default values

        return np.column_stack(features)

    def train_model(self, training_data: pd.DataFrame, prediction_type: str) -> Dict:
        """Train neural network model for specific prediction type"""
        logger.info(f"Training {prediction_type} model...")

        if prediction_type not in self.model_configs:
            raise ValueError(f"Unknown prediction type: {prediction_type}")

        # Prepare features
        X = self._prepare_features(training_data)

        # Prepare targets based on prediction type
        if prediction_type == 'match_outcome':
            # One-hot encode match outcomes
            y = pd.get_dummies(training_data['outcome']).values
        elif prediction_type == 'goals_total':
            y = training_data['total_goals'].values
        elif prediction_type == 'btts':
            y = training_data['both_teams_scored'].astype(int).values
        elif prediction_type == 'corners':
            y = training_data['total_corners'].values

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=None
        )

        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # Update model config with actual input dimension
        config = self.model_configs[prediction_type].copy()
        config['input_dim'] = X_train_scaled.shape[1]

        # Build and train model
        model = self._build_model(config)

        # Callbacks for training
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=20,
                restore_best_weights=True
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=10,
                min_lr=1e-6
            ),
            keras.callbacks.ModelCheckpoint(
                filepath=f"{self.model_path}{prediction_type}_best.h5",
                monitor='val_loss',
                save_best_only=True
            )
        ]

        # Train model
        history = model.fit(
            X_train_scaled, y_train,
            validation_data=(X_test_scaled, y_test),
            epochs=200,
            batch_size=32,
            callbacks=callbacks,
            verbose=1
        )

        # Evaluate model
        test_loss = model.evaluate(X_test_scaled, y_test, verbose=0)

        # Save model and preprocessors
        model.save(f"{self.model_path}{prediction_type}_model.h5")
        joblib.dump(scaler, f"{self.model_path}{prediction_type}_scaler.pkl")

        # Store in memory
        self.models[prediction_type] = model
        self.scalers[prediction_type] = scaler

        logger.info(f"Model {prediction_type} trained successfully. Test loss: {test_loss}")

        return {
            'model': model,
            'scaler': scaler,
            'history': history.history,
            'test_loss': test_loss,
            'config': config
        }

    def load_model(self, prediction_type: str) -> bool:
        """Load trained model from disk"""
        try:
            model_path = f"{self.model_path}{prediction_type}_model.h5"
            scaler_path = f"{self.model_path}{prediction_type}_scaler.pkl"

            if os.path.exists(model_path) and os.path.exists(scaler_path):
                self.models[prediction_type] = keras.models.load_model(model_path)
                self.scalers[prediction_type] = joblib.load(scaler_path)
                logger.info(f"Loaded {prediction_type} model successfully")
                return True
            else:
                logger.warning(f"Model files not found for {prediction_type}")
                return False
        except Exception as e:
            logger.error(f"Error loading {prediction_type} model: {e}")
            return False

    def predict(self, data: pd.DataFrame, prediction_type: str) -> Dict:
        """Make predictions using trained model"""
        if prediction_type not in self.models:
            if not self.load_model(prediction_type):
                raise ValueError(f"Model {prediction_type} not available")

        # Prepare features
        X = self._prepare_features(data)
        X_scaled = self.scalers[prediction_type].transform(X)

        # Make predictions
        predictions = self.models[prediction_type].predict(X_scaled)

        # Process predictions based on type
        if prediction_type == 'match_outcome':
            # Convert softmax output to probabilities
            home_prob = predictions[:, 0]
            draw_prob = predictions[:, 1]
            away_prob = predictions[:, 2]

            return {
                'home_win_probability': home_prob.tolist(),
                'draw_probability': draw_prob.tolist(),
                'away_win_probability': away_prob.tolist(),
                'predicted_outcome': np.argmax(predictions, axis=1).tolist()
            }

        elif prediction_type == 'goals_total':
            return {
                'predicted_total_goals': predictions.flatten().tolist()
            }

        elif prediction_type == 'btts':
            btts_prob = predictions.flatten()
            return {
                'btts_probability': btts_prob.tolist(),
                'btts_prediction': (btts_prob > 0.5).astype(int).tolist()
            }

        elif prediction_type == 'corners':
            return {
                'predicted_corners': predictions.flatten().tolist()
            }

    def predict_all_markets(self, data: pd.DataFrame) -> Dict:
        """Make predictions for all available markets"""
        results = {}

        for prediction_type in self.model_configs.keys():
            try:
                results[prediction_type] = self.predict(data, prediction_type)
            except Exception as e:
                logger.error(f"Error predicting {prediction_type}: {e}")
                results[prediction_type] = None

        return results

    def calculate_model_confidence(self, predictions: Dict, data: pd.DataFrame) -> float:
        """Calculate overall confidence score for predictions"""
        confidence_factors = []

        # Check prediction consistency across markets
        if 'match_outcome' in predictions and predictions['match_outcome']:
            outcome_probs = predictions['match_outcome']
            max_prob = max(outcome_probs['home_win_probability'][0],
                          outcome_probs['draw_probability'][0],
                          outcome_probs['away_win_probability'][0])
            confidence_factors.append(max_prob)

        # Check feature quality
        feature_quality = self._assess_feature_quality(data)
        confidence_factors.append(feature_quality)

        # Historical model performance (would be loaded from database)
        model_performance = 0.85  # Placeholder
        confidence_factors.append(model_performance)

        return np.mean(confidence_factors) if confidence_factors else 0.5

    def _assess_feature_quality(self, data: pd.DataFrame) -> float:
        """Assess quality of input features"""
        quality_score = 1.0

        # Check for missing important features
        important_features = [
            'home_recent_form', 'away_recent_form',
            'home_goals_scored_avg', 'away_goals_scored_avg',
            'h2h_avg_goals'
        ]

        missing_count = sum(1 for feat in important_features if feat not in data.columns or data[feat].isna().all())
        quality_score -= (missing_count / len(important_features)) * 0.3

        # Check data recency
        if 'last_update' in data.columns:
            days_old = (datetime.now() - pd.to_datetime(data['last_update'])).dt.days.mean()
            if days_old > 7:
                quality_score -= 0.2

        return max(0.0, quality_score)

    def get_feature_importance(self, prediction_type: str) -> Dict:
        """Get feature importance for interpretability (approximate for neural networks)"""
        if prediction_type not in self.models:
            return {}

        # For neural networks, we can use gradient-based importance
        # This is a simplified version - in practice, you'd use techniques like SHAP or LIME

        model = self.models[prediction_type]

        # Get weights from first layer as proxy for feature importance
        first_layer_weights = model.layers[0].get_weights()[0]
        feature_importance = np.mean(np.abs(first_layer_weights), axis=1)

        # Normalize
        feature_importance = feature_importance / np.sum(feature_importance)

        # Create feature names (simplified)
        feature_names = [
            'home_form', 'away_form', 'home_goals_avg', 'away_goals_avg',
            'home_xg', 'away_xg', 'h2h_history', 'weather_impact',
            'elo_ratings', 'market_odds', 'injuries', 'time_factors'
        ]

        return dict(zip(feature_names[:len(feature_importance)], feature_importance))