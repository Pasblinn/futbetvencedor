#!/usr/bin/env python3
"""
🚀 TREINAMENTO ML COM FEATURES AVANÇADAS
Features: forma recente, H2H, estatísticas da temporada
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, func
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import classification_report, accuracy_score
import joblib
import json

from app.core.database import SessionLocal
from app.models.match import Match
from app.models.statistics import MatchStatistics
from app.models.team import Team

class EnhancedFeatureExtractor:
    """Extrator de features avançadas para ML"""

    def __init__(self, db):
        self.db = db
        self.cache = {}  # Cache para otimizar queries

    def get_recent_form(self, team_id: int, match_date: datetime, n_games: int = 5) -> dict:
        """
        Forma recente do time (últimos N jogos antes da data)

        Returns:
            dict com wins, draws, losses, goals_for, goals_against, points
        """
        cache_key = f"form_{team_id}_{match_date.date()}_{n_games}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Buscar últimos N jogos do time antes da data
        recent_matches = self.db.query(Match).filter(
            or_(Match.home_team_id == team_id, Match.away_team_id == team_id),
            Match.match_date < match_date,
            Match.status == 'FT'
        ).order_by(Match.match_date.desc()).limit(n_games).all()

        wins = 0
        draws = 0
        losses = 0
        goals_for = 0
        goals_against = 0

        for match in recent_matches:
            is_home = match.home_team_id == team_id
            team_goals = match.home_score if is_home else match.away_score
            opponent_goals = match.away_score if is_home else match.home_score

            if team_goals is not None and opponent_goals is not None:
                goals_for += team_goals
                goals_against += opponent_goals

                if team_goals > opponent_goals:
                    wins += 1
                elif team_goals == opponent_goals:
                    draws += 1
                else:
                    losses += 1

        games_played = len(recent_matches)
        points = wins * 3 + draws

        result = {
            'games_played': games_played,
            'wins': wins,
            'draws': draws,
            'losses': losses,
            'goals_for': goals_for,
            'goals_against': goals_against,
            'points': points,
            'avg_goals_for': goals_for / games_played if games_played > 0 else 0,
            'avg_goals_against': goals_against / games_played if games_played > 0 else 0,
            'win_rate': wins / games_played if games_played > 0 else 0,
            'points_per_game': points / games_played if games_played > 0 else 0
        }

        self.cache[cache_key] = result
        return result

    def get_h2h_stats(self, home_team_id: int, away_team_id: int, match_date: datetime, n_games: int = 5) -> dict:
        """
        Estatísticas de confrontos diretos (Head-to-Head)

        Returns:
            dict com histórico de confrontos
        """
        cache_key = f"h2h_{home_team_id}_{away_team_id}_{match_date.date()}_{n_games}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Buscar últimos confrontos entre os times
        h2h_matches = self.db.query(Match).filter(
            or_(
                and_(Match.home_team_id == home_team_id, Match.away_team_id == away_team_id),
                and_(Match.home_team_id == away_team_id, Match.away_team_id == home_team_id)
            ),
            Match.match_date < match_date,
            Match.status == 'FT'
        ).order_by(Match.match_date.desc()).limit(n_games).all()

        home_wins = 0
        draws = 0
        away_wins = 0
        total_goals_home = 0
        total_goals_away = 0

        for match in h2h_matches:
            # Verificar qual time era o "home" neste confronto
            was_home = match.home_team_id == home_team_id

            if match.home_score is not None and match.away_score is not None:
                if was_home:
                    total_goals_home += match.home_score
                    total_goals_away += match.away_score

                    if match.home_score > match.away_score:
                        home_wins += 1
                    elif match.home_score == match.away_score:
                        draws += 1
                    else:
                        away_wins += 1
                else:
                    total_goals_home += match.away_score
                    total_goals_away += match.home_score

                    if match.away_score > match.home_score:
                        home_wins += 1
                    elif match.away_score == match.home_score:
                        draws += 1
                    else:
                        away_wins += 1

        games_played = len(h2h_matches)

        result = {
            'h2h_games': games_played,
            'h2h_home_wins': home_wins,
            'h2h_draws': draws,
            'h2h_away_wins': away_wins,
            'h2h_home_win_rate': home_wins / games_played if games_played > 0 else 0.33,
            'h2h_avg_goals_home': total_goals_home / games_played if games_played > 0 else 0,
            'h2h_avg_goals_away': total_goals_away / games_played if games_played > 0 else 0
        }

        self.cache[cache_key] = result
        return result

    def get_season_stats(self, team_id: int, match_date: datetime, season: int) -> dict:
        """
        Estatísticas da temporada até a data do jogo

        Returns:
            dict com médias da temporada
        """
        cache_key = f"season_{team_id}_{match_date.date()}_{season}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Buscar todos os jogos do time na temporada até a data
        season_matches = self.db.query(Match).join(
            MatchStatistics, Match.id == MatchStatistics.match_id
        ).filter(
            or_(Match.home_team_id == team_id, Match.away_team_id == team_id),
            Match.match_date < match_date,
            Match.season == season,
            Match.status == 'FT'
        ).all()

        total_possession = 0
        total_shots = 0
        total_shots_on_target = 0
        total_corners = 0
        clean_sheets = 0
        games_with_stats = 0

        for match in season_matches:
            is_home = match.home_team_id == team_id

            # Buscar estatísticas
            stats = self.db.query(MatchStatistics).filter(
                MatchStatistics.match_id == match.id
            ).first()

            if stats:
                games_with_stats += 1

                if is_home:
                    if stats.possession_home:
                        total_possession += stats.possession_home
                    if stats.shots_home:
                        total_shots += stats.shots_home
                    if stats.shots_on_target_home:
                        total_shots_on_target += stats.shots_on_target_home
                    if stats.corners_home:
                        total_corners += stats.corners_home

                    # Clean sheet se não sofreu gols
                    if match.away_score == 0:
                        clean_sheets += 1
                else:
                    if stats.possession_away:
                        total_possession += stats.possession_away
                    if stats.shots_away:
                        total_shots += stats.shots_away
                    if stats.shots_on_target_away:
                        total_shots_on_target += stats.shots_on_target_away
                    if stats.corners_away:
                        total_corners += stats.corners_away

                    if match.home_score == 0:
                        clean_sheets += 1

        result = {
            'season_games': len(season_matches),
            'season_games_with_stats': games_with_stats,
            'avg_possession': total_possession / games_with_stats if games_with_stats > 0 else 50,
            'avg_shots': total_shots / games_with_stats if games_with_stats > 0 else 10,
            'avg_shots_on_target': total_shots_on_target / games_with_stats if games_with_stats > 0 else 4,
            'avg_corners': total_corners / games_with_stats if games_with_stats > 0 else 5,
            'clean_sheet_rate': clean_sheets / len(season_matches) if len(season_matches) > 0 else 0
        }

        self.cache[cache_key] = result
        return result


def create_enhanced_dataset(db):
    """Criar dataset com features avançadas"""
    print("📊 Carregando matches com estatísticas...")

    # Buscar matches finalizados com estatísticas
    matches = db.query(Match).join(
        MatchStatistics, Match.id == MatchStatistics.match_id
    ).filter(
        Match.status == 'FT',
        Match.home_score.isnot(None),
        Match.away_score.isnot(None)
    ).order_by(Match.match_date).all()

    print(f"   ✅ {len(matches)} matches carregados")

    extractor = EnhancedFeatureExtractor(db)

    data = []

    print("\n🔧 Extraindo features avançadas...")
    for i, match in enumerate(matches, 1):
        if i % 200 == 0:
            print(f"   Processando {i}/{len(matches)}...")

        # Buscar estatísticas do jogo
        stats = db.query(MatchStatistics).filter(
            MatchStatistics.match_id == match.id
        ).first()

        if not stats:
            continue

        # Features básicas (do treino anterior)
        basic_features = {
            'possession_home': stats.possession_home or 50,
            'possession_away': stats.possession_away or 50,
            'shots_home': stats.shots_home or 0,
            'shots_away': stats.shots_away or 0,
            'shots_on_target_home': stats.shots_on_target_home or 0,
            'shots_on_target_away': stats.shots_on_target_away or 0,
            'corners_home': stats.corners_home or 0,
            'corners_away': stats.corners_away or 0,
            'fouls_home': stats.fouls_home or 0,
            'fouls_away': stats.fouls_away or 0,
        }

        # Features derivadas
        basic_features['possession_diff'] = basic_features['possession_home'] - basic_features['possession_away']
        basic_features['shots_diff'] = basic_features['shots_home'] - basic_features['shots_away']
        basic_features['shots_on_target_diff'] = basic_features['shots_on_target_home'] - basic_features['shots_on_target_away']
        basic_features['corners_diff'] = basic_features['corners_home'] - basic_features['corners_away']

        # Features avançadas - Forma recente
        home_form = extractor.get_recent_form(match.home_team_id, match.match_date, n_games=5)
        away_form = extractor.get_recent_form(match.away_team_id, match.match_date, n_games=5)

        # Features avançadas - H2H
        h2h = extractor.get_h2h_stats(match.home_team_id, match.away_team_id, match.match_date, n_games=5)

        # Features avançadas - Temporada
        home_season = extractor.get_season_stats(match.home_team_id, match.match_date, match.season or 2024)
        away_season = extractor.get_season_stats(match.away_team_id, match.match_date, match.season or 2024)

        # Resultado
        if match.home_score > match.away_score:
            result = 'H'
        elif match.home_score < match.away_score:
            result = 'A'
        else:
            result = 'D'

        # Combinar todas as features
        row = {
            **basic_features,
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
            # Resultado
            'result': result
        }

        data.append(row)

    df = pd.DataFrame(data)
    print(f"   ✅ Dataset criado: {len(df)} matches com features avançadas")

    return df


def train_enhanced_models(df):
    """Treinar modelos com features avançadas"""
    print("\n📊 Preparando dados para treinamento...")

    # Separar features e target
    X = df.drop('result', axis=1)
    y = df['result']

    # Encodar target para modelos que precisam (XGBoost, LightGBM)
    from sklearn.preprocessing import LabelEncoder
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)  # A=0, D=1, H=2

    print(f"   ✅ {len(X.columns)} features")
    print(f"   ✅ {len(df)} amostras")
    print(f"\n   Distribuição de resultados:")
    print(y.value_counts())

    # Split treino/teste
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Split também para versão encoded
    _, _, y_train_enc, y_test_enc = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42, stratify=y
    )

    print(f"\n📊 Split dos dados:")
    print(f"   Treino: {len(X_train)} matches")
    print(f"   Teste: {len(X_test)} matches")

    models = {}
    scores = {}

    print("\n🎯 Treinando modelos...\n")

    # Random Forest
    print("   1️⃣  Random Forest...")
    rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=15,
        min_samples_split=10,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1
    )
    rf.fit(X_train, y_train)
    y_pred_rf = rf.predict(X_test)
    acc_rf = accuracy_score(y_test, y_pred_rf)
    models['random_forest'] = rf
    scores['random_forest'] = acc_rf
    print(f"      ✅ Acurácia: {acc_rf*100:.2f}%")

    # Gradient Boosting
    print("\n   2️⃣  Gradient Boosting...")
    gb = GradientBoostingClassifier(
        n_estimators=200,
        learning_rate=0.1,
        max_depth=5,
        random_state=42
    )
    gb.fit(X_train, y_train)
    y_pred_gb = gb.predict(X_test)
    acc_gb = accuracy_score(y_test, y_pred_gb)
    models['gradient_boosting'] = gb
    scores['gradient_boosting'] = acc_gb
    print(f"      ✅ Acurácia: {acc_gb*100:.2f}%")

    # XGBoost (se disponível)
    try:
        import xgboost as xgb
        print("\n   3️⃣  XGBoost...")
        xgb_model = xgb.XGBClassifier(
            n_estimators=200,
            learning_rate=0.1,
            max_depth=5,
            random_state=42,
            n_jobs=-1
        )
        xgb_model.fit(X_train, y_train_enc)
        y_pred_xgb_enc = xgb_model.predict(X_test)
        # Decodificar para comparar
        y_pred_xgb = label_encoder.inverse_transform(y_pred_xgb_enc)
        acc_xgb = accuracy_score(y_test, y_pred_xgb)
        models['xgboost'] = xgb_model
        scores['xgboost'] = acc_xgb
        print(f"      ✅ Acurácia: {acc_xgb*100:.2f}%")
    except ImportError:
        print("\n   ⚠️  XGBoost não disponível (pip install xgboost)")
    except Exception as e:
        print(f"\n   ⚠️  Erro no XGBoost: {e}")

    # LightGBM (se disponível)
    try:
        import lightgbm as lgb
        print("\n   4️⃣  LightGBM...")
        lgb_model = lgb.LGBMClassifier(
            n_estimators=200,
            learning_rate=0.1,
            max_depth=5,
            random_state=42,
            n_jobs=-1,
            verbose=-1
        )
        lgb_model.fit(X_train, y_train_enc)
        y_pred_lgb_enc = lgb_model.predict(X_test)
        y_pred_lgb = label_encoder.inverse_transform(y_pred_lgb_enc)
        acc_lgb = accuracy_score(y_test, y_pred_lgb)
        models['lightgbm'] = lgb_model
        scores['lightgbm'] = acc_lgb
        print(f"      ✅ Acurácia: {acc_lgb*100:.2f}%")
    except ImportError:
        print("\n   ⚠️  LightGBM não disponível (pip install lightgbm)")
    except Exception as e:
        print(f"\n   ⚠️  Erro no LightGBM: {e}")

    # Melhor modelo
    best_model_name = max(scores, key=scores.get)
    best_model = models[best_model_name]
    best_score = scores[best_model_name]

    print(f"\n🏆 Melhor modelo: {best_model_name} ({best_score*100:.2f}%)")

    # Relatório detalhado
    y_pred_best = best_model.predict(X_test)

    print(f"\n📋 Relatório de Classificação:")
    print("="*60)
    print(classification_report(y_test, y_pred_best, target_names=['Away', 'Draw', 'Home']))

    # Feature importance
    if hasattr(best_model, 'feature_importances_'):
        importances = pd.DataFrame({
            'feature': X.columns,
            'importance': best_model.feature_importances_
        }).sort_values('importance', ascending=False)

        print("\n📊 Importância das Features (Top 15):")
        for idx, row in importances.head(15).iterrows():
            print(f"   {row['feature']}: {row['importance']:.4f}")

    return models, scores, best_model_name, X.columns.tolist(), label_encoder


def save_models(models, scores, best_model_name, feature_names, label_encoder=None):
    """Salvar modelos treinados"""
    print("\n💾 Salvando modelos...")

    models_dir = Path(__file__).parent / 'models'
    models_dir.mkdir(exist_ok=True)

    # Salvar cada modelo
    for name, model in models.items():
        path = models_dir / f"{name}_enhanced_model.joblib"
        joblib.dump(model, path)
        print(f"   ✅ {name} salvo em {path}")

    # Salvar feature names
    feature_path = models_dir / 'enhanced_feature_names.joblib'
    joblib.dump(feature_names, feature_path)
    print(f"   ✅ Feature names salvos em {feature_path}")

    # Salvar label encoder
    if label_encoder:
        encoder_path = models_dir / 'label_encoder.joblib'
        joblib.dump(label_encoder, encoder_path)
        print(f"   ✅ Label encoder salvo em {encoder_path}")

    # Salvar metadata
    metadata = {
        'model_type': 'enhanced_ml',
        'best_model': best_model_name,
        'scores': {k: float(v) for k, v in scores.items()},
        'feature_count': len(feature_names),
        'trained_at': datetime.now().isoformat(),
        'features': feature_names
    }

    metadata_path = models_dir / 'enhanced_model_metadata.json'
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"   ✅ Metadata salvos em {metadata_path}")


def main():
    print("🤖 TREINAMENTO ML COM FEATURES AVANÇADAS")
    print("="*60)

    db = SessionLocal()

    try:
        # Criar dataset
        df = create_enhanced_dataset(db)

        # Treinar modelos
        models, scores, best_model_name, feature_names, label_encoder = train_enhanced_models(df)

        # Salvar modelos
        save_models(models, scores, best_model_name, feature_names, label_encoder)

        print("\n" + "="*60)
        print("🎉 TREINAMENTO CONCLUÍDO!")
        print("="*60)
        print(f"📊 Matches usados: {len(df)}")
        print(f"🎯 Melhor modelo: {best_model_name}")
        print(f"🎯 Melhor acurácia: {scores[best_model_name]*100:.2f}%")
        print(f"💾 Modelos salvos em: models/")

    finally:
        db.close()


if __name__ == "__main__":
    main()
