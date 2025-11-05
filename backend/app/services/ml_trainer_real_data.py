"""
🤖 ML TRAINER REAL DATA - Treinamento ML com dados reais coletados
Treina modelos usando os jogos finalizados das APIs
Foco em predições práticas e utilizáveis
"""

import asyncio
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib
import os

from app.core.database import get_db_session
from app.models.match import Match
from app.models.team import Team

logger = logging.getLogger(__name__)

class MLTrainerRealData:
    """
    🤖 Treinador ML usando dados reais coletados
    """

    def __init__(self, league_filter: Optional[List[str]] = None):
        self.models = {}
        self.encoders = {}
        self.feature_importance = {}
        self.training_stats = {}

        # Lista de ligas para treinar (None = todas as ligas)
        self.league_filter = league_filter

        # Diretório para salvar modelos - agora universal
        if league_filter and len(league_filter) == 1:
            # Modelo específico de uma liga
            league_name = league_filter[0].lower().replace(' ', '_').replace('ã', 'a')
            self.models_dir = f"models/{league_name}_real"
        else:
            # Modelo universal para todas as ligas
            self.models_dir = "models/universal_real"

        os.makedirs(self.models_dir, exist_ok=True)

    async def train_models_with_real_data(self) -> Dict:
        """
        🤖 Treinar modelos ML com dados reais do banco
        """
        logger.info("🤖 INICIANDO TREINAMENTO ML COM DADOS REAIS...")

        results = {
            'start_time': datetime.now().isoformat(),
            'data_stats': {},
            'models_trained': {},
            'performance': {},
            'success': True
        }

        try:
            # 1. Carregar dados do banco
            training_data = await self._load_training_data_from_db()

            if training_data.empty:
                raise ValueError("Nenhum dado de treinamento encontrado no banco")

            results['data_stats'] = self._analyze_training_data(training_data)
            logger.info(f"📊 Dados carregados: {len(training_data)} jogos")

            # 2. Preparar features
            X, y, feature_names = self._prepare_features(training_data)
            logger.info(f"🔧 Features preparadas: {len(feature_names)} características")

            # 3. Dividir dados para treino/teste
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.3, random_state=42, stratify=y
            )

            # 4. Treinar múltiplos modelos
            models_to_train = {
                'random_forest': RandomForestClassifier(n_estimators=100, random_state=42),
                'gradient_boosting': GradientBoostingClassifier(n_estimators=100, random_state=42),
                'logistic_regression': LogisticRegression(random_state=42, max_iter=1000)
            }

            for model_name, model in models_to_train.items():
                logger.info(f"🎯 Treinando {model_name}...")

                # Treinar modelo
                model.fit(X_train, y_train)

                # Avaliar performance
                train_score = model.score(X_train, y_train)
                test_score = model.score(X_test, y_test)

                y_pred = model.predict(X_test)

                # Salvar modelo e estatísticas
                self.models[model_name] = model
                results['models_trained'][model_name] = {
                    'train_accuracy': train_score,
                    'test_accuracy': test_score,
                    'classification_report': classification_report(y_test, y_pred, output_dict=True)
                }

                # Feature importance (se disponível)
                if hasattr(model, 'feature_importances_'):
                    self.feature_importance[model_name] = dict(zip(
                        feature_names, model.feature_importances_
                    ))

                # Salvar modelo em disco
                model_path = os.path.join(self.models_dir, f"{model_name}_real_data.joblib")
                joblib.dump(model, model_path)

                logger.info(f"✅ {model_name}: Train={train_score:.3f}, Test={test_score:.3f}")

            # 5. Salvar metadados
            metadata = {
                'feature_names': feature_names,
                'training_date': datetime.now().isoformat(),
                'total_samples': len(training_data),
                'encoders': self.encoders
            }

            metadata_path = os.path.join(self.models_dir, "training_metadata.joblib")
            joblib.dump(metadata, metadata_path)

            results['performance'] = self._calculate_ensemble_performance(X_test, y_test)

        except Exception as e:
            logger.error(f"❌ Erro no treinamento ML: {e}")
            results['success'] = False
            results['error'] = str(e)

        results['end_time'] = datetime.now().isoformat()
        logger.info("🤖 TREINAMENTO ML CONCLUÍDO")

        return results

    async def _load_training_data_from_db(self) -> pd.DataFrame:
        """
        📊 Carregar dados de treinamento do banco
        """
        data = []

        with get_db_session() as session:
            # Buscar jogos finalizados com resultados
            query = session.query(Match).filter(
                Match.home_score.isnot(None),
                Match.away_score.isnot(None),
                Match.status == 'FINISHED'
            )

            # Filtrar por ligas se especificado
            if self.league_filter:
                query = query.filter(Match.league.in_(self.league_filter))

            finished_matches = query.all()

            logger.info(f"📊 Encontrados {len(finished_matches)} jogos finalizados")

            for match in finished_matches:
                try:
                    # Buscar informações dos times
                    home_team = session.query(Team).filter(Team.id == match.home_team_id).first()
                    away_team = session.query(Team).filter(Team.id == match.away_team_id).first()

                    if home_team and away_team:
                        # Determinar resultado
                        if match.home_score > match.away_score:
                            result = 'home_win'
                        elif match.away_score > match.home_score:
                            result = 'away_win'
                        else:
                            result = 'draw'

                        # Criar registro de dados
                        data.append({
                            'home_team': home_team.name,
                            'away_team': away_team.name,
                            'home_country': home_team.country or 'Unknown',
                            'away_country': away_team.country or 'Unknown',
                            'league': match.league,
                            'home_score': match.home_score,
                            'away_score': match.away_score,
                            'total_goals': match.home_score + match.away_score,
                            'result': result,
                            'match_date': match.match_date,
                            'source': match.external_id
                        })

                except Exception as e:
                    logger.warning(f"⚠️ Erro processando match {match.id}: {e}")
                    continue

        return pd.DataFrame(data)

    def _prepare_features(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        🔧 Preparar features para treinamento
        """
        logger.info("🔧 Preparando features...")

        # Encoders para variáveis categóricas
        self.encoders = {
            'home_team': LabelEncoder(),
            'away_team': LabelEncoder(),
            'league': LabelEncoder(),
            'home_country': LabelEncoder(),
            'away_country': LabelEncoder()
        }

        # Aplicar encoding
        data_encoded = data.copy()

        for column, encoder in self.encoders.items():
            if column in data_encoded.columns:
                data_encoded[f'{column}_encoded'] = encoder.fit_transform(data_encoded[column].astype(str))

        # Criar features adicionais
        data_encoded['is_international'] = (data_encoded['home_country'] != data_encoded['away_country']).astype(int)

        # Features baseadas em histórico (simplified)
        data_encoded['home_team_strength'] = self._calculate_team_strength(data, data_encoded['home_team'])
        data_encoded['away_team_strength'] = self._calculate_team_strength(data, data_encoded['away_team'])
        data_encoded['strength_diff'] = data_encoded['home_team_strength'] - data_encoded['away_team_strength']

        # Features finais
        feature_columns = [
            'home_team_encoded', 'away_team_encoded', 'league_encoded',
            'home_country_encoded', 'away_country_encoded',
            'is_international', 'home_team_strength', 'away_team_strength', 'strength_diff'
        ]

        X = data_encoded[feature_columns].values
        y = data_encoded['result'].values

        return X, y, feature_columns

    def _calculate_team_strength(self, data: pd.DataFrame, team_series: pd.Series) -> pd.Series:
        """
        💪 Calcular força dos times baseado em resultados
        """
        # Simplified team strength calculation
        strength_map = {}

        for team in data['home_team'].unique():
            home_games = data[data['home_team'] == team]
            away_games = data[data['away_team'] == team]

            home_wins = len(home_games[home_games['result'] == 'home_win'])
            away_wins = len(away_games[away_games['result'] == 'away_win'])
            total_games = len(home_games) + len(away_games)

            if total_games > 0:
                win_rate = (home_wins + away_wins) / total_games
                strength_map[team] = win_rate
            else:
                strength_map[team] = 0.5  # Neutral strength

        return team_series.map(strength_map).fillna(0.5)

    def _analyze_training_data(self, data: pd.DataFrame) -> Dict:
        """
        📊 Analisar dados de treinamento
        """
        return {
            'total_matches': len(data),
            'leagues': data['league'].value_counts().to_dict(),
            'results_distribution': data['result'].value_counts().to_dict(),
            'avg_goals_per_match': data['total_goals'].mean(),
            'unique_teams': data['home_team'].nunique() + data['away_team'].nunique(),
            'date_range': {
                'earliest': str(data['match_date'].min()) if 'match_date' in data.columns else 'N/A',
                'latest': str(data['match_date'].max()) if 'match_date' in data.columns else 'N/A'
            }
        }

    def _calculate_ensemble_performance(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict:
        """
        🎯 Calcular performance ensemble
        """
        if not self.models:
            return {}

        # Fazer predições com todos os modelos
        predictions = {}
        for model_name, model in self.models.items():
            predictions[model_name] = model.predict(X_test)

        # Ensemble por votação majoritária
        ensemble_pred = []
        for i in range(len(X_test)):
            votes = [predictions[model][i] for model in predictions]
            ensemble_pred.append(max(set(votes), key=votes.count))

        ensemble_accuracy = accuracy_score(y_test, ensemble_pred)

        return {
            'ensemble_accuracy': ensemble_accuracy,
            'individual_accuracies': {
                model_name: accuracy_score(y_test, pred)
                for model_name, pred in predictions.items()
            },
            'best_model': max(
                self.models.keys(),
                key=lambda m: accuracy_score(y_test, predictions[m])
            )
        }

    async def predict_match_outcome(self, home_team: str, away_team: str, league: str = None) -> Dict:
        """
        🔮 Predizer resultado de um jogo
        """
        try:
            if not self.models:
                # Tentar carregar modelos salvos
                await self._load_saved_models()

            # Preparar dados do jogo
            match_data = pd.DataFrame([{
                'home_team': home_team,
                'away_team': away_team,
                'league': league or 'Unknown',
                'home_country': 'Unknown',
                'away_country': 'Unknown'
            }])

            # Aplicar mesmas transformações
            for column, encoder in self.encoders.items():
                if column in match_data.columns:
                    try:
                        match_data[f'{column}_encoded'] = encoder.transform(match_data[column].astype(str))
                    except ValueError:
                        # Valor não visto no treinamento
                        match_data[f'{column}_encoded'] = 0

            # Preparar features
            match_data['is_international'] = 0
            match_data['home_team_strength'] = 0.5
            match_data['away_team_strength'] = 0.5
            match_data['strength_diff'] = 0

            feature_columns = [
                'home_team_encoded', 'away_team_encoded', 'league_encoded',
                'home_country_encoded', 'away_country_encoded',
                'is_international', 'home_team_strength', 'away_team_strength', 'strength_diff'
            ]

            X = match_data[feature_columns].values

            # Fazer predições com todos os modelos
            predictions = {}
            probabilities = {}

            for model_name, model in self.models.items():
                pred = model.predict(X)[0]
                predictions[model_name] = pred

                if hasattr(model, 'predict_proba'):
                    proba = model.predict_proba(X)[0]
                    probabilities[model_name] = dict(zip(model.classes_, proba))

            # Predição ensemble
            votes = list(predictions.values())
            ensemble_prediction = max(set(votes), key=votes.count)

            return {
                'home_team': home_team,
                'away_team': away_team,
                'ensemble_prediction': ensemble_prediction,
                'individual_predictions': predictions,
                'probabilities': probabilities,
                'confidence': votes.count(ensemble_prediction) / len(votes)
            }

        except Exception as e:
            logger.error(f"❌ Erro na predição: {e}")
            return {'error': str(e)}

    async def _load_saved_models(self):
        """
        📁 Carregar modelos salvos do disco
        """
        try:
            metadata_path = os.path.join(self.models_dir, "training_metadata.joblib")
            if os.path.exists(metadata_path):
                metadata = joblib.load(metadata_path)
                self.encoders = metadata.get('encoders', {})

            for model_file in os.listdir(self.models_dir):
                if model_file.endswith('_real_data.joblib'):
                    model_name = model_file.replace('_real_data.joblib', '')
                    model_path = os.path.join(self.models_dir, model_file)
                    self.models[model_name] = joblib.load(model_path)

        except Exception as e:
            logger.error(f"❌ Erro carregando modelos: {e}")

# Instâncias globais
ml_trainer_real_data = MLTrainerRealData()  # Para compatibilidade
universal_ml_trainer = MLTrainerRealData(league_filter=None)  # Universal para todas as ligas