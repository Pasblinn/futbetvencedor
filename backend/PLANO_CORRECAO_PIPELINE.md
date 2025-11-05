# 🔧 PLANO DE CORREÇÃO DA PIPELINE

**Data:** 2025-10-20
**Status:** 🔴 CRÍTICO - Requer ação imediata
**Accuracy Atual:** 34.3% (Meta: 60%+)

---

## 🚨 PROBLEMAS CRÍTICOS IDENTIFICADOS

### 📊 Resumo Executivo

| Problema | Impacto | Prioridade | Causa Raiz |
|----------|---------|------------|------------|
| **#1: ML prevendo DRAW demais** | 🔴 CRÍTICO | P0 | Gerador cria predictions para TODOS markets com edge > 0 |
| **#2: 63.4% predictions não validadas** | 🟡 ALTO | P1 | Jogos futuros + falta de limpeza |
| **#3: Confidence scores descalibrados** | 🟡 ALTO | P1 | Usando probabilidade direta sem calibração |

---

## 🔥 PROBLEMA #1: ML PREVENDO DRAW DEMAIS

### Dados do Problema

**Distribuição REAL dos resultados:**
- Home Win: 44.4%
- Draw: 22.5%
- Away Win: 33.1%

**Distribuição das PREDICTIONS do ML:**
- HOME_WIN: 12.5%
- DRAW: 36.6% ⚠️ (deveria ser ~22%)
- AWAY_WIN: 13.2%
- BTTS_NO: 36.4%

**Accuracy por Outcome:**
- HOME_WIN: 28.3%
- DRAW: 17.3% 🔴 PÉSSIMO!
- AWAY_WIN: 26.1%
- BTTS_NO: 55.7% ✅ BOM
- 1X2 (antigo): 48.6% ✅ OK

### Causa Raiz

**Arquivo:** `app/services/ml_prediction_generator.py` (linha 48-57, 439-444)

```python
MARKETS = [
    'HOME_WIN', 'DRAW', 'AWAY_WIN',
    'BTTS_YES', 'BTTS_NO',
    'OVER_2_5', 'UNDER_2_5',
]

# Filtro atual (linha 439-444):
if not (is_value_bet or probability > 0.60 or edge > 0):
    return None
```

**O problema:**
1. O gerador itera sobre TODOS os 7 markets
2. Para CADA market, se tiver edge > 0 (qualquer edge positivo), cria prediction
3. DRAW geralmente tem odds ~3.0-3.5 (altas)
4. Com probabilidade Poisson de 25-30%, facilmente tem edge > 0
5. Resultado: MUITAS predictions de DRAW são geradas
6. Mas DRAW é o outcome mais difícil de prever!

### Soluções Propostas

#### Solução 1: Selecionar MELHOR outcome por jogo (RECOMENDADO)

```python
def _select_best_1x2_outcome(self, match: Match) -> Optional[str]:
    """
    Analisa os 3 outcomes (HOME_WIN, DRAW, AWAY_WIN) e retorna apenas o MELHOR

    Critérios:
    1. Maior probabilidade
    2. Se probabilidades próximas (diff < 10%), escolher por edge
    3. DRAW só se probabilidade > 35% OU edge > 20%
    """
    poisson_analysis = self._get_poisson_analysis(match)

    outcomes = {
        'HOME_WIN': {
            'prob': poisson_analysis.probabilities['HOME_WIN'],
            'edge': self._calculate_edge(match, 'HOME_WIN')
        },
        'DRAW': {
            'prob': poisson_analysis.probabilities['DRAW'],
            'edge': self._calculate_edge(match, 'DRAW')
        },
        'AWAY_WIN': {
            'prob': poisson_analysis.probabilities['AWAY_WIN'],
            'edge': self._calculate_edge(match, 'AWAY_WIN')
        }
    }

    # FILTRO ESPECIAL PARA DRAW: Exigir mais
    if outcomes['DRAW']['prob'] < 0.35 and outcomes['DRAW']['edge'] < 20:
        outcomes['DRAW']['prob'] = 0  # Remover DRAW da competição

    # Selecionar outcome com maior probabilidade
    best_outcome = max(outcomes.items(), key=lambda x: x[1]['prob'])

    # Se probabilidade muito baixa, não gerar prediction
    if best_outcome[1]['prob'] < 0.30:
        return None

    return best_outcome[0]
```

**Impacto estimado:**
- ✅ Reduzir predictions DRAW de 36.6% para ~20-25%
- ✅ Aumentar accuracy DRAW de 17.3% para ~30-35%
- ✅ Aumentar accuracy geral de 34.3% para ~45-50%

#### Solução 2: Ajustar thresholds por outcome

```python
# Thresholds específicos por market
MARKET_THRESHOLDS = {
    'HOME_WIN': {'min_prob': 0.30, 'min_edge': 0},
    'DRAW': {'min_prob': 0.35, 'min_edge': 15},  # DRAW mais exigente
    'AWAY_WIN': {'min_prob': 0.30, 'min_edge': 0},
    'BTTS_YES': {'min_prob': 0.45, 'min_edge': 5},
    'BTTS_NO': {'min_prob': 0.50, 'min_edge': 5},
    'OVER_2_5': {'min_prob': 0.50, 'min_edge': 5},
    'UNDER_2_5': {'min_prob': 0.50, 'min_edge': 5},
}

# No filtro:
threshold = MARKET_THRESHOLDS[market]
if probability < threshold['min_prob'] or edge < threshold['min_edge']:
    return None
```

**Impacto estimado:**
- ✅ Reduzir predictions DRAW de 36.6% para ~25-28%
- ✅ Aumentar accuracy DRAW de 17.3% para ~25-30%
- ✅ Aumentar accuracy geral de 34.3% para ~40-45%

#### Solução 3: Usar ML Classifier para escolher outcome

```python
def _use_ml_classifier(self, match: Match) -> Optional[str]:
    """
    Usa modelo ML treinado para escolher o melhor outcome
    ao invés de gerar todos com edge positivo
    """
    features = self._extract_features(match)

    # Classificador 1X2 (já treinado)
    prediction = self.ml_1x2_classifier.predict(features)
    probability = self.ml_1x2_classifier.predict_proba(features)

    # Só retornar se confidence > 40%
    if max(probability) < 0.40:
        return None

    return prediction
```

**Impacto estimado:**
- ✅ Accuracy baseada no modelo treinado (~45.6% atual)
- ⚠️ Requer retreinar com dados balanceados
- ⏱️ Mais complexo de implementar

### Recomendação

**Implementar Solução 1 + Solução 2 combinadas:**

1. Para 1X2 (HOME_WIN, DRAW, AWAY_WIN): Selecionar APENAS o melhor outcome
2. Para BTTS e O/U: Usar thresholds ajustados
3. Validar com dados históricos antes de rodar em produção

---

## ⚠️ PROBLEMA #2: 63.4% PREDICTIONS NÃO VALIDADAS

### Dados do Problema

- Total predictions: 14,783
- Validadas: 5,407 (36.6%)
- Pendentes: 9,376 (63.4%)

### Causas

1. **Jogos futuros:** Predictions geradas para jogos que ainda não aconteceram
2. **Falta de limpeza:** Predictions de jogos antigos cancelados não removidas
3. **Bug anterior:** Antes da correção, muitas predictions ficaram órfãs

### Soluções

#### Solução 1: Limpar predictions de jogos cancelados/adiados

```python
def cleanup_invalid_predictions():
    """
    Remove predictions de jogos que foram cancelados, adiados ou muito antigos
    """
    from datetime import datetime, timedelta

    # Jogos cancelados/adiados
    cancelled_matches = db.query(Match).filter(
        Match.status.in_(['CANC', 'PST', 'ABD', 'AWD', 'WO'])
    ).all()

    for match in cancelled_matches:
        db.query(Prediction).filter(
            Prediction.match_id == match.id
        ).delete()

    # Predictions de jogos antigos (>30 dias) ainda não finalizados
    cutoff = datetime.now() - timedelta(days=30)
    old_predictions = db.query(Prediction).join(Match).filter(
        Match.match_date < cutoff,
        Match.status.in_(['NS', 'TBD', 'SCHEDULED']),
        Prediction.is_validated == False
    ).all()

    count = db.query(Prediction).filter(
        Prediction.id.in_([p.id for p in old_predictions])
    ).delete(synchronize_session=False)

    db.commit()

    print(f"🧹 {count} predictions antigas removidas")
```

#### Solução 2: Validar predictions pendentes em batch

```python
def validate_pending_predictions_batch():
    """
    Valida todas predictions pendentes de jogos já finalizados
    """
    pending = db.query(Prediction).join(Match).filter(
        Prediction.is_validated == False,
        Match.status == 'FT',
        Match.home_score.isnot(None)
    ).count()

    if pending > 0:
        run_historical_validation(db)
        print(f"✅ {pending} predictions validadas")
```

#### Solução 3: Adicionar job de limpeza ao scheduler

```python
# Em app/core/scheduler.py

def cleanup_old_predictions_job():
    """
    Job para limpar predictions antigas/inválidas
    Executa diariamente às 04:00
    """
    logger.info("🧹 Limpando predictions antigas...")

    db = get_db_session()
    try:
        cleanup_invalid_predictions(db)
        validate_pending_predictions_batch(db)
    finally:
        db.close()

# Adicionar ao scheduler
scheduler.add_job(
    cleanup_old_predictions_job,
    trigger=CronTrigger(hour=4, minute=0),
    id='cleanup_predictions',
    name='🧹 Limpeza de Predictions (diário 04:00)',
    replace_existing=True
)
```

**Impacto estimado:**
- ✅ Aumentar % de validadas de 36.6% para ~80%+
- ✅ Dados mais limpos para ML retraining
- ✅ Menos ruído nos dashboards

---

## ⚠️ PROBLEMA #3: CONFIDENCE SCORES DESCALIBRADOS

### Dados do Problema

- Confidence médio GREENS: 59.3%
- Confidence médio REDS: 45.4%
- Diferença: 13.8%

**Predictions com confidence >= 70%:**
- Total: 1,968
- REDS: 871 (44.3%) ⚠️

**Problema:** Mesmo predictions com alta confidence (70%+) têm 44.3% de erro!

### Causa Raiz

```python
# app/services/ml_prediction_generator.py (linha 434)
confidence_score = probability  # Usando probabilidade direta!
```

A probabilidade do Poisson NÃO é o mesmo que confidence. Confidence deveria refletir:
1. Histórico de accuracy do modelo
2. Qualidade dos dados de entrada
3. Incerteza das features

### Soluções

#### Solução 1: Calibrar confidence com histórico

```python
def calibrate_confidence(self, raw_probability: float, market: str) -> float:
    """
    Calibra confidence baseado no histórico de accuracy do market

    Usa Platt Scaling ou Isotonic Regression
    """
    # Buscar accuracy histórica do market
    historical_accuracy = self._get_historical_accuracy(market)

    # Fórmula simples:
    # confidence = raw_probability * (historical_accuracy / 0.5)
    # Isso ajusta para cima se accuracy > 50%, para baixo se < 50%

    calibration_factor = historical_accuracy / 0.5
    calibrated = raw_probability * calibration_factor

    # Clamp entre 0 e 1
    return max(0.0, min(1.0, calibrated))
```

**Exemplo:**
- DRAW tem 17.3% accuracy (calibration_factor = 0.346)
- Probabilidade Poisson: 30%
- Confidence calibrado: 30% * 0.346 = 10.4%
- Resultado: Não gerar prediction (< threshold)

#### Solução 2: Usar sklearn CalibratedClassifierCV

```python
from sklearn.calibration import CalibratedClassifierCV

# Após treinar modelo
calibrated_model = CalibratedClassifierCV(
    base_model,
    method='isotonic',  # ou 'sigmoid'
    cv=5
)
calibrated_model.fit(X_train, y_train)

# Usar para predictions
probabilities = calibrated_model.predict_proba(features)
# Estas probabilidades serão calibradas!
```

#### Solução 3: Adicionar penalidade por incerteza

```python
def calculate_confidence_with_uncertainty(self, probability: float, match: Match) -> float:
    """
    Ajusta confidence baseado em fatores de incerteza
    """
    uncertainty_factors = {
        'missing_stats': 0.9 if (not match.home_stats or not match.away_stats) else 1.0,
        'no_odds': 0.85 if not match.odds else 1.0,
        'low_sample_h2h': 0.95 if match.h2h_count < 3 else 1.0,
        'new_team': 0.9 if match.team_is_new else 1.0,
    }

    # Multiplicar todos os fatores
    total_uncertainty = 1.0
    for factor in uncertainty_factors.values():
        total_uncertainty *= factor

    return probability * total_uncertainty
```

### Recomendação

**Implementar todas as 3 soluções:**
1. Calibrar com histórico (rápido, impacto imediato)
2. sklearn CalibratedClassifierCV no próximo retraining
3. Penalidade por incerteza (melhora qualidade)

**Impacto estimado:**
- ✅ Confidence scores refletem accuracy real
- ✅ Menos predictions com alta confidence que dão RED
- ✅ Melhor para AI Agent usar como input

---

## 📋 PLANO DE IMPLEMENTAÇÃO

### Fase 1: Correções Críticas (2-3 dias)

**Prioridade P0:**

1. **Selecionar melhor outcome 1X2**
   - [ ] Implementar `_select_best_1x2_outcome()`
   - [ ] Ajustar `generate_daily_predictions()` para usar
   - [ ] Testar com dados históricos
   - [ ] Validar melhoria de accuracy

2. **Ajustar thresholds por market**
   - [ ] Criar `MARKET_THRESHOLDS` dict
   - [ ] DRAW: min_prob=0.35, min_edge=15
   - [ ] Aplicar nos filtros
   - [ ] Testar geração de predictions

3. **Limpar predictions pendentes**
   - [ ] Implementar `cleanup_invalid_predictions()`
   - [ ] Rodar manualmente
   - [ ] Validar que removed correto
   - [ ] Adicionar ao scheduler

**Tempo estimado:** 2-3 dias
**Impacto esperado:** Accuracy 34.3% → 45-50%

### Fase 2: Calibração e Otimização (3-5 dias)

**Prioridade P1:**

1. **Calibrar confidence scores**
   - [ ] Implementar `calibrate_confidence()`
   - [ ] Calcular accuracy histórica por market
   - [ ] Aplicar calibração
   - [ ] Validar que confidence = accuracy real

2. **Retreinar ML com dados balanceados**
   - [ ] Preparar dataset balanceado (SMOTE ou undersampling)
   - [ ] Retreinar 1x2_classifier
   - [ ] Retreinar btts_classifier
   - [ ] Validar melhorias

3. **Adicionar validação contínua**
   - [ ] Job de validação a cada 1h
   - [ ] Job de limpeza diário
   - [ ] Logs detalhados
   - [ ] Métricas de accuracy por market

**Tempo estimado:** 3-5 dias
**Impacto esperado:** Accuracy 45-50% → 55-60%

### Fase 3: Refinamento (5-7 dias)

**Prioridade P2:**

1. **Features avançadas**
   - [ ] Adicionar form (últimos 5 jogos)
   - [ ] Adicionar H2H history
   - [ ] Adicionar injuries impact
   - [ ] Adicionar weather conditions

2. **Multi-model ensemble**
   - [ ] Testar XGBoost, LightGBM
   - [ ] Implementar voting classifier
   - [ ] Comparar accuracy
   - [ ] Escolher melhor combinação

3. **AI Agent otimização**
   - [ ] Usar confidence calibrado
   - [ ] Refinar prompts
   - [ ] Validar adjustments
   - [ ] Medir impacto real

**Tempo estimado:** 5-7 dias
**Impacto esperado:** Accuracy 55-60% → 60-65%

---

## 📊 MÉTRICAS DE SUCESSO

### Targets por Fase

| Fase | Accuracy Target | DRAW Accuracy | % Validadas | Confidence Calibration |
|------|----------------|---------------|-------------|------------------------|
| **Atual** | 34.3% | 17.3% | 36.6% | ❌ Descalibrado |
| **Fase 1** | 45-50% | 30-35% | 80%+ | ⚠️ Parcial |
| **Fase 2** | 55-60% | 35-40% | 90%+ | ✅ Calibrado |
| **Fase 3** | 60-65% | 40-45% | 95%+ | ✅ Otimizado |

### KPIs a Monitorar

**Diariamente:**
- Accuracy geral
- Accuracy por market
- % predictions validadas
- Confidence médio GREEN vs RED

**Semanalmente:**
- Melhoria de accuracy ML após retraining
- ROI simulado de predictions
- Distribuição de outcomes gerados

**Mensalmente:**
- Accuracy trend (deve subir)
- Predictions/dia geradas
- GREEN/RED ratio por league

---

## 🚀 PRÓXIMOS PASSOS IMEDIATOS

### Hoje (20/10/2025)

1. ✅ Análise completa - CONCLUÍDO
2. ✅ Identificar problemas - CONCLUÍDO
3. ✅ Criar plano de correção - CONCLUÍDO
4. ⏳ **PRÓXIMO:** Implementar Fase 1 - Correções Críticas

### Amanhã (21/10/2025)

1. Implementar `_select_best_1x2_outcome()`
2. Ajustar thresholds DRAW
3. Testar nova geração de predictions
4. Validar melhoria de accuracy

### Próxima Semana

1. Completar Fase 1
2. Iniciar Fase 2 (calibração)
3. Monitorar métricas diárias
4. Ajustar conforme necessário

---

## ⚠️ RISCOS E MITIGAÇÕES

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Accuracy não melhorar após Fase 1 | BAIXA | ALTO | Rollback + investigar features |
| Over-fitting ao corrigir DRAW | MÉDIA | MÉDIO | Validar com dados out-of-sample |
| Muito poucas predictions geradas | MÉDIA | MÉDIO | Ajustar thresholds gradualmente |
| ML retraining piorar modelos | BAIXA | ALTO | Backup de modelos, A/B test |

---

## 📝 CONCLUSÃO

**Estado Atual:**
- ❌ Accuracy 34.3% (abaixo da meta de 60%)
- ❌ ML prevendo DRAW demais (36.6% vs 22.5% real)
- ❌ DRAW com apenas 17.3% accuracy
- ❌ 63.4% predictions não validadas
- ❌ Confidence scores descalibrados

**Após Implementação Completa:**
- ✅ Accuracy 60-65% (meta atingida)
- ✅ Distribuição de outcomes balanceada
- ✅ DRAW com 40-45% accuracy
- ✅ 95%+ predictions validadas
- ✅ Confidence scores calibrados = accuracy real

**Tempo Total Estimado:** 10-15 dias
**Prioridade:** 🔴 CRÍTICA

**Antes de pensar em CI/CD e cloud deployment, precisamos ter uma pipeline de ML funcionando corretamente com 60%+ accuracy!**

---

**Criado por:** Equipe de desenvolvimento
**Data:** 2025-10-20
**Versão:** 1.0
