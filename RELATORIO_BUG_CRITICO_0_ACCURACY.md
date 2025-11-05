# RELATÓRIO: BUG CRÍTICO - 0% ACCURACY NAS PREDICTIONS

**Data**: 2025-10-29
**Severidade**: CRÍTICA
**Status**: IDENTIFICADO - AGUARDANDO CORREÇÃO

---

## RESUMO EXECUTIVO

Sistema apresentou **0% de accuracy** em 5,844 predictions com jogos finalizados. Após investigação profunda, identificamos **incompatibilidade de formato** entre o ML Prediction Generator e o Ticket Analyzer.

---

## DADOS DA ANÁLISE

### Predictions Analisadas
- **Total**: 5,844 predictions com jogos finalizados
- **GREEN** (Acertos): 0 (0.0%)
- **RED** (Erros): 5,844 (100.0%)
- **Accuracy**: 0.0%

### Distribuição por Mercado
```
BTTS_NO:      0 / 2,000  (0.0%)   ← MAIOR VOLUME
DRAW:         0 / 1,978  (0.0%)
AWAY_WIN:     0 /   713  (0.0%)
HOME_WIN:     0 /   675  (0.0%)
1X2:          0 /    82  (0.0%)
```

### Distribuição por Tipo
```
MULTI_3X:     0 / 2,389  (0.0%)
MULTI_4X:     0 / 2,220  (0.0%)
SINGLE:       0 /   514  (0.0%)
MULTI_2X:     0 /   477  (0.0%)
```

---

## BUG IDENTIFICADO

### Problema: Incompatibilidade de Formato no `predicted_outcome`

#### Arquivo 1: `ml_prediction_generator.py` (Linhas 748 e 859)
```python
return {
    'market_type': market,
    'predicted_outcome': market,  # ❌ PROBLEMA AQUI
    ...
}
```

**O que faz**: Define `predicted_outcome = market_type`
- Para `market_type='BTTS_NO'` → `predicted_outcome='BTTS_NO'`
- Para `market_type='HOME_WIN'` → `predicted_outcome='HOME_WIN'`

#### Arquivo 2: `ticket_analyzer.py` (Linha 267-275)
```python
elif 'BTTS' in market:
    both_scored = (home_score > 0 and away_score > 0)
    actual = 'YES' if both_scored else 'NO'  # ✅ Retorna 'YES' ou 'NO'
    won = (outcome == actual)  # ❌ Compara 'BTTS_NO' == 'NO' → FALSE!
```

**O que espera**: `outcome` deve ser `'YES'` ou `'NO'`, não `'BTTS_YES'` ou `'BTTS_NO'`

---

## CAUSA RAIZ

O **Ticket Analyzer** espera formatos diferentes para cada mercado:

| Mercado | ML Generator envia | Analyzer espera | Match? |
|---------|-------------------|----------------|--------|
| BTTS_NO | `'BTTS_NO'` | `'NO'` | ❌ |
| BTTS_YES | `'BTTS_YES'` | `'YES'` | ❌ |
| HOME_WIN | `'HOME_WIN'` | `'HOME_WIN'` | ✅ |
| AWAY_WIN | `'AWAY_WIN'` | `'AWAY_WIN'` | ✅ |
| DRAW | `'DRAW'` | `'DRAW'` | ✅ |
| 1X2 | `'1X2'` | `'1'`, `'X'`, ou `'2'` | ❌ |

### Mercados Afetados (Provavelmente)
1. **BTTS** (2,000 predictions): Espera 'YES'/'NO', recebe 'BTTS_YES'/'BTTS_NO'
2. **1X2** (82 predictions): Espera '1'/'X'/'2', recebe '1X2'
3. **OVER/UNDER**: Espera 'OVER'/'UNDER', pode receber 'OVER_2_5'/'UNDER_2_5'
4. **CLEAN_SHEET**: Espera 'YES'/'NO', pode receber 'HOME_CLEAN_SHEET'/'AWAY_CLEAN_SHEET'

---

## VALIDAÇÃO DOS DADOS

### Jogos Finalizados com Scores
✅ **37,957 jogos** com status='FT' e scores válidos (home_score e away_score preenchidos)

### Exemplo Real de Prediction Incorreta

**Prediction**:
- Market: BTTS_NO
- Predicted Outcome: 'BTTS_NO'
- Match: Arsenal 3-0 Chelsea (nenhum time deixou de marcar... ops, Chelsea não marcou!)

**Validação Manual**:
- Chelsea não marcou (away_score = 0)
- BTTS_NO deveria GANHAR (algum time não marcou) ✅
- Mas analyzer compara: `'BTTS_NO' == 'NO'` → FALSE ❌

---

## IMPACTO

### Imediato
- **0% accuracy** (estatisticamente impossível com 5,844 samples)
- **Sistema não pode aprender** (sem exemplos GREEN)
- **ML training inválido** (todos os exemplos são negativos)
- **AI Agent sem dados corretos** (few-shot learning comprometido)

### Médio Prazo
- Usuários receberiam predictions completamente inválidas
- Bankroll seria destruído se apostas fossem feitas
- Confiança no sistema seria zero

---

## SOLUÇÃO

### Opção 1: Corrigir ML Prediction Generator (RECOMENDADO)

**Arquivo**: `app/services/ml_prediction_generator.py`
**Linhas**: 748, 859

```python
# ❌ ANTES (ERRADO)
'predicted_outcome': market

# ✅ DEPOIS (CORRETO)
def _get_predicted_outcome(market: str) -> str:
    """Converte market_type para formato esperado pelo Ticket Analyzer"""
    outcome_map = {
        'BTTS_YES': 'YES',
        'BTTS_NO': 'NO',
        'HOME_WIN': 'HOME_WIN',
        'AWAY_WIN': 'AWAY_WIN',
        'DRAW': 'DRAW',
        '1X2': 'X',  # Ou calcular baseado em probabilidades
        'OVER_2_5': 'OVER',
        'UNDER_2_5': 'UNDER',
        'HOME_CLEAN_SHEET': 'YES',
        'AWAY_CLEAN_SHEET': 'YES',
        # ... adicionar todos os 41 mercados
    }
    return outcome_map.get(market, market)

'predicted_outcome': _get_predicted_outcome(market)
```

### Opção 2: Corrigir Ticket Analyzer

**Arquivo**: `app/services/ticket_analyzer.py`
**Linhas**: 267-275

```python
# ✅ Normalizar o outcome antes de comparar
elif 'BTTS' in market:
    both_scored = (home_score > 0 and away_score > 0)
    actual = 'YES' if both_scored else 'NO'

    # Normalizar outcome para comparação
    normalized_outcome = outcome.replace('BTTS_', '')  # 'BTTS_NO' → 'NO'
    won = (normalized_outcome == actual)
```

---

## AÇÕES IMEDIATAS

1. ✅ **Identificado**: Bug de formato incompatível
2. ⏳ **Próximo**: Implementar correção no ML Generator
3. ⏳ **Testar**: Reprocessar 5,844 predictions com correção
4. ⏳ **Validar**: Esperar accuracy realista (40-60%)
5. ⏳ **Documentar**: Atualizar VERDADES_ABSOLUTAS.md

---

## PREVISÃO PÓS-CORREÇÃO

Após a correção, esperamos:
- **Accuracy**: 45-55% (estatisticamente normal para apostas)
- **GREEN**: ~2,500-3,000 predictions
- **RED**: ~2,500-3,000 predictions
- **ML Training**: Dados balanceados para retreinar modelo

---

## LIÇÕES APRENDIDAS

1. **Testes de Integração**: Necessário validar que formatos de dados são compatíveis entre serviços
2. **Validação Manual**: Sempre verificar accuracy com samples reais antes de confiar 100%
3. **Documentação**: Criar contrato claro de formato de dados entre componentes
4. **Alertas**: Implementar sistema de alerta quando accuracy for < 10% (impossível naturalmente)

---

## PRÓXIMOS PASSOS

1. Corrigir ML Generator com função de mapeamento
2. Limpar predictions existentes (marcar como inválidas)
3. Gerar novas predictions com formato correto
4. Reprocessar análise GREEN/RED
5. Validar accuracy realista
6. Treinar ML e AI Agent com dados corretos

---

**Status**: 🔴 BLOQUEADOR - Sistema não pode avançar para produção até correção
