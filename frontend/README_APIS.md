pr# 🔥 Football Analytics - APIs Reais

Sistema de análise de futebol com **dados reais ao vivo** do Brasileirão, Copa do Brasil, Libertadores e mais.

## 🚀 Quick Start

### 1. Configure as APIs

Copie o arquivo de exemplo e configure suas chaves:

```bash
cp .env.example .env
```

Edite o arquivo `.env` com suas chaves de API:

```env
# API-Football (RapidAPI) - RECOMENDADA
REACT_APP_RAPIDAPI_KEY=your-rapidapi-key-here

# Football-Data.org - Gratuita limitada
REACT_APP_FOOTBALL_DATA_KEY=your-football-data-key-here

# API-Sports - Alternativa
REACT_APP_API_SPORTS_KEY=your-api-sports-key-here
```

### 2. Como Obter as Chaves de API

#### 🥇 **API-Football (RapidAPI) - Melhor Opção**
- **URL**: https://rapidapi.com/api-sports/api/api-football
- **Plano Gratuito**: 500 requests/dia
- **Cobertura**: Brasileirão, Copa do Brasil, Libertadores, Estaduais
- **Dados**: Ao vivo, estatísticas completas, odds

1. Acesse RapidAPI
2. Crie uma conta
3. Subscribe no API-Football
4. Copie sua `X-RapidAPI-Key`

#### 🥈 **Football-Data.org - Gratuita**
- **URL**: https://www.football-data.org/client/register
- **Plano Gratuito**: 100 requests/dia
- **Cobertura**: Limitada (principais ligas europeias)

1. Registre-se no site
2. Confirme seu email
3. Copie sua `X-Auth-Token`

#### 🥉 **API-Sports - Alternativa**
- **URL**: https://www.api-sports.io/
- **Plano Gratuito**: 1000 requests/dia
- **Cobertura**: Completa

### 3. Execute o Projeto

```bash
npm install
npm start
```

## 📊 Recursos Implementados

### ✅ **Dados em Tempo Real**
- Jogos de hoje do futebol brasileiro
- Resultados ao vivo
- Próximos jogos (7 dias)
- Status dos jogos (não iniciado, ao vivo, finalizado)

### ✅ **Competições Suportadas**
- 🏆 **Brasileirão Série A** (ID: 71)
- 🥈 **Brasileirão Série B** (ID: 72)
- 🏅 **Copa do Brasil** (ID: 73)
- 🌎 **Copa Libertadores** (ID: 13)
- 🌎 **Copa Sul-Americana** (ID: 11)
- 🔴 **Campeonato Paulista** (ID: 74)
- ⚫ **Campeonato Carioca** (ID: 75)

### ✅ **IA e Predições**
- Algoritmo ensemble com 6 modelos
- Análise de +50 métricas
- Todos os mercados de apostas (15+ categorias)
- Estratégias de apostas inteligentes
- Kelly Criterion otimizado

### ✅ **Performance Otimizada**
- Cache inteligente (TTL dinâmico)
- Requisições paralelas
- Fallback automático
- Monitoramento de limites de API

## 🔧 Configuração Avançada

### Variáveis de Ambiente

```env
# Habilitar dados reais (true/false)
REACT_APP_ENABLE_REAL_DATA=true

# Cache TTL em minutos
REACT_APP_CACHE_TTL_MINUTES=30

# Auto-refresh em segundos
REACT_APP_AUTO_REFRESH_SECONDS=120
```

### Limites de API

| Provedor | Gratuito | Pago | Recomendação |
|----------|----------|------|--------------|
| API-Football | 500/dia | 15.000/mês | ⭐ Melhor |
| Football-Data | 100/dia | 3.000/mês | Backup |
| API-Sports | 1.000/dia | 30.000/mês | Alternativa |

## 📱 Como Usar

1. **Acesse "Jogos Reais BR"** no menu lateral
2. **Veja jogos ao vivo** com indicador verde
3. **Clique em "Prever IA"** em qualquer jogo
4. **Analise os mercados** gerados automaticamente
5. **Use as estratégias** de apostas sugeridas

## 🎯 Mercados Suportados

### **Básicos**
- Resultado Final (1x2)
- Dupla Chance
- Over/Under (0.5 a 4.5 gols)
- Ambos Marcam

### **Avançados**
- Asian Handicap (múltiplas linhas)
- European Handicap
- Primeiro/Último Gol
- Resultado Correto
- Margem de Vitória

### **Estatísticas**
- Escanteios (7+ linhas)
- Cartões (amarelos/vermelhos)
- Chutes/Chutes no Gol
- Pênaltis

### **Especiais**
- Clean Sheets
- Gols por Tempo
- Timing do Primeiro Gol
- Comeback Win

## 🔄 Sistema de Sincronização

### **Automático**
- Atualização a cada 2 minutos
- Cache inteligente de 30 minutos
- Fallback automático se API falhar

### **Manual**
- Botão "Atualizar" disponível
- Status das APIs em tempo real
- Contador de requisições

## 🏆 Vantagens Competitivas

### **Dados Brasileiros**
- ✅ Foco no mercado brasileiro
- ✅ Todas as competições nacionais
- ✅ Rivalidades e contexto local
- ✅ Fatores climáticos tropicais

### **IA Avançada**
- ✅ 6 modelos de machine learning
- ✅ Ensemble otimizado
- ✅ 50+ métricas analisadas
- ✅ Distribuição de Poisson

### **Performance**
- ✅ Cache multi-camadas
- ✅ Requisições otimizadas
- ✅ Fallback inteligente
- ✅ Monitoramento em tempo real

## 🚨 Troubleshooting

### **Erro: "API limit exceeded"**
- Verifique seus limites diários
- Use múltiplas APIs como backup
- Aumente o TTL do cache

### **Erro: "Failed to load matches"**
- Verifique sua chave de API
- Confirme se está ativa
- Teste em https://rapidapi.com/

### **Dados não atualizando**
- Force refresh (Ctrl+F5)
- Limpe o cache do navegador
- Verifique console para erros

## 📞 Suporte

- **GitHub Issues**: Para bugs e melhorias
- **Documentação**: Este README
- **Console**: Logs detalhados para debug

---

🔥 **Sistema pronto para produção com dados reais do futebol brasileiro!** ⚽🇧🇷