# 🎯 ROADMAP - SISTEMA FOCADO NO USUÁRIO E SUA BANCA

**Data**: 07/10/2025
**Visão**: Plataforma de apostas esportivas focada na gestão de banca do usuário

---

## 📋 ÍNDICE

1. [Filosofia do Sistema](#filosofia)
2. [Fluxos Automatizados](#fluxos)
3. [Funcionalidades Focadas no Usuário](#funcionalidades)
4. [Arquitetura para Deploy](#arquitetura)
5. [Próximos Passos](#proximos-passos)

---

## 🎭 FILOSOFIA DO SISTEMA {#filosofia}

### ❌ O que REMOVER (Páginas Técnicas):
- `GlobalDashboard` - Métricas da API
- `LiveMonitoring` - Monitoramento técnico
- `PerformanceAnalytics` - Análise da ML
- Qualquer métrica de infraestrutura

### ✅ O que MANTER/CRIAR (Foco no Usuário):
- **Dashboard do Usuário**: Visão geral da BANCA DELE
- **Meus Bilhetes**: Tickets criados pelo usuário
- **Histórico de Apostas**: GREEN/RED do usuário
- **Gestão de Banca**: Controle financeiro pessoal
- **Predictions ML**: Sugestões de apostas
- **Live Matches**: Jogos ao vivo para apostar

### 🎯 Princípio Central:
> **"Tudo gira em torno da BANCA do usuário, não da ML"**

---

## 🔄 FLUXOS AUTOMATIZADOS {#fluxos}

### ✅ 1. IMPORTAÇÃO DIÁRIA (06:00 AM)
**Arquivo**: `daily_matches_importer.py`

**O que faz**:
- Busca jogos de hoje das 17 ligas principais
- Brasil (Série A, Série B)
- Europa (Premier, La Liga, Serie A, Ligue 1, Bundesliga)
- Libertadores, Sul-Americana, Champions, Europa League
- MLS, Argentina, Portugal, Holanda

**Resultado**: Sistema sempre atualizado com jogos do dia

---

### ✅ 2. ATUALIZAÇÃO DE RESULTADOS (A cada 1 hora)
**Arquivo**: `results_updater.py`

**O que faz**:
- Busca jogos finalizados
- Atualiza placares da API
- Calcula GREEN/RED das predictions
- Atualiza profit/loss

**Resultado**: GREEN/RED sempre atualizado

---

### ✅ 3. LIMPEZA DE JOGOS ANTIGOS (00:00 diariamente)
**Arquivo**: `scheduler.py`

**O que faz**:
- Remove jogos de +7 dias das abas
- Mantém no banco para histórico
- Libera espaço na interface

**Resultado**: Interface limpa e rápida

---

### ✅ 4. STATS AO VIVO (A cada 1 minuto)
**Arquivo**: `live_stats_service.py`

**O que faz**:
- Atualiza placares de jogos ao vivo
- Busca estatísticas em tempo real
- Atualiza eventos (gols, cartões)

**Resultado**: Dados ao vivo para decisões

---

### 🆕 5. GERAÇÃO DE PREDICTIONS ML (A cada 6 horas)
**Ainda não criado - PRIORIDADE**

**O que deve fazer**:
```python
def generate_predictions_job():
    """
    Gera predictions para jogos das próximas 48h

    - Busca jogos sem prediction
    - Executa modelos ML
    - Calcula probabilidades
    - Salva recommendations
    - Marca confiança (alta/média/baixa)
    """
```

**Resultado**: Usuário sempre tem sugestões atualizadas

---

### 🆕 6. CÁLCULO DE BANCA (Quando usuário faz aposta)
**Ainda não criado - PRIORIDADE**

**O que deve fazer**:
```python
def update_user_bankroll(user_id, bet_amount, outcome):
    """
    Atualiza banca do usuário

    - Deduz valor apostado
    - Adiciona ganhos (se GREEN)
    - Calcula ROI pessoal
    - Atualiza estatísticas
    - Registra histórico
    """
```

**Resultado**: Controle financeiro preciso

---

## 🎯 FUNCIONALIDADES FOCADAS NO USUÁRIO {#funcionalidades}

### 1. 💰 GESTÃO DE BANCA (PRIORIDADE MÁXIMA)

#### 1.1. **Perfil do Usuário**
```typescript
interface UserBankroll {
  user_id: string;
  initial_bankroll: number;    // Banca inicial
  current_bankroll: number;    // Banca atual
  total_staked: number;        // Total apostado
  total_profit: number;        // Lucro total
  roi: number;                 // Retorno sobre investimento
  win_rate: number;            // Taxa de acerto

  // Estatísticas
  total_bets: number;
  greens: number;
  reds: number;
  pending: number;

  // Controle de risco
  max_bet_percentage: number;  // % máxima por aposta
  kelly_criterion: boolean;    // Usar critério de Kelly?
  risk_level: 'conservative' | 'moderate' | 'aggressive';
}
```

#### 1.2. **Dashboard do Usuário** (página principal)
```
┌─────────────────────────────────────────────┐
│ 💰 MINHA BANCA                              │
│                                             │
│ Banca Inicial: R$ 1.000,00                 │
│ Banca Atual: R$ 1.247,50 (+24.8%) ✅       │
│                                             │
│ ┌──────┬──────┬──────┬──────┐             │
│ │GREEN │ RED  │PEND  │ ROI  │             │
│ │ 42   │ 28   │ 15   │+24.8%│             │
│ └──────┴──────┴──────┴──────┘             │
│                                             │
│ 📊 Gráfico de Evolução (30 dias)           │
│ [Linha mostrando crescimento da banca]      │
│                                             │
│ 🎯 Sugestões do Dia (5 jogos)              │
│ [Cards com predictions ML]                  │
└─────────────────────────────────────────────┘
```

---

### 2. 🎫 MEUS BILHETES

#### 2.1. **Criar Bilhete Manual**
```typescript
interface UserTicket {
  id: string;
  user_id: string;
  created_at: datetime;

  // Seleções
  selections: BetSelection[];

  // Financeiro
  stake: number;              // Valor apostado
  potential_return: number;   // Retorno potencial
  total_odds: number;         // Odd total

  // Resultado
  status: 'pending' | 'won' | 'lost';
  actual_return: number;      // Ganho real
  profit_loss: number;        // Lucro/prejuízo

  // Metadata
  ticket_type: 'single' | 'multiple' | 'system';
  notes: string;              // Análise do usuário
  source: 'manual' | 'ml_suggestion';
}

interface BetSelection {
  match_id: number;
  market: string;             // '1X2', 'Over/Under', etc
  outcome: string;
  odd: number;
  result: 'won' | 'lost' | 'pending';
}
```

#### 2.2. **Fluxo de Criação**:
1. Usuário navega em **Predictions** ou **Live Matches**
2. Clica em "Adicionar ao Bilhete"
3. Seleciona mercado e outcome
4. Sistema adiciona ao carrinho
5. Usuário revisa e confirma
6. Sistema calcula:
   - Odd total
   - Retorno potencial
   - % da banca que representa
   - Sugestão de stake (Kelly Criterion)
7. Usuário define valor e confirma
8. Bilhete salvo com `user_id`

---

### 3. 📊 HISTÓRICO INTELIGENTE

#### 3.1. **Análise de Performance**
```
┌─────────────────────────────────────────────┐
│ 📈 MINHA PERFORMANCE                        │
│                                             │
│ Últimos 30 dias:                           │
│ • ROI: +18.5% ✅                           │
│ • Win Rate: 62% 🎯                         │
│ • Profit: +R$ 370,00 💰                    │
│                                             │
│ Por Liga:                                   │
│ • Brasileirão Série A: +25% (12 apostas)  │
│ • Premier League: +10% (8 apostas)        │
│ • La Liga: -5% (6 apostas) ⚠️            │
│                                             │
│ Por Tipo de Aposta:                        │
│ • 1X2: 58% win rate                        │
│ • Over/Under: 70% win rate ⭐             │
│ • BTTS: 45% win rate                       │
│                                             │
│ 💡 Insights:                               │
│ - Suas melhores apostas são em Over/Under │
│ - Considere reduzir stakes em La Liga     │
│ - Brasileirão tem seu melhor ROI          │
└─────────────────────────────────────────────┘
```

---

### 4. 🤖 PREDICTIONS ML (Reformuladas)

#### 4.1. **Nova Abordagem**:
```
Antes: "Modelo XGBoost prevê..."
Depois: "Sugerimos apostar em..."

Foco: AJUDAR o usuário, não mostrar técnicas da ML
```

#### 4.2. **Card de Prediction**:
```
┌─────────────────────────────────────┐
│ ⚽ Palmeiras vs Flamengo           │
│ 🏆 Brasileirão Série A             │
│ 🕐 Hoje, 16:00                     │
│                                     │
│ 🎯 SUGESTÃO: Casa Vence            │
│    Confiança: ⭐⭐⭐⭐⭐ (Alta)      │
│    Odd: 2.10                       │
│    Retorno: R$ 210 (para R$ 100)   │
│                                     │
│ 📊 Análise Rápida:                 │
│ • Palmeiras 5 jogos invicto em casa│
│ • Flamengo com 3 desfalques        │
│ • H2H: Palmeiras venceu 4 dos últ 5│
│                                     │
│ 💰 Sugestão de Stake:              │
│    R$ 25,00 (2.5% da banca)        │
│                                     │
│ [Adicionar ao Bilhete] [Ver Mais]  │
└─────────────────────────────────────┘
```

---

### 5. 🎮 LIVE MATCHES (Melhorado)

#### 5.1. **Adicionar Funcionalidades**:
- ✅ Estatísticas em tempo real (já temos)
- 🆕 **Botão "Apostar Agora"** funcional
- 🆕 **Odds atualizadas** a cada minuto
- 🆕 **Alertas de mudança** de odd
- 🆕 **Sugestões dinâmicas** baseadas no jogo

#### 5.2. **Alerts em Tempo Real**:
```python
def check_live_opportunities(match):
    """
    Identifica oportunidades durante o jogo

    Exemplos:
    - Time dominando mas placar 0x0? → Sugerir Over 0.5
    - Favorito perdendo no 1T? → Sugerir virada
    - Muitos escanteios? → Sugerir Total Corners
    """
```

---

## 🏗️ ARQUITETURA PARA DEPLOY {#arquitetura}

### 🐳 CONTAINERIZAÇÃO

#### 1. **Serviços Principais**:
```yaml
# docker-compose.yml

services:
  # 1. API Backend
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://...
      - REDIS_URL=redis://redis:6379
      - API_SPORTS_KEY=${API_SPORTS_KEY}
    depends_on:
      - postgres
      - redis
    restart: always

  # 2. Frontend
  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: always

  # 3. Scheduler (Fluxos Automatizados)
  scheduler:
    build: ./backend
    command: python -m app.scheduler
    environment:
      - DATABASE_URL=postgresql://...
      - API_SPORTS_KEY=${API_SPORTS_KEY}
    depends_on:
      - postgres
    restart: always

  # 4. Database (PostgreSQL em produção)
  postgres:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=football_analytics
      - POSTGRES_USER=admin
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    restart: always

  # 5. Redis (Cache)
  redis:
    image: redis:7-alpine
    restart: always

  # 6. Nginx (Reverse Proxy)
  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend
    restart: always

volumes:
  postgres_data:
```

---

### ☁️ OPÇÕES DE HOSPEDAGEM

#### Opção 1: **Railway** (Recomendado para início)
- ✅ Deploy automático via GitHub
- ✅ PostgreSQL incluído
- ✅ SSL gratuito
- ✅ $5-10/mês
- ✅ Fácil escalar

**Jobs que podem rodar**:
- Backend API (24/7)
- Scheduler (24/7)
- Frontend (24/7)

**O que precisa rodar localmente**:
- Nada! Tudo na nuvem ✅

---

#### Opção 2: **Fly.io**
- ✅ Free tier generoso
- ✅ PostgreSQL gratuito
- ✅ Deploy global
- Limite: 3 VMs gratuitas

---

#### Opção 3: **DigitalOcean Droplet**
- VPS próprio ($6/mês)
- Controle total
- Requer manutenção

---

#### Opção 4: **Render**
- Similar ao Railway
- Free tier para testes
- $7/mês produção

---

### 📦 ESTRUTURA DE DEPLOY

```
Serviços 24/7 na Nuvem:
├── API Backend (FastAPI)
│   └── Responde requests do frontend
│
├── Scheduler (APScheduler)
│   ├── 06:00 - Importa jogos do dia
│   ├── A cada 1h - Atualiza resultados
│   ├── 00:00 - Limpa jogos antigos
│   └── A cada 1min - Stats ao vivo
│
├── Frontend (React)
│   └── Interface do usuário
│
└── Database (PostgreSQL)
    └── Dados persistentes

Usuário:
└── Acessa via navegador
    └── Tudo funciona sem seu PC ligado! ✅
```

---

## 🚀 PRÓXIMOS PASSOS (PRIORIDADES) {#proximos-passos}

### 🔥 FASE 1: BANCA DO USUÁRIO (1-2 semanas)

#### 1.1. **Modelo de Dados**
```sql
-- Tabela de usuários
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    password_hash VARCHAR NOT NULL,
    initial_bankroll DECIMAL(10,2),
    current_bankroll DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tabela de bilhetes do usuário
CREATE TABLE user_tickets (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    stake DECIMAL(10,2) NOT NULL,
    total_odds DECIMAL(10,2) NOT NULL,
    potential_return DECIMAL(10,2),
    actual_return DECIMAL(10,2),
    profit_loss DECIMAL(10,2),
    status VARCHAR DEFAULT 'pending',
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Seleções do bilhete
CREATE TABLE ticket_selections (
    id SERIAL PRIMARY KEY,
    ticket_id INT REFERENCES user_tickets(id),
    match_id INT REFERENCES matches(id),
    market VARCHAR NOT NULL,
    outcome VARCHAR NOT NULL,
    odd DECIMAL(10,2) NOT NULL,
    result VARCHAR DEFAULT 'pending'
);

-- Histórico financeiro
CREATE TABLE bankroll_history (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    amount DECIMAL(10,2),
    type VARCHAR, -- 'bet', 'win', 'loss'
    description TEXT,
    balance_after DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 1.2. **Endpoints Necessários**
```python
# Auth
POST   /api/v1/auth/register
POST   /api/v1/auth/login

# Banca
GET    /api/v1/user/bankroll
POST   /api/v1/user/bankroll/deposit
POST   /api/v1/user/bankroll/withdraw

# Bilhetes
GET    /api/v1/user/tickets
POST   /api/v1/user/tickets              # Criar
GET    /api/v1/user/tickets/{id}
DELETE /api/v1/user/tickets/{id}

# Histórico
GET    /api/v1/user/history
GET    /api/v1/user/statistics
GET    /api/v1/user/performance
```

---

### 🎯 FASE 2: REMOVER PÁGINAS TÉCNICAS (2-3 dias)

**Deletar**:
- `GlobalDashboard.tsx`
- `LiveMonitoring.tsx`
- `PerformanceAnalytics.tsx`

**Criar**:
- `MyBankroll.tsx` - Gestão de banca
- `MyTickets.tsx` - Bilhetes do usuário
- `MyHistory.tsx` - Histórico pessoal
- `UserDashboard.tsx` - Dashboard focado no usuário

---

### ⚡ FASE 3: FLUXO DE PREDICTIONS ML (3-4 dias)

```python
# Job para gerar predictions
def generate_predictions_job():
    """
    A cada 6 horas:
    1. Busca jogos próximas 48h sem prediction
    2. Executa modelos ML
    3. Calcula probabilidades
    4. Gera recommendation
    5. Classifica confiança (alta/média/baixa)
    """
```

---

### 🐳 FASE 4: CONTAINERIZAÇÃO (1 semana)

1. Criar Dockerfiles
2. Configurar docker-compose
3. Testar localmente
4. Deploy no Railway
5. Configurar domínio
6. SSL/HTTPS
7. Monitoramento

---

### 📊 FASE 5: ANALYTICS AVANÇADO (2 semanas)

- Gráficos de evolução de banca
- Análise por liga/time
- Sugestões personalizadas
- Machine Learning adaptativo por usuário
- Alertas inteligentes

---

## 🎨 WIREFRAMES (VISÃO)

### Dashboard Principal:
```
┌───────────────────────────────────────────────┐
│ [Logo] Football Analytics        [User] ▼    │
├───────────────────────────────────────────────┤
│                                               │
│ 💰 MINHA BANCA                               │
│ ┌──────────────────────────────────────┐    │
│ │ R$ 1.247,50  (+24.8%) ✅            │    │
│ │ [Depositar] [Sacar] [Histórico]     │    │
│ └──────────────────────────────────────┘    │
│                                               │
│ 📊 ÚLTIMOS 30 DIAS                           │
│ [Gráfico de linha mostrando evolução]        │
│                                               │
│ 🎯 SUGESTÕES DE HOJE (5)                     │
│ ┌────────┐ ┌────────┐ ┌────────┐           │
│ │Palmeiras│ │Flamengo│ │Santos │ ...       │
│ │vs Galo │ │vs Corinth│ │vs ...│           │
│ │⭐⭐⭐⭐⭐│ │⭐⭐⭐⭐  │ │⭐⭐⭐  │           │
│ └────────┘ └────────┘ └────────┘           │
│                                               │
│ 📋 MEUS BILHETES ATIVOS (3)                  │
│ [Lista de bilhetes pendentes]                 │
│                                               │
└───────────────────────────────────────────────┘
```

---

## ✅ CHECKLIST FINAL

### Sistema Atual (já temos):
- [x] API Backend funcionando
- [x] Scheduler com 4 jobs
- [x] Importação automática de jogos
- [x] Atualização de resultados
- [x] Stats ao vivo
- [x] Frontend básico
- [x] Predictions ML

### Próximas Implementações:
- [ ] Sistema de usuários (auth)
- [ ] Gestão de banca
- [ ] Criação de bilhetes
- [ ] Tracking GREEN/RED por usuário
- [ ] Dashboard do usuário
- [ ] Remover páginas técnicas
- [ ] Containerização
- [ ] Deploy em produção

---

## 📞 RESUMO EXECUTIVO

### O que temos:
✅ Sistema funcional com dados em tempo real
✅ ML gerando predictions
✅ Scheduler automatizado
✅ Live stats funcionando

### O que falta:
🎯 **Foco no USUÁRIO e sua BANCA**
💰 Sistema de gestão financeira
🎫 Bilhetes pessoais
📊 Analytics personalizado

### Próximo passo imediato:
**Implementar sistema de usuários e banca** (Fase 1)

---

**Última atualização**: 07/10/2025
**Status**: Pronto para Fase 1 - Banca do Usuário
