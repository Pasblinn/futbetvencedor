#!/usr/bin/env python3
"""
Script simples para buscar dados reais - respeitando rate limits
"""
import requests
import json
import sys
import os
from datetime import datetime

# Adicionar app ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.core.config import settings

# API Keys
FOOTBALL_DATA_API_KEY = settings.FOOTBALL_DATA_API_KEY
if not FOOTBALL_DATA_API_KEY:
    raise ValueError("FOOTBALL_DATA_API_KEY não configurada. Configure no arquivo .env")

def fetch_one_request(endpoint):
    """Fazer apenas 1 request por vez"""
    headers = {'X-Auth-Token': FOOTBALL_DATA_API_KEY}
    url = f"https://api.football-data.org/v4/{endpoint}"

    try:
        print(f"🔍 Request: {url}")
        response = requests.get(url, headers=headers)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Data keys: {list(data.keys())}")
            return data
        else:
            print(f"❌ Error: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

def main():
    print("🚀 BUSCANDO DADOS REAIS - 1 REQUEST POR VEZ")

    # Primeiro: buscar competições para ver IDs disponíveis
    print("\n1️⃣ Buscando competições disponíveis...")
    competitions = fetch_one_request("competitions")

    if competitions:
        # Salvar dados
        with open('/tmp/app/competitions.json', 'w') as f:
            json.dump(competitions, f, indent=2)
        print("📁 Salvo em /tmp/app/competitions.json")

        # Mostrar algumas competições relevantes
        print("\n🏆 Competições encontradas:")
        for comp in competitions.get('competitions', [])[:10]:
            print(f"  {comp.get('code', 'N/A')}: {comp.get('name', 'N/A')}")

if __name__ == "__main__":
    main()