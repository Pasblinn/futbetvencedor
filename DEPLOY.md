# 🚀 GUIA DE DEPLOY - Football Analytics

## 📋 Resumo

Este guia explica como fazer deploy do sistema de forma 100% automatizada, permitindo que rode 24/7 mesmo com seu computador desligado.

---

## ⚙️ Como funciona AGORA (localhost)

**✅ O que JÁ funciona:**
- Scheduler roda automaticamente quando você inicia o backend
- Jobs automáticos executam em background:
  - Importar jogos (4x/dia)
  - Atualizar jogos ao vivo (a cada 2 min)
  - Gerar predictions (a cada 6h)
  - Limpar finalizados (a cada 1h)
  - Normalizar ligas (diário)

**❌ Limitação:**
- Para quando você desliga o computador (está no localhost)

---

## 🌐 OPÇÃO 1: Docker + VPS (Recomendado)

### Serviços recomendados:
- **DigitalOcean** - $6/mês (Droplet básico)
- **AWS EC2** - Nível gratuito disponível
- **Google Cloud** - $300 créditos iniciais
- **Vultr** - $5/mês
- **Linode** - $5/mês

### Passos:

#### 1. Criar `docker-compose.yml` na raiz do projeto

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    container_name: football-analytics-backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/football_analytics
      - API_FOOTBALL_KEY=${API_FOOTBALL_KEY}
      - SECRET_KEY=${SECRET_KEY}
      - PYTHONUNBUFFERED=1
    depends_on:
      - db
    restart: unless-stopped
    volumes:
      - ./backend/logs:/app/logs
      - ./backend/cache:/app/cache

  frontend:
    build: ./frontend
    container_name: football-analytics-frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    container_name: football-analytics-db
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=football_analytics
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

#### 2. Criar `.env` na raiz do projeto

```env
# API Keys
API_FOOTBALL_KEY=sua_chave_aqui

# Security
SECRET_KEY=gere_uma_chave_segura_aqui

# Database (Docker)
DATABASE_URL=postgresql://user:password@db:5432/football_analytics
```

#### 3. No servidor VPS:

```bash
# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clonar projeto
git clone seu-repositorio.git
cd football-analytics

# Configurar variáveis de ambiente
nano .env  # Editar com suas credenciais

# Iniciar containers
docker-compose up -d

# Ver logs
docker-compose logs -f backend
```

#### 4. Verificar que está funcionando:

```bash
# Ver status
docker-compose ps

# Ver logs do scheduler
docker-compose logs -f backend | grep "⏰"

# Acessar
curl http://seu-ip:8000/health
```

---

## 🔄 OPÇÃO 2: Railway.app (Mais Fácil)

### Vantagens:
- Deploy com 1 clique
- $5/mês (grátis nos primeiros meses)
- Não precisa gerenciar servidor

### Passos:

1. **Criar conta em railway.app**

2. **Conectar repositório GitHub**

3. **Adicionar serviços:**
   - PostgreSQL (plugin oficial)
   - Backend (detecta Dockerfile automaticamente)
   - Frontend

4. **Configurar variáveis de ambiente:**
   - `API_FOOTBALL_KEY`
   - `SECRET_KEY`
   - `DATABASE_URL` (gerado automaticamente pelo Railway)

5. **Deploy automático** 🚀

---

## 🛠️ OPÇÃO 3: Heroku

```bash
# Instalar Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh

# Login
heroku login

# Criar app
heroku create football-analytics-app

# Adicionar PostgreSQL
heroku addons:create heroku-postgresql:mini

# Configurar variáveis
heroku config:set API_FOOTBALL_KEY=sua_chave
heroku config:set SECRET_KEY=sua_secret_key

# Deploy
git push heroku main

# Ver logs
heroku logs --tail
```

---

## 🔐 Variáveis de Ambiente Necessárias

```env
# API Football
API_FOOTBALL_KEY=sua_chave_api_football

# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Security
SECRET_KEY=chave_super_secreta_aqui

# Optional
LOG_LEVEL=INFO
ENABLE_REAL_TIME_PREDICTIONS=true
CACHE_PREDICTIONS=true
```

---

## ✅ Checklist Pré-Deploy

- [ ] API Football key válida
- [ ] Secret key gerada (pode usar `openssl rand -hex 32`)
- [ ] Database configurado
- [ ] `.env` criado com todas variáveis
- [ ] Testado localmente com Docker
- [ ] CORS configurado corretamente no backend
- [ ] Frontend apontando para URL do backend

---

## 🧪 Testar Localmente com Docker (Antes de Deploy)

```bash
# Build
docker-compose build

# Iniciar
docker-compose up

# Verificar se scheduler está rodando
docker-compose logs backend | grep "⏰ Scheduler"

# Parar
docker-compose down
```

---

## 📊 Monitoramento Após Deploy

### Ver logs do scheduler:
```bash
# Docker
docker-compose logs -f backend | grep "📥\|🔴\|🧠\|🧹"

# Heroku
heroku logs --tail | grep "📥\|🔴\|🧠\|🧹"
```

### Jobs que devem aparecer:
```
✅ Scheduler COMPLETO iniciado com sucesso!

🤖 JOBS AUTOMÁTICOS ATIVOS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📥 Importar Jogos (próximos 7 dias)  → 4x/dia (00h, 06h, 12h, 18h)
🔴 Atualizar Jogos AO VIVO           → A cada 2 minutos
🧠 Gerar Predictions ML              → A cada 6 horas
🧹 Limpar Jogos Finalizados          → A cada 1 hora
🏆 Normalizar Nomes de Ligas         → Diário às 03:00
🔄 Atualizar Resultados [LEGACY]     → A cada 1 hora
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 🆘 Troubleshooting

### Scheduler não inicia:
```python
# Verificar se está ativado em app/main.py
from app.core.scheduler import start_scheduler

@app.on_event("startup")
async def startup_event():
    start_scheduler()  # Deve estar presente
```

### Database não conecta:
- Verificar `DATABASE_URL` nas variáveis de ambiente
- Testar conexão: `psql $DATABASE_URL`

### Jobs não executam:
```bash
# Ver logs do APScheduler
docker-compose logs backend | grep "apscheduler"
```

---

## 💰 Custos Estimados

| Serviço | Custo/mês | Recursos |
|---------|-----------|----------|
| Railway | $5 | 512MB RAM, Postgres incluído |
| DigitalOcean | $6 | 1GB RAM, 25GB SSD |
| Heroku | $7 | 512MB RAM + $5 DB |
| AWS EC2 | Grátis/12 meses | t2.micro |

---

## 📝 Próximos Passos Após Deploy

1. ✅ Verificar que scheduler iniciou corretamente
2. ✅ Aguardar próximo job automático (máx 2 min)
3. ✅ Verificar importação de jogos
4. ✅ Confirmar predictions sendo geradas
5. ✅ Monitorar logs por 24h

---

## 🎯 Resposta Direta à Sua Pergunta

**"ele ja roda automaticamente em background?"**
✅ SIM - quando você inicia o FastAPI, o scheduler inicia automaticamente

**"mesmo após desligar meu computador?"**
❌ NÃO - precisa fazer deploy em servidor para rodar 24/7

**"o que preciso fazer?"**
Escolher uma das opções acima e fazer deploy. Recomendo Railway (mais fácil) ou DigitalOcean (mais controle).
