#!/usr/bin/env python3
"""
Script para importar jogo ao vivo da API-Sports
Racing Club x Independiente Rivadavia - Liga Professional Argentina
"""
import requests
import sys
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.config import settings
from app.models.match import Match
from app.models.odds import Odds
from app.models.team import Team

API_KEY = settings.API_SPORTS_KEY
if not API_KEY:
    raise ValueError("API_SPORTS_KEY não configurada. Configure no arquivo .env")
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

def buscar_jogos_ao_vivo_argentina():
    """Busca jogos ao vivo da Liga Professional Argentina"""
    print("🔍 Buscando jogos ao vivo da Argentina...")

    # Liga Professional Argentina - ID 128
    response = requests.get(
        f"{BASE_URL}/fixtures",
        headers=HEADERS,
        params={
            "league": 128,  # Liga Professional Argentina
            "season": 2025,
            "live": "all"  # Todos os jogos ao vivo
        }
    )

    if response.status_code != 200:
        print(f"❌ Erro ao buscar jogos: {response.status_code}")
        print(response.text)
        return None

    data = response.json()
    fixtures = data.get('response', [])

    print(f"✅ Encontrados {len(fixtures)} jogos ao vivo")

    # Procurar Racing Club x Independiente Rivadavia
    for fixture in fixtures:
        home_team = fixture['teams']['home']['name']
        away_team = fixture['teams']['away']['name']

        print(f"  - {home_team} vs {away_team}")

        if 'Racing' in home_team and 'Rivadavia' in away_team:
            print(f"\n🎯 Jogo encontrado: {home_team} vs {away_team}")
            return fixture

    print(f"\n⚠️ Jogo Racing x Rivadavia não encontrado ao vivo")
    if fixtures:
        print("Retornando primeiro jogo ao vivo encontrado:")
        fixture = fixtures[0]
        print(f"  {fixture['teams']['home']['name']} vs {fixture['teams']['away']['name']}")
        return fixture

    return None

def get_or_create_team(team_data: dict, league: str, db: Session) -> Team:
    """Busca ou cria um time no banco de dados"""
    external_id = str(team_data['id'])

    # Tentar encontrar pelo external_id
    team = db.query(Team).filter(Team.external_id == external_id).first()

    if team:
        return team

    # Criar novo time
    team = Team(
        external_id=external_id,
        name=team_data['name'],
        country='Argentina',  # Liga Argentina
        league=league,
        logo_url=team_data.get('logo', '')
    )

    db.add(team)
    db.commit()
    db.refresh(team)

    print(f"  ✅ Time criado: {team.name} (ID: {team.id})")
    return team

def buscar_odds(fixture_id: int):
    """Busca odds do jogo"""
    print(f"💰 Buscando odds do jogo {fixture_id}...")

    response = requests.get(
        f"{BASE_URL}/odds",
        headers=HEADERS,
        params={
            "fixture": fixture_id,
            "bookmaker": 8  # Bet365
        }
    )

    if response.status_code != 200:
        print(f"⚠️ Erro ao buscar odds: {response.status_code}")
        return None

    data = response.json()
    odds_data = data.get('response', [])

    if odds_data and len(odds_data) > 0:
        print(f"✅ Odds encontradas!")
        return odds_data[0]

    return None

def importar_jogo(fixture, db: Session):
    """Importa jogo para o banco de dados"""
    print(f"\n📥 Importando jogo para o banco...")

    # Buscar ou criar times
    league_name = fixture['league']['name']
    home_team = get_or_create_team(fixture['teams']['home'], league_name, db)
    away_team = get_or_create_team(fixture['teams']['away'], league_name, db)

    # Verificar se já existe
    existing = db.query(Match).filter(
        Match.external_id == str(fixture['fixture']['id'])
    ).first()

    if existing:
        print(f"⚠️ Jogo já existe (ID: {existing.id}). Atualizando...")
        match = existing
    else:
        match = Match()

    # Preencher dados do jogo
    match.external_id = str(fixture['fixture']['id'])
    match.league = league_name
    match.home_team_id = home_team.id
    match.away_team_id = away_team.id
    match.match_date = datetime.fromisoformat(fixture['fixture']['date'].replace('Z', '+00:00'))
    match.venue = fixture['fixture']['venue']['name'] if fixture['fixture']['venue'] else 'Unknown'
    match.status = fixture['fixture']['status']['short']

    # Placar (se disponível)
    if fixture['goals']['home'] is not None:
        match.home_score = fixture['goals']['home']
    if fixture['goals']['away'] is not None:
        match.away_score = fixture['goals']['away']

    if not existing:
        db.add(match)

    db.commit()
    db.refresh(match)

    print(f"✅ Jogo importado! ID: {match.id}")
    print(f"   {match.home_team} {match.home_score or 0} x {match.away_score or 0} {match.away_team}")
    print(f"   Status: {match.status}")

    # Buscar e importar odds
    odds_data = buscar_odds(fixture['fixture']['id'])

    if odds_data:
        importar_odds(match.id, odds_data, db)

    return match

def importar_odds(match_id: int, odds_data: dict, db: Session):
    """Importa odds do jogo"""
    print(f"💰 Importando odds...")

    bookmaker_data = odds_data.get('bookmakers', [])
    if not bookmaker_data:
        print("⚠️ Nenhuma odd encontrada")
        return

    bet365 = bookmaker_data[0]

    for bet in bet365.get('bets', []):
        bet_name = bet['name']
        values = bet['values']

        # Criar ou atualizar odd
        existing_odd = db.query(Odds).filter(
            Odds.match_id == match_id,
            Odds.market == bet_name
        ).first()

        if existing_odd:
            odd = existing_odd
        else:
            odd = Odds(
                match_id=match_id,
                bookmaker='Bet365',
                market=bet_name,
                odds_timestamp=datetime.now()
            )

        # 1X2 Market
        if bet_name == 'Match Winner':
            for value in values:
                if value['value'] == 'Home':
                    odd.home_win = float(value['odd'])
                elif value['value'] == 'Draw':
                    odd.draw = float(value['odd'])
                elif value['value'] == 'Away':
                    odd.away_win = float(value['odd'])

        # Over/Under
        elif 'Over/Under' in bet_name:
            for value in values:
                if value['value'] == 'Over':
                    if '2.5' in bet_name:
                        odd.over_2_5 = float(value['odd'])
                    elif '1.5' in bet_name:
                        odd.over_1_5 = float(value['odd'])
                    elif '3.5' in bet_name:
                        odd.over_3_5 = float(value['odd'])
                elif value['value'] == 'Under':
                    if '2.5' in bet_name:
                        odd.under_2_5 = float(value['odd'])
                    elif '1.5' in bet_name:
                        odd.under_1_5 = float(value['odd'])
                    elif '3.5' in bet_name:
                        odd.under_3_5 = float(value['odd'])

        # BTTS
        elif 'Both Teams Score' in bet_name:
            for value in values:
                if value['value'] == 'Yes':
                    odd.btts_yes = float(value['odd'])
                elif value['value'] == 'No':
                    odd.btts_no = float(value['odd'])

        if not existing_odd:
            db.add(odd)

    db.commit()
    print(f"✅ Odds importadas!")

def main():
    print("=" * 60)
    print("🏆 IMPORTAÇÃO DE JOGO AO VIVO")
    print("=" * 60)

    # Buscar jogo ao vivo
    fixture = buscar_jogos_ao_vivo_argentina()

    if not fixture:
        print("\n❌ Nenhum jogo ao vivo encontrado")
        return

    # Importar para banco
    db = SessionLocal()
    try:
        match = importar_jogo(fixture, db)

        print("\n" + "=" * 60)
        print("✅ IMPORTAÇÃO CONCLUÍDA!")
        print("=" * 60)
        print(f"\n🎮 Teste a integração em:")
        print(f"   Backend:  http://localhost:8000/api/v1/live/stats")
        print(f"   Frontend: http://localhost:3001/live-matches")
        print()

    finally:
        db.close()

if __name__ == "__main__":
    main()
