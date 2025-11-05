#!/usr/bin/env python3
"""
Script para buscar dados reais de jogos usando as APIs
"""
import requests
import json
import sys
from datetime import datetime, timedelta
import os

# Adicionar app ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.core.config import settings

# API Keys from .env
FOOTBALL_DATA_API_KEY = settings.FOOTBALL_DATA_API_KEY
ODDS_API_KEY = settings.ODDS_API_KEY
API_SPORTS_KEY = settings.API_SPORTS_KEY

if not FOOTBALL_DATA_API_KEY or not ODDS_API_KEY or not API_SPORTS_KEY:
    raise ValueError("Uma ou mais API keys não estão configuradas. Configure no arquivo .env")

def fetch_football_data_api(endpoint):
    """Fetch data from Football-Data.org API"""
    headers = {
        'X-Auth-Token': FOOTBALL_DATA_API_KEY
    }
    url = f"https://api.football-data.org/v4/{endpoint}"

    try:
        response = requests.get(url, headers=headers)
        print(f"Football-Data API Status: {response.status_code}")
        print(f"URL: {url}")

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error response: {response.text}")
            return None
    except Exception as e:
        print(f"Football-Data API Error: {e}")
        return None

def fetch_api_sports(endpoint):
    """Fetch data from API-Sports"""
    headers = {
        'X-RapidAPI-Key': API_SPORTS_KEY,
        'X-RapidAPI-Host': 'v3.football.api-sports.io'
    }
    url = f"https://v3.football.api-sports.io/{endpoint}"

    try:
        response = requests.get(url, headers=headers)
        print(f"API-Sports Status: {response.status_code}")
        print(f"URL: {url}")

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error response: {response.text}")
            return None
    except Exception as e:
        print(f"API-Sports Error: {e}")
        return None

def search_flamengo_recent_matches():
    """Search for recent Flamengo matches"""
    print("🔥 BUSCANDO JOGOS DO FLAMENGO...")

    # Try Football-Data API first
    print("\n--- Tentando Football-Data.org ---")

    # Search for Copa Libertadores (competition ID: CLI)
    libertadores_data = fetch_football_data_api("competitions/CLI/matches")
    if libertadores_data:
        print(f"Libertadores matches found: {len(libertadores_data.get('matches', []))}")

        # Look for Flamengo matches in recent days
        recent_matches = []
        for match in libertadores_data.get('matches', []):
            home_team = match.get('homeTeam', {}).get('name', '') or ''
            away_team = match.get('awayTeam', {}).get('name', '') or ''

            if 'Flamengo' in home_team or 'Flamengo' in away_team or \
               'CR Flamengo' in home_team or 'CR Flamengo' in away_team:
                recent_matches.append(match)
                print(f"  Found: {home_team} vs {away_team} - {match.get('utcDate', '')}")

        print(f"Flamengo Libertadores matches: {len(recent_matches)}")
        return recent_matches[:3]  # Return last 3 matches

    # Try API-Sports if Football-Data doesn't work
    print("\n--- Tentando API-Sports ---")

    # Search for Flamengo team ID and recent matches
    flamengo_data = fetch_api_sports("fixtures?team=127&last=5")  # Flamengo team ID
    if flamengo_data:
        print("API-Sports Flamengo data retrieved")
        return flamengo_data.get('response', [])

    return None

def search_bayern_today():
    """Search for Bayern matches today"""
    print("⚽ BUSCANDO JOGO DO BAYERN HOJE...")

    today = datetime.now().strftime('%Y-%m-%d')

    # Try Football-Data API
    print("\n--- Tentando Football-Data.org ---")

    # Bundesliga competition ID: BL1
    bundesliga_data = fetch_football_data_api(f"competitions/BL1/matches?dateFrom={today}&dateTo={today}")
    if bundesliga_data:
        bayern_matches = []
        for match in bundesliga_data.get('matches', []):
            if 'Bayern' in match.get('homeTeam', {}).get('name', '') or \
               'Bayern' in match.get('awayTeam', {}).get('name', ''):
                bayern_matches.append(match)

        if bayern_matches:
            print(f"Bayern matches today: {len(bayern_matches)}")
            return bayern_matches

    # Try API-Sports
    print("\n--- Tentando API-Sports ---")

    bayern_data = fetch_api_sports(f"fixtures?team=157&date={today}")  # Bayern team ID
    if bayern_data:
        print("API-Sports Bayern data retrieved")
        return bayern_data.get('response', [])

    return None

def main():
    print("🚀 INICIANDO BUSCA DE DADOS REAIS...")
    print("=" * 50)

    # Search Flamengo matches
    flamengo_matches = search_flamengo_recent_matches()
    if flamengo_matches:
        print(f"\n✅ FLAMENGO: Encontrados {len(flamengo_matches)} jogos")

        # Save to file
        with open('/tmp/app/flamengo_matches.json', 'w') as f:
            json.dump(flamengo_matches, f, indent=2, default=str)
        print("📁 Dados salvos em /tmp/app/flamengo_matches.json")
    else:
        print("\n❌ FLAMENGO: Nenhum jogo encontrado")

    # Search Bayern matches
    bayern_matches = search_bayern_today()
    if bayern_matches:
        print(f"\n✅ BAYERN: Encontrados {len(bayern_matches)} jogos")

        # Save to file
        with open('/tmp/app/bayern_matches.json', 'w') as f:
            json.dump(bayern_matches, f, indent=2, default=str)
        print("📁 Dados salvos em /tmp/app/bayern_matches.json")
    else:
        print("\n❌ BAYERN: Nenhum jogo encontrado")

    print("\n🎯 BUSCA CONCLUÍDA!")

if __name__ == "__main__":
    main()