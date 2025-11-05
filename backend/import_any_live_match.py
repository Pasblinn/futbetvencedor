#!/usr/bin/env python3
"""
Script para importar qualquer jogo ao vivo disponível
Busca em todas as ligas e importa o primeiro encontrado
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

def get_or_create_team(team_data: dict, league: str, db: Session) -> Team:
    """Busca ou cria um time no banco de dados"""
    external_id = str(team_data['id'])
    team = db.query(Team).filter(Team.external_id == external_id).first()

    if team:
        return team

    team = Team(
        external_id=external_id,
        name=team_data['name'],
        country=team_data.get('country', 'Unknown'),
        league=league,
        logo_url=team_data.get('logo', '')
    )
    db.add(team)
    db.commit()
    db.refresh(team)
    return team

def buscar_qualquer_jogo_ao_vivo():
    """Busca qualquer jogo ao vivo disponível"""
    print("🔍 Buscando jogos ao vivo em TODAS as ligas...")

    response = requests.get(
        f"{BASE_URL}/fixtures",
        headers=HEADERS,
        params={"live": "all"}
    )

    if response.status_code != 200:
        print(f"❌ Erro ao buscar jogos: {response.status_code}")
        return None

    data = response.json()
    fixtures = data.get('response', [])

    print(f"✅ Encontrados {len(fixtures)} jogos ao vivo total")

    if not fixtures:
        print("⚠️ Nenhum jogo ao vivo no momento")
        return None

    # Mostrar primeiros 10 jogos
    print("\n📋 Jogos ao vivo disponíveis:\n")
    for i, fixture in enumerate(fixtures[:10], 1):
        home = fixture['teams']['home']['name']
        away = fixture['teams']['away']['name']
        league = fixture['league']['name']
        status = fixture['fixture']['status']['short']
        elapsed = fixture['fixture']['status']['elapsed']

        print(f"  {i}. {home} vs {away}")
        print(f"     Liga: {league}")
        print(f"     Status: {status} ({elapsed}')")
        print()

    # Retornar o primeiro
    return fixtures[0]

def importar_jogo(fixture, db: Session):
    """Importa jogo para o banco de dados"""
    print(f"\n📥 Importando jogo...")

    league_name = fixture['league']['name']
    home_team = get_or_create_team(fixture['teams']['home'], league_name, db)
    away_team = get_or_create_team(fixture['teams']['away'], league_name, db)

    existing = db.query(Match).filter(
        Match.external_id == str(fixture['fixture']['id'])
    ).first()

    if existing:
        match = existing
        print(f"⚠️ Jogo já existe (ID: {match.id}). Atualizando...")
    else:
        match = Match()

    match.external_id = str(fixture['fixture']['id'])
    match.league = league_name
    match.home_team_id = home_team.id
    match.away_team_id = away_team.id
    match.match_date = datetime.fromisoformat(fixture['fixture']['date'].replace('Z', '+00:00'))
    match.venue = fixture['fixture']['venue']['name'] if fixture['fixture']['venue'] else 'Unknown'
    match.status = fixture['fixture']['status']['short']
    match.minute = fixture['fixture']['status']['elapsed']

    if fixture['goals']['home'] is not None:
        match.home_score = fixture['goals']['home']
    if fixture['goals']['away'] is not None:
        match.away_score = fixture['goals']['away']

    if not existing:
        db.add(match)

    db.commit()
    db.refresh(match)

    print(f"✅ Jogo importado! ID: {match.id}")
    print(f"   {home_team.name} {match.home_score or 0} x {match.away_score or 0} {away_team.name}")
    print(f"   Liga: {match.league}")
    print(f"   Status: {match.status} ({match.minute}')")

    return match

def main():
    print("=" * 60)
    print("🏆 IMPORTAÇÃO DE JOGO AO VIVO (QUALQUER LIGA)")
    print("=" * 60)

    fixture = buscar_qualquer_jogo_ao_vivo()

    if not fixture:
        print("\n❌ Nenhum jogo ao vivo disponível no momento")
        print("💡 Tente novamente em alguns minutos quando houver jogos ao vivo")
        return

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
