"""
🤖 REAL PREDICTIONS API - Endpoints para ML com dados reais
Usa os modelos treinados com dados reais do Brasileirão 2024
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Optional
from datetime import datetime
import joblib
import numpy as np
import os
from pydantic import BaseModel

router = APIRouter()

class PredictionResponse(BaseModel):
    home_team: str
    away_team: str
    prediction: str
    confidence: float
    individual_models: Dict
    model_source: str

class BrasileiraoPredictionEngine:
    """
    🇧🇷 Motor de predições do Brasileirão com modelos reais
    """

    def __init__(self):
        self.models = {}
        self.encoders = {}
        self.models_loaded = False
        self.models_dir = "models/brasileirao_real"

    def load_models(self):
        """Carregar modelos treinados"""
        try:
            if not os.path.exists(self.models_dir):
                raise Exception(f"Diretório de modelos não encontrado: {self.models_dir}")

            # Carregar metadados
            metadata_path = os.path.join(self.models_dir, "metadata.joblib")
            if os.path.exists(metadata_path):
                metadata = joblib.load(metadata_path)
                self.encoders = metadata.get('encoders', {})

            # Carregar modelos
            model_files = {
                'random_forest': 'random_forest_brasileirao.joblib',
                'gradient_boosting': 'gradient_boosting_brasileirao.joblib',
                'logistic_regression': 'logistic_regression_brasileirao.joblib'
            }

            for model_name, filename in model_files.items():
                model_path = os.path.join(self.models_dir, filename)
                if os.path.exists(model_path):
                    self.models[model_name] = joblib.load(model_path)

            self.models_loaded = len(self.models) > 0
            return True

        except Exception as e:
            print(f"❌ Erro carregando modelos: {e}")
            return False

    def predict_match(self, home_team: str, away_team: str) -> Dict:
        """Predizer resultado do jogo"""
        try:
            if not self.models_loaded:
                if not self.load_models():
                    raise Exception("Modelos não disponíveis")

            # Verificar se times existem nos encoders
            if not self.encoders.get('home_team') or not self.encoders.get('away_team'):
                raise Exception("Encoders não disponíveis")

            # Mapear nomes de times para códigos conhecidos
            team_mapping = {
                'flamengo': 'Flamengo',
                'palmeiras': 'Palmeiras',
                'botafogo': 'Botafogo',
                'sao-paulo': 'São Paulo',
                'corinthians': 'Corinthians',
                'vasco': 'Vasco da Gama',
                'atletico-mg': 'Atlético Mineiro',
                'fortaleza': 'Fortaleza',
                'internacional': 'Internacional',
                'cruzeiro': 'Cruzeiro',
                'bahia': 'Bahia',
                'gremio': 'Grêmio',
                'atletico-go': 'Atlético Goianiense',
                'vitoria': 'Vitória',
                'cuiaba': 'Cuiabá',
                'criciuma': 'Criciúma',
                'rb-bragantino': 'RB Bragantino',
                'juventude': 'Juventude',
                'fluminense': 'Fluminense',
                'athletico-pr': 'Athletico Paranaense'
            }

            # Converter nomes para formato conhecido
            home_team_clean = team_mapping.get(home_team.lower(), home_team)
            away_team_clean = team_mapping.get(away_team.lower(), away_team)

            # Verificar se times existem nos dados de treino
            home_classes = list(self.encoders['home_team'].classes_)
            away_classes = list(self.encoders['away_team'].classes_)

            if home_team_clean not in home_classes:
                raise Exception(f"Time {home_team_clean} não encontrado nos dados de treino")

            if away_team_clean not in away_classes:
                raise Exception(f"Time {away_team_clean} não encontrado nos dados de treino")

            # Encode times
            home_encoded = self.encoders['home_team'].transform([home_team_clean])[0]
            away_encoded = self.encoders['away_team'].transform([away_team_clean])[0]

            # Criar features (valores padrão para strength)
            features = np.array([[
                home_encoded,      # home_team_encoded
                away_encoded,      # away_team_encoded
                0.5,              # home_strength
                0.5,              # away_strength
                0.0,              # strength_diff
                0                 # is_high_scoring_teams
            ]])

            # Fazer predições com todos os modelos
            predictions = {}
            for model_name, model in self.models.items():
                try:
                    pred = model.predict(features)[0]
                    predictions[model_name] = pred

                    # Tentar obter probabilidades
                    if hasattr(model, 'predict_proba'):
                        proba = model.predict_proba(features)[0]
                        predictions[f"{model_name}_proba"] = dict(zip(model.classes_, proba))
                except Exception as e:
                    predictions[model_name] = f"Error: {e}"

            # Ensemble por votação
            valid_predictions = [p for p in predictions.values() if isinstance(p, str) and p in ['home_win', 'away_win', 'draw']]

            if not valid_predictions:
                raise Exception("Nenhuma predição válida obtida")

            ensemble_pred = max(set(valid_predictions), key=valid_predictions.count)
            confidence = valid_predictions.count(ensemble_pred) / len(valid_predictions)

            return {
                'home_team': home_team_clean,
                'away_team': away_team_clean,
                'ensemble_prediction': ensemble_pred,
                'confidence': confidence,
                'individual_predictions': predictions,
                'models_used': list(self.models.keys()),
                'prediction_timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'error': str(e),
                'home_team': home_team,
                'away_team': away_team
            }

# Instância global do motor
prediction_engine = BrasileiraoPredictionEngine()

@router.get("/brasileirao/predict/{home_team}/{away_team}")
async def predict_brasileirao_match(home_team: str, away_team: str) -> Dict:
    """
    🇧🇷 Predizer jogo do Brasileirão usando modelos ML reais

    **Parâmetros:**
    - home_team: Nome do time mandante (ex: flamengo, palmeiras)
    - away_team: Nome do time visitante

    **Retorna:**
    - Predição ensemble de 3 modelos ML
    - Confiança da predição
    - Predições individuais de cada modelo
    """
    result = prediction_engine.predict_match(home_team, away_team)

    if 'error' in result:
        raise HTTPException(
            status_code=400,
            detail=result['error']
        )

    return {
        "status": "success",
        "prediction": result,
        "model_info": {
            "source": "Brasileirão 2024 Real Data",
            "training_samples": 380,
            "models": ["Random Forest", "Gradient Boosting", "Logistic Regression"]
        }
    }

@router.get("/system/status")
async def get_system_status() -> Dict:
    """
    📊 Status do sistema de predições ML
    """
    try:
        models_available = prediction_engine.load_models() if not prediction_engine.models_loaded else True

        return {
            "status": "success",
            "system": {
                "models_loaded": prediction_engine.models_loaded,
                "models_available": models_available,
                "models_count": len(prediction_engine.models),
                "encoders_available": len(prediction_engine.encoders) > 0,
                "models_dir": prediction_engine.models_dir,
                "supported_teams": list(prediction_engine.encoders.get('home_team', {}).classes_ if prediction_engine.encoders.get('home_team') else [])
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@router.get("/teams/supported")
async def get_supported_teams() -> Dict:
    """
    🏟️ Lista de times suportados pelo sistema
    """
    try:
        if not prediction_engine.models_loaded:
            prediction_engine.load_models()

        if not prediction_engine.encoders.get('home_team'):
            return {
                "status": "error",
                "message": "Modelos não carregados"
            }

        teams = list(prediction_engine.encoders['home_team'].classes_)

        # Mapear para códigos da API
        api_mapping = {
            'Flamengo': 'flamengo',
            'Palmeiras': 'palmeiras',
            'Botafogo': 'botafogo',
            'São Paulo': 'sao-paulo',
            'Corinthians': 'corinthians',
            'Vasco da Gama': 'vasco',
            'Atlético Mineiro': 'atletico-mg',
            'Fortaleza': 'fortaleza',
            'Internacional': 'internacional',
            'Cruzeiro': 'cruzeiro',
            'Bahia': 'bahia',
            'Grêmio': 'gremio',
            'Atlético Goianiense': 'atletico-go',
            'Vitória': 'vitoria',
            'Cuiabá': 'cuiaba',
            'Criciúma': 'criciuma',
            'RB Bragantino': 'rb-bragantino',
            'Juventude': 'juventude',
            'Fluminense': 'fluminense',
            'Athletico Paranaense': 'athletico-pr'
        }

        teams_with_codes = [
            {
                "name": team,
                "api_code": api_mapping.get(team, team.lower().replace(' ', '-')),
                "supported": True
            }
            for team in teams
        ]

        return {
            "status": "success",
            "teams": teams_with_codes,
            "total_teams": len(teams_with_codes)
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@router.post("/system/reload-models")
async def reload_models() -> Dict:
    """
    🔄 Recarregar modelos ML
    """
    try:
        prediction_engine.models_loaded = False
        prediction_engine.models = {}
        prediction_engine.encoders = {}

        success = prediction_engine.load_models()

        return {
            "status": "success" if success else "error",
            "models_loaded": prediction_engine.models_loaded,
            "models_count": len(prediction_engine.models),
            "reload_timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }