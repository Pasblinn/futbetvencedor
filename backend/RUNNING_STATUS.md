# 🚀 SISTEMA EM EXECUÇÃO - Background Mode

**Data de Início:** 2025-10-18 14:11 UTC
**Status:** ✅ RODANDO EM BACKGROUND
**PID do Backend:** 1606132

---

## 📊 STATUS ATUAL

✅ Backend FastAPI rodando (porta 8000)
✅ Scheduler com 12 jobs automáticos ATIVO
✅ Ollama (AI Agent) ATIVO
✅ Logs sendo gravados continuamente

---

## 🔍 COMO VERIFICAR STATUS

### 1. Verificar se o backend ainda está rodando:
```bash
ps aux | grep "uvicorn app.main:app" | grep -v grep
```

### 2. Monitorar jobs do scheduler (RECOMENDADO):
```bash
./monitor_scheduler.sh
```

**Opções do monitor:**
- `1` - Status do Scheduler (jobs ativos)
- `2` - Últimos logs (tail -50)
- `3` - Erros recentes
- `4` - Logs do AI Agent
- `5` - Logs do ML Retraining
- `6` - Logs de Importação
- `7` - Logs de Predictions
- `8` - Estatísticas do Banco (predictions, matches)
- `9` - Limpar logs grandes (>100MB)

### 3. Ver logs em tempo real:
```bash
# Backend geral
tail -f logs/backend.log

# Apenas erros
tail -f logs/scheduler_error.log

# Filtrar por job específico
tail -f logs/backend.log | grep "🧠"  # AI Agent
tail -f logs/backend.log | grep "🤖"  # ML Retraining
tail -f logs/backend.log | grep "📥"  # Importação
```

### 4. Verificar estatísticas do banco:
```bash
source venv/bin/activate
python -c "
from app.core.database import get_db_session
from app.models import Match, Prediction

db = get_db_session()

total_predictions = db.query(Prediction).count()
ai_analyzed = db.query(Prediction).filter(Prediction.ai_analyzed == True).count()
greens = db.query(Prediction).filter(Prediction.is_winner == True).count()
reds = db.query(Prediction).filter(Prediction.is_winner == False).count()

print(f'\n📊 ESTATÍSTICAS:')
print(f'  Total Predictions: {total_predictions}')
print(f'  AI Analyzed: {ai_analyzed}')
print(f'  🟢 GREENS: {greens}')
print(f'  🔴 REDS: {reds}')
print(f'  📈 Accuracy: {(greens/(greens+reds)*100) if greens+reds > 0 else 0:.1f}%\n')

db.close()
"
```

---

## 🤖 JOBS AUTOMÁTICOS ATIVOS (12)

| Job | Frequência | Próxima Execução |
|-----|-----------|------------------|
| 📥 Importar Jogos | 4x/dia (00h, 06h, 12h, 18h) | Verificar no monitor |
| 🔴 Atualizar AO VIVO | A cada 2 minutos | Contínuo |
| 🧠 Gerar Predictions | A cada 6 horas | Verificar no monitor |
| 🧠 **AI Agent Batch** | **A cada 2 horas** ⚡ | Verificar no monitor |
| 🤖 **ML Retraining** | **Diário às 02:00** 🎉 | Próxima às 02:00 |
| 🧹 Limpar Finalizados | A cada 1 hora | Contínuo |
| 🏆 Normalizar Ligas | Diário às 03:00 | Próxima às 03:00 |
| 🔄 Atualizar Resultados | A cada 1 hora | Contínuo |

---

## ⚠️ TROUBLESHOOTING

### Se o backend parou:
```bash
# Verificar se processo existe
ps aux | grep uvicorn | grep -v grep

# Se não estiver rodando, reiniciar:
cd /home/pablintadini/mododeus/football-analytics/backend
nohup bash -c "source venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000" > logs/backend.log 2>&1 &

# Anotar novo PID
echo $!
```

### Se Ollama parou (AI Agent não funcionará):
```bash
# Verificar
curl http://localhost:11434/api/tags

# Se não responder, iniciar:
ollama serve &
```

### Logs muito grandes:
```bash
# Usar opção 9 do monitor_scheduler.sh
# Ou manualmente:
./monitor_scheduler.sh
# Escolher opção 9
```

---

## 📈 O QUE OBSERVAR NAS PRÓXIMAS 14 HORAS

### Esperado:
1. **Importação de jogos:** Executará às 18:00 (próximo horário agendado)
2. **Atualização AO VIVO:** Executando a cada 2 minutos (se houver jogos ao vivo)
3. **AI Agent Batch:** Executará ~7 vezes (a cada 2h) - 100 predictions por execução
4. **Predictions ML:** Executará ~2-3 vezes (a cada 6h)
5. **Acúmulo de resultados:** Jogos finalizados → GREENS/REDS atualizados

### Métricas a acompanhar quando voltar:
- Quantidade de predictions criadas
- Quantidade analisada por AI
- GREENS vs REDS acumulados
- Erros no log (se houver)
- Performance do Ollama

---

## 🛑 PARAR O SISTEMA

```bash
# Encontrar PID
ps aux | grep uvicorn | grep -v grep

# Parar gracefully
kill -15 1606132

# Forçar parada (se necessário)
kill -9 1606132

# Verificar que parou
ps aux | grep uvicorn | grep -v grep
```

---

**Status:** ✅ **SISTEMA 100% AUTOMATIZADO RODANDO**
**Última atualização:** 2025-10-18 14:11 UTC
**Monitoramento:** Use `./monitor_scheduler.sh` quando voltar!
