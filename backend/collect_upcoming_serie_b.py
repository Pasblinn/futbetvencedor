#!/usr/bin/env python3
"""
🔥 COLETOR DE JOGOS FUTUROS - SÉRIE B
Busca próximos jogos da Série B com odds reais da Bet365
"""

import asyncio
import httpx
import os
from datetime import datetime, timedelta
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

SERIE_B_ID = 72  # Brasileirão Série B
SERIE_A_ID = 71  # Brasileirão Série A

async def fetch_upcoming_fixtures(league_id: int, days: int = 7):
    """Busca próximos jogos de uma liga"""
    print(f"🔍 Buscando próximos {days} dias de jogos (liga {league_id})...")

    today = datetime.now().strftime('%Y-%m-%d')
    future = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')

    url = f"{BASE_URL}/fixtures"
    params = {
        'league': league_id,
        'season': 2025,
        'from': today,
        'to': future,
        'timezone': 'America/Sao_Paulo'
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=HEADERS, params=params)

        if response.status_code == 200:
            data = response.json()
            fixtures = data.get('response', [])
            print(f"✅ Encontrados {len(fixtures)} jogos futuros")
            return fixtures
        else:
            print(f"❌ Erro ao buscar fixtures: {response.status_code}")
            print(f"Response: {response.text}")
            return []

async def fetch_odds_for_fixture(fixture_id: int):
    """Busca odds da Bet365 para um fixture"""
    print(f"💰 Buscando odds para fixture {fixture_id}...")

    url = f"{BASE_URL}/odds"
    params = {
        'fixture': fixture_id,
        'bookmaker': 8  # Bet365 = bookmaker_id 8
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=HEADERS, params=params)

        if response.status_code == 200:
            data = response.json()
            odds_data = data.get('response', [])

            if odds_data and len(odds_data) > 0:
                print(f"✅ Odds encontradas para fixture {fixture_id}")
                return odds_data[0]  # Primeira (Bet365)
            else:
                print(f"⚠️ Sem odds para fixture {fixture_id}")
                return None
        else:
            print(f"❌ Erro ao buscar odds: {response.status_code}")
            return None

def get_or_create_team(db: Session, team_data: dict):
    """Busca ou cria um time"""
    team_id = team_data['id']
    team_name = team_data['name']

    # Buscar time existente
    team = db.query(Team).filter(Team.external_id == str(team_id)).first()

    if not team:
        # Criar novo time
        team = Team(
            external_id=str(team_id),
            name=team_name,
            country=team_data.get('country', 'Brazil')
        )
        db.add(team)
        db.commit()
        db.refresh(team)
        print(f"✨ Time criado: {team_name}")

    return team

def save_match_and_odds(db: Session, fixture_data: dict, odds_data: dict = None):
    """Salva match e odds no banco"""

    # Extrair dados do fixture
    fixture = fixture_data['fixture']
    teams = fixture_data['teams']
    league = fixture_data['league']

    fixture_id = fixture['id']
    match_date_str = fixture['date']
    match_date = datetime.fromisoformat(match_date_str.replace('Z', '+00:00'))
    status = fixture['status']['short']

    home_team_data = teams['home']
    away_team_data = teams['away']

    # Buscar/criar times
    home_team = get_or_create_team(db, home_team_data)
    away_team = get_or_create_team(db, away_team_data)

    # Verificar se match já existe
    existing_match = db.query(Match).filter(Match.external_id == str(fixture_id)).first()

    if existing_match:
        match = existing_match
        print(f"📝 Match já existe: {home_team.name} vs {away_team.name}")
    else:
        # Criar novo match
        match = Match(
            external_id=str(fixture_id),
            home_team_id=home_team.id,
            away_team_id=away_team.id,
            league=str(league['id']),
            season='2025',
            match_date=match_date,
            venue=fixture.get('venue', {}).get('name', ''),
            status=status
        )
        db.add(match)
        db.commit()
        db.refresh(match)
        print(f"✨ Match criado: {home_team.name} vs {away_team.name} - {match_date.strftime('%d/%m %H:%M')}")

    # Processar odds se disponíveis
    if odds_data:
        bookmaker_data = odds_data.get('bookmakers', [])

        if bookmaker_data and len(bookmaker_data) > 0:
            bet365_data = bookmaker_data[0]
            bets = bet365_data.get('bets', [])

            # Buscar mercado 1X2 (Match Winner)
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
                        # Verificar se odds já existem
                        existing_odds = db.query(Odds).filter(
                            Odds.match_id == match.id,
                            Odds.bookmaker == 'Bet365',
                            Odds.market == '1X2'
                        ).first()

                        if existing_odds:
                            # Atualizar odds existentes
                            existing_odds.home_win = odds_map['home_win']
                            existing_odds.draw = odds_map['draw']
                            existing_odds.away_win = odds_map['away_win']
                            existing_odds.odds_timestamp = datetime.now()
                            print(f"📊 Odds atualizadas: {odds_map['home_win']} / {odds_map['draw']} / {odds_map['away_win']}")
                        else:
                            # Criar novas odds
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
                            print(f"✨ Odds criadas: {odds_map['home_win']} / {odds_map['draw']} / {odds_map['away_win']}")

                        db.commit()
                        break

    return match

async def main():
    """Main function"""
    print("=" * 60)
    print("🔥 INICIANDO COLETA - PRÓXIMOS JOGOS")
    print("=" * 60)

    # Tentar Série B primeiro
    fixtures = await fetch_upcoming_fixtures(SERIE_B_ID, days=14)

    if not fixtures or len(fixtures) == 0:
        print("\n⚠️ Nenhum jogo na Série B, tentando Série A...")
        fixtures = await fetch_upcoming_fixtures(SERIE_A_ID, days=7)

    if not fixtures:
        print("❌ Nenhum jogo encontrado")
        return

    db = SessionLocal()
    processed = 0

    try:
        for fixture_data in fixtures[:10]:  # Limitar a 10 jogos
            fixture_id = fixture_data['fixture']['id']
            home_team = fixture_data['teams']['home']['name']
            away_team = fixture_data['teams']['away']['name']
            match_date = fixture_data['fixture']['date']

            print(f"\n{'=' * 60}")
            print(f"🏆 {home_team} vs {away_team}")
            print(f"📅 {match_date}")
            print(f"{'=' * 60}")

            # Buscar odds
            await asyncio.sleep(1)  # Rate limiting
            odds_data = await fetch_odds_for_fixture(fixture_id)

            # Salvar no banco
            match = save_match_and_odds(db, fixture_data, odds_data)
            processed += 1

            print(f"✅ Processado: Match ID {match.id}")

        print(f"\n{'=' * 60}")
        print(f"✅ COLETA CONCLUÍDA - {processed} jogos processados")
        print(f"{'=' * 60}")

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
