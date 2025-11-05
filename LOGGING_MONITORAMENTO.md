# 📊 SISTEMA DE LOGGING E MONITORAMENTO

**Data**: 10/10/2025
**Status**: ✅ IMPLEMENTADO

---

## 🎯 VISÃO GERAL

Sistema completo de logging para monitorar e debugar erros em tempo real, tanto no backend (Python) quanto no frontend (React).

---

## 🔧 BACKEND - PYTHON LOGGING

### **Onde ver os logs:**

```bash
# Logs do scheduler (jobs automáticos)
tail -f logs/scheduler.log

# Logs gerais da aplicação
tail -f logs/app.log

# Erros do scheduler
tail -f logs/scheduler_error.log
```

---

### **Logs importantes adicionados:**

#### **1. Live Matches Sync (data_synchronizer.py)**

**Logs de início:**
```
🔴 Checking 3 live matches for updates...
```

**Logs de mudança de status (IMPORTANTE!):**
```
⚽ Match 2794 status changed: 2H → FT (San Lorenzo vs San Martin S.J.) Score: 0-1
```

**Logs de conclusão:**
```
✅ Updated 3 live matches
```

---

#### **2. Stuck Matches Cleanup (scheduler.py)**

**Logs de início:**
```
🔧 Running stuck matches cleanup job...
```

**Logs de correção:**
```
Fixed match 5381: Brann U19 vs Tromsø U19 (INT → FT)
```

**Logs de conclusão:**
```
✅ Stuck matches cleanup completed: 2 matches fixed
```

---

### **Como filtrar logs específicos:**

```bash
# Ver apenas mudanças de status de live matches
tail -f logs/scheduler.log | grep "status changed"

# Ver apenas limpeza de partidas travadas
tail -f logs/scheduler.log | grep "stuck"

# Ver apenas erros
tail -f logs/scheduler.log | grep "❌"

# Ver apenas sucessos
tail -f logs/scheduler.log | grep "✅"
```

---

## 💻 FRONTEND - REACT LOGGING

### **Sistema de logger criado:**

Arquivo: `frontend/src/utils/logger.ts`

**Características:**
- ✅ Logs coloridos por tipo
- ✅ Desativado automaticamente em produção
- ✅ Suporte a timing/performance
- ✅ Agrupamento de logs relacionados

---

### **Tipos de log disponíveis:**

```typescript
import { logger } from './utils/logger';

// Log informativo (azul)
logger.info('ModuleName', 'Something happened', data);

// Warning (amarelo)
logger.warn('ModuleName', 'Potential issue', data);

// Erro (vermelho) - sempre ativo, mesmo em produção
logger.error('ModuleName', 'Error occurred', error);

// Sucesso (verde)
logger.success('ModuleName', 'Operation successful', result);

// API call (roxo)
logger.api('GET', '/api/endpoint', params);

// Performance timing
logger.time('OperationLabel');
// ... código ...
logger.timeEnd('OperationLabel');

// Agrupar logs relacionados
logger.group('GroupName');
logger.info('ModuleName', 'Log 1');
logger.info('ModuleName', 'Log 2');
logger.groupEnd();

// Tabela (útil para arrays)
logger.table([{ id: 1, name: 'Test' }]);
```

---

### **Logs implementados:**

#### **1. Date Utils (dateUtils.ts)**

**Quando recebe data null/undefined:**
```
⚠️ [dateUtils] Received null/undefined date string
```

**Quando data é inválida:**
```
⚠️ [dateUtils] Invalid date string: "invalid-date-2025"
```

**Quando erro ao parsear:**
```
❌ [dateUtils] Error parsing date: "bad-date" TypeError: ...
```

---

#### **2. API Client (apiClient.ts)**

**Início de requisição:**
```
🟣 [API] GET /predictions/upcoming { limit: 10 }
```

**Performance timing:**
```
⏱️ GET /predictions/upcoming: 234ms
```

**Sucesso:**
```
✅ [apiClient] GET /predictions/upcoming success { predictions: [...] }
```

**Erro:**
```
❌ [apiClient] GET /predictions/upcoming failed: 404 Not Found
```

---

## 📱 COMO MONITORAR NO NAVEGADOR

### **1. Abrir DevTools**
- Chrome/Edge: `F12` ou `Ctrl+Shift+I`
- Firefox: `F12`
- Safari: `Cmd+Option+I`

### **2. Ir para aba "Console"**

### **3. Filtrar logs específicos:**

```javascript
// Filtrar apenas warnings
// No campo de filtro: warn

// Filtrar apenas erros
// No campo de filtro: error

// Filtrar módulo específico
// No campo de filtro: [dateUtils]

// Filtrar API calls
// No campo de filtro: [API]
```

---

## 🎨 LOGS COLORIDOS NO CONSOLE

Os logs aparecem coloridos para facilitar identificação:

- 🔵 **Info** (azul) - Informações gerais
- 🟡 **Warn** (amarelo) - Avisos, possíveis problemas
- 🔴 **Error** (vermelho) - Erros críticos
- 🟢 **Success** (verde) - Operações bem-sucedidas
- 🟣 **API** (roxo) - Chamadas HTTP

---

## 🔍 CENÁRIOS DE DEBUG

### **Cenário 1: Data aparecendo "Invalid Date"**

**No Console do Navegador:**
```
⚠️ [dateUtils] Invalid date string: "2025-13-45T00:00:00"
```

**Ação**: Verificar por que o backend está enviando data inválida.

---

### **Cenário 2: Partida não sai da lista "Live"**

**Nos Logs do Backend:**
```bash
tail -f logs/scheduler.log | grep "status changed"
```

**Esperar por:**
```
⚽ Match 123 status changed: 2H → FT (Time A vs Time B) Score: 2-1
```

**Se não aparecer após 5 minutos:**
1. Verificar se API externa está respondendo
2. Verificar logs de erro: `tail -f logs/scheduler_error.log`
3. Rodar cleanup manual: `python fix_stuck_matches.py --dry-run`

---

### **Cenário 3: API request falhando**

**No Console do Navegador:**
```
❌ [apiClient] GET /predictions/123/all-markets failed: 404 Not Found
```

**Ação**:
1. Verificar se match_id existe
2. Verificar se backend está rodando: `curl http://localhost:8000/health`
3. Verificar logs do backend

---

### **Cenário 4: Performance lenta**

**No Console do Navegador:**
```
⏱️ GET /predictions/upcoming: 5234ms  ← MUITO LENTO!
```

**Ação**:
1. Verificar rede (aba Network do DevTools)
2. Verificar se banco de dados está lento
3. Verificar logs do backend para ver tempo de query

---

## 🛠️ COMO USAR O LOGGER

### **Em componentes React:**

```typescript
import { logger } from '../utils/logger';

function PredictionsPage() {
  useEffect(() => {
    logger.info('PredictionsPage', 'Component mounted');

    fetchPredictions()
      .then(data => {
        logger.success('PredictionsPage', 'Predictions loaded', data);
      })
      .catch(error => {
        logger.error('PredictionsPage', 'Failed to load predictions', error);
      });
  }, []);

  return <div>...</div>;
}
```

---

### **Em serviços/utils:**

```typescript
import { logger } from './logger';

export async function fetchAllMarkets(matchId: number) {
  logger.time(`fetchAllMarkets-${matchId}`);

  try {
    const response = await fetch(`/api/v1/predictions/${matchId}/all-markets`);

    if (!response.ok) {
      logger.error('fetchAllMarkets', 'Request failed', response.status);
      throw new Error('Failed to fetch');
    }

    const data = await response.json();
    logger.success('fetchAllMarkets', 'Markets loaded', data);

    return data;
  } catch (error) {
    logger.error('fetchAllMarkets', 'Error', error);
    throw error;
  } finally {
    logger.timeEnd(`fetchAllMarkets-${matchId}`);
  }
}
```

---

## 🚀 PRODUÇÃO vs DESENVOLVIMENTO

### **Desenvolvimento** (NODE_ENV=development):
- ✅ Todos os logs ativos
- ✅ Logs coloridos
- ✅ Performance timing
- ✅ Agrupamento

### **Produção** (NODE_ENV=production):
- ❌ Info/Warn/Success desabilitados
- ✅ Apenas Errors ativos
- ✅ Console limpo
- ✅ Melhor performance

---

## 📊 EXEMPLO COMPLETO - FLUXO DE DEBUG

### **Problema**: "Jogo não atualiza o placar"

**1. Verificar logs do scheduler:**
```bash
tail -f logs/scheduler.log | grep "live matches"
```

**Esperado:**
```
🔴 Checking 1 live matches for updates...
✅ Updated 1 live matches
```

**2. Se não está atualizando, verificar erros:**
```bash
tail -f logs/scheduler_error.log
```

**3. Verificar no frontend:**
```javascript
// Abrir DevTools e filtrar: [API]
```

**Esperado:**
```
🟣 [API] GET /live-matches/live
⏱️ GET /live-matches/live: 145ms
✅ [apiClient] GET /live-matches/live success { matches: [...] }
```

**4. Verificar data formatting:**
```javascript
// No console, filtrar: [dateUtils]
```

**Se houver erro:**
```
⚠️ [dateUtils] Invalid date string: "..."
```

**5. Solução encontrada!**

---

## 🎯 CHECKLIST DE MONITORAMENTO

### **Verificação Diária:**
- [ ] Verificar logs de erro: `grep "❌" logs/scheduler.log | tail -20`
- [ ] Verificar stuck matches: `grep "stuck" logs/scheduler.log | tail -20`
- [ ] Verificar mudanças de status: `grep "status changed" logs/scheduler.log | tail -20`

### **Quando Reportar Bug:**
- [ ] Copiar logs relevantes do backend
- [ ] Copiar logs do console do navegador
- [ ] Anotar timestamp do erro
- [ ] Anotar steps para reproduzir

---

## 📞 COMANDOS ÚTEIS

### **Backend:**

```bash
# Ver últimas 100 linhas de logs
tail -100 logs/scheduler.log

# Seguir logs em tempo real
tail -f logs/scheduler.log

# Buscar por erro específico
grep "Failed to update" logs/scheduler.log

# Ver apenas erros hoje
grep "$(date +%Y-%m-%d)" logs/scheduler.log | grep "❌"

# Contar quantos erros por hora
grep "$(date +%Y-%m-%d)" logs/scheduler.log | grep "❌" | cut -d' ' -f1 | uniq -c
```

---

### **Frontend:**

```javascript
// No console do navegador

// Limpar console
clear()

// Ativar logs manualmente (se desabilitados)
localStorage.setItem('debug', 'true')

// Desativar logs
localStorage.removeItem('debug')

// Ver todas as chamadas de API
performance.getEntriesByType('resource').filter(r => r.name.includes('/api/'))
```

---

## ✅ RESUMO

**Backend**:
- ✅ Logs em `logs/scheduler.log` e `logs/app.log`
- ✅ Logs de status changes adicionados
- ✅ Logs de stuck matches cleanup

**Frontend**:
- ✅ Logger colorido criado (`utils/logger.ts`)
- ✅ API client com logging (`utils/apiClient.ts`)
- ✅ Date utils com validação e logs
- ✅ Desabilitado em produção automaticamente

**Monitoramento**:
- ✅ Comandos para filtrar logs
- ✅ Guia de debug por cenário
- ✅ Checklist de verificação

---

**🎉 Sistema 100% monitorado e pronto para debug!**

**Desenvolvido**: 10/10/2025
**Próximo passo**: Implementar frontend dos 45 mercados
