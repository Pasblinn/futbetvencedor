#!/usr/bin/env python3
"""
Coletar TODOS os mercados de odds disponíveis da Bet365 para os jogos atuais
"""
import asyncio
import httpx
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.config import settings
from app.models import Match, Odds

# API-Football PRO
API_KEY = settings.API_SPORTS_KEY
if not API_KEY:
    raise ValueError("API_SPORTS_KEY não configurada. Configure no arquivo .env")
BASE_URL = 'https://v3.football.api-sports.io'
HEADERS = {'x-apisports-key': API_KEY}


async def fetch_all_markets_for_fixture(fixture_id: int):
    """Busca TODOS os mercados de odds da Bet365 para um fixture"""
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


def save_all_markets_to_db(db: Session, match: Match, odds_data: list):
    """Salva TODOS os mercados disponíveis no banco"""
    if not odds_data:
        print(f"⚠️  Sem odds para match {match.id}")
        return

    markets_saved = []

    for odds_response in odds_data:
        bookmakers = odds_response.get('bookmakers', [])

        for bookmaker in bookmakers:
            if bookmaker['name'] != 'Bet365':
                continue

            for bet in bookmaker.get('bets', []):
                bet_name = bet['name']
                bet_id = bet['id']
                values = bet.get('values', [])

                print(f"   📊 Mercado: {bet_name} (ID: {bet_id})")

                # Verificar se já existe
                existing = db.query(Odds).filter(
                    Odds.match_id == match.id,
                    Odds.bookmaker == 'Bet365',
                    Odds.market == bet_name
                ).first()

                if bet_name == 'Match Winner':
                    # 1X2
                    odds_dict = {v['value']: float(v['odd']) for v in values}

                    if existing:
                        existing.home_win = odds_dict.get('Home')
                        existing.draw = odds_dict.get('Draw')
                        existing.away_win = odds_dict.get('Away')
                        existing.updated_at = datetime.utcnow()
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
                        markets_saved.append('1X2')

                    print(f"      💰 {odds_dict.get('Home')} / {odds_dict.get('Draw')} / {odds_dict.get('Away')}")

                elif bet_name == 'Double Chance':
                    # Dupla Chance
                    odds_dict = {v['value']: float(v['odd']) for v in values}

                    if not existing:
                        new_odds = Odds(
                            match_id=match.id,
                            bookmaker='Bet365',
                            market='Dupla Chance',
                            home_win=odds_dict.get('Home/Draw'),
                            draw=odds_dict.get('Home/Away'),
                            away_win=odds_dict.get('Draw/Away'),
                            odds_timestamp=datetime.utcnow(),
                            is_active=True
                        )
                        db.add(new_odds)
                        markets_saved.append('Dupla Chance')

                    print(f"      💰 1X: {odds_dict.get('Home/Draw')} | 12: {odds_dict.get('Home/Away')} | X2: {odds_dict.get('Draw/Away')}")

                elif bet_name == 'Both Teams Score':
                    # BTTS
                    odds_dict = {v['value']: float(v['odd']) for v in values}

                    if existing:
                        existing.btts_yes = odds_dict.get('Yes')
                        existing.btts_no = odds_dict.get('No')
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
                        markets_saved.append('BTTS')

                    print(f"      💰 Sim: {odds_dict.get('Yes')} | Não: {odds_dict.get('No')}")

                elif bet_name == 'Goals Over/Under':
                    # Over/Under para cada linha
                    for value in values:
                        line = value['value']
                        odd = float(value['odd'])

                        if 'Over' in line:
                            if '0.5' in line:
                                market_name = 'Over/Under 0.5'
                            elif '1.5' in line:
                                market_name = 'Over/Under 1.5'
                            elif '2.5' in line:
                                market_name = 'Over/Under 2.5'
                            elif '3.5' in line:
                                market_name = 'Over/Under 3.5'
                            elif '4.5' in line:
                                market_name = 'Over/Under 4.5'
                            else:
                                continue

                            existing_ou = db.query(Odds).filter(
                                Odds.match_id == match.id,
                                Odds.bookmaker == 'Bet365',
                                Odds.market == market_name
                            ).first()

                            if existing_ou:
                                existing_ou.over_2_5 = odd
                            else:
                                new_odds = Odds(
                                    match_id=match.id,
                                    bookmaker='Bet365',
                                    market=market_name,
                                    over_2_5=odd,
                                    odds_timestamp=datetime.utcnow(),
                                    is_active=True
                                )
                                db.add(new_odds)
                                markets_saved.append(market_name)

                            print(f"      💰 {line}: {odd}")

                        elif 'Under' in line:
                            if '0.5' in line:
                                market_name = 'Over/Under 0.5'
                            elif '1.5' in line:
                                market_name = 'Over/Under 1.5'
                            elif '2.5' in line:
                                market_name = 'Over/Under 2.5'
                            elif '3.5' in line:
                                market_name = 'Over/Under 3.5'
                            elif '4.5' in line:
                                market_name = 'Over/Under 4.5'
                            else:
                                continue

                            existing_ou = db.query(Odds).filter(
                                Odds.match_id == match.id,
                                Odds.bookmaker == 'Bet365',
                                Odds.market == market_name
                            ).first()

                            if existing_ou:
                                existing_ou.under_2_5 = odd
                            else:
                                new_odds = Odds(
                                    match_id=match.id,
                                    bookmaker='Bet365',
                                    market=market_name,
                                    under_2_5=odd,
                                    odds_timestamp=datetime.utcnow(),
                                    is_active=True
                                )
                                db.add(new_odds)

                            print(f"      💰 {line}: {odd}")

                elif 'Asian Handicap' in bet_name:
                    # Handicap Asiático
                    for value in values:
                        line = value['value']
                        odd = float(value['odd'])
                        print(f"      💰 {line}: {odd}")

                    # Salvar primeiro handicap encontrado
                    if values and not existing:
                        new_odds = Odds(
                            match_id=match.id,
                            bookmaker='Bet365',
                            market='Handicap Asiático',
                            asian_handicap_line=float(values[0]['value'].split(':')[0]) if ':' in values[0]['value'] else 0,
                            home_win=float(values[0]['odd']) if values else None,
                            odds_timestamp=datetime.utcnow(),
                            is_active=True
                        )
                        db.add(new_odds)
                        markets_saved.append('Handicap Asiático')

                elif 'Exact Score' in bet_name or 'Correct Score' in bet_name:
                    # Placar Exato
                    print(f"      💰 Placar Exato disponível com {len(values)} opções")

                    if values and not existing:
                        # Salvar os 3 placares mais prováveis
                        top_scores = sorted(values, key=lambda x: float(x['odd']))[:3]
                        new_odds = Odds(
                            match_id=match.id,
                            bookmaker='Bet365',
                            market='Placar Exato',
                            odds_timestamp=datetime.utcnow(),
                            is_active=True
                        )
                        db.add(new_odds)
                        markets_saved.append('Placar Exato')

                else:
                    # Outros mercados (Corners, Cards, etc)
                    print(f"      ℹ️  {len(values)} opções disponíveis")

    db.commit()
    print(f"   ✅ Mercados salvos: {', '.join(set(markets_saved)) if markets_saved else 'nenhum novo'}")


async def main():
    """Main execution"""
    db = SessionLocal()

    try:
        # Buscar todos os jogos válidos (futuros e ao vivo)
        all_matches = db.query(Match).filter(
            Match.status.in_(['NS', 'TBD', 'SCHEDULED', 'LIVE', 'HT', '1H', '2H']),
            Match.external_id.isnot(None)
        ).order_by(Match.match_date).all()

        # Filtrar apenas jogos com external_id numérico (da API real)
        matches = []
        for match in all_matches:
            try:
                int(match.external_id)
                matches.append(match)
            except ValueError:
                continue

        print(f"📊 Encontrados {len(matches)} jogos para coletar mercados\n")

        for i, match in enumerate(matches, 1):
            print(f"\n[{i}/{len(matches)}] {match.home_team} vs {match.away_team}")
            print(f"   📅 {match.match_date.strftime('%d/%m/%Y %H:%M')} | External ID: {match.external_id}")

            # Buscar todos os mercados
            odds_data = await fetch_all_markets_for_fixture(int(match.external_id))

            if odds_data:
                save_all_markets_to_db(db, match, odds_data)
            else:
                print(f"   ❌ Sem dados de odds da API")

            # Rate limiting
            await asyncio.sleep(1.5)

        print("\n✅ COLETA CONCLUÍDA!")

        # Mostrar resumo
        total_odds = db.query(Odds).filter(Odds.bookmaker == 'Bet365').count()
        markets = db.query(Odds.market).filter(Odds.bookmaker == 'Bet365').distinct().all()

        print(f"\n📊 RESUMO:")
        print(f"   Total de registros de odds: {total_odds}")
        print(f"   Mercados únicos coletados: {len(markets)}")
        print(f"\n   Mercados disponíveis:")
        for market in markets:
            count = db.query(Odds).filter(Odds.market == market[0], Odds.bookmaker == 'Bet365').count()
            print(f"      - {market[0]}: {count} jogos")

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
