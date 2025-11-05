#!/usr/bin/env python3
"""
🔮 GERADOR DE PREDIÇÕES
Gera predições para matches futuros usando modelo treinado
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import numpy as np
from datetime import datetime
import joblib
import json

from app.core.database import SessionLocal
from app.models.match import Match
from app.models.prediction import Prediction
from app.models.team import Team
from enhanced_ml_trainer import EnhancedFeatureExtractor


class PredictionGenerator:
    """Gerador de predições para matches futuros"""

    def __init__(self, db, model_name='random_forest'):
        self.db = db
        self.model_name = model_name

        models_dir = Path(__file__).parent / 'models'

        # Carregar modelo
        model_path = models_dir / f'{model_name}_enhanced_model.joblib'
        if not model_path.exists():
            raise FileNotFoundError(f"Modelo não encontrado: {model_path}")

        self.model = joblib.load(model_path)
        print(f"✅ Modelo carregado: {model_name}")

        # Carregar feature names
        feature_path = models_dir / 'enhanced_feature_names.joblib'
        if feature_path.exists():
            self.feature_names = joblib.load(feature_path)
            print(f"✅ Features carregadas: {len(self.feature_names)}")
        else:
            raise FileNotFoundError("Feature names não encontrados")

        # Carregar label encoder (para XGBoost, LightGBM)
        encoder_path = models_dir / 'label_encoder.joblib'
        if encoder_path.exists():
            self.label_encoder = joblib.load(encoder_path)
        else:
            self.label_encoder = None

        # Carregar metadata
        metadata_path = models_dir / 'enhanced_model_metadata.json'
        if metadata_path.exists():
            with open(metadata_path) as f:
                self.metadata = json.load(f)
            print(f"✅ Metadata carregada")

        # Feature extractor
        self.extractor = EnhancedFeatureExtractor(db)

    def extract_features_for_match(self, match: Match) -> dict:
        """
        Extrair features para um match futuro

        Como não temos estatísticas reais (jogo ainda não aconteceu),
        usamos:
        1. Forma recente
        2. H2H
        3. Médias da temporada

        Features do jogo em si serão substituídas pelas médias dos times
        """
        # Features de forma recente
        home_form = self.extractor.get_recent_form(
            match.home_team_id,
            match.match_date,
            n_games=5
        )
        away_form = self.extractor.get_recent_form(
            match.away_team_id,
            match.match_date,
            n_games=5
        )

        # H2H
        h2h = self.extractor.get_h2h_stats(
            match.home_team_id,
            match.away_team_id,
            match.match_date,
            n_games=5
        )

        # Stats da temporada
        home_season = self.extractor.get_season_stats(
            match.home_team_id,
            match.match_date,
            match.season or 2024
        )
        away_season = self.extractor.get_season_stats(
            match.away_team_id,
            match.match_date,
            match.season or 2024
        )

        # Features "básicas" estimadas a partir das médias
        # (já que o jogo não aconteceu ainda)
        estimated_features = {
            'possession_home': home_season['avg_possession'],
            'possession_away': away_season['avg_possession'],
            'shots_home': home_season['avg_shots'],
            'shots_away': away_season['avg_shots'],
            'shots_on_target_home': home_season['avg_shots_on_target'],
            'shots_on_target_away': away_season['avg_shots_on_target'],
            'corners_home': home_season['avg_corners'],
            'corners_away': away_season['avg_corners'],
            'fouls_home': 10,  # Default
            'fouls_away': 10,  # Default
        }

        # Features derivadas
        estimated_features['possession_diff'] = (
            estimated_features['possession_home'] - estimated_features['possession_away']
        )
        estimated_features['shots_diff'] = (
            estimated_features['shots_home'] - estimated_features['shots_away']
        )
        estimated_features['shots_on_target_diff'] = (
            estimated_features['shots_on_target_home'] - estimated_features['shots_on_target_away']
        )
        estimated_features['corners_diff'] = (
            estimated_features['corners_home'] - estimated_features['corners_away']
        )

        # Combinar todas as features
        features = {
            **estimated_features,
            # Forma recente - Home
            'home_recent_wins': home_form['wins'],
            'home_recent_draws': home_form['draws'],
            'home_recent_losses': home_form['losses'],
            'home_recent_goals_for': home_form['avg_goals_for'],
            'home_recent_goals_against': home_form['avg_goals_against'],
            'home_recent_win_rate': home_form['win_rate'],
            'home_recent_ppg': home_form['points_per_game'],
            # Forma recente - Away
            'away_recent_wins': away_form['wins'],
            'away_recent_draws': away_form['draws'],
            'away_recent_losses': away_form['losses'],
            'away_recent_goals_for': away_form['avg_goals_for'],
            'away_recent_goals_against': away_form['avg_goals_against'],
            'away_recent_win_rate': away_form['win_rate'],
            'away_recent_ppg': away_form['points_per_game'],
            # H2H
            'h2h_games': h2h['h2h_games'],
            'h2h_home_wins': h2h['h2h_home_wins'],
            'h2h_draws': h2h['h2h_draws'],
            'h2h_away_wins': h2h['h2h_away_wins'],
            'h2h_home_win_rate': h2h['h2h_home_win_rate'],
            # Temporada - Home
            'home_season_avg_possession': home_season['avg_possession'],
            'home_season_avg_shots': home_season['avg_shots'],
            'home_season_clean_sheets': home_season['clean_sheet_rate'],
            # Temporada - Away
            'away_season_avg_possession': away_season['avg_possession'],
            'away_season_avg_shots': away_season['avg_shots'],
            'away_season_clean_sheets': away_season['clean_sheet_rate'],
            # Diferenças de forma
            'form_ppg_diff': home_form['points_per_game'] - away_form['points_per_game'],
            'form_win_rate_diff': home_form['win_rate'] - away_form['win_rate'],
        }

        return features

    def predict_match(self, match: Match) -> dict:
        """
        Fazer predição para um match

        Returns:
            dict com predição, probabilidades e confiança
        """
        # Extrair features
        features = self.extract_features_for_match(match)

        # Criar DataFrame com features na ordem correta
        X = pd.DataFrame([features])[self.feature_names]

        # Fazer predição
        if self.model_name in ['xgboost', 'lightgbm'] and self.label_encoder:
            # Modelos que usam encoding
            pred_encoded = self.model.predict(X)[0]
            predicted_result = self.label_encoder.inverse_transform([pred_encoded])[0]

            # Probabilidades
            proba = self.model.predict_proba(X)[0]
            # proba está em ordem [A, D, H] (alfabética)
            # Precisamos mapear corretamente
            proba_dict = {}
            for i, label in enumerate(self.label_encoder.classes_):
                proba_dict[label] = float(proba[i])
        else:
            # Random Forest, Gradient Boosting
            predicted_result = self.model.predict(X)[0]

            # Probabilidades
            proba = self.model.predict_proba(X)[0]
            classes = self.model.classes_

            proba_dict = {classes[i]: float(proba[i]) for i in range(len(classes))}

        # Buscar times
        home_team = self.db.query(Team).filter(Team.id == match.home_team_id).first()
        away_team = self.db.query(Team).filter(Team.id == match.away_team_id).first()

        result = {
            'match_id': match.id,
            'home_team': home_team.name if home_team else 'Unknown',
            'away_team': away_team.name if away_team else 'Unknown',
            'match_date': match.match_date,
            'predicted_result': predicted_result,
            'confidence_home': proba_dict.get('H', 0.0),
            'confidence_draw': proba_dict.get('D', 0.0),
            'confidence_away': proba_dict.get('A', 0.0),
            'model_version': f'{self.model_name}_enhanced',
        }

        return result

    def generate_predictions_for_upcoming_matches(self, days_ahead: int = 7):
        """Gerar predições para próximos N dias"""
        from datetime import timedelta

        today = datetime.now()
        future_date = today + timedelta(days=days_ahead)

        # Buscar matches futuros
        upcoming_matches = self.db.query(Match).filter(
            Match.status.in_(['NS', 'TBD', 'SCHEDULED']),
            Match.match_date >= today,
            Match.match_date <= future_date
        ).order_by(Match.match_date).all()

        print(f"\n📅 Matches futuros (próximos {days_ahead} dias): {len(upcoming_matches)}")

        predictions = []
        created = 0
        updated = 0

        for match in upcoming_matches:
            try:
                # Fazer predição
                pred_data = self.predict_match(match)

                # Adaptar ao modelo Prediction existente
                market_outcome_map = {
                    'H': '1',  # Home win
                    'D': 'X',  # Draw
                    'A': '2'   # Away win
                }

                # Verificar se já existe predição 1X2 para este match
                existing = self.db.query(Prediction).filter(
                    Prediction.match_id == match.id,
                    Prediction.market_type == '1X2',
                    Prediction.prediction_type == 'SINGLE'
                ).first()

                # Preparar dados
                predicted_outcome = market_outcome_map[pred_data['predicted_result']]
                confidence_score = max(
                    pred_data['confidence_home'],
                    pred_data['confidence_draw'],
                    pred_data['confidence_away']
                )

                key_factors = {
                    'model': pred_data['model_version'],
                    'confidence_home': float(pred_data['confidence_home']),
                    'confidence_draw': float(pred_data['confidence_draw']),
                    'confidence_away': float(pred_data['confidence_away']),
                    'predicted_result': pred_data['predicted_result']
                }

                analysis = (
                    f"Casa: {pred_data['confidence_home']*100:.1f}% | "
                    f"Empate: {pred_data['confidence_draw']*100:.1f}% | "
                    f"Fora: {pred_data['confidence_away']*100:.1f}%"
                )

                if existing:
                    # Atualizar
                    existing.predicted_outcome = predicted_outcome
                    existing.predicted_probability = float(confidence_score)
                    existing.confidence_score = float(confidence_score)
                    existing.key_factors = key_factors
                    existing.analysis_summary = analysis
                    existing.updated_at = datetime.now()
                    updated += 1
                else:
                    # Criar nova
                    prediction = Prediction(
                        match_id=match.id,
                        prediction_type='SINGLE',
                        market_type='1X2',
                        predicted_outcome=predicted_outcome,
                        predicted_probability=float(confidence_score),
                        confidence_score=float(confidence_score),
                        key_factors=key_factors,
                        analysis_summary=analysis,
                        final_recommendation='MONITOR'  # Default
                    )
                    self.db.add(prediction)
                    created += 1

                predictions.append(pred_data)

            except Exception as e:
                print(f"   ❌ Erro no match {match.id}: {e}")

        self.db.commit()

        return {
            'total': len(predictions),
            'created': created,
            'updated': updated,
            'predictions': predictions
        }


def main():
    print("🔮 GERADOR DE PREDIÇÕES")
    print("="*60)

    db = SessionLocal()

    try:
        # Criar gerador
        generator = PredictionGenerator(db, model_name='random_forest')

        # Gerar predições para próximos 7 dias
        result = generator.generate_predictions_for_upcoming_matches(days_ahead=30)

        print(f"\n✅ Predições geradas:")
        print(f"   Criadas: {result['created']}")
        print(f"   Atualizadas: {result['updated']}")
        print(f"   Total: {result['total']}")

        # Mostrar algumas predições
        if result['predictions']:
            print(f"\n📋 Primeiras 10 predições:")
            print("="*80)
            for pred in result['predictions'][:10]:
                result_emoji = {'H': '🏠', 'D': '🤝', 'A': '✈️'}
                emoji = result_emoji.get(pred['predicted_result'], '❓')

                print(f"\n{pred['match_date'].strftime('%d/%m %H:%M')} - {emoji} {pred['predicted_result']}")
                print(f"   {pred['home_team']} vs {pred['away_team']}")
                print(f"   Casa: {pred['confidence_home']*100:.1f}% | "
                      f"Empate: {pred['confidence_draw']*100:.1f}% | "
                      f"Fora: {pred['confidence_away']*100:.1f}%")

        print("\n" + "="*60)
        print("🎉 PREDIÇÕES SALVAS NO BANCO!")
        print("="*60)

    finally:
        db.close()


if __name__ == "__main__":
    main()
