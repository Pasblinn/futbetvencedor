#!/usr/bin/env python3
"""
🔴 ATUALIZAR JOGOS AO VIVO AGORA - API-Sports
Busca jogos ao vivo + odds reais + atualiza predictions
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sqlalchemy import and_, or_

from app.core.database import SessionLocal
from app.models.match import Match
from app.models.team import Team
from app.models.odds import Odds
from app.models.prediction import Prediction
from app.models.statistics import MatchStatistics

load_dotenv()

class LiveMatchUpdater:
    """Atualizador de jogos ao vivo com API-Sports"""

    def __init__(self):
        self.db = SessionLocal()
        self.api_key = os.getenv('API_SPORTS_KEY')
        self.base_url = os.getenv('API_SPORTS_BASE_URL', 'https://v3.football.api-sports.io')
        self.headers = {
            'x-rapidapi-key': self.api_key,
            'x-rapidapi-host': 'v3.football.api-sports.io'
        }

        # IDs das principais ligas
        self.leagues = {
            'Premier League': 39,
            'La Liga': 140,
            'Bundesliga': 78,
            'Serie A': 135,
            'Ligue 1': 61,
            'Brasileirão': 71
        }

    def fetch_live_matches(self):
        """Buscar jogos AO VIVO agora"""
        print("🔴 Buscando jogos AO VIVO na API-Sports...")

        url = f"{self.base_url}/fixtures"
        params = {'live': 'all'}  # TODOS os jogos ao vivo

        response = requests.get(url, headers=self.headers, params=params)

        if response.status_code != 200:
            print(f"❌ Erro API: {response.status_code}")
            return []

        data = response.json()
        live_matches = data.get('response', [])

        print(f"✅ {len(live_matches)} jogos AO VIVO encontrados!")
        return live_matches

    def fetch_todays_matches(self):
        """Buscar TODOS os jogos de hoje (ao vivo + agendados)"""
        print("\n📅 Buscando TODOS os jogos de hoje...")

        today = datetime.now().strftime('%Y-%m-%d')
        all_matches = []

        # Buscar por liga
        for league_name, league_id in self.leagues.items():
            url = f"{self.base_url}/fixtures"
            params = {
                'league': league_id,
                'date': today,
                'season': 2024
            }

            response = requests.get(url, headers=self.headers, params=params)

            if response.status_code == 200:
                data = response.json()
                matches = data.get('response', [])
                all_matches.extend(matches)
                if matches:
                    print(f"   ✅ {league_name}: {len(matches)} jogos")

        print(f"\n✅ Total: {len(all_matches)} jogos de hoje")
        return all_matches

    def fetch_odds(self, fixture_id):
        """Buscar odds REAIS para um jogo"""
        url = f"{self.base_url}/odds"
        params = {
            'fixture': fixture_id,
            'bookmaker': 1  # Bet365
        }

        response = requests.get(url, headers=self.headers, params=params)

        if response.status_code == 200:
            data = response.json()
            odds_data = data.get('response', [])

            if odds_data and odds_data[0].get('bookmakers'):
                bookmaker = odds_data[0]['bookmakers'][0]
                for bet in bookmaker.get('bets', []):
                    if bet['name'] == 'Match Winner':
                        values = bet['values']
                        return {
                            'home': float(values[0]['odd']) if len(values) > 0 else 2.5,
                            'draw': float(values[1]['odd']) if len(values) > 1 else 3.2,
                            'away': float(values[2]['odd']) if len(values) > 2 else 2.8
                        }

        return None

    def get_or_create_team(self, team_data):
        """Obter ou criar time no DB"""
        team_id = str(team_data['id'])

        team = self.db.query(Team).filter(Team.external_id == team_id).first()

        if not team:
            team = Team(
                external_id=team_id,
                name=team_data['name'],
                short_name=team_data.get('code', team_data['name'][:3].upper()),
                country='Unknown',
                logo_url=team_data.get('logo')
            )
            self.db.add(team)
            self.db.commit()
            self.db.refresh(team)

        return team

    def update_match(self, fixture_data):
        """Atualizar ou criar match no DB"""
        fixture_id = str(fixture_data['fixture']['id'])

        # Obter ou criar times
        home_team = self.get_or_create_team(fixture_data['teams']['home'])
        away_team = self.get_or_create_team(fixture_data['teams']['away'])

        # Buscar match existente
        match = self.db.query(Match).filter(Match.external_id == fixture_id).first()

        # Status mapping
        status_map = {
            'NS': 'SCHEDULED',
            'TBD': 'SCHEDULED',
            '1H': 'LIVE',
            'HT': 'LIVE',
            '2H': 'LIVE',
            'ET': 'LIVE',
            'P': 'LIVE',
            'FT': 'FT',
            'AET': 'FT',
            'PEN': 'FT'
        }

        status = status_map.get(fixture_data['fixture']['status']['short'], 'SCHEDULED')

        # Dados do match
        match_data = {
            'external_id': fixture_id,
            'home_team_id': home_team.id,
            'away_team_id': away_team.id,
            'league': fixture_data['league']['name'],
            'match_date': datetime.fromisoformat(fixture_data['fixture']['date'].replace('Z', '+00:00')),
            'status': status,
            'home_score': fixture_data['goals']['home'],
            'away_score': fixture_data['goals']['away']
        }

        if match:
            # Atualizar match existente
            for key, value in match_data.items():
                setattr(match, key, value)
            action = "Atualizado"
        else:
            # Criar novo match
            match = Match(**match_data)
            self.db.add(match)
            action = "Criado"

        self.db.commit()
        self.db.refresh(match)

        # Buscar e salvar ODDS REAIS
        odds_data = self.fetch_odds(fixture_id)

        if odds_data:
            existing_odds = self.db.query(Odds).filter(
                Odds.match_id == match.id,
                Odds.market == '1X2'
            ).first()

            if existing_odds:
                existing_odds.home_win = odds_data['home']
                existing_odds.draw = odds_data['draw']
                existing_odds.away_win = odds_data['away']
                existing_odds.odds_timestamp = datetime.now()
                existing_odds.updated_at = datetime.now()
            else:
                new_odds = Odds(
                    match_id=match.id,
                    home_win=odds_data['home'],
                    draw=odds_data['draw'],
                    away_win=odds_data['away'],
                    bookmaker='Bet365',
                    market='1X2',
                    odds_timestamp=datetime.now()
                )
                self.db.add(new_odds)

            self.db.commit()
            odds_str = f"H:{odds_data['home']:.2f} D:{odds_data['draw']:.2f} A:{odds_data['away']:.2f}"
        else:
            odds_str = "N/A"

        # Status info
        status_emoji = "🔴" if status == "LIVE" else "📅" if status == "SCHEDULED" else "✅"
        score = f"{match.home_score or 0}-{match.away_score or 0}" if status != "SCHEDULED" else "vs"

        print(f"   {status_emoji} {action}: {home_team.name} {score} {away_team.name}")
        print(f"      Odds: {odds_str} | Status: {status}")

        return match

    def run(self):
        """Executar atualização completa"""
        print("🚀 ATUALIZANDO JOGOS E ODDS AGORA!\n")
        print("="*70)

        # 1. Jogos AO VIVO
        live_matches = self.fetch_live_matches()
        for fixture in live_matches:
            self.update_match(fixture)

        # 2. Todos os jogos de hoje
        today_matches = self.fetch_todays_matches()
        for fixture in today_matches:
            self.update_match(fixture)

        print("\n" + "="*70)
        print(f"✅ CONCLUÍDO!")
        print(f"   🔴 Jogos ao vivo processados: {len(live_matches)}")
        print(f"   📅 Jogos de hoje processados: {len(today_matches)}")
        print("="*70)


if __name__ == "__main__":
    updater = LiveMatchUpdater()
    updater.run()
