# ⚡ Quick Start - Pipeline de Dados

Guia rápido de 5 minutos para começar a coletar dados!

---

## 🚀 Início Rápido (3 Comandos)

```bash
cd football-analytics/backend
source venv/bin/activate

# 1. Instalar dependência do scheduler
pip install apscheduler

# 2. Setup automático
python setup_data_pipeline.py --full-setup

# 3. Pronto! O pipeline está rodando
```

---

## 📋 O que acontece no setup?

### 1. Criar Tabelas do Banco ✅
- `fixture_cache` - Cache de dados da API
- `matches` - Jogos estruturados
- `match_statistics` - Estatísticas dos jogos
- `api_request_logs` - Log de requisições
- `daily_api_quota` - Controle de quota
- `league_configs` - Configuração de ligas
- `data_collection_jobs` - Jobs de coleta

### 2. Configurar Ligas Prioritárias ✅
- 🇧🇷 Brasileirão Série A (Prioridade 1)
- 🇧🇷 Brasileirão Série B (Prioridade 2)
- 🏆 Copa Libertadores (Prioridade 3)
- 🏆 Copa Sul-Americana (Prioridade 4)
- 🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League (Prioridade 5)
- 🇪🇸 La Liga (Prioridade 6)
- 🇩🇪 Bundesliga (Prioridade 7)
- 🇮🇹 Serie A (Prioridade 8)

### 3. Coleta Histórica (Opcional) ⏳
Você pode optar por coletar dados históricos agora ou depois.

### 4. Scheduler Automático ⏰
Jobs agendados:
- **Coleta Diária**: 6h da manhã
- **Jogos Ao Vivo**: A cada 10min
- **Sync Cache**: A cada 1h
- **Verificação Quota**: A cada 30min

---

## 🎯 Comandos Individuais

### Criar Tabelas

```bash
python setup_data_pipeline.py --create-tables
```

### Configurar Ligas

```bash
python setup_data_pipeline.py --configure-leagues
```

### Coletar Histórico

```bash
# Todas as ligas (usa ~400-600 requests)
python setup_data_pipeline.py --initial-historical

# Apenas primeiras 2 ligas
python setup_data_pipeline.py --initial-historical --max-leagues 2
```

### Iniciar Scheduler

```bash
python setup_data_pipeline.py --start-scheduler
```

---

## 📊 Verificar Status

### Quota Disponível

```bash
python -c "
from app.services.api_quota_manager import APIQuotaManager
from app.core.database import SessionLocal

db = SessionLocal()
quota = APIQuotaManager(db)
stats = quota.get_usage_stats()

print(f\"Quota Diária: {stats['requests_used']}/{stats['daily_limit']}\")
print(f\"Disponível: {stats['requests_remaining']}\")
print(f\"Uso: {stats['usage_percentage']:.1f}%\")
"
```

### Dados Coletados

```bash
python -c "
from app.models.api_tracking import FixtureCache
from app.core.database import SessionLocal

db = SessionLocal()
total = db.query(FixtureCache).count()
with_stats = db.query(FixtureCache).filter(
    FixtureCache.has_statistics == True
).count()

print(f\"Total de fixtures: {total}\")
print(f\"Com estatísticas: {with_stats}\")
"
```

### Últimas Coletas

```bash
python -c "
from app.models.api_tracking import DataCollectionJob
from app.core.database import SessionLocal

db = SessionLocal()
jobs = db.query(DataCollectionJob).order_by(
    DataCollectionJob.created_at.desc()
).limit(5).all()

for job in jobs:
    print(f\"{job.job_name}: {job.status} - {job.fixtures_collected} fixtures\")
"
```

---

## ⚙️ Configuração Avançada

### Alterar Prioridades de Ligas

```python
from app.models.api_tracking import LeagueConfig
from app.core.database import SessionLocal

db = SessionLocal()

# Desativar liga
liga = db.query(LeagueConfig).filter(LeagueConfig.league_id == 135).first()
liga.is_active = False
db.commit()

# Alterar prioridade
liga = db.query(LeagueConfig).filter(LeagueConfig.league_id == 71).first()
liga.priority = 1
db.commit()
```

### Ajustar Horários do Scheduler

Editar `app/services/data_scheduler.py`:

```python
# Mudar horário da coleta diária (padrão: 6h)
self.scheduler.add_job(
    self.daily_incremental_job,
    CronTrigger(hour=8, minute=0),  # Mudou para 8h
    id='daily_incremental',
    name='Coleta Diária Incremental'
)
```

---

## 🔄 Fluxo Diário Automático

### 6:00 AM - Coleta Diária
```
1. Coleta jogos de ontem (resultados finais)
2. Coleta jogos de hoje (novos agendamentos)
3. Coleta jogos de amanhã (próximos jogos)
4. ~10-30 requests usados
```

### Durante o Dia - Atualizações Ao Vivo
```
A cada 10 minutos:
1. Identifica jogos com status LIVE
2. Atualiza placares e minuto
3. Quando finaliza, coleta estatísticas
4. ~5-20 requests/hora durante jogos
```

### A Cada Hora - Sincronização
```
1. Converte cache → database estruturado
2. Prepara dados para ML
3. Marca fixtures como sincronizados
```

### Meia-Noite - Reset de Quota
```
1. Quota reseta para 7500 requests
2. Nova oportunidade para coletas grandes
```

---

## 📈 Estimativa de Uso Diário

| Atividade | Requests | Quando |
|-----------|----------|--------|
| Coleta Diária | 10-30 | 6h AM |
| Atualizações Ao Vivo | 50-100 | Durante jogos |
| Estatísticas Extras | 20-50 | Conforme necessário |
| **Total Médio** | **80-180** | **24h** |
| **Margem de Segurança** | **7320** | **Disponível** |

**Conclusão**: Uso médio de apenas **2.4%** da quota diária!

---

## 🎓 Integração com ML

Após a coleta inicial, os dados estarão prontos para ML:

```python
from app.services.data_pipeline import DataPipeline
from app.ml.neural_network_predictor import NeuralNetworkPredictor

# Treinar modelo com dados coletados
ml_engine = NeuralNetworkPredictor()

# Dados já estão no banco local
# Nenhuma chamada à API necessária!
ml_engine.train_from_database()
```

---

## 🆘 Troubleshooting

### "No module named 'apscheduler'"
```bash
pip install apscheduler
```

### "Quota esgotada"
```bash
# Verificar uso
python -c "from app.services.api_quota_manager import APIQuotaManager; from app.core.database import SessionLocal; db = SessionLocal(); quota = APIQuotaManager(db); print(quota.check_health())"

# Aguardar reset (meia-noite UTC)
```

### "Scheduler não inicia"
```bash
# Verificar se já está rodando
ps aux | grep python | grep scheduler

# Parar processos antigos
pkill -f scheduler

# Reiniciar
python setup_data_pipeline.py --start-scheduler
```

### "Banco de dados não encontrado"
```bash
# Criar tabelas primeiro
python setup_data_pipeline.py --create-tables
```

---

## ✅ Checklist Pós-Setup

- [ ] Tabelas criadas
- [ ] Ligas configuradas
- [ ] Dados históricos coletados (opcional)
- [ ] Scheduler rodando
- [ ] Quota monitorada
- [ ] Primeira coleta diária executada
- [ ] Dados sincronizados no banco
- [ ] ML pode acessar os dados

---

## 📞 Próximos Passos

1. ✅ **Pipeline configurado** → Aguardar coleta diária
2. ⏳ **Treinar modelos ML** → Com dados coletados
3. ⏳ **Monitorar quota** → Verificar uso diário
4. ⏳ **Ajustar ligas** → Conforme necessidade

---

**Status**: ✅ Sistema pronto para coleta automática!

Para mais detalhes, consulte: `DATA_PIPELINE_GUIDE.md`
