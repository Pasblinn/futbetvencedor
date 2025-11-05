"""
🤖 ML PREDICTION ENGINE - Sistema Avançado de Machine Learning
Combina múltiplos modelos para predições de alta precisão
Integra com o motor matemático existente para criar ensemble poderoso
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import cross_val_score, TimeSeriesSplit
from sklearn.metrics import classification_report, mean_squared_error, accuracy_score
import joblib
import os
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Importar serviços existentes
from app.services.football_data_service import FootballDataService
from app.services.real_prediction_engine import RealPredictionEngine
from app.core.config import settings

class MLPredictionEngine:
    """
    🧠 Motor de ML que combina múltiplos algoritmos para predições avançadas
    """

    def __init__(self):
        self.football_service = FootballDataService()
        self.real_engine = RealPredictionEngine()

        # Diretórios para modelos
        self.models_dir = Path("app/ml/models")
        self.models_dir.mkdir(parents=True, exist_ok=True)

        # Modelos para classificação de resultados (1X2)
        self.result_models = {
            'random_forest': RandomForestClassifier(
                n_estimators=200,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42
            ),
            'gradient_boosting': GradientBoostingClassifier(
                n_estimators=150,
                learning_rate=0.1,
                max_depth=8,
                random_state=42
            ),
            'neural_network': MLPClassifier(
                hidden_layer_sizes=(100, 50, 25),
                activation='relu',
                solver='adam',
                max_iter=1000,
                random_state=42
            ),
            'logistic_regression': LogisticRegression(
                random_state=42,
                max_iter=1000
            )
        }

        # Modelos para regressão de gols
        self.goals_models = {
            'random_forest': RandomForestRegressor(
                n_estimators=200,
                max_depth=12,
                min_samples_split=5,
                random_state=42
            ),
            'gradient_boosting': GradientBoostingClassifier(
                n_estimators=150,
                learning_rate=0.1,
                max_depth=6,
                random_state=42
            ),
            'neural_network': MLPRegressor(
                hidden_layer_sizes=(80, 40, 20),
                activation='relu',
                solver='adam',
                max_iter=1000,
                random_state=42
            )
        }

        # Scalers para normalização
        self.result_scaler = StandardScaler()
        self.goals_scaler = StandardScaler()

        # Encoders
        self.label_encoder = LabelEncoder()

        # Configurações
        self.min_matches_for_training = 500
        self.feature_importance_threshold = 0.01

    async def create_advanced_features(self, matches_data: List[Dict]) -> pd.DataFrame:
        """
        🔧 Feature Engineering Avançado
        Cria features sofisticadas para os modelos de ML
        """
        print("🔧 Criando features avançadas para ML...")

        features_list = []

        for match in matches_data:
            if match.get('status') != 'FINISHED':
                continue

            home_team_id = str(match.get('homeTeam', {}).get('id', ''))
            away_team_id = str(match.get('awayTeam', {}).get('id', ''))
            match_date = match.get('utcDate', '')

            if not all([home_team_id, away_team_id, match_date]):
                continue

            # Features básicas
            basic_features = await self._extract_basic_features(match)

            # Features de forma recente
            form_features = await self._extract_form_features(home_team_id, away_team_id, match_date)

            # Features de força dos times
            strength_features = await self._extract_strength_features(home_team_id, away_team_id, match_date)

            # Features de contexto
            context_features = await self._extract_context_features(match)

            # Features de séries temporais
            temporal_features = await self._extract_temporal_features(home_team_id, away_team_id, match_date)

            # Target variables
            targets = self._extract_targets(match)

            # Combinar todas as features
            match_features = {
                **basic_features,
                **form_features,
                **strength_features,
                **context_features,
                **temporal_features,
                **targets
            }

            features_list.append(match_features)

        df = pd.DataFrame(features_list)

        # Limpar dados
        df = df.dropna()

        print(f"✅ Features criadas: {len(df)} amostras, {len(df.columns)} features")
        return df

    async def _extract_basic_features(self, match: Dict) -> Dict:
        """📊 Features básicas do jogo"""
        return {
            'home_team_id': match.get('homeTeam', {}).get('id', 0),
            'away_team_id': match.get('awayTeam', {}).get('id', 0),
            'competition_id': match.get('competition', {}).get('id', 0),
            'matchday': match.get('matchday', 0),
            'venue': 1,  # 1 para casa, 0 para fora
        }

    async def _extract_form_features(self, home_team_id: str, away_team_id: str, match_date: str) -> Dict:
        """🏃‍♂️ Features de forma recente dos times"""
        try:
            # Buscar jogos recentes de cada time
            home_matches = await self.football_service.get_team_matches(home_team_id, limit=10)
            away_matches = await self.football_service.get_team_matches(away_team_id, limit=10)

            # Features do time da casa
            home_form = self._calculate_team_form(home_matches, home_team_id, match_date)
            away_form = self._calculate_team_form(away_matches, away_team_id, match_date)

            return {
                # Forma casa
                'home_recent_points': home_form['points_per_game'],
                'home_recent_goals_scored': home_form['goals_scored_per_game'],
                'home_recent_goals_conceded': home_form['goals_conceded_per_game'],
                'home_recent_wins': home_form['win_rate'],
                'home_recent_form_trend': home_form['form_trend'],
                'home_consistency': home_form['consistency'],

                # Forma visitante
                'away_recent_points': away_form['points_per_game'],
                'away_recent_goals_scored': away_form['goals_scored_per_game'],
                'away_recent_goals_conceded': away_form['goals_conceded_per_game'],
                'away_recent_wins': away_form['win_rate'],
                'away_recent_form_trend': away_form['form_trend'],
                'away_consistency': away_form['consistency'],

                # Diferenças relativas
                'form_difference': home_form['points_per_game'] - away_form['points_per_game'],
                'attack_difference': home_form['goals_scored_per_game'] - away_form['goals_scored_per_game'],
                'defense_difference': away_form['goals_conceded_per_game'] - home_form['goals_conceded_per_game']
            }

        except Exception as e:
            print(f"⚠️ Erro ao extrair features de forma: {e}")
            return self._get_default_form_features()

    def _calculate_team_form(self, matches: List[Dict], team_id: str, cutoff_date: str) -> Dict:
        """📈 Calcular estatísticas de forma do time"""
        if not matches:
            return self._get_default_team_form()

        # Filtrar jogos anteriores à data de corte
        filtered_matches = []
        for match in matches:
            if match.get('utcDate', '') < cutoff_date and match.get('status') == 'FINISHED':
                filtered_matches.append(match)

        if len(filtered_matches) < 3:
            return self._get_default_team_form()

        # Calcular estatísticas
        points = []
        goals_scored = []
        goals_conceded = []

        for match in filtered_matches[:10]:  # Últimos 10 jogos
            home_id = str(match.get('homeTeam', {}).get('id', ''))
            is_home = home_id == team_id

            home_score = match.get('score', {}).get('fullTime', {}).get('home', 0) or 0
            away_score = match.get('score', {}).get('fullTime', {}).get('away', 0) or 0

            if is_home:
                goals_scored.append(home_score)
                goals_conceded.append(away_score)
                if home_score > away_score:
                    points.append(3)
                elif home_score == away_score:
                    points.append(1)
                else:
                    points.append(0)
            else:
                goals_scored.append(away_score)
                goals_conceded.append(home_score)
                if away_score > home_score:
                    points.append(3)
                elif away_score == home_score:
                    points.append(1)
                else:
                    points.append(0)

        # Calcular métricas
        return {
            'points_per_game': np.mean(points) if points else 1.0,
            'goals_scored_per_game': np.mean(goals_scored) if goals_scored else 1.0,
            'goals_conceded_per_game': np.mean(goals_conceded) if goals_conceded else 1.0,
            'win_rate': sum(1 for p in points if p == 3) / len(points) if points else 0.33,
            'form_trend': np.polyfit(range(len(points)), points, 1)[0] if len(points) > 2 else 0,
            'consistency': 1 - (np.std(points) / 3) if points and len(points) > 1 else 0.5
        }

    async def _extract_strength_features(self, home_team_id: str, away_team_id: str, match_date: str) -> Dict:
        """💪 Features de força dos times baseadas em temporada completa"""
        try:
            # Usar dados do motor real para obter métricas de força
            home_data = await self.real_engine._get_team_real_form(home_team_id, "home")
            away_data = await self.real_engine._get_team_real_form(away_team_id, "away")

            home_metrics = home_data.get('attack_metrics', {})
            away_metrics = away_data.get('attack_metrics', {})
            home_defense = home_data.get('defense_metrics', {})
            away_defense = away_data.get('defense_metrics', {})

            return {
                'home_attack_strength': home_metrics.get('goals_per_game', 1.0),
                'home_defense_strength': 1 / max(home_defense.get('goals_conceded_per_game', 1.0), 0.1),
                'away_attack_strength': away_metrics.get('goals_per_game', 1.0),
                'away_defense_strength': 1 / max(away_defense.get('goals_conceded_per_game', 1.0), 0.1),
                'home_clean_sheet_rate': home_defense.get('clean_sheet_rate', 0.3),
                'away_clean_sheet_rate': away_defense.get('clean_sheet_rate', 0.3),
                'home_over_2_5_rate': home_metrics.get('games_over_2_5_goals', 0.3),
                'away_over_2_5_rate': away_metrics.get('games_over_2_5_goals', 0.3)
            }

        except Exception as e:
            print(f"⚠️ Erro ao extrair features de força: {e}")
            return self._get_default_strength_features()

    async def _extract_context_features(self, match: Dict) -> Dict:
        """🎯 Features de contexto do jogo"""
        match_date = datetime.fromisoformat(match.get('utcDate', '').replace('Z', '+00:00'))

        return {
            'month': match_date.month,
            'day_of_week': match_date.weekday(),
            'hour': match_date.hour,
            'is_weekend': 1 if match_date.weekday() >= 5 else 0,
            'season_phase': self._get_season_phase(match_date),
            'competition_importance': self._get_competition_importance(match.get('competition', {}).get('id', 0))
        }

    async def _extract_temporal_features(self, home_team_id: str, away_team_id: str, match_date: str) -> Dict:
        """⏰ Features de séries temporais"""
        try:
            # H2H histórico
            h2h_matches = await self.football_service.get_head_to_head(home_team_id, away_team_id, limit=10)

            if len(h2h_matches) < 2:
                return self._get_default_temporal_features()

            # Análise de momentum
            recent_h2h = h2h_matches[:5]
            home_wins = sum(1 for m in recent_h2h if self._determine_winner(m, home_team_id) == 'home')

            return {
                'h2h_total_matches': len(h2h_matches),
                'h2h_home_wins': home_wins,
                'h2h_home_win_rate': home_wins / len(recent_h2h) if recent_h2h else 0.33,
                'h2h_avg_goals': np.mean([
                    (m.get('score', {}).get('fullTime', {}).get('home', 0) or 0) +
                    (m.get('score', {}).get('fullTime', {}).get('away', 0) or 0)
                    for m in recent_h2h
                ]) if recent_h2h else 2.5,
                'h2h_momentum': self._calculate_h2h_momentum(h2h_matches, home_team_id)
            }

        except Exception as e:
            print(f"⚠️ Erro ao extrair features temporais: {e}")
            return self._get_default_temporal_features()

    def _extract_targets(self, match: Dict) -> Dict:
        """🎯 Extrair variáveis target do jogo"""
        home_score = match.get('score', {}).get('fullTime', {}).get('home', 0) or 0
        away_score = match.get('score', {}).get('fullTime', {}).get('away', 0) or 0
        total_goals = home_score + away_score

        # Target para classificação de resultado
        if home_score > away_score:
            result = 'H'  # Home win
        elif away_score > home_score:
            result = 'A'  # Away win
        else:
            result = 'D'  # Draw

        return {
            'result': result,
            'home_goals': home_score,
            'away_goals': away_score,
            'total_goals': total_goals,
            'over_2_5': 1 if total_goals > 2.5 else 0,
            'btts': 1 if home_score > 0 and away_score > 0 else 0
        }

    async def train_models(self, df: pd.DataFrame) -> Dict:
        """🎓 Treinar todos os modelos de ML"""
        print("🎓 Treinando modelos de Machine Learning...")

        if len(df) < self.min_matches_for_training:
            print(f"❌ Dados insuficientes para treino: {len(df)} < {self.min_matches_for_training}")
            return {}

        # Separar features e targets
        feature_columns = [col for col in df.columns if col not in ['result', 'home_goals', 'away_goals', 'total_goals', 'over_2_5', 'btts']]
        X = df[feature_columns]

        # Remover features com muitos valores faltando ou variância zero
        X = X.select_dtypes(include=[np.number])
        X = X.fillna(X.mean())

        # Remover features com variância zero
        variance_filter = X.var() > 0
        X = X.loc[:, variance_filter]

        results = {}

        # 1. Treinar modelos para classificação de resultado (1X2)
        print("🎯 Treinando modelos de classificação de resultado...")
        y_result = df['result']

        # Normalizar features
        X_scaled = self.result_scaler.fit_transform(X)

        result_scores = {}
        for name, model in self.result_models.items():
            try:
                # Cross-validation com time series split
                tscv = TimeSeriesSplit(n_splits=5)
                scores = cross_val_score(model, X_scaled, y_result, cv=tscv, scoring='accuracy')

                # Treinar modelo final
                model.fit(X_scaled, y_result)

                result_scores[name] = {
                    'cv_mean': scores.mean(),
                    'cv_std': scores.std(),
                    'model': model
                }

                print(f"   ✅ {name}: {scores.mean():.3f} ± {scores.std():.3f}")

            except Exception as e:
                print(f"   ❌ Erro no {name}: {e}")

        results['result_models'] = result_scores

        # 2. Treinar modelos para predição de gols
        print("⚽ Treinando modelos de predição de gols...")
        y_goals = df['total_goals']

        X_goals_scaled = self.goals_scaler.fit_transform(X)

        goals_scores = {}
        for name, model in self.goals_models.items():
            try:
                if name == 'gradient_boosting':
                    # Para GB, usar classificação para bins de gols
                    y_goals_binned = pd.cut(y_goals, bins=[0, 1.5, 2.5, 3.5, 10], labels=['Low', 'Medium', 'High', 'Very High'])
                    scores = cross_val_score(model, X_goals_scaled, y_goals_binned, cv=5, scoring='accuracy')
                    model.fit(X_goals_scaled, y_goals_binned)
                else:
                    scores = cross_val_score(model, X_goals_scaled, y_goals, cv=5, scoring='neg_mean_squared_error')
                    model.fit(X_goals_scaled, y_goals)

                goals_scores[name] = {
                    'cv_mean': scores.mean(),
                    'cv_std': scores.std(),
                    'model': model
                }

                print(f"   ✅ {name}: {scores.mean():.3f} ± {scores.std():.3f}")

            except Exception as e:
                print(f"   ❌ Erro no {name}: {e}")

        results['goals_models'] = goals_scores

        # Salvar metadados
        results['feature_columns'] = list(X.columns)
        results['training_date'] = datetime.now().isoformat()
        results['training_samples'] = len(df)

        # Salvar modelos
        await self._save_models(results)

        print(f"✅ Treinamento concluído! {len(results['result_models'])} modelos de resultado, {len(results['goals_models'])} modelos de gols")
        return results

    async def predict_with_ml(self, home_team_id: str, away_team_id: str, match_date: datetime) -> Dict:
        """🔮 Fazer predições usando modelos de ML"""
        try:
            # Carregar modelos
            models_data = await self._load_models()
            if not models_data:
                return {"error": "Modelos não encontrados - execute o treinamento primeiro"}

            # Criar features para o jogo
            match_features = await self._create_match_features(home_team_id, away_team_id, match_date)

            # Predições de resultado
            result_predictions = await self._predict_result(match_features, models_data)

            # Predições de gols
            goals_predictions = await self._predict_goals(match_features, models_data)

            # Combinar com motor matemático para ensemble
            math_prediction = await self.real_engine.generate_real_prediction(
                f"{home_team_id}_vs_{away_team_id}",
                home_team_id,
                away_team_id,
                match_date
            )

            # Ensemble final
            ensemble_prediction = self._create_ensemble_prediction(
                result_predictions,
                goals_predictions,
                math_prediction
            )

            return {
                "ml_predictions": {
                    "result": result_predictions,
                    "goals": goals_predictions
                },
                "mathematical_prediction": math_prediction,
                "ensemble_prediction": ensemble_prediction,
                "prediction_timestamp": datetime.now().isoformat(),
                "engine_version": "ML_v1.0"
            }

        except Exception as e:
            print(f"❌ Erro na predição ML: {e}")
            return {"error": str(e)}

    # Helper methods
    def _get_default_form_features(self) -> Dict:
        """Retorna features padrão quando há erro"""
        return {
            'home_recent_points': 1.5, 'home_recent_goals_scored': 1.0, 'home_recent_goals_conceded': 1.0,
            'home_recent_wins': 0.33, 'home_recent_form_trend': 0, 'home_consistency': 0.5,
            'away_recent_points': 1.5, 'away_recent_goals_scored': 1.0, 'away_recent_goals_conceded': 1.0,
            'away_recent_wins': 0.33, 'away_recent_form_trend': 0, 'away_consistency': 0.5,
            'form_difference': 0, 'attack_difference': 0, 'defense_difference': 0
        }

    def _get_default_team_form(self) -> Dict:
        return {
            'points_per_game': 1.5, 'goals_scored_per_game': 1.0, 'goals_conceded_per_game': 1.0,
            'win_rate': 0.33, 'form_trend': 0, 'consistency': 0.5
        }

    def _get_default_strength_features(self) -> Dict:
        return {
            'home_attack_strength': 1.0, 'home_defense_strength': 1.0,
            'away_attack_strength': 1.0, 'away_defense_strength': 1.0,
            'home_clean_sheet_rate': 0.3, 'away_clean_sheet_rate': 0.3,
            'home_over_2_5_rate': 0.3, 'away_over_2_5_rate': 0.3
        }

    def _get_default_temporal_features(self) -> Dict:
        return {
            'h2h_total_matches': 0, 'h2h_home_wins': 0, 'h2h_home_win_rate': 0.33,
            'h2h_avg_goals': 2.5, 'h2h_momentum': 0
        }

    def _get_season_phase(self, match_date: datetime) -> int:
        """Determina fase da temporada: 0=início, 1=meio, 2=fim"""
        month = match_date.month
        if month in [8, 9, 10]:
            return 0  # Início
        elif month in [11, 12, 1, 2]:
            return 1  # Meio
        else:
            return 2  # Fim

    def _get_competition_importance(self, comp_id: int) -> float:
        """Retorna importância da competição (0-1)"""
        important_competitions = {
            2001: 1.0,  # Champions League
            2018: 0.9,  # European Championship
            2000: 0.8,  # World Cup
            2021: 0.8,  # Premier League
            2014: 0.8,  # La Liga
            2019: 0.8,  # Serie A
            2002: 0.7   # Bundesliga
        }
        return important_competitions.get(comp_id, 0.5)

    def _determine_winner(self, match: Dict, team_id: str) -> str:
        """Determina vencedor do jogo"""
        home_id = str(match.get('homeTeam', {}).get('id', ''))
        home_score = match.get('score', {}).get('fullTime', {}).get('home', 0) or 0
        away_score = match.get('score', {}).get('fullTime', {}).get('away', 0) or 0

        if home_score > away_score:
            return 'home' if home_id == team_id else 'away'
        elif away_score > home_score:
            return 'away' if home_id == team_id else 'home'
        else:
            return 'draw'

    def _calculate_h2h_momentum(self, matches: List[Dict], team_id: str) -> float:
        """Calcula momentum no H2H"""
        if len(matches) < 3:
            return 0

        recent_results = []
        for match in matches[:5]:
            winner = self._determine_winner(match, team_id)
            if winner == 'home' or winner == 'away':
                recent_results.append(1)
            else:
                recent_results.append(0)

        # Calcular tendência
        if len(recent_results) > 1:
            return np.polyfit(range(len(recent_results)), recent_results, 1)[0]
        return 0

    async def _save_models(self, models_data: Dict):
        """Salvar modelos treinados"""
        try:
            model_file = self.models_dir / "trained_models.joblib"
            joblib.dump(models_data, model_file)
            print(f"💾 Modelos salvos em {model_file}")
        except Exception as e:
            print(f"❌ Erro ao salvar modelos: {e}")

    async def _load_models(self) -> Optional[Dict]:
        """Carregar modelos treinados"""
        try:
            model_file = self.models_dir / "trained_models.joblib"
            if model_file.exists():
                return joblib.load(model_file)
            return None
        except Exception as e:
            print(f"❌ Erro ao carregar modelos: {e}")
            return None

    def _create_ensemble_prediction(self, ml_result: Dict, ml_goals: Dict, math_pred: Dict) -> Dict:
        """🎯 Combinar predições ML + Matemática em ensemble"""

        # Pesos para ensemble (podem ser ajustados com base na performance)
        ml_weight = 0.6
        math_weight = 0.4

        try:
            # Combinar probabilidades de resultado
            ml_probs = ml_result.get('probabilities', {})
            math_outcome = math_pred.get('match_outcome', {})

            ensemble_result = {
                'home_win_probability': (
                    ml_probs.get('H', 0.33) * ml_weight +
                    math_outcome.get('home_win_probability', 0.33) * math_weight
                ),
                'draw_probability': (
                    ml_probs.get('D', 0.33) * ml_weight +
                    math_outcome.get('draw_probability', 0.33) * math_weight
                ),
                'away_win_probability': (
                    ml_probs.get('A', 0.33) * ml_weight +
                    math_outcome.get('away_win_probability', 0.33) * math_weight
                )
            }

            # Determinar resultado mais provável
            max_prob = max(ensemble_result.values())
            if ensemble_result['home_win_probability'] == max_prob:
                predicted_result = '1'
            elif ensemble_result['away_win_probability'] == max_prob:
                predicted_result = '2'
            else:
                predicted_result = 'X'

            # Combinar predições de gols
            ml_total_goals = ml_goals.get('predicted_total_goals', 2.5)
            math_total_goals = math_pred.get('goals_prediction', {}).get('expected_total_goals', 2.5)

            ensemble_goals = ml_total_goals * ml_weight + math_total_goals * math_weight

            return {
                'match_outcome': {
                    **ensemble_result,
                    'predicted_result': predicted_result,
                    'confidence': max_prob
                },
                'goals_prediction': {
                    'expected_total_goals': round(ensemble_goals, 2),
                    'over_2_5_probability': 1 - np.exp(-ensemble_goals) * sum(
                        np.power(ensemble_goals, k) / np.math.factorial(k) for k in range(3)
                    )
                },
                'ensemble_weights': {
                    'ml_weight': ml_weight,
                    'mathematical_weight': math_weight
                },
                'confidence_level': 'HIGH' if max_prob > 0.6 else 'MEDIUM' if max_prob > 0.45 else 'LOW'
            }

        except Exception as e:
            print(f"❌ Erro no ensemble: {e}")
            return math_pred  # Fallback para predição matemática