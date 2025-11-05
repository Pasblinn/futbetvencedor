"""
🤖 TRAIN ML WITH CSV - Treinar modelos ML com dados coletados do CSV
Usa os 380 jogos reais do Brasileirão 2024 extraídos da Wikipedia
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib
import os
from datetime import datetime

class MLTrainerCSV:
    """
    🤖 Treinador ML usando dados do CSV coletado
    """

    def __init__(self):
        self.models = {}
        self.encoders = {}
        self.feature_importance = {}

        # Diretório para salvar modelos
        self.models_dir = "models/brasileirao_real"
        os.makedirs(self.models_dir, exist_ok=True)

    def load_data(self):
        """
        📊 Carregar dados do CSV
        """
        print("📊 CARREGANDO DADOS DO BRASILEIRÃO 2024...")

        if not os.path.exists('brasileirao_2024_matches_clean.csv'):
            print("❌ Arquivo brasileirao_2024_matches_clean.csv não encontrado!")
            return None

        df = pd.read_csv('brasileirao_2024_matches_clean.csv')
        print(f"⚽ Jogos carregados: {len(df)}")
        print(f"📋 Colunas: {list(df.columns)}")

        # Estatísticas básicas
        print(f"\n📊 ESTATÍSTICAS DOS DADOS:")
        print(f"  🏠 Vitórias casa: {len(df[df['result'] == 'home_win'])}")
        print(f"  ✈️ Vitórias visitante: {len(df[df['result'] == 'away_win'])}")
        print(f"  🤝 Empates: {len(df[df['result'] == 'draw'])}")
        print(f"  ⚽ Média gols: {df['total_goals'].mean():.2f}")
        print(f"  🏟️ Times únicos: {df['home_team'].nunique()}")

        return df

    def prepare_features(self, df):
        """
        🔧 Preparar features para treinamento
        """
        print("\n🔧 PREPARANDO FEATURES...")

        # Criar encoders para times
        self.encoders = {
            'home_team': LabelEncoder(),
            'away_team': LabelEncoder()
        }

        # Aplicar encoding
        df_encoded = df.copy()
        df_encoded['home_team_encoded'] = self.encoders['home_team'].fit_transform(df['home_team'])
        df_encoded['away_team_encoded'] = self.encoders['away_team'].fit_transform(df['away_team'])

        # Features baseadas em estatísticas dos times
        # Calcular força dos times baseado em desempenho geral
        team_stats = self.calculate_team_strength(df)

        df_encoded['home_strength'] = df_encoded['home_team'].map(team_stats).fillna(0.5)
        df_encoded['away_strength'] = df_encoded['away_team'].map(team_stats).fillna(0.5)
        df_encoded['strength_diff'] = df_encoded['home_strength'] - df_encoded['away_strength']

        # Features adicionais
        df_encoded['is_high_scoring_teams'] = (
            (df_encoded['home_strength'] > 0.6) |
            (df_encoded['away_strength'] > 0.6)
        ).astype(int)

        # Features finais para o modelo
        feature_columns = [
            'home_team_encoded', 'away_team_encoded',
            'home_strength', 'away_strength', 'strength_diff',
            'is_high_scoring_teams'
        ]

        X = df_encoded[feature_columns].values
        y = df_encoded['result'].values

        print(f"✅ Features preparadas: {len(feature_columns)} características")
        print(f"📊 Samples: {len(X)}")

        return X, y, feature_columns

    def calculate_team_strength(self, df):
        """
        💪 Calcular força dos times baseado em resultados
        """
        team_stats = {}

        # Calcular estatísticas para cada time
        for team in df['home_team'].unique():
            # Jogos em casa
            home_games = df[df['home_team'] == team]
            home_wins = len(home_games[home_games['result'] == 'home_win'])
            home_draws = len(home_games[home_games['result'] == 'draw'])

            # Jogos fora
            away_games = df[df['away_team'] == team]
            away_wins = len(away_games[away_games['result'] == 'away_win'])
            away_draws = len(away_games[away_games['result'] == 'draw'])

            # Calcular força (win rate ponderada)
            total_games = len(home_games) + len(away_games)
            if total_games > 0:
                points = (home_wins + away_wins) * 3 + (home_draws + away_draws) * 1
                max_points = total_games * 3
                strength = points / max_points
            else:
                strength = 0.5

            team_stats[team] = strength

        return team_stats

    def train_models(self, X, y, feature_names):
        """
        🎯 Treinar múltiplos modelos ML
        """
        print("\n🎯 TREINANDO MODELOS ML...")

        # Dividir dados
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        print(f"📊 Treino: {len(X_train)} | Teste: {len(X_test)}")

        # Modelos a treinar
        models_to_train = {
            'random_forest': RandomForestClassifier(n_estimators=100, random_state=42),
            'gradient_boosting': GradientBoostingClassifier(n_estimators=100, random_state=42),
            'logistic_regression': LogisticRegression(random_state=42, max_iter=1000)
        }

        results = {}

        for model_name, model in models_to_train.items():
            print(f"\n🔄 Treinando {model_name}...")

            # Treinar
            model.fit(X_train, y_train)

            # Avaliar
            train_score = model.score(X_train, y_train)
            test_score = model.score(X_test, y_test)
            y_pred = model.predict(X_test)

            # Salvar modelo
            self.models[model_name] = model
            model_path = os.path.join(self.models_dir, f"{model_name}_brasileirao.joblib")
            joblib.dump(model, model_path)

            # Feature importance
            if hasattr(model, 'feature_importances_'):
                importance = dict(zip(feature_names, model.feature_importances_))
                self.feature_importance[model_name] = importance
                print(f"  📊 Top features: {sorted(importance.items(), key=lambda x: x[1], reverse=True)[:3]}")

            results[model_name] = {
                'train_accuracy': train_score,
                'test_accuracy': test_score,
                'classification_report': classification_report(y_test, y_pred, output_dict=True)
            }

            print(f"  ✅ Treino: {train_score:.3f} | Teste: {test_score:.3f}")

        # Ensemble
        ensemble_score = self.evaluate_ensemble(X_test, y_test)

        return results, ensemble_score

    def evaluate_ensemble(self, X_test, y_test):
        """
        🎯 Avaliar ensemble de modelos
        """
        if len(self.models) < 2:
            return None

        print(f"\n🎯 AVALIANDO ENSEMBLE...")

        # Predições de todos os modelos
        predictions = {}
        for model_name, model in self.models.items():
            predictions[model_name] = model.predict(X_test)

        # Votação majoritária
        ensemble_pred = []
        for i in range(len(X_test)):
            votes = [predictions[model][i] for model in predictions]
            ensemble_pred.append(max(set(votes), key=votes.count))

        ensemble_accuracy = accuracy_score(y_test, ensemble_pred)
        print(f"🏆 Ensemble Accuracy: {ensemble_accuracy:.3f}")

        return ensemble_accuracy

    def save_metadata(self, feature_names):
        """
        💾 Salvar metadados do treinamento
        """
        metadata = {
            'feature_names': feature_names,
            'training_date': datetime.now().isoformat(),
            'encoders': self.encoders,
            'data_source': 'brasileirao_2024_wikipedia',
            'total_samples': 380
        }

        metadata_path = os.path.join(self.models_dir, "metadata.joblib")
        joblib.dump(metadata, metadata_path)
        print(f"💾 Metadados salvos: {metadata_path}")

    def predict_match(self, home_team, away_team):
        """
        🔮 Predizer resultado de um jogo
        """
        try:
            # Preparar dados do jogo
            if home_team not in self.encoders['home_team'].classes_:
                print(f"⚠️ Time {home_team} não conhecido")
                return None

            if away_team not in self.encoders['away_team'].classes_:
                print(f"⚠️ Time {away_team} não conhecido")
                return None

            # Encode times
            home_encoded = self.encoders['home_team'].transform([home_team])[0]
            away_encoded = self.encoders['away_team'].transform([away_team])[0]

            # Features básicas (usar valores médios para strength)
            features = np.array([[
                home_encoded, away_encoded,
                0.5, 0.5, 0.0, 0  # Valores padrão
            ]])

            # Predições de todos os modelos
            predictions = {}
            for model_name, model in self.models.items():
                pred = model.predict(features)[0]
                if hasattr(model, 'predict_proba'):
                    proba = model.predict_proba(features)[0]
                    predictions[model_name] = {
                        'prediction': pred,
                        'probabilities': dict(zip(model.classes_, proba))
                    }
                else:
                    predictions[model_name] = {'prediction': pred}

            # Ensemble
            votes = [pred['prediction'] for pred in predictions.values()]
            ensemble_pred = max(set(votes), key=votes.count)
            confidence = votes.count(ensemble_pred) / len(votes)

            return {
                'home_team': home_team,
                'away_team': away_team,
                'ensemble_prediction': ensemble_pred,
                'confidence': confidence,
                'individual_predictions': predictions
            }

        except Exception as e:
            print(f"❌ Erro na predição: {e}")
            return None

def main():
    """Função principal"""
    print("🤖 TREINAMENTO ML COM DADOS REAIS DO BRASILEIRÃO 2024")
    print("🎯 Dataset: 380 jogos extraídos da Wikipedia")
    print("🔬 Algoritmos: Random Forest, Gradient Boosting, Logistic Regression")
    print("=" * 80)

    trainer = MLTrainerCSV()

    # 1. Carregar dados
    df = trainer.load_data()
    if df is None:
        return

    # 2. Preparar features
    X, y, feature_names = trainer.prepare_features(df)

    # 3. Treinar modelos
    results, ensemble_score = trainer.train_models(X, y, feature_names)

    # 4. Salvar metadados
    trainer.save_metadata(feature_names)

    # 5. Relatório final
    print(f"\n" + "="*80)
    print("🎉 TREINAMENTO CONCLUÍDO!")
    print(f"📁 Modelos salvos em: {trainer.models_dir}/")
    print(f"🎯 Melhor modelo individual: {max(results.keys(), key=lambda k: results[k]['test_accuracy'])}")
    print(f"🏆 Ensemble accuracy: {ensemble_score:.3f}")

    # 6. Testar predições
    print(f"\n🔮 TESTANDO PREDIÇÕES:")
    test_matches = [
        ("Flamengo", "Palmeiras"),
        ("Botafogo", "São Paulo"),
        ("Corinthians", "Vasco da Gama")
    ]

    for home, away in test_matches:
        pred = trainer.predict_match(home, away)
        if pred:
            print(f"  🔮 {home} vs {away}: {pred['ensemble_prediction']} (confiança: {pred['confidence']:.2f})")

    print(f"\n🚀 PRÓXIMO PASSO: Integrar com endpoints da API!")

if __name__ == "__main__":
    main()