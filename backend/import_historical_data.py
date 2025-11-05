#!/usr/bin/env python3
"""
📊 IMPORTAÇÃO HISTÓRICA DE DADOS
Importa jogos de Agosto/2025 até hoje para análise na página History
Executa em batches para não sobrecarregar a API
"""
import asyncio
from datetime import datetime, timedelta
from app.services.api_football_service import APIFootballService
from app.core.database import get_db_session
from app.models import Match, Team
import time

async def import_matches_for_date_range(start_date: datetime, end_date: datetime):
    """Importa matches em um range de datas"""
    api = APIFootballService()
    db = get_db_session()

    total_imported = 0
    total_skipped = 0
    total_errors = 0

    current_date = start_date

    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        print(f"\n📅 Processando {date_str}...")

        try:
            # Buscar jogos do dia
            fixtures = await api.get_fixtures_by_date(date=date_str)
            print(f"   📥 {len(fixtures)} jogos encontrados")

            day_imported = 0
            day_skipped = 0

            for fixture in fixtures:
                try:
                    fixture_id = fixture['fixture']['id']

                    # Verificar se já existe
                    existing = db.query(Match).filter(
                        Match.external_id == str(fixture_id)
                    ).first()

                    if existing:
                        day_skipped += 1
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
                    match_date = datetime.fromisoformat(
                        fixture['fixture']['date'].replace('Z', '+00:00')
                    )

                    # Extrair scores se o jogo já terminou
                    home_score = None
                    away_score = None
                    status = fixture['fixture']['status']['short']

                    if status in ['FT', 'AET', 'PEN']:
                        home_score = fixture['goals']['home']
                        away_score = fixture['goals']['away']

                    new_match = Match(
                        external_id=str(fixture_id),
                        home_team_id=home_team.id,
                        away_team_id=away_team.id,
                        league=fixture['league']['name'],
                        season='2025',
                        match_date=match_date,
                        venue=fixture['fixture'].get('venue', {}).get('name'),
                        status=status,
                        home_score=home_score,
                        away_score=away_score
                    )

                    db.add(new_match)
                    day_imported += 1

                    # Commit a cada 10 jogos
                    if day_imported % 10 == 0:
                        db.commit()

                except Exception as e:
                    print(f"   ❌ Erro ao importar jogo {fixture_id}: {e}")
                    total_errors += 1
                    continue

            # Commit final do dia
            db.commit()

            total_imported += day_imported
            total_skipped += day_skipped

            print(f"   ✅ {day_imported} importados, {day_skipped} já existiam")

            # Sleep de 1 segundo entre dias para não sobrecarregar a API
            time.sleep(1)

        except Exception as e:
            print(f"   ❌ Erro ao processar {date_str}: {e}")
            db.rollback()

        # Próximo dia
        current_date += timedelta(days=1)

    db.close()

    return {
        "imported": total_imported,
        "skipped": total_skipped,
        "errors": total_errors
    }

async def main():
    print("=" * 80)
    print("📊 IMPORTAÇÃO HISTÓRICA DE DADOS")
    print("Período: Agosto/2025 até Hoje")
    print("=" * 80)

    # Data de início: 1º de agosto de 2025
    start_date = datetime(2025, 8, 1)

    # Data de fim: hoje
    end_date = datetime.now()

    # Calcular dias
    total_days = (end_date - start_date).days + 1

    print(f"\n📅 Período: {start_date.strftime('%d/%m/%Y')} até {end_date.strftime('%d/%m/%Y')}")
    print(f"📊 Total de dias: {total_days}")
    print(f"\n⚠️  IMPORTANTE: Este processo pode levar vários minutos...")
    print(f"   A API tem rate limits, então fazemos pausas entre requisições\n")
    print("\n🚀 Iniciando importação...\n")

    start_time = time.time()

    # Executar importação
    results = await import_matches_for_date_range(start_date, end_date)

    end_time = time.time()
    duration = end_time - start_time

    # Relatório final
    print("\n" + "=" * 80)
    print("📊 RELATÓRIO DE IMPORTAÇÃO")
    print("=" * 80)
    print(f"\n✅ Jogos importados:  {results['imported']}")
    print(f"⏭️  Jogos já existiam: {results['skipped']}")
    print(f"❌ Erros:             {results['errors']}")
    print(f"\n⏱️  Tempo total: {duration/60:.1f} minutos")
    print(f"📊 Total processado: {results['imported'] + results['skipped']} jogos")
    print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
