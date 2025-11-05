#!/bin/bash
# Script para rodar coleta histórica em background

cd /home/pablintadini/mododeus/football-analytics/backend

source venv/bin/activate

# Executar com yes para auto-confirmar
echo "" | python collect_all_historical.py 2>&1 | tee logs/historical_collection.log
