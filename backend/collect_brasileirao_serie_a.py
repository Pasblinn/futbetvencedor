"""
Coletar jogos da Série A do Brasileirão 2025 (rodada 04-05 outubro)
"""
import asyncio
import httpx
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.database import engine, SessionLocal, Base
from app.core.config import settings
from app.models import Match, Team, Odds

Base.metadata.create_all(bind=engine)

# API-Football PRO (7500 requests/day)
API_KEY = settings.API_SPORTS_KEY
if not API_KEY:
    raise ValueError("API_SPORTS_KEY não configurada. Configure no arquivo .env")
BASE_URL = 'https://v3.football.api-sports.io'
HEADERS = {
    'x-apisports-key': API_KEY
}

# Brasil Série A = league_id 71
SERIE_A_LEAGUE_ID = 71


async def fetch_serie_a_upcoming():
    """Busca próximos jogos da Série A"""

    # 1️⃣ Tentar buscar próximos jogos (independente de temporada)
    print(f"🔍 Buscando próximos jogos da Série A...")
    url = f"{BASE_URL}/fixtures"
    params = {
        'league': SERIE_A_LEAGUE_ID,
        'next': 20  # Próximos 20 jogos
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(url, headers=HEADERS, params=params)
        data = response.json()

        if response.status_code == 200:
            fixtures = data.get('response', [])
            if fixtures:
                season = fixtures[0]['league']['season']
                print(f"✅ Encontrados {len(fixtures)} jogos futuros da Série A (temporada {season})")
                return fixtures, season

    # 2️⃣ Se não encontrou, tentar por temporadas específicas
    print("⚠️ Tentando buscar por temporadas...")
    for season in [2024, 2025, 2023]:
        params = {
            'league': SERIE_A_LEAGUE_ID,
            'season': season
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url, headers=HEADERS, params=params)
            data = response.json()

            if response.status_code == 200:
                fixtures = data.get('response', [])
                if fixtures:
                    print(f"✅ Encontrados {len(fixtures)} jogos na temporada {season}")
                    # Pegar últimos 20 jogos
                    return fixtures[-20:], season

    print("❌ Nenhum fixture encontrado")
    return [], None


async def fetch_odds_for_fixture(fixture_id: int):
    """Busca odds da Bet365 para um fixture"""
    url = f"{BASE_URL}/odds"
    params = {
        'fixture': fixture_id,
        'bookmaker': 8  # Bet365
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(url, headers=HEADERS, params=params)
        data = response.json()

        if response.status_code != 200 or not data.get('response'):
            return None

        return data.get('response', [])


def save_match_to_db(db: Session, fixture_data: dict, season: int):
    """Salva ou atualiza partida no banco"""
    fixture = fixture_data['fixture']
    teams = fixture_data['teams']
    league = fixture_data['league']

    # Verificar se já existe
    existing = db.query(Match).filter(Match.external_id == str(fixture['id'])).first()

    if existing:
        # Atualizar status
        existing.status = fixture['status']['short']
        existing.match_date = datetime.fromisoformat(fixture['date'].replace('Z', '+00:00'))
        db.commit()
        print(f"♻️  Match {existing.id} atualizado: {teams['home']['name']} vs {teams['away']['name']}")
        return existing

    # Criar novo
    new_match = Match(
        external_id=str(fixture['id']),
        home_team=teams['home']['name'],
        away_team=teams['away']['name'],
        league=league['name'],
        season=str(season),
        match_date=datetime.fromisoformat(fixture['date'].replace('Z', '+00:00')),
        status=fixture['status']['short'],
        venue=fixture.get('venue', {}).get('name', 'Unknown'),
        round=league.get('round', 'Regular Season')
    )

    db.add(new_match)
    db.commit()
    db.refresh(new_match)

    print(f"✅ Match {new_match.id} criado: {teams['home']['name']} vs {teams['away']['name']}")
    return new_match


async def save_odds_to_db(db: Session, match: Match, odds_data: list):
    """Salva odds da Bet365 no banco"""
    if not odds_data:
        print(f"⚠️  Sem odds para match {match.id}")
        return

    for odds_response in odds_data:
        bookmakers = odds_response.get('bookmakers', [])

        for bookmaker in bookmakers:
            if bookmaker['name'] != 'Bet365':
                continue

            for bet in bookmaker.get('bets', []):
                bet_name = bet['name']
                values = bet.get('values', [])

                # Verificar se já existe odds para esse match
                existing_odds = db.query(Odds).filter(
                    Odds.match_id == match.id,
                    Odds.bookmaker == 'Bet365',
                    Odds.market == bet_name
                ).first()

                if bet_name == 'Match Winner':
                    # 1X2
                    odds_dict = {v['value']: float(v['odd']) for v in values}

                    if existing_odds:
                        existing_odds.home_win = odds_dict.get('Home')
                        existing_odds.draw = odds_dict.get('Draw')
                        existing_odds.away_win = odds_dict.get('Away')
                        existing_odds.updated_at = datetime.utcnow()
                    else:
                        new_odds = Odds(
                            match_id=match.id,
                            bookmaker='Bet365',
                            market='1X2',
                            home_win=odds_dict.get('Home'),
                            draw=odds_dict.get('Draw'),
                            away_win=odds_dict.get('Away'),
                            odds_timestamp=datetime.utcnow(),
                            is_active=True
                        )
                        db.add(new_odds)

                    print(f"   💰 1X2: {odds_dict.get('Home')} / {odds_dict.get('Draw')} / {odds_dict.get('Away')}")

                elif bet_name == 'Goals Over/Under':
                    # Over/Under
                    for value in values:
                        line = value['value']
                        odd = float(value['odd'])

                        if 'Over' in line:
                            if '2.5' in line:
                                if existing_odds:
                                    existing_odds.over_2_5 = odd
                                else:
                                    new_odds = Odds(
                                        match_id=match.id,
                                        bookmaker='Bet365',
                                        market='Over/Under 2.5',
                                        over_2_5=odd,
                                        odds_timestamp=datetime.utcnow(),
                                        is_active=True
                                    )
                                    db.add(new_odds)
                        elif 'Under' in line:
                            if '2.5' in line:
                                if existing_odds:
                                    existing_odds.under_2_5 = odd

                elif bet_name == 'Both Teams Score':
                    # BTTS
                    odds_dict = {v['value']: float(v['odd']) for v in values}

                    if existing_odds:
                        existing_odds.btts_yes = odds_dict.get('Yes')
                        existing_odds.btts_no = odds_dict.get('No')
                    else:
                        new_odds = Odds(
                            match_id=match.id,
                            bookmaker='Bet365',
                            market='BTTS',
                            btts_yes=odds_dict.get('Yes'),
                            btts_no=odds_dict.get('No'),
                            odds_timestamp=datetime.utcnow(),
                            is_active=True
                        )
                        db.add(new_odds)

    db.commit()


async def main():
    """Main execution"""
    db = SessionLocal()

    try:
        # 1️⃣ Buscar fixtures da Série A
        fixtures, season = await fetch_serie_a_upcoming()

        if not fixtures or not season:
            print("❌ Nenhum fixture encontrado para Série A")
            return

        # Filtrar apenas jogos dos dias 04 e 05 de outubro de 2025
        print("\n🎯 Filtrando jogos de 04-05 de outubro de 2025...")
        target_fixtures = []

        for fixture in fixtures:
            match_date = datetime.fromisoformat(fixture['fixture']['date'].replace('Z', '+00:00'))

            # Verificar se é dia 04 ou 05 de outubro de 2025
            if match_date.year == 2025 and match_date.month == 10 and match_date.day in [4, 5]:
                target_fixtures.append(fixture)
                print(f"   ✅ {fixture['teams']['home']['name']} vs {fixture['teams']['away']['name']} - {match_date.strftime('%d/%m/%Y %H:%M')}")

        if not target_fixtures:
            print("⚠️ Nenhum jogo encontrado para 04-05/10/2025")
            print("📋 Mostrando próximos jogos disponíveis:")

            for fixture in fixtures[:10]:
                match_date = datetime.fromisoformat(fixture['fixture']['date'].replace('Z', '+00:00'))
                print(f"   - {fixture['teams']['home']['name']} vs {fixture['teams']['away']['name']} - {match_date.strftime('%d/%m/%Y %H:%M')}")

            # Processar os próximos jogos disponíveis
            print("\n🔄 Processando próximos jogos disponíveis...")
            target_fixtures = fixtures[:10]

        print(f"\n📊 Total de jogos a processar: {len(target_fixtures)}")

        # 2️⃣ Processar cada fixture
        for i, fixture_data in enumerate(target_fixtures, 1):
            fixture_id = fixture_data['fixture']['id']
            home = fixture_data['teams']['home']['name']
            away = fixture_data['teams']['away']['name']
            match_date = datetime.fromisoformat(fixture_data['fixture']['date'].replace('Z', '+00:00'))

            print(f"\n[{i}/{len(target_fixtures)}] {home} vs {away}")
            print(f"   📅 {match_date.strftime('%d/%m/%Y %H:%M')}")

            # Salvar match
            match = save_match_to_db(db, fixture_data, season)

            # Buscar e salvar odds
            odds_data = await fetch_odds_for_fixture(fixture_id)
            await save_odds_to_db(db, match, odds_data)

            # Rate limiting
            await asyncio.sleep(1.5)

        print("\n✅ PROCESSO CONCLUÍDO!")
        print(f"📊 Total de jogos processados: {len(target_fixtures)}")

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
