#!/usr/bin/env python3
"""
🌎 IMPORTAR JOGOS DAS ELIMINATÓRIAS DE HOJE
Busca jogos das eliminatórias da Copa do Mundo para 09/10/2025
"""
import asyncio
from datetime import datetime
from app.services.api_football_service import APIFootballService
from app.core.database import get_db_session
from app.models import Match, Team
from sqlalchemy import or_

async def main():
    print("=" * 80)
    print("🌎 IMPORTANDO JOGOS DAS ELIMINATÓRIAS - 09/10/2025")
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

        # Filtrar apenas eliminatórias
        qualifiers = [
            f for f in fixtures
            if 'World Cup' in f['league']['name'] or 'Qualif' in f['league']['name']
        ]

        print(f"🌎 {len(qualifiers)} jogos de eliminatórias encontrados\n")

        if len(qualifiers) == 0:
            print("⚠️  Nenhum jogo de eliminatórias encontrado para hoje")
            print("Vou buscar TODOS os jogos do dia e importar:")
            qualifiers = fixtures[:20]  # Limitar a 20 jogos

        imported = 0
        for fixture in qualifiers:
            try:
                fixture_id = fixture['fixture']['id']

                # Verificar se já existe
                existing = db.query(Match).filter(
                    Match.external_id == str(fixture_id)
                ).first()

                if existing:
                    print(f"  ⏭️  Já existe: {fixture['teams']['home']['name']} vs {fixture['teams']['away']['name']}")
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

                print(f"  ✅ {fixture['league']['name']}: {home_team.name} vs {away_team.name}")
                print(f"      Horário: {match_date.strftime('%d/%m %H:%M')}")

            except Exception as e:
                print(f"  ❌ Erro ao importar jogo: {e}")
                continue

        db.commit()
        db.close()

        print(f"\n✅ IMPORTAÇÃO CONCLUÍDA!")
        print(f"   📥 {imported} jogos importados")
        print("=" * 80)

    except Exception as e:
        print(f"❌ Erro: {e}")
        db.rollback()
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
