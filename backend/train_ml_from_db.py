#!/usr/bin/env python3
"""
🤖 TREINO DE ML A PARTIR DO BANCO DE DADOS
Treina modelos de predição usando dados do pipeline
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.models.match import Match
from app.models.statistics import MatchStatistics
from sqlalchemy.orm import joinedload

print("🤖 TREINAMENTO DE MODELOS ML")
print("="*60)

# Criar sessão
db = SessionLocal()

# Buscar matches com estatísticas
print("\n📊 Carregando dados do banco...")
matches = db.query(Match).options(
    joinedload(Match.home_team),
    joinedload(Match.away_team),
    joinedload(Match.statistics)
).filter(
    Match.status == 'FT',
    Match.home_score != None,
    Match.away_score != None
).join(MatchStatistics).all()

print(f"   ✅ {len(matches)} matches carregados")

if len(matches) < 100:
    print("\n❌ Dados insuficientes para treino (mínimo 100 matches)")
    print(f"   Temos apenas {len(matches)} matches com estatísticas")
    db.close()
    sys.exit(1)

# Preparar dataset
print("\n🔧 Preparando dataset...")

data = []
for match in matches:
    stats = match.statistics
    if not stats:
        continue

    # Calcular resultado
    if match.home_score > match.away_score:
        result = 'H'  # Home win
    elif match.home_score < match.away_score:
        result = 'A'  # Away win
    else:
        result = 'D'  # Draw

    # Features
    features = {
        # Estatísticas do jogo
        'possession_home': stats.possession_home or 50.0,
        'possession_away': stats.possession_away or 50.0,
        'shots_home': stats.shots_home or 0,
        'shots_away': stats.shots_away or 0,
        'shots_on_target_home': stats.shots_on_target_home or 0,
        'shots_on_target_away': stats.shots_on_target_away or 0,
        'corners_home': stats.corners_home or 0,
        'corners_away': stats.corners_away or 0,
        'fouls_home': stats.fouls_home or 0,
        'fouls_away': stats.fouls_away or 0,
        'yellow_cards_home': stats.yellow_cards_home or 0,
        'yellow_cards_away': stats.yellow_cards_away or 0,

        # Features derivadas
        'possession_diff': (stats.possession_home or 50) - (stats.possession_away or 50),
        'shots_diff': (stats.shots_home or 0) - (stats.shots_away or 0),
        'shots_on_target_diff': (stats.shots_on_target_home or 0) - (stats.shots_on_target_away or 0),
        'corners_diff': (stats.corners_home or 0) - (stats.corners_away or 0),

        # Target
        'result': result
    }

    data.append(features)

df = pd.DataFrame(data)

print(f"   ✅ Dataset criado: {len(df)} matches")
print(f"\n   Distribuição de resultados:")
print(df['result'].value_counts())

# Separar features e target
X = df.drop('result', axis=1)
y = df['result']

# Split train/test
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"\n📊 Split dos dados:")
print(f"   Treino: {len(X_train)} matches")
print(f"   Teste: {len(X_test)} matches")

# Treinar modelos
print("\n🎯 Treinando modelos...")

models = {}

# 1. Random Forest
print("\n   1️⃣  Random Forest...")
rf = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    random_state=42,
    n_jobs=-1
)
rf.fit(X_train, y_train)
y_pred_rf = rf.predict(X_test)
acc_rf = accuracy_score(y_test, y_pred_rf)
models['random_forest'] = rf

print(f"      ✅ Acurácia: {acc_rf:.2%}")

# 2. Gradient Boosting
print("\n   2️⃣  Gradient Boosting...")
gb = GradientBoostingClassifier(
    n_estimators=100,
    max_depth=5,
    random_state=42
)
gb.fit(X_train, y_train)
y_pred_gb = gb.predict(X_test)
acc_gb = accuracy_score(y_test, y_pred_gb)
models['gradient_boosting'] = gb

print(f"      ✅ Acurácia: {acc_gb:.2%}")

# Escolher melhor modelo
best_model_name = 'random_forest' if acc_rf > acc_gb else 'gradient_boosting'
best_model = models[best_model_name]
best_acc = max(acc_rf, acc_gb)

print(f"\n🏆 Melhor modelo: {best_model_name} ({best_acc:.2%})")

# Relatório detalhado
print(f"\n📋 Relatório de Classificação:")
print("="*60)
if best_model_name == 'random_forest':
    print(classification_report(y_test, y_pred_rf, target_names=['Away', 'Draw', 'Home']))
else:
    print(classification_report(y_test, y_pred_gb, target_names=['Away', 'Draw', 'Home']))

# Feature importance
print(f"\n📊 Importância das Features (Top 10):")
feature_importance = pd.DataFrame({
    'feature': X.columns,
    'importance': best_model.feature_importances_
}).sort_values('importance', ascending=False)

for idx, row in feature_importance.head(10).iterrows():
    print(f"   {row['feature']}: {row['importance']:.4f}")

# Salvar modelos
print(f"\n💾 Salvando modelos...")
models_dir = Path("models")
models_dir.mkdir(exist_ok=True)

for name, model in models.items():
    model_path = models_dir / f"{name}_model.joblib"
    joblib.dump(model, model_path)
    print(f"   ✅ {name} salvo em {model_path}")

# Salvar feature names
feature_names_path = models_dir / "feature_names.joblib"
joblib.dump(list(X.columns), feature_names_path)
print(f"   ✅ Feature names salvos em {feature_names_path}")

# Salvar metadados
metadata = {
    'trained_at': str(pd.Timestamp.now()),
    'n_matches': len(df),
    'n_train': len(X_train),
    'n_test': len(X_test),
    'best_model': best_model_name,
    'accuracy': float(best_acc),
    'features': list(X.columns)
}

import json
metadata_path = models_dir / "model_metadata.json"
with open(metadata_path, 'w') as f:
    json.dump(metadata, f, indent=2)

print(f"   ✅ Metadata salvos em {metadata_path}")

print(f"\n{'='*60}")
print("🎉 TREINAMENTO CONCLUÍDO!")
print(f"{'='*60}")
print(f"📊 Matches usados: {len(df)}")
print(f"🎯 Melhor acurácia: {best_acc:.2%}")
print(f"💾 Modelos salvos em: {models_dir}")

db.close()
