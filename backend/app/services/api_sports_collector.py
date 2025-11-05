"""
🔑 API-SPORTS COLLECTOR - Coletor especializado para API-Sports
Foca em ligas brasileiras e espanholas com coleta de jogos ao vivo
"""

import asyncio
import httpx
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

class ApiSportsCollector:
    """
    🔑 Coletor especializado para API-Sports
    """

    def __init__(self):
        self.api_key = os.getenv('API_SPORTS_KEY', '417697345fe23e648c0a462b39d319af')
        self.base_url = "https://v3.football.api-sports.io"

        self.headers = {
            'X-RapidAPI-Key': self.api_key,
            'X-RapidAPI-Host': 'v3.football.api-sports.io'
        }

        # IDs das ligas prioritárias
        self.priority_leagues = {
            'brasileirao': {
                'id': 71,  # Série A Brasil
                'name': 'Brasileirão Série A',
                'country': 'Brazil',
                'season': 2024
            },
            'la_liga': {
                'id': 140,  # La Liga
                'name': 'La Liga',
                'country': 'Spain',
                'season': 2024
            },
            'premier_league': {
                'id': 39,  # Premier League
                'name': 'Premier League',
                'country': 'England',
                'season': 2024
            },
            'serie_a': {
                'id': 135,  # Serie A
                'name': 'Serie A',
                'country': 'Italy',
                'season': 2024
            }
        }

        self.rate_limit_calls = 0
        self.rate_limit_reset = datetime.now()

    async def collect_priority_leagues(self) -> Dict:
        """
        🎯 Coletar das ligas prioritárias
        """
        logger.info("🔑 INICIANDO COLETA API-SPORTS - LIGAS PRIORITÁRIAS")

        results = {
            'start_time': datetime.now().isoformat(),
            'leagues': {},
            'live_matches': [],
            'all_matches': [],
            'total_matches': 0,
            'success': True
        }

        try:
            # 1. Jogos ao vivo (primeira prioridade)
            logger.info("⚡ Coletando jogos ao vivo...")
            live_matches = await self._get_live_matches()
            results['live_matches'] = live_matches
            results['all_matches'].extend(live_matches)

            # 2. Ligas por prioridade (Brasil primeiro)
            for league_key, league_info in self.priority_leagues.items():
                try:
                    if not self._can_make_request():
                        logger.warning("⚠️ Rate limit atingido, pulando...")
                        break

                    logger.info(f"🏆 Coletando {league_info['name']}...")

                    # Próximos jogos
                    upcoming_matches = await self._get_league_upcoming_matches(league_info)

                    # Jogos recentes
                    recent_matches = await self._get_league_recent_matches(league_info)

                    league_matches = upcoming_matches + recent_matches
                    results['leagues'][league_key] = {
                        'league_info': league_info,
                        'matches': league_matches,
                        'count': len(league_matches)
                    }
                    results['all_matches'].extend(league_matches)

                    # Rate limiting
                    await asyncio.sleep(1)

                except Exception as e:
                    logger.error(f"❌ Erro coletando {league_key}: {e}")
                    continue

        except Exception as e:
            logger.error(f"❌ Erro na coleta API-Sports: {e}")
            results['success'] = False

        results['total_matches'] = len(results['all_matches'])
        results['end_time'] = datetime.now().isoformat()

        logger.info(f"✅ API-Sports: {results['total_matches']} jogos coletados")
        return results

    async def _get_live_matches(self) -> List[Dict]:
        """
        ⚡ Buscar jogos ao vivo
        """
        matches = []

        try:
            if not self._can_make_request():
                return matches

            url = f"{self.base_url}/fixtures"
            params = {'live': 'all'}

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=self.headers, params=params)
                self._update_rate_limit()

                if response.status_code == 200:
                    data = response.json()

                    for fixture in data.get('response', [])[:10]:  # Máximo 10 ao vivo
                        try:
                            match_data = self._parse_api_sports_fixture(fixture)
                            match_data['is_live'] = True
                            matches.append(match_data)

                            home_team = fixture['teams']['home']['name']
                            away_team = fixture['teams']['away']['name']
                            logger.info(f"⚡ AO VIVO: {home_team} vs {away_team}")

                        except Exception as e:
                            logger.warning(f"⚠️ Erro processando jogo ao vivo: {e}")
                            continue

                elif response.status_code == 429:
                    logger.warning("⚠️ API-Sports: Rate limit atingido")

        except Exception as e:
            logger.error(f"❌ Erro jogos ao vivo: {e}")

        return matches

    async def _get_league_upcoming_matches(self, league_info: Dict) -> List[Dict]:
        """
        📅 Buscar próximos jogos de uma liga
        """
        matches = []

        try:
            if not self._can_make_request():
                return matches

            url = f"{self.base_url}/fixtures"
            params = {
                'league': league_info['id'],
                'season': league_info['season'],
                'next': 10  # Próximos 10 jogos
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=self.headers, params=params)
                self._update_rate_limit()

                if response.status_code == 200:
                    data = response.json()

                    for fixture in data.get('response', []):
                        try:
                            match_data = self._parse_api_sports_fixture(fixture)
                            match_data['league_info'] = league_info
                            matches.append(match_data)

                        except Exception as e:
                            logger.warning(f"⚠️ Erro processando fixture: {e}")
                            continue

                elif response.status_code == 429:
                    logger.warning("⚠️ API-Sports: Rate limit atingido")

        except Exception as e:
            logger.error(f"❌ Erro próximos jogos {league_info['name']}: {e}")

        return matches

    async def _get_league_recent_matches(self, league_info: Dict) -> List[Dict]:
        """
        📊 Buscar jogos recentes de uma liga
        """
        matches = []

        try:
            if not self._can_make_request():
                return matches

            url = f"{self.base_url}/fixtures"
            params = {
                'league': league_info['id'],
                'season': league_info['season'],
                'last': 5  # Últimos 5 jogos
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=self.headers, params=params)
                self._update_rate_limit()

                if response.status_code == 200:
                    data = response.json()

                    for fixture in data.get('response', []):
                        try:
                            match_data = self._parse_api_sports_fixture(fixture)
                            match_data['league_info'] = league_info
                            matches.append(match_data)

                        except Exception as e:
                            logger.warning(f"⚠️ Erro processando fixture recente: {e}")
                            continue

        except Exception as e:
            logger.error(f"❌ Erro jogos recentes {league_info['name']}: {e}")

        return matches

    def _parse_api_sports_fixture(self, fixture: Dict) -> Dict:
        """
        🔄 Converter fixture da API-Sports para formato padrão
        """
        try:
            home_team = fixture['teams']['home']['name']
            away_team = fixture['teams']['away']['name']
            league_name = fixture['league']['name']

            # Status mapping
            status_map = {
                'TBD': 'SCHEDULED',
                'NS': 'SCHEDULED',
                '1H': 'LIVE',
                'HT': 'LIVE',
                '2H': 'LIVE',
                'ET': 'LIVE',
                'FT': 'FINISHED',
                'AET': 'FINISHED',
                'PEN': 'FINISHED',
                'PST': 'POSTPONED',
                'CANC': 'CANCELLED'
            }

            api_status = fixture['fixture']['status']['short']
            status = status_map.get(api_status, 'SCHEDULED')

            match_data = {
                'home_team': {
                    'name': home_team,
                    'id': fixture['teams']['home']['id']
                },
                'away_team': {
                    'name': away_team,
                    'id': fixture['teams']['away']['id']
                },
                'tournament': league_name,
                'match_date': fixture['fixture']['date'],
                'status': status,
                'venue': fixture['fixture']['venue']['name'] if fixture['fixture']['venue'] else None,
                'referee': fixture['fixture']['referee'],
                'source': 'api_sports',
                'match_id': fixture['fixture']['id'],
                'collected_at': datetime.now().isoformat()
            }

            # Adicionar placar se disponível
            if fixture['goals']['home'] is not None:
                match_data['home_score'] = fixture['goals']['home']
            if fixture['goals']['away'] is not None:
                match_data['away_score'] = fixture['goals']['away']

            return match_data

        except Exception as e:
            logger.error(f"❌ Erro parsing fixture: {e}")
            raise

    def _can_make_request(self) -> bool:
        """
        ⏰ Verificar se pode fazer request (rate limiting)
        """
        now = datetime.now()

        # Reset counter a cada minuto
        if now > self.rate_limit_reset:
            self.rate_limit_calls = 0
            self.rate_limit_reset = now + timedelta(minutes=1)

        # API-Sports: 100 requests por minuto no plano free
        return self.rate_limit_calls < 100

    def _update_rate_limit(self):
        """
        📊 Atualizar contador de rate limit
        """
        self.rate_limit_calls += 1

    async def get_finished_matches_with_results(self) -> List[Dict]:
        """
        🏁 Buscar jogos finalizados com resultados reais das principais ligas
        """
        matches = []

        try:
            logger.info("🏁 COLETANDO JOGOS FINALIZADOS COM RESULTADOS REAIS...")

            for league_key, league_info in self.priority_leagues.items():
                try:
                    if not self._can_make_request():
                        logger.warning("⚠️ Rate limit atingido, parando...")
                        break

                    logger.info(f"🏆 Buscando jogos finalizados: {league_info['name']}")

                    # Buscar jogos finalizados dos últimos 30 dias
                    from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                    to_date = datetime.now().strftime('%Y-%m-%d')

                    url = f"{self.base_url}/fixtures"
                    params = {
                        'league': league_info['id'],
                        'season': league_info['season'],
                        'from': from_date,
                        'to': to_date,
                        'status': 'FT'  # Finished
                    }

                    async with httpx.AsyncClient(timeout=30.0) as client:
                        response = await client.get(url, headers=self.headers, params=params)
                        self._update_rate_limit()

                        if response.status_code == 200:
                            data = response.json()

                            for fixture in data.get('response', []):
                                try:
                                    # Só pegar jogos com placar definido
                                    if (fixture['goals']['home'] is not None and
                                        fixture['goals']['away'] is not None):

                                        match_data = self._parse_api_sports_fixture(fixture)
                                        match_data['league_info'] = league_info
                                        matches.append(match_data)

                                        home_team = fixture['teams']['home']['name']
                                        away_team = fixture['teams']['away']['name']
                                        home_score = fixture['goals']['home']
                                        away_score = fixture['goals']['away']

                                        logger.info(f"🏁 {home_team} {home_score}-{away_score} {away_team}")

                                except Exception as e:
                                    logger.warning(f"⚠️ Erro processando fixture finalizado: {e}")
                                    continue

                        elif response.status_code == 429:
                            logger.warning("⚠️ API-Sports: Rate limit atingido")
                            break

                    # Rate limiting entre ligas
                    await asyncio.sleep(2)

                except Exception as e:
                    logger.error(f"❌ Erro coletando jogos finalizados {league_key}: {e}")
                    continue

        except Exception as e:
            logger.error(f"❌ Erro geral na coleta de jogos finalizados: {e}")

        logger.info(f"✅ Coletados {len(matches)} jogos finalizados com resultados")
        return matches

    async def get_brazilian_teams_specifically(self) -> List[Dict]:
        """
        🇧🇷 Buscar especificamente times brasileiros
        """
        teams = []

        try:
            if not self._can_make_request():
                return teams

            url = f"{self.base_url}/teams"
            params = {
                'league': 71,  # Brasileirão
                'season': 2024
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=self.headers, params=params)
                self._update_rate_limit()

                if response.status_code == 200:
                    data = response.json()

                    for team in data.get('response', []):
                        team_data = {
                            'name': team['team']['name'],
                            'id': team['team']['id'],
                            'country': 'Brazil',
                            'founded': team['team']['founded'],
                            'venue': team['venue']['name'] if team['venue'] else None,
                            'logo_url': team['team']['logo'],
                            'source': 'api_sports'
                        }
                        teams.append(team_data)

        except Exception as e:
            logger.error(f"❌ Erro times brasileiros: {e}")

        return teams

# Instância global
api_sports_collector = ApiSportsCollector()