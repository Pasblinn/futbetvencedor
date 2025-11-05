#!/usr/bin/env python3
"""
🔮 PUXAR JOGOS FUTUROS COM TODOS OS MERCADOS
Foca em predictions para o futuro com odds de múltiplos mercados
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import requests
from datetime import datetime, timedelta
from sqlalchemy import and_
from app.core.database import SessionLocal
from app.models import Match, Team, Odds

class UpcomingMatchesFetcher:
    """Busca jogos futuros com todos os mercados disponíveis"""

    def __init__(self):
        self.db = SessionLocal()
        self.api_key = "c3c86901a78a8c5d15d7cbfc15e6d18a"
        self.base_url = "https://v3.football.api-sports.io"

        # Mercados disponíveis na API
        self.markets = [
            'Match Winner',           # 1X2
            'Goals Over/Under',       # O/U 0.5, 1.5, 2.5, 3.5, 4.5
            'Both Teams Score',       # BTTS
            'Double Chance',          # 1X, 12, X2
            'Asian Handicap',         # AH
            'European Handicap',      # EH
            'Exact Score',            # Resultado exato
            'First Half Winner',      # HT 1X2
            'Second Half Winner',     # 2H 1X2
            'Home Goals',             # Gols casa
            'Away Goals',             # Gols fora
        ]

        # Top ligas para focar
        self.top_leagues = [
            39,   # Premier League
            140,  # La Liga
            78,   # Bundesliga
            135,  # Serie A
            61,   # Ligue 1
            94,   # Primeira Liga (Portugal)
            71,   # Brasileirão
            128,  # Liga Argentina
            2,    # Champions League
            3,    # Europa League
        ]

    def get_or_create_team(self, team_data):
        """Busca ou cria time"""
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

    def fetch_upcoming_matches(self, days_ahead=7):
        """Buscar jogos dos próximos N dias"""
        print(f"🔮 BUSCANDO JOGOS FUTUROS - PRÓXIMOS {days_ahead} DIAS\n")
        print("="*80)

        today = datetime.now().date()
        end_date = today + timedelta(days=days_ahead)

        total_matches = 0
        total_odds_fetched = 0

        # Buscar jogos por liga
        for league_id in self.top_leagues:
            print(f"\n🏆 Liga ID: {league_id}")

            # Buscar jogos da liga
            url = f"{self.base_url}/fixtures"
            params = {
                'league': league_id,
                'season': 2024,  # Football season year
                'from': today.isoformat(),
                'to': end_date.isoformat()
            }

            headers = {
                'x-rapidapi-host': 'v3.football.api-sports.io',
                'x-rapidapi-key': self.api_key
            }

            try:
                response = requests.get(url, headers=headers, params=params, timeout=10)
                data = response.json()

                if data.get('response'):
                    fixtures = data['response']
                    print(f"   📅 {len(fixtures)} jogos encontrados")

                    for fixture in fixtures[:20]:  # Limitar para não exceder rate limit
                        match_data = self.process_fixture(fixture)
                        if match_data:
                            total_matches += 1

                            # Buscar odds para este jogo
                            odds_count = self.fetch_odds_for_match(fixture['fixture']['id'], match_data)
                            total_odds_fetched += odds_count

                else:
                    print(f"   ⚠️  Sem dados")

            except Exception as e:
                print(f"   ❌ Erro: {e}")
                continue

        print("\n" + "="*80)
        print("📊 RESUMO")
        print("="*80)
        print(f"✅ {total_matches} jogos futuros adicionados")
        print(f"💰 {total_odds_fetched} conjuntos de odds coletados")
        print(f"🎯 {len(self.markets)} mercados monitorados")

        return {
            'total_matches': total_matches,
            'total_odds': total_odds_fetched,
            'markets': len(self.markets)
        }

    def process_fixture(self, fixture):
        """Processar dados do jogo"""
        fixture_id = str(fixture['fixture']['id'])

        # Verificar se jogo já existe
        existing = self.db.query(Match).filter(Match.external_id == fixture_id).first()
        if existing:
            return existing

        # Criar times
        home_team = self.get_or_create_team(fixture['teams']['home'])
        away_team = self.get_or_create_team(fixture['teams']['away'])

        # Criar jogo
        match_date = datetime.fromisoformat(fixture['fixture']['date'].replace('Z', '+00:00'))

        match = Match(
            external_id=fixture_id,
            home_team_id=home_team.id,
            away_team_id=away_team.id,
            league_id=None,  # Criar league se necessário
            match_date=match_date,
            status='NS',
            round_number=fixture['league'].get('round'),
            venue=fixture['fixture']['venue'].get('name') if fixture['fixture'].get('venue') else None
        )

        self.db.add(match)
        self.db.commit()
        self.db.refresh(match)

        print(f"   ✅ {home_team.name} vs {away_team.name} - {match_date.strftime('%d/%m %H:%M')}")

        return match

    def fetch_odds_for_match(self, fixture_id, match):
        """Buscar odds de todos os mercados para um jogo"""
        url = f"{self.base_url}/odds"
        params = {
            'fixture': fixture_id,
            'bookmaker': 8  # Bet365
        }

        headers = {
            'x-rapidapi-host': 'v3.football.api-sports.io',
            'x-rapidapi-key': self.api_key
        }

        odds_count = 0

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            data = response.json()

            if data.get('response') and len(data['response']) > 0:
                bookmaker_data = data['response'][0]['bookmakers']

                if bookmaker_data and len(bookmaker_data) > 0:
                    bets = bookmaker_data[0]['bets']

                    for bet in bets:
                        market_name = bet['name']

                        # Match Winner (1X2)
                        if market_name == 'Match Winner' and len(bet['values']) == 3:
                            home_odds = float(bet['values'][0]['odd'])
                            draw_odds = float(bet['values'][1]['odd'])
                            away_odds = float(bet['values'][2]['odd'])

                            odds = Odds(
                                match_id=match.id,
                                home_win=home_odds,
                                draw=draw_odds,
                                away_win=away_odds,
                                bookmaker='Bet365',
                                market='1X2',
                                odds_timestamp=datetime.now()
                            )
                            self.db.add(odds)
                            odds_count += 1

                        # Over/Under
                        elif 'Over/Under' in market_name:
                            for value in bet['values']:
                                if 'Over' in value['value']:
                                    line = value['value'].split()[-1]  # Ex: "2.5"
                                    over_odds = float(value['odd'])

                                    # Buscar Under correspondente
                                    under = next((v for v in bet['values'] if f'Under {line}' in v['value']), None)
                                    if under:
                                        under_odds = float(under['odd'])

                                        odds = Odds(
                                            match_id=match.id,
                                            over_under=float(line),
                                            over_odds=over_odds,
                                            under_odds=under_odds,
                                            bookmaker='Bet365',
                                            market=f'O/U {line}',
                                            odds_timestamp=datetime.now()
                                        )
                                        self.db.add(odds)
                                        odds_count += 1
                                        break

                        # BTTS (Both Teams Score)
                        elif 'Both Teams Score' in market_name and len(bet['values']) == 2:
                            yes_odds = float(bet['values'][0]['odd']) if 'Yes' in bet['values'][0]['value'] else float(bet['values'][1]['odd'])
                            no_odds = float(bet['values'][1]['odd']) if 'No' in bet['values'][1]['value'] else float(bet['values'][0]['odd'])

                            odds = Odds(
                                match_id=match.id,
                                btts_yes=yes_odds,
                                btts_no=no_odds,
                                bookmaker='Bet365',
                                market='BTTS',
                                odds_timestamp=datetime.now()
                            )
                            self.db.add(odds)
                            odds_count += 1

                    if odds_count > 0:
                        self.db.commit()
                        print(f"      💰 {odds_count} mercados com odds")

        except Exception as e:
            print(f"      ⚠️  Erro ao buscar odds: {e}")

        return odds_count


if __name__ == "__main__":
    print("🔮 SISTEMA DE COLETA - JOGOS FUTUROS\n")

    fetcher = UpcomingMatchesFetcher()

    # Buscar jogos dos próximos 7 dias
    stats = fetcher.fetch_upcoming_matches(days_ahead=7)

    print("\n" + "="*80)
    print("✅ COLETA CONCLUÍDA!")
    print("="*80)
    print(f"🎯 Foco: JOGOS FUTUROS para predictions ML")
    print(f"📊 {stats['total_matches']} jogos | {stats['total_odds']} odds | {stats['markets']} mercados")
