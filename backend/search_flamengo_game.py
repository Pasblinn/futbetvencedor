#!/usr/bin/env python3
"""
Script para buscar jogo Flamengo vs Estudiantes pela Libertadores
Usando as APIs configuradas no sistema
"""

import asyncio
import httpx
import json
import os
from datetime import datetime
from app.core.config import settings

async def search_flamengo_game():
    """
    Busca específica pelo jogo Flamengo vs Estudiantes
    """
    print("🔍 BUSCANDO JOGO: Flamengo vs Estudiantes - Copa Libertadores")
    print("=" * 60)

    results = {
        'search_terms': ['Flamengo', 'Estudiantes', 'Libertadores'],
        'apis_tested': [],
        'matches_found': [],
        'team_info': {},
        'api_responses': {}
    }

    # 1. FOOTBALL-DATA.ORG - Busca na Copa Libertadores
    print("\n📡 1. FOOTBALL-DATA.ORG - Copa Libertadores 2025")
    try:
        async with httpx.AsyncClient() as client:
            headers = {"X-Auth-Token": settings.FOOTBALL_DATA_API_KEY}

            # Buscar todos os jogos da Libertadores
            url = f"{settings.FOOTBALL_DATA_BASE_URL}/competitions/CLI/matches"
            response = await client.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                results['api_responses']['football_data'] = {
                    'status': 'success',
                    'total_matches': data.get('count', 0),
                    'matches_found': len(data.get('matches', []))
                }

                # Filtrar jogos do Flamengo
                flamengo_matches = []
                for match in data.get('matches', []):
                    home_team = match.get('homeTeam', {}).get('name', '')
                    away_team = match.get('awayTeam', {}).get('name', '')

                    if ('Flamengo' in home_team or 'Flamengo' in away_team or
                        'flamengo' in home_team.lower() or 'flamengo' in away_team.lower()):
                        flamengo_matches.append({
                            'id': match.get('id'),
                            'date': match.get('utcDate'),
                            'home_team': home_team,
                            'away_team': away_team,
                            'status': match.get('status'),
                            'score': match.get('score', {}),
                            'competition': match.get('competition', {}).get('name')
                        })

                results['matches_found'].extend(flamengo_matches)
                print(f"✅ Football-Data.org: {len(flamengo_matches)} jogos do Flamengo encontrados")

                # Buscar especificamente Estudiantes
                estudiantes_matches = []
                for match in data.get('matches', []):
                    home_team = match.get('homeTeam', {}).get('name', '')
                    away_team = match.get('awayTeam', {}).get('name', '')

                    if ('Estudiantes' in home_team or 'Estudiantes' in away_team or
                        'estudiantes' in home_team.lower() or 'estudiantes' in away_team.lower()):
                        estudiantes_matches.append({
                            'id': match.get('id'),
                            'date': match.get('utcDate'),
                            'home_team': home_team,
                            'away_team': away_team,
                            'status': match.get('status'),
                            'score': match.get('score', {}),
                            'competition': match.get('competition', {}).get('name')
                        })

                print(f"✅ Football-Data.org: {len(estudiantes_matches)} jogos do Estudiantes encontrados")

            else:
                print(f"❌ Football-Data.org: Erro {response.status_code}")
                results['api_responses']['football_data'] = {
                    'status': 'error',
                    'code': response.status_code,
                    'message': response.text
                }

    except Exception as e:
        print(f"❌ Football-Data.org: Erro - {str(e)}")
        results['api_responses']['football_data'] = {'status': 'error', 'message': str(e)}

    # 2. API-SPORTS - Busca por Flamengo (tentativa com dados históricos)
    print("\n📡 2. API-SPORTS - Busca Flamengo")
    try:
        async with httpx.AsyncClient() as client:
            headers = {
                "x-rapidapi-key": settings.API_SPORTS_KEY,
                "x-rapidapi-host": "v3.football.api-sports.io"
            }

            # Tentar buscar Flamengo por nome
            url = "https://v3.football.api-sports.io/teams?search=Flamengo"
            response = await client.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get('response'):
                    team_info = data['response'][0]
                    results['team_info']['flamengo'] = {
                        'id': team_info.get('team', {}).get('id'),
                        'name': team_info.get('team', {}).get('name'),
                        'country': team_info.get('team', {}).get('country'),
                        'logo': team_info.get('team', {}).get('logo'),
                        'venue': team_info.get('venue', {})
                    }
                    print(f"✅ API-Sports: Flamengo encontrado (ID: {team_info.get('team', {}).get('id')})")
                else:
                    print("❌ API-Sports: Flamengo não encontrado")

                results['api_responses']['api_sports'] = {
                    'status': 'success' if data.get('response') else 'no_data',
                    'teams_found': len(data.get('response', []))
                }
            else:
                print(f"❌ API-Sports: Erro {response.status_code}")
                results['api_responses']['api_sports'] = {
                    'status': 'error',
                    'code': response.status_code
                }

    except Exception as e:
        print(f"❌ API-Sports: Erro - {str(e)}")
        results['api_responses']['api_sports'] = {'status': 'error', 'message': str(e)}

    # 3. BUSCA LOCAL NO NOSSO BANCO DE DADOS
    print("\n📡 3. BANCO DE DADOS LOCAL")
    try:
        import sqlite3
        db_path = "football_analytics_dev.db"

        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Buscar jogos com Flamengo
            cursor.execute("""
                SELECT m.*, l.name as league_name
                FROM matches m
                LEFT JOIN leagues l ON m.league_id = l.id
                WHERE (m.home_team LIKE '%Flamengo%' OR m.away_team LIKE '%Flamengo%'
                       OR m.home_team LIKE '%flamengo%' OR m.away_team LIKE '%flamengo%')
                   OR (m.home_team LIKE '%Estudiantes%' OR m.away_team LIKE '%Estudiantes%'
                       OR m.home_team LIKE '%estudiantes%' OR m.away_team LIKE '%estudiantes%')
                ORDER BY m.match_date DESC
                LIMIT 10
            """)

            local_matches = cursor.fetchall()
            if local_matches:
                print(f"✅ Banco Local: {len(local_matches)} jogos encontrados")
                for match in local_matches[:3]:  # Mostrar apenas os 3 primeiros
                    print(f"   - {match[2]} vs {match[3]} ({match[1]})")

                results['api_responses']['local_db'] = {
                    'status': 'success',
                    'matches_found': len(local_matches)
                }
            else:
                print("❌ Banco Local: Nenhum jogo encontrado")
                results['api_responses']['local_db'] = {
                    'status': 'no_data',
                    'matches_found': 0
                }

            conn.close()
        else:
            print("❌ Banco Local: Arquivo não encontrado")
            results['api_responses']['local_db'] = {
                'status': 'error',
                'message': 'Database file not found'
            }

    except Exception as e:
        print(f"❌ Banco Local: Erro - {str(e)}")
        results['api_responses']['local_db'] = {'status': 'error', 'message': str(e)}

    # BUSCA ESPECÍFICA POR DATA (hoje 25/09, jogo às 21:30)
    print("\n📡 4. BUSCA POR DATA - 25/09/2024 21:30")
    today = datetime.now().strftime('%Y-%m-%d')
    print(f"Procurando jogos para hoje: {today}")

    try:
        # Football-Data com filtro de data
        async with httpx.AsyncClient() as client:
            headers = {"X-Auth-Token": settings.FOOTBALL_DATA_API_KEY}

            # Buscar jogos de hoje na Libertadores
            url = f"{settings.FOOTBALL_DATA_BASE_URL}/competitions/CLI/matches?dateFrom={today}&dateTo={today}"
            response = await client.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                today_matches = data.get('matches', [])

                if today_matches:
                    print(f"✅ Jogos hoje na Libertadores: {len(today_matches)}")
                    for match in today_matches:
                        home = match.get('homeTeam', {}).get('name', '')
                        away = match.get('awayTeam', {}).get('name', '')
                        time = match.get('utcDate', '')
                        print(f"   - {home} vs {away} ({time})")
                else:
                    print("❌ Nenhum jogo hoje na Libertadores")

                results['api_responses']['today_matches'] = {
                    'status': 'success',
                    'matches_found': len(today_matches),
                    'matches': today_matches
                }
            else:
                print(f"❌ Busca por data: Erro {response.status_code}")

    except Exception as e:
        print(f"❌ Busca por data: Erro - {str(e)}")

    # RESULTADOS FINAIS
    print("\n" + "=" * 60)
    print("📊 RESUMO DA BUSCA")
    print("=" * 60)

    print(f"🔍 APIs testadas: {len(results['api_responses'])}")
    for api, status in results['api_responses'].items():
        print(f"   - {api}: {status.get('status', 'unknown')}")

    print(f"⚽ Jogos do Flamengo encontrados: {len(results['matches_found'])}")
    print(f"📋 Informações de equipe coletadas: {len(results['team_info'])}")

    # Salvar resultados
    with open('search_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n💾 Resultados salvos em: search_results.json")

    return results

if __name__ == "__main__":
    asyncio.run(search_flamengo_game())