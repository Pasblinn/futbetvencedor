# 🗺️ MoDoDeus Football Analytics - ROADMAP

**Última atualização:** 2025-10-16
**Versão atual:** 3.0 (Modo Assistido com múltiplas categorias)

---

## 🔴 PRIORIDADE CRÍTICA (Implementar IMEDIATAMENTE)

### 1. ✅ **Fix AllMarketsModal - toFixed Error** ⚠️ PARCIALMENTE RESOLVIDO
**Problema:** `Cannot read properties of undefined (reading 'toFixed')`
**Causa:** Alguns mercados não têm `fair_odds` definidos
**Localização:** `AllMarketsModal.tsx` linha 77
**Impacto:** ⭐⭐⭐⭐⭐ (Quebra a experiência do usuário)
**Solução:**
```typescript
// Adicionar validação robusta antes de toFixed()
const displayOdds = odds?.fair_odds !== undefined
  ? odds.fair_odds.toFixed(2)
  : 'N/A';
```
**Status:** Fix parcial aplicado (filtro), mas ainda ocorre
**Tempo estimado:** 1-2 horas

---

### 2. **Ordenação de Jogos em Predictions** 📅
**Problema:** Jogos não estão ordenados cronologicamente
**Requisito:** Mostrar jogos de HOJE primeiro, depois próximos jogos
**Localização:** `Predictions.tsx` - lógica de fetch/sort
**Impacto:** ⭐⭐⭐⭐ (Usabilidade ruim)
**Solução:**
```typescript
// Backend: Ordenar por match_date ASC
predictions.sort((a, b) =>
  new Date(a.match_date) - new Date(b.match_date)
);
```
**Tempo estimado:** 1 hora

---

### 3. **ML Gerar Predictions para TODOS os 45+ Mercados** 🤖
**Problema:** ML automático gera predictions principalmente para 1X2
**Objetivo:** Gerar predictions para TODOS os mercados calculados via Poisson
**Localização:** `ml_prediction_generator.py` ou `automated_pipeline.py`
**Impacto:** ⭐⭐⭐⭐⭐ (Aumenta volume de predictions de 100/dia para 4500+/dia)
**Lógica:**
```python
# Para cada match:
for match in upcoming_matches:
    poisson_analysis = poisson_service.analyze_match(...)

    # Para cada mercado com value bet:
    for market_key, prob in poisson_analysis.probabilities.items():
        fair_odds = poisson_analysis.fair_odds.get(market_key)
        market_odds = get_market_odds(match, market_key)
        edge = calculate_edge(market_odds, fair_odds)

        if edge > 10.0 and prob > 0.15:  # Thresholds
            # Criar prediction para este mercado
            create_prediction(match, market_key, prob, edge)
```
**Benefícios:**
- 📈 45x mais predictions por dia
- 🎯 Cobrir todos os tipos de apostas
- 💰 Mais oportunidades de value bets
**Tempo estimado:** 4-6 horas

---

### 4. **Adicionar `marketId` ao BettingCart** 🛒
**Problema:** BettingCart ainda usa sistema antigo (`selection: home/draw/away`)
**Objetivo:** Suportar qualquer mercado (OVER_2_5, BTTS_YES, etc)
**Localização:** `Predictions.tsx` - função `addToTicket()`
**Impacto:** ⭐⭐⭐⭐ (Necessário para adicionar mercados avançados ao bilhete)
**Solução:**
```typescript
interface TicketItem {
  match: Match;
  selection: string;  // Manter para compatibilidade
  marketId: string;   // 🔥 NOVO: "OVER_2_5", "BTTS_YES", etc
  marketName: string; // 🔥 NOVO: "Mais de 2.5 Gols"
  odds: number;       // 🔥 NOVO: Odd específica do mercado
  stake: number;
  kellyPercentage: number;
  market: string;     // ID único
}

// Ao adicionar ao bilhete:
const addToTicket = (prediction, marketId) => {
  setSelectedBets([...selectedBets, {
    match: prediction.match,
    selection: 'custom',
    marketId: marketId,
    marketName: translateMarket(marketId),
    odds: prediction.market_odds,
    stake: 10,
    kellyPercentage: prediction.kelly_percentage,
    market: `${prediction.match.id}-${marketId}`
  }]);
};
```
**Tempo estimado:** 2-3 horas

---

## 🟡 PRIORIDADE ALTA (Próximas 2 semanas)

### 5. **Review e Cleanup da Página Predictions** 🧹
**Objetivo:** Melhorar performance e remover código morto
**Tarefas:**
- [ ] Remover variáveis não usadas (currentStep, setInvestmentAmount, etc)
- [ ] Adicionar filtros (por liga, por confidence, por value)
- [ ] Implementar lazy loading / virtualization para longas listas
- [ ] Melhorar responsividade mobile
- [ ] Adicionar indicador de loading
- [ ] Corrigir warnings de lint

**Impacto:** ⭐⭐⭐ (Melhora experiência e performance)
**Tempo estimado:** 6-8 horas

---

### 6. **Persistência de Bilhetes no Banco** 💾
**Objetivo:** Salvar bilhetes criados no banco de dados
**Tabela:** `user_tickets` (já existe!)
**Features:**
- [ ] Botão "Fazer Aposta" salva bilhete no banco
- [ ] Página "Meus Bilhetes" lista histórico
- [ ] Status: pendente, green, red
- [ ] Cálculo automático de ROI

**Localização:** `BettingCart.tsx` + novo endpoint backend
**Impacto:** ⭐⭐⭐⭐ (Tracking essencial para ROI)
**Tempo estimado:** 8-10 horas

---

### 7. **Implementar Modo "Escanteios" e "Cartões"** 🚩
**Objetivo:** Expandir mercados além de gols
**Requisitos:**
- [ ] Adicionar odds de escanteios na API-Sports
- [ ] Criar `PoissonService` para escanteios
- [ ] Adicionar categorias: "Total de Escanteios", "Cartões Amarelos", "Cartões Vermelhos"
- [ ] Atualizar `MARKET_TRANSLATIONS` com novos mercados

**Mercados novos:**
```typescript
'CORNERS_OVER_8_5': 'Mais de 8.5 Escanteios',
'CORNERS_UNDER_8_5': 'Menos de 8.5 Escanteios',
'CARDS_OVER_3_5': 'Mais de 3.5 Cartões',
'CARDS_UNDER_3_5': 'Menos de 3.5 Cartões',
```

**Impacto:** ⭐⭐⭐⭐ (Expande tipos de apostas)
**Tempo estimado:** 12-16 horas

---

### 8. **Dashboard de Performance do Usuário** 📊
**Objetivo:** Mostrar estatísticas de desempenho
**Métricas:**
- Total de apostas feitas
- Win rate (% de greens)
- ROI total
- ROI por mercado
- ROI por liga
- Gráfico de profit ao longo do tempo
- Melhor streak de greens
- Comparação vs ML automático

**Localização:** Nova página `UserPerformance.tsx`
**Impacto:** ⭐⭐⭐⭐ (Gamificação e transparência)
**Tempo estimado:** 10-12 horas

---

## 🟢 PRIORIDADE MÉDIA (Próximo mês)

### 9. **Bankroll Management Automático** 💰
**Objetivo:** Integração real com sistema de bankroll
**Features:**
- [ ] Input de bankroll inicial
- [ ] Tracking automático de bankroll atual
- [ ] Kelly Criterion automático baseado em bankroll real
- [ ] Alertas quando bankroll < 20%
- [ ] Sugestões de stake baseadas em % da banca

**Localização:** `user_bankroll.py` (já existe!)
**Impacto:** ⭐⭐⭐⭐ (Gestão profissional de banca)
**Tempo estimado:** 8-10 horas

---

### 10. **Live Predictions (In-Play)** ⚡
**Objetivo:** Predictions durante o jogo
**Requisitos:**
- [ ] Integração com API de eventos ao vivo
- [ ] Atualização em tempo real (WebSocket)
- [ ] Recalcular probabilidades baseado no placar atual
- [ ] Alertas de value bets durante o jogo

**Impacto:** ⭐⭐⭐⭐⭐ (Game changer - apostas ao vivo)
**Tempo estimado:** 20-24 horas (complexo)

---

### 11. **Sistema de Notificações** 🔔
**Objetivo:** Alertar usuário sobre eventos importantes
**Tipos de notificação:**
- ✅ Nova prediction de alta confiança disponível
- 🟢 Seu bilhete deu GREEN!
- 🔴 Seu bilhete deu RED
- 📈 Nova oportunidade de value bet
- ⚠️ Jogo começando em 15 minutos
- 💎 Novo bilhete recomendado pelo ML

**Localização:**
- Backend: novo service `notification_service.py`
- Frontend: já tem `notificationService.ts`

**Impacto:** ⭐⭐⭐ (Engajamento)
**Tempo estimado:** 6-8 horas

---

### 12. **Modo "Combo Builder" 🎲**
**Objetivo:** AI sugere combinações inteligentes de jogos
**Lógica:**
- [ ] Analisar correlação entre jogos
- [ ] Evitar jogos da mesma liga (risco correlacionado)
- [ ] Sugerir combos com probabilidade combinada > 15%
- [ ] Limitar odds totais (evitar combos insanos)

**Exemplo:**
```
🎯 COMBO SUGERIDO - Odd Total: 4.50
✅ Flamengo vence (1.80) - 65% prob
✅ Over 2.5 PSG vs Lyon (2.00) - 55% prob
✅ BTTS Yes - Real vs Atlético (1.65) - 70% prob
📊 Probabilidade combinada: 23.4%
💰 Stake sugerido: 1.5% da banca
```

**Impacto:** ⭐⭐⭐⭐ (Feature premium)
**Tempo estimado:** 12-16 horas

---

## 🟣 PRIORIDADE BAIXA (Features Futuras)

### 13. **Backtesting System** 📈
**Objetivo:** Testar estratégias em dados históricos
**Features:**
- Rodar predictions em jogos passados
- Calcular ROI hipotético
- Comparar diferentes estratégias
- Otimizar parâmetros (min confidence, min edge, etc)

**Impacto:** ⭐⭐⭐ (Validação científica)
**Tempo estimado:** 16-20 horas

---

### 14. **Integração com Casas de Apostas** 🏦
**Objetivo:** Comparar odds de múltiplas casas
**Casas sugeridas:**
- Bet365
- Betano
- Betfair
- Pinnacle

**Impacto:** ⭐⭐⭐⭐⭐ (Maximiza edge)
**Tempo estimado:** 24+ horas (APIs privadas)

---

### 15. **Mobile App (React Native)** 📱
**Objetivo:** App nativo iOS/Android
**Impacto:** ⭐⭐⭐⭐⭐
**Tempo estimado:** 80-100 horas

---

### 16. **Social Features** 👥
**Objetivo:** Comunidade de apostadores
**Features:**
- Ranking de usuários por ROI
- Compartilhar bilhetes
- Seguir experts
- Comentários em predictions

**Impacto:** ⭐⭐⭐ (Engajamento de longo prazo)
**Tempo estimado:** 40-50 horas

---

## 📋 ORDEM DE IMPLEMENTAÇÃO RECOMENDADA

### Sprint 1 (Esta semana - 16-20 horas)
1. ✅ Fix AllMarketsModal toFixed error (2h)
2. ✅ Ordenação de jogos em Predictions (1h)
3. ✅ ML gerar predictions para todos os mercados (6h)
4. ✅ Adicionar marketId ao BettingCart (3h)
5. ✅ Review básico da página Predictions (8h)

### Sprint 2 (Próxima semana - 20-24 horas)
6. ✅ Persistência de bilhetes no banco (10h)
7. ✅ Dashboard de performance do usuário (12h)

### Sprint 3 (Semana 3 - 20-24 horas)
8. ✅ Implementar escanteios e cartões (16h)
9. ✅ Sistema de notificações (8h)

### Sprint 4 (Semana 4 - 20-24 horas)
10. ✅ Bankroll management automático (10h)
11. ✅ Modo Combo Builder (14h)

### Sprint 5+ (Longo prazo)
12. Live Predictions
13. Backtesting
14. Integração com casas de apostas
15. Mobile app

---

## 🎯 MÉTRICAS DE SUCESSO

**Objetivos para próximo mês:**
- 📊 4500+ predictions/dia (vs 100 atual)
- 🎯 Win rate > 60%
- 💰 ROI médio > 15%
- 👥 100% de coverage em mercados principais
- 🚀 Tempo de resposta < 500ms em 95% das requests

---

## 💡 OBSERVAÇÕES IMPORTANTES

1. **Priorizar sempre:**
   - Bugs que quebram funcionalidade
   - Features que aumentam win rate
   - Features que aumentam volume de predictions

2. **Não priorizar ainda:**
   - Features cosméticas
   - Otimizações prematuras
   - Features que não impactam ROI

3. **Testar sempre:**
   - Cada feature com dados reais
   - Performance sob carga
   - Edge cases e erros

---

**Preparado por:** Equipe de desenvolvimento
**Revisão:** Necessária após cada sprint
**Próxima atualização:** Após Sprint 1
