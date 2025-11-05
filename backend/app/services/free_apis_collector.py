"""
🆓 FREE APIS COLLECTOR - Coletor de APIs gratuitas
Implementa coleta de dados das melhores APIs gratuitas:
- Football-Data.org (já configurada)
- SportDB
- OpenLigaDB
- OpenFootball datasets
- API-Sports (plano free)
- FootyStats
"""

import asyncio
import httpx
import aiohttp
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta, timezone
import json
import os
from ..core.config import settings

logger = logging.getLogger(__name__)

class FreeApisCollector:
    """
    🆓 Coletor de APIs gratuitas com rate limiting inteligente
    """

    def __init__(self):
        self.rate_limits = {
            'football_data': {'calls': 0, 'reset_time': datetime.now(), 'max_per_minute': 10},
            'sportdb': {'calls': 0, 'reset_time': datetime.now(), 'max_per_minute': 60},
            'openliga': {'calls': 0, 'reset_time': datetime.now(), 'max_per_minute': 30},
            'api_sports': {'calls': 0, 'reset_time': datetime.now(), 'max_per_minute': 100},
            'footystats': {'calls': 0, 'reset_time': datetime.now(), 'max_per_minute': 50}
        }

    async def collect_from_all_free_apis(self) -> Dict:
        """
        🆓 Coleta de todas as APIs gratuitas disponíveis
        """
        logger.info("🆓 INICIANDO COLETA DE APIS GRATUITAS...")

        results = {
            'start_time': datetime.now().isoformat(),
            'sources': {},
            'all_matches': [],
            'total_matches': 0,
            'api_status': {},
            'success': True
        }

        try:
            # 1. Football-Data.org (já temos configurada)
            if settings.FOOTBALL_DATA_API_KEY:
                logger.info("⚽ Coletando Football-Data.org...")
                football_data_matches = await self._collect_football_data()
                results['sources']['football_data'] = football_data_matches
                results['all_matches'].extend(football_data_matches)
                results['api_status']['football_data'] = 'configured'
            else:
                results['api_status']['football_data'] = 'missing_key'

            await asyncio.sleep(2)

            # 2. SportDB (gratuita, sem key)
            logger.info("🏟️ Coletando SportDB...")
            sportdb_matches = await self._collect_sportdb()
            results['sources']['sportdb'] = sportdb_matches
            results['all_matches'].extend(sportdb_matches)
            results['api_status']['sportdb'] = 'free'

            await asyncio.sleep(2)

            # 3. OpenLigaDB (gratuita, alemã)
            logger.info("🇩🇪 Coletando OpenLigaDB...")
            openliga_matches = await self._collect_openliga()
            results['sources']['openliga'] = openliga_matches
            results['all_matches'].extend(openliga_matches)
            results['api_status']['openliga'] = 'free'

            await asyncio.sleep(2)

            # 4. OpenFootball (datasets estáticos)
            logger.info("📊 Coletando OpenFootball datasets...")
            openfootball_matches = await self._collect_openfootball()
            results['sources']['openfootball'] = openfootball_matches
            results['all_matches'].extend(openfootball_matches)
            results['api_status']['openfootball'] = 'free'

            # 5. API-Sports (se configurada)
            if os.getenv('API_SPORTS_KEY'):
                logger.info("🔑 Coletando API-Sports...")
                api_sports_matches = await self._collect_api_sports()
                results['sources']['api_sports'] = api_sports_matches
                results['all_matches'].extend(api_sports_matches)
                results['api_status']['api_sports'] = 'configured'
            else:
                results['api_status']['api_sports'] = 'missing_key'

        except Exception as e:
            logger.error(f"❌ Erro na coleta de APIs gratuitas: {e}")
            results['success'] = False

        results['total_matches'] = len(results['all_matches'])
        results['end_time'] = datetime.now().isoformat()

        logger.info(f"✅ APIS GRATUITAS: {results['total_matches']} jogos coletados")
        return results

    async def _collect_football_data(self) -> List[Dict]:
        """
        ⚽ Football-Data.org (já configurada)
        """
        matches = []

        if not settings.FOOTBALL_DATA_API_KEY:
            logger.warning("⚠️ Football-Data.org: API key não configurada")
            return matches

        try:
            headers = {
                'X-Auth-Token': settings.FOOTBALL_DATA_API_KEY,
                'User-Agent': 'Football Analytics App'
            }

            base_url = settings.FOOTBALL_DATA_BASE_URL

            # Endpoints principais
            endpoints = [
                '/competitions/PL/matches',  # Premier League
                '/competitions/PD/matches',  # La Liga
                '/competitions/SA/matches',  # Serie A
                '/competitions/BL1/matches', # Bundesliga
                '/competitions/FL1/matches', # Ligue 1
            ]

            async with httpx.AsyncClient(timeout=30.0) as client:
                for endpoint in endpoints:
                    try:
                        if not self._can_make_request('football_data'):
                            logger.info("⏰ Rate limit Football-Data, pulando...")
                            break

                        url = f"{base_url}{endpoint}"
                        logger.info(f"🔍 Football-Data: {endpoint}")

                        response = await client.get(url, headers=headers)

                        if response.status_code == 200:
                            data = response.json()

                            for match in data.get('matches', [])[:10]:  # Limite por liga
                                try:
                                    home_team = match['homeTeam']['name']
                                    away_team = match['awayTeam']['name']
                                    competition = match['competition']['name']

                                    match_data = {
                                        'home_team': {'name': home_team, 'id': match['homeTeam']['id']},
                                        'away_team': {'name': away_team, 'id': match['awayTeam']['id']},
                                        'tournament': competition,
                                        'match_date': match.get('utcDate'),
                                        'status': match.get('status'),
                                        'source': 'football_data_org',
                                        'match_id': match.get('id'),
                                        'collected_at': datetime.now().isoformat()
                                    }

                                    matches.append(match_data)
                                    logger.info(f"⚽ Football-Data: {home_team} vs {away_team} ({competition})")

                                except Exception as e:
                                    logger.warning(f"⚠️ Erro processando match Football-Data: {e}")
                                    continue

                            self._update_rate_limit('football_data')

                        elif response.status_code == 429:
                            logger.warning("⚠️ Football-Data: Rate limit atingido")
                            break
                        elif response.status_code == 403:
                            logger.warning("⚠️ Football-Data: API key inválida")
                            break

                    except Exception as e:
                        logger.warning(f"⚠️ Erro endpoint Football-Data {endpoint}: {e}")
                        continue

                    await asyncio.sleep(1)  # Rate limiting

        except Exception as e:
            logger.error(f"❌ Erro Football-Data: {e}")

        return matches

    async def _collect_sportdb(self) -> List[Dict]:
        """
        🏟️ SportDB - API gratuita sem necessidade de key
        """
        matches = []

        try:
            base_url = "https://www.thesportsdb.com/api/v1/json/3"

            # Endpoints disponíveis
            endpoints = [
                '/eventsseason.php?id=4328&s=2023-2024',  # Premier League
                '/eventsseason.php?id=4335&s=2023-2024',  # La Liga
                '/eventsseason.php?id=4332&s=2023-2024',  # Serie A
                '/eventsseason.php?id=4331&s=2023-2024',  # Bundesliga
            ]

            async with httpx.AsyncClient(timeout=30.0) as client:
                for endpoint in endpoints:
                    try:
                        if not self._can_make_request('sportdb'):
                            logger.info("⏰ Rate limit SportDB, pulando...")
                            break

                        url = f"{base_url}{endpoint}"
                        logger.info(f"🔍 SportDB: {endpoint}")

                        response = await client.get(url)

                        if response.status_code == 200:
                            data = response.json()

                            events = data.get('events', [])
                            for event in events[:15]:  # Limite por liga
                                try:
                                    # Verificar se é jogo futuro/próximo
                                    event_date = event.get('dateEvent')
                                    if event_date:
                                        # Pegar apenas jogos recentes/futuros
                                        home_team = event.get('strHomeTeam')
                                        away_team = event.get('strAwayTeam')
                                        league = event.get('strLeague', 'SportDB League')

                                        if home_team and away_team:
                                            match_data = {
                                                'home_team': {'name': home_team},
                                                'away_team': {'name': away_team},
                                                'tournament': league,
                                                'match_date': event_date,
                                                'time': event.get('strTime'),
                                                'source': 'sportdb',
                                                'event_id': event.get('idEvent'),
                                                'collected_at': datetime.now().isoformat()
                                            }

                                            matches.append(match_data)
                                            logger.info(f"🏟️ SportDB: {home_team} vs {away_team} ({league})")

                                except Exception as e:
                                    logger.warning(f"⚠️ Erro processando event SportDB: {e}")
                                    continue

                            self._update_rate_limit('sportdb')

                        elif response.status_code == 429:
                            logger.warning("⚠️ SportDB: Rate limit atingido")
                            break

                    except Exception as e:
                        logger.warning(f"⚠️ Erro endpoint SportDB {endpoint}: {e}")
                        continue

                    await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"❌ Erro SportDB: {e}")

        return matches

    async def _collect_openliga(self) -> List[Dict]:
        """
        🇩🇪 OpenLigaDB - API alemã gratuita
        """
        matches = []

        try:
            base_url = "https://api.openligadb.de"

            # Endpoints para ligas alemãs e europeias
            endpoints = [
                '/getmatchdata/bl1/2023',  # Bundesliga
                '/getmatchdata/bl2/2023',  # 2. Bundesliga
                '/getmatchdata/em/2024',   # Euro 2024
            ]

            async with httpx.AsyncClient(timeout=30.0) as client:
                for endpoint in endpoints:
                    try:
                        if not self._can_make_request('openliga'):
                            logger.info("⏰ Rate limit OpenLigaDB, pulando...")
                            break

                        url = f"{base_url}{endpoint}"
                        logger.info(f"🔍 OpenLigaDB: {endpoint}")

                        response = await client.get(url)

                        if response.status_code == 200:
                            data = response.json()

                            # OpenLigaDB retorna array de jogos
                            if isinstance(data, list):
                                for match in data[:20]:  # Limite por liga
                                    try:
                                        team1 = match.get('team1', {}).get('teamName')
                                        team2 = match.get('team2', {}).get('teamName')
                                        league = match.get('leagueName', 'OpenLigaDB')

                                        if team1 and team2:
                                            match_data = {
                                                'home_team': {'name': team1},
                                                'away_team': {'name': team2},
                                                'tournament': league,
                                                'match_date': match.get('matchDateTime'),
                                                'match_day': match.get('group', {}).get('groupName'),
                                                'source': 'openligadb',
                                                'match_id': match.get('matchID'),
                                                'collected_at': datetime.now().isoformat()
                                            }

                                            matches.append(match_data)
                                            logger.info(f"🇩🇪 OpenLigaDB: {team1} vs {team2} ({league})")

                                    except Exception as e:
                                        logger.warning(f"⚠️ Erro processando match OpenLigaDB: {e}")
                                        continue

                            self._update_rate_limit('openliga')

                        elif response.status_code == 429:
                            logger.warning("⚠️ OpenLigaDB: Rate limit atingido")
                            break

                    except Exception as e:
                        logger.warning(f"⚠️ Erro endpoint OpenLigaDB {endpoint}: {e}")
                        continue

                    await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"❌ Erro OpenLigaDB: {e}")

        return matches

    async def _collect_openfootball(self) -> List[Dict]:
        """
        📊 OpenFootball - Datasets GitHub gratuitos
        """
        matches = []

        try:
            # URLs dos datasets OpenFootball
            github_datasets = [
                'https://raw.githubusercontent.com/openfootball/football.json/master/2023-24/en.1.json',  # Premier League
                'https://raw.githubusercontent.com/openfootball/football.json/master/2023-24/es.1.json',  # La Liga
                'https://raw.githubusercontent.com/openfootball/football.json/master/2023-24/it.1.json',  # Serie A
                'https://raw.githubusercontent.com/openfootball/football.json/master/2023-24/de.1.json',  # Bundesliga
            ]

            async with httpx.AsyncClient(timeout=30.0) as client:
                for dataset_url in github_datasets:
                    try:
                        logger.info(f"📊 OpenFootball dataset: {dataset_url}")

                        response = await client.get(dataset_url)

                        if response.status_code == 200:
                            data = response.json()

                            # Estrutura típica OpenFootball
                            rounds = data.get('rounds', [])
                            league_name = data.get('name', 'OpenFootball League')

                            for round_data in rounds[:5]:  # Limite de rounds
                                matches_in_round = round_data.get('matches', [])

                                for match in matches_in_round[:10]:  # Limite por round
                                    try:
                                        team1 = match.get('team1')
                                        team2 = match.get('team2')
                                        match_date = match.get('date')

                                        if team1 and team2:
                                            match_data = {
                                                'home_team': {'name': team1},
                                                'away_team': {'name': team2},
                                                'tournament': league_name,
                                                'match_date': match_date,
                                                'round': round_data.get('name'),
                                                'score': match.get('score'),
                                                'source': 'openfootball_github',
                                                'collected_at': datetime.now().isoformat()
                                            }

                                            matches.append(match_data)
                                            logger.info(f"📊 OpenFootball: {team1} vs {team2} ({league_name})")

                                    except Exception as e:
                                        logger.warning(f"⚠️ Erro processando match OpenFootball: {e}")
                                        continue

                        elif response.status_code == 404:
                            logger.warning(f"⚠️ OpenFootball dataset não encontrado: {dataset_url}")

                    except Exception as e:
                        logger.warning(f"⚠️ Erro dataset OpenFootball {dataset_url}: {e}")
                        continue

                    await asyncio.sleep(2)  # GitHub rate limiting

        except Exception as e:
            logger.error(f"❌ Erro OpenFootball: {e}")

        return matches

    async def _collect_api_sports(self) -> List[Dict]:
        """
        🔑 API-Sports (se configurada)
        """
        matches = []
        api_key = os.getenv('API_SPORTS_KEY')

        if not api_key:
            logger.info("🔑 API-Sports: Chave não configurada")
            return matches

        try:
            headers = {
                'X-RapidAPI-Key': api_key,
                'X-RapidAPI-Host': 'api-football-v1.p.rapidapi.com'
            }

            base_url = "https://api-football-v1.p.rapidapi.com/v3"

            # Ligas principais IDs
            league_ids = [39, 140, 135, 78, 61]  # Premier, La Liga, Serie A, Bundesliga, Ligue 1

            async with httpx.AsyncClient(timeout=30.0) as client:
                for league_id in league_ids:
                    try:
                        if not self._can_make_request('api_sports'):
                            logger.info("⏰ Rate limit API-Sports, pulando...")
                            break

                        url = f"{base_url}/fixtures"
                        params = {
                            'league': league_id,
                            'season': 2023,
                            'next': 10
                        }

                        response = await client.get(url, headers=headers, params=params)

                        if response.status_code == 200:
                            data = response.json()

                            fixtures = data.get('response', [])
                            for fixture in fixtures:
                                try:
                                    teams = fixture.get('teams', {})
                                    home_team = teams.get('home', {}).get('name')
                                    away_team = teams.get('away', {}).get('name')
                                    league = fixture.get('league', {}).get('name')

                                    if home_team and away_team:
                                        match_data = {
                                            'home_team': {'name': home_team},
                                            'away_team': {'name': away_team},
                                            'tournament': league,
                                            'match_date': fixture.get('fixture', {}).get('date'),
                                            'status': fixture.get('fixture', {}).get('status', {}).get('long'),
                                            'source': 'api_sports',
                                            'fixture_id': fixture.get('fixture', {}).get('id'),
                                            'collected_at': datetime.now().isoformat()
                                        }

                                        matches.append(match_data)
                                        logger.info(f"🔑 API-Sports: {home_team} vs {away_team} ({league})")

                                except Exception as e:
                                    logger.warning(f"⚠️ Erro processando fixture API-Sports: {e}")
                                    continue

                            self._update_rate_limit('api_sports')

                        elif response.status_code == 429:
                            logger.warning("⚠️ API-Sports: Rate limit atingido")
                            break

                    except Exception as e:
                        logger.warning(f"⚠️ Erro league API-Sports {league_id}: {e}")
                        continue

                    await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"❌ Erro API-Sports: {e}")

        return matches

    def _can_make_request(self, api_name: str) -> bool:
        """Verificar se pode fazer request baseado no rate limit"""
        now = datetime.now()
        rate_info = self.rate_limits[api_name]

        # Reset counter se passou 1 minuto
        if now > rate_info['reset_time']:
            rate_info['calls'] = 0
            rate_info['reset_time'] = now + timedelta(minutes=1)

        return rate_info['calls'] < rate_info['max_per_minute']

    def _update_rate_limit(self, api_name: str):
        """Atualizar contador de rate limit"""
        self.rate_limits[api_name]['calls'] += 1

    def get_registration_urls(self) -> Dict[str, str]:
        """
        🔗 URLs para registro nas APIs gratuitas
        """
        return {
            'football_data_org': 'https://www.football-data.org/client/register',
            'api_sports': 'https://rapidapi.com/api-sports/api/api-football',
            'footystats': 'https://footystats.org/api',
            'sportdb': 'https://www.thesportsdb.com/api.php (Gratuita, sem registro)',
            'openligadb': 'https://www.openligadb.de/ (Gratuita, sem registro)',
            'openfootball': 'https://github.com/openfootball (Gratuita, sem registro)'
        }

# Instância global
free_apis_collector = FreeApisCollector()