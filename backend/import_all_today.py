#!/usr/bin/env python3
"""
🔥 IMPORTAR TODOS OS JOGOS DE HOJE - 09/10/2025
Importa todos os jogos disponíveis para testar Live Matches
"""
import asyncio
from datetime import datetime
from app.services.api_football_service import APIFootballService
from app.core.database import get_db_session
from app.models import Match, Team

async def main():
    print("=" * 80)
    print("🔥 IMPORTANDO TODOS OS JOGOS DE HOJE - 09/10/2025")
    print("=" * 80)

    api = APIFootballService()
    db = get_db_session()

    # Data de hoje
    target_date = datetime(2025, 10, 9)
    date_str = target_date.strftime('%Y-%m-%d')

    print(f"\n📅 Buscando jogos para: {date_str}")

    try:
        # Buscar todos os jogos do dia
        fixtures = await api.get_fixtures_by_date(date=date_str)

        print(f"📥 {len(fixtures)} jogos encontrados para {date_str}")
        print(f"🚀 Importando TODOS os jogos...\n")

        imported = 0
        skipped = 0

        for fixture in fixtures:
            try:
                fixture_id = fixture['fixture']['id']

                # Verificar se já existe
                existing = db.query(Match).filter(
                    Match.external_id == str(fixture_id)
                ).first()

                if existing:
                    skipped += 1
                    continue

                # Buscar ou criar times
                home_team_data = fixture['teams']['home']
                away_team_data = fixture['teams']['away']

                home_team = db.query(Team).filter(
                    Team.external_id == str(home_team_data['id'])
                ).first()

                if not home_team:
                    home_team = Team(
                        external_id=str(home_team_data['id']),
                        name=home_team_data['name'],
                        logo_url=home_team_data.get('logo')
                    )
                    db.add(home_team)
                    db.flush()

                away_team = db.query(Team).filter(
                    Team.external_id == str(away_team_data['id'])
                ).first()

                if not away_team:
                    away_team = Team(
                        external_id=str(away_team_data['id']),
                        name=away_team_data['name'],
                        logo_url=away_team_data.get('logo')
                    )
                    db.add(away_team)
                    db.flush()

                # Criar match
                match_date = datetime.fromisoformat(fixture['fixture']['date'].replace('Z', '+00:00'))

                new_match = Match(
                    external_id=str(fixture_id),
                    home_team_id=home_team.id,
                    away_team_id=away_team.id,
                    league=fixture['league']['name'],
                    season='2025',
                    match_date=match_date,
                    venue=fixture['fixture'].get('venue', {}).get('name'),
                    status='NS'
                )

                db.add(new_match)
                imported += 1

                if imported % 10 == 0:
                    print(f"  ✅ {imported} jogos importados...")

            except Exception as e:
                print(f"  ❌ Erro ao importar jogo {fixture_id}: {e}")
                continue

        db.commit()
        db.close()

        print(f"\n✅ IMPORTAÇÃO CONCLUÍDA!")
        print(f"   📥 {imported} jogos importados")
        print(f"   ⏭️  {skipped} jogos já existiam")
        print(f"   📊 Total: {imported + skipped} jogos")
        print("=" * 80)

    except Exception as e:
        print(f"❌ Erro: {e}")
        db.rollback()
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
