#!/usr/bin/env python3
"""
⚡ COLETOR DE JOGOS AO VIVO
Busca jogos AO VIVO de QUALQUER liga com odds reais da Bet365
"""

import asyncio
import httpx
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.database import engine, SessionLocal, Base
from app.models import Match, Team, Odds

# Criar todas as tabelas
Base.metadata.create_all(bind=engine)

API_KEY = '417697345fe23e648c0a462b39d319af'
BASE_URL = 'https://v3.football.api-sports.io'

HEADERS = {
    'X-RapidAPI-Key': API_KEY,
    'X-RapidAPI-Host': 'v3.football.api-sports.io'
}

async def fetch_live_matches():
    """Busca TODOS os jogos AO VIVO"""
    print("⚡ Buscando jogos AO VIVO...")

    url = f"{BASE_URL}/fixtures"
    params = {'live': 'all'}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=HEADERS, params=params)

        if response.status_code == 200:
            data = response.json()
            fixtures = data.get('response', [])
            print(f"✅ {len(fixtures)} jogos AO VIVO encontrados!")
            return fixtures
        else:
            print(f"❌ Erro: {response.status_code}")
            print(f"Response: {response.text}")
            return []

async def fetch_odds_for_fixture(fixture_id: int):
    """Busca odds da Bet365 para um fixture"""
    print(f"💰 Buscando odds para fixture {fixture_id}...")

    url = f"{BASE_URL}/odds"
    params = {
        'fixture': fixture_id,
        'bookmaker': 8  # Bet365
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=HEADERS, params=params)

        if response.status_code == 200:
            data = response.json()
            odds_data = data.get('response', [])

            if odds_data and len(odds_data) > 0:
                print(f"✅ Odds encontradas!")
                return odds_data[0]
            else:
                print(f"⚠️ Sem odds")
                return None
        else:
            return None

def get_or_create_team(db: Session, team_data: dict):
    """Busca ou cria um time"""
    team_id = team_data['id']
    team_name = team_data['name']

    team = db.query(Team).filter(Team.external_id == str(team_id)).first()

    if not team:
        team = Team(
            external_id=str(team_id),
            name=team_name,
            country=team_data.get('country', 'Unknown')
        )
        db.add(team)
        db.commit()
        db.refresh(team)
        print(f"✨ Time criado: {team_name}")

    return team

def save_match_and_odds(db: Session, fixture_data: dict, odds_data: dict = None):
    """Salva match e odds no banco"""

    fixture = fixture_data['fixture']
    teams = fixture_data['teams']
    league = fixture_data['league']
    score = fixture_data.get('goals', {})

    fixture_id = fixture['id']
    match_date_str = fixture['date']
    match_date = datetime.fromisoformat(match_date_str.replace('Z', '+00:00'))
    status = fixture['status']['short']

    home_team = get_or_create_team(db, teams['home'])
    away_team = get_or_create_team(db, teams['away'])

    existing_match = db.query(Match).filter(Match.external_id == str(fixture_id)).first()

    if existing_match:
        # Atualizar placar se ao vivo
        if score.get('home') is not None:
            existing_match.home_score = score['home']
        if score.get('away') is not None:
            existing_match.away_score = score['away']
        existing_match.status = status
        existing_match.minute = fixture['status'].get('elapsed')
        db.commit()
        match = existing_match
        print(f"📝 Match atualizado: {home_team.name} {score.get('home', 0)} x {score.get('away', 0)} {away_team.name}")
    else:
        match = Match(
            external_id=str(fixture_id),
            home_team_id=home_team.id,
            away_team_id=away_team.id,
            league=str(league['id']),
            season='2025',
            match_date=match_date,
            venue=fixture.get('venue', {}).get('name', ''),
            status=status,
            home_score=score.get('home'),
            away_score=score.get('away'),
            minute=fixture['status'].get('elapsed')
        )
        db.add(match)
        db.commit()
        db.refresh(match)
        print(f"✨ Match criado: {home_team.name} vs {away_team.name}")

    # Processar odds
    if odds_data:
        bookmaker_data = odds_data.get('bookmakers', [])

        if bookmaker_data and len(bookmaker_data) > 0:
            bet365_data = bookmaker_data[0]
            bets = bet365_data.get('bets', [])

            for bet in bets:
                if bet.get('name') == 'Match Winner':
                    values = bet.get('values', [])

                    odds_map = {}
                    for value in values:
                        val_name = value.get('value', '')
                        odd = float(value.get('odd', 0))

                        if val_name == 'Home':
                            odds_map['home_win'] = odd
                        elif val_name == 'Draw':
                            odds_map['draw'] = odd
                        elif val_name == 'Away':
                            odds_map['away_win'] = odd

                    if len(odds_map) == 3:
                        existing_odds = db.query(Odds).filter(
                            Odds.match_id == match.id,
                            Odds.bookmaker == 'Bet365',
                            Odds.market == '1X2'
                        ).first()

                        if existing_odds:
                            existing_odds.home_win = odds_map['home_win']
                            existing_odds.draw = odds_map['draw']
                            existing_odds.away_win = odds_map['away_win']
                            existing_odds.odds_timestamp = datetime.now()
                            print(f"📊 Odds LIVE: {odds_map['home_win']} / {odds_map['draw']} / {odds_map['away_win']}")
                        else:
                            odds = Odds(
                                match_id=match.id,
                                bookmaker='Bet365',
                                market='1X2',
                                home_win=odds_map['home_win'],
                                draw=odds_map['draw'],
                                away_win=odds_map['away_win'],
                                odds_timestamp=datetime.now(),
                                is_active=True
                            )
                            db.add(odds)
                            print(f"✨ Odds: {odds_map['home_win']} / {odds_map['draw']} / {odds_map['away_win']}")

                        db.commit()
                        break

    return match

async def main():
    """Main"""
    print("=" * 60)
    print("⚡ BUSCANDO JOGOS AO VIVO - QUALQUER LIGA")
    print("=" * 60)

    fixtures = await fetch_live_matches()

    if not fixtures:
        print("❌ Nenhum jogo ao vivo agora")
        return

    db = SessionLocal()
    processed = 0

    try:
        for fixture_data in fixtures[:15]:  # Limitar a 15 jogos
            fixture_id = fixture_data['fixture']['id']
            home_team = fixture_data['teams']['home']['name']
            away_team = fixture_data['teams']['away']['name']
            league_name = fixture_data['league']['name']
            score = fixture_data.get('goals', {})
            minute = fixture_data['fixture']['status'].get('elapsed', 0)

            print(f"\n{'=' * 60}")
            print(f"⚡ LIVE ({minute}'): {home_team} {score.get('home', 0)} x {score.get('away', 0)} {away_team}")
            print(f"🏆 {league_name}")
            print(f"{'=' * 60}")

            # Buscar odds
            await asyncio.sleep(1)
            odds_data = await fetch_odds_for_fixture(fixture_id)

            # Salvar
            match = save_match_and_odds(db, fixture_data, odds_data)
            processed += 1

            print(f"✅ Match ID: {match.id}")

        print(f"\n{'=' * 60}")
        print(f"✅ COLETA CONCLUÍDA - {processed} jogos AO VIVO processados")
        print(f"{'=' * 60}")

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
