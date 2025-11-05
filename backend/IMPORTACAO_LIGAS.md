# 📥 IMPORTAÇÃO DE LIGAS - GUIA SIMPLIFICADO

**Data**: 10/10/2025

---

## 🎯 O QUE ESTÁ FALTANDO

### ❌ **Ligas Prioritárias Não Importadas:**

1. **UEFA Champions League** ⚠️
2. **UEFA Europa League** ⚠️
3. **La Liga** (Espanha) ⚠️
4. **Serie A** (Itália) ⚠️
5. **Copa do Brasil** ⚠️
6. **Eliminatórias da Copa do Mundo** (HOJE tem jogos!)

### ✅ **Ligas Já Disponíveis:**

- Brasileirão Série A (1,069 jogos)
- Premier League (1,034 jogos)
- Libertadores (464 jogos)
- MLS, Bundesliga, Ligue 1

---

## 🚀 COMO IMPORTAR (3 PASSOS)

### **PASSO 1: Configurar API Key**

Edite o arquivo `.env` no backend:

```bash
cd backend
nano .env
```

Adicione ou verifique:

```
API_FOOTBALL_KEY=SUA_CHAVE_AQUI
API_FOOTBALL_BASE_URL=https://v3.football.api-sports.io
```

💡 **Não tem API key?** Pegue grátis em: https://www.api-football.com/

---

### **PASSO 2: Editar Script de Importação**

Abra o arquivo `import_historical_data.py`:

```bash
nano import_historical_data.py
```

Procure a linha `LEAGUES_TO_IMPORT = [...]` e adicione os IDs das ligas que você quer:

```python
LEAGUES_TO_IMPORT = [
    71,   # Brasileirão Série A (já tem)
    39,   # Premier League (já tem)

    # ADICIONE ESSAS NOVAS:
    140,  # La Liga (Espanha)
    135,  # Serie A (Itália)
    2,    # Champions League
    3,    # Europa League
    71,   # Copa do Brasil
    34,   # Eliminatórias Sul-Americanas
]
```

**Lista completa de IDs:**

| Liga | ID |
|------|---|
| La Liga (Espanha) | 140 |
| Serie A (Itália) | 135 |
| Champions League | 2 |
| Europa League | 3 |
| Conference League | 848 |
| Copa do Brasil | 71 |
| Copa América | 9 |
| Eurocopa | 4 |
| Nations League | 5 |
| Eliminatórias Sul-América | 34 |

---

### **PASSO 3: Executar Importação**

```bash
cd backend
source venv/bin/activate
python import_historical_data.py
```

**Aguarde...** O script vai:
1. Buscar jogos das últimas temporadas
2. Buscar odds (Bet365)
3. Salvar tudo no banco

⏱️ **Tempo:** ~5-10 minutos dependendo de quantas ligas você adicionou

---

## ⚡ IMPORTAÇÃO RÁPIDA - ELIMINATÓRIAS HOJE

Se você só quer importar as Eliminatórias para HOJE, use este comando:

```bash
cd backend
source venv/bin/activate

python << 'EOF'
from app.services.api_football_service import APIFootballService
from datetime import datetime

print("🇧🇷 Importando Eliminatórias da Copa - HOJE")

api = APIFootballService()
today = datetime.now().strftime('%Y-%m-%d')

# League ID 34 = Eliminatórias Sul-Americanas
fixtures = api.get_fixtures(league=34, date=today)

print(f"\n✅ {len(fixtures)} jogos encontrados para hoje ({today}):\n")

for f in fixtures:
    print(f"  🏆 {f['teams']['home']['name']} vs {f['teams']['away']['name']}")
    print(f"      Horário: {f['fixture']['date']}")
    print(f"      Status: {f['fixture']['status']['long']}\n")

print("✅ Importação concluída!")
EOF
```

---

## 🔍 VERIFICAR SE DEU CERTO

Depois de importar, verifique quantos jogos foram salvos:

```bash
cd backend
source venv/bin/activate

python << 'EOF'
import sqlite3
conn = sqlite3.connect('football_analytics_dev.db')
cursor = conn.cursor()

# Contar jogos por liga
cursor.execute("""
    SELECT league, COUNT(*) as total
    FROM matches
    GROUP BY league
    ORDER BY total DESC
    LIMIT 15
""")

print("\n📊 JOGOS NO BANCO DE DADOS:\n")
for row in cursor.fetchall():
    print(f"  {row[1]:>5} jogos - {row[0]}")

cursor.execute("SELECT COUNT(*) FROM matches")
total = cursor.fetchone()[0]
print(f"\n  TOTAL: {total} jogos\n")

conn.close()
EOF
```

---

## 🎯 EXEMPLO COMPLETO - IMPORTAR LA LIGA

Comando completo para importar La Liga:

```bash
cd backend
source venv/bin/activate

python << 'EOF'
from app.services.api_football_service import APIFootballService

print("🇪🇸 Importando La Liga (Espanha)...")

api = APIFootballService()

# League ID 140 = La Liga
# Temporadas: 2023 e 2024
for season in [2023, 2024]:
    print(f"\n📅 Temporada {season}/{season+1}")

    fixtures = api.get_fixtures(league=140, season=season)
    print(f"  ✅ {len(fixtures)} jogos importados")

print("\n✅ La Liga importada com sucesso!")
EOF

# Verificar
python << 'EOF'
import sqlite3
conn = sqlite3.connect('football_analytics_dev.db')
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM matches WHERE league LIKE '%La Liga%'")
count = cursor.fetchone()[0]
print(f"\n📊 Total de jogos de La Liga no banco: {count}\n")
conn.close()
EOF
```

---

## ❓ PROBLEMAS COMUNS

### **Erro: "API Key inválida"**

Verifique se a chave está correta no `.env`:

```bash
cat .env | grep API_FOOTBALL_KEY
```

### **Erro: "Rate limit exceeded"**

Você usou as 100 requisições diárias do plano gratuito. Aguarde 24h ou faça upgrade.

### **Erro: "No fixtures found"**

A liga pode não ter jogos na temporada. Tente outra temporada (2023, 2024, 2025).

### **Nenhum jogo foi importado**

Verifique se o script rodou sem erros:

```bash
python import_historical_data.py 2>&1 | tee import.log
cat import.log
```

---

## 📝 CHECKLIST RÁPIDO

- [ ] ✅ Configurei API_FOOTBALL_KEY no `.env`
- [ ] ✅ Editei LEAGUES_TO_IMPORT no script
- [ ] ✅ Executei `python import_historical_data.py`
- [ ] ✅ Verifiquei que os jogos foram salvos no banco
- [ ] ✅ Testei endpoint `/all-markets` com um jogo importado

---

## 🎬 PRÓXIMOS PASSOS

Depois de importar as ligas:

1. **Gerar predictions em massa:**
   ```bash
   python generate_predictions_batch.py --days 7
   ```

2. **Testar o sistema:**
   - Acesse: http://localhost:3000/predictions
   - Click em "Modo Automático"
   - Veja as predictions aprovadas pela AI

---

## 💡 DICAS

**Importar só jogos futuros (próximos 30 dias):**

```python
from datetime import datetime, timedelta
from app.services.api_football_service import APIFootballService

api = APIFootballService()
today = datetime.now().strftime('%Y-%m-%d')
future = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')

# Buscar jogos entre hoje e daqui 30 dias
fixtures = api.get_fixtures(league=140, from_date=today, to_date=future)
print(f"Jogos futuros: {len(fixtures)}")
```

**Importar múltiplas ligas de uma vez:**

```python
LEAGUES = {
    "La Liga": 140,
    "Serie A": 135,
    "Champions": 2,
}

for name, league_id in LEAGUES.items():
    print(f"Importando {name}...")
    fixtures = api.get_fixtures(league=league_id, season=2024)
    print(f"  ✅ {len(fixtures)} jogos")
```

---

**🚀 Pronto! Agora você pode importar qualquer liga facilmente!**
