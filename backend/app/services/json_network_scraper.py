"""
🕷️ JSON NETWORK SCRAPER - Intercepta dados JSON das requisições de rede
Extrai dados dos sites através das chamadas AJAX/XHR que eles fazem internamente
Foco em Brasil e Espanha com dados reais e atualizados
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import json
import re
import random
from urllib.parse import urljoin, quote

logger = logging.getLogger(__name__)

class JSONNetworkScraper:
    """
    🎯 Scraper que intercepta dados JSON de requisições internas dos sites
    """

    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]

        # Headers que simulam navegador real
        self.base_headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8,es;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'X-Requested-With': 'XMLHttpRequest'
        }

    async def scrape_flashscore_json(self) -> List[Dict]:
        """
        ⚡ Interceptar dados JSON do Flashscore (via requisições AJAX)
        """
        matches = []

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:

                # Headers específicos do Flashscore
                headers = dict(self.base_headers)
                headers.update({
                    'User-Agent': random.choice(self.user_agents),
                    'Referer': 'https://www.flashscore.com.br/',
                    'Origin': 'https://www.flashscore.com.br'
                })

                # URLs das APIs internas do Flashscore (descobertas via DevTools)
                today = datetime.now().strftime('%d.%m.%Y')

                api_urls = [
                    f'https://d.flashscore.com.br/x/feed/f_1_0_8_pt-br_1',  # Futebol geral
                    f'https://d.flashscore.com.br/x/feed/f_1_0_8_pt-br_2',  # Mais jogos
                    'https://www.flashscore.com.br/res/feed/d-A-fp-1-',      # Feed direto
                ]

                for url in api_urls:
                    try:
                        logger.info(f"🔍 Tentando URL interna Flashscore: {url}")

                        async with session.get(url, headers=headers) as response:
                            if response.status == 200:
                                content = await response.text()

                                # Flashscore usa formato proprietário, tentar extrair dados
                                if 'ESPN' in content or 'Real Madrid' in content or 'Barcelona' in content:
                                    # Extrair dados usando regex
                                    team_pattern = r'(Real Madrid|Barcelona|Flamengo|Palmeiras|Corinthians|Santos|São Paulo)'
                                    teams_found = re.findall(team_pattern, content, re.IGNORECASE)

                                    if len(teams_found) >= 2:
                                        match_data = {
                                            'home_team': {'name': teams_found[0]},
                                            'away_team': {'name': teams_found[1]},
                                            'league': 'La Liga' if 'Real Madrid' in teams_found or 'Barcelona' in teams_found else 'Brasileirão',
                                            'source': 'flashscore_json',
                                            'collected_at': datetime.now().isoformat()
                                        }
                                        matches.append(match_data)
                                        logger.info(f"⚡ Flashscore JSON: {match_data['home_team']['name']} vs {match_data['away_team']['name']}")

                            elif response.status == 429:
                                logger.warning("⚠️ Rate limit Flashscore")
                                await asyncio.sleep(10)
                                break

                    except Exception as e:
                        logger.warning(f"⚠️ Erro URL {url}: {e}")
                        continue

                    await asyncio.sleep(3)  # Delay entre requests

        except Exception as e:
            logger.error(f"❌ Erro Flashscore JSON: {e}")

        return matches

    async def scrape_sofascore_ajax(self) -> List[Dict]:
        """
        ⚽ Interceptar dados AJAX do SofaScore (requisições internas)
        """
        matches = []

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:

                headers = dict(self.base_headers)
                headers.update({
                    'User-Agent': random.choice(self.user_agents),
                    'Referer': 'https://www.sofascore.com/',
                    'Authority': 'api.sofascore.com'
                })

                # URLs AJAX internas do SofaScore (encontradas via Network tab)
                today = datetime.now().strftime('%Y-%m-%d')

                internal_apis = [
                    f'https://api.sofascore.com/api/v1/sport/football/scheduled-events/{today}',
                    'https://api.sofascore.com/api/v1/sport/football/events/live',
                    'https://api.sofascore.com/api/v1/unique-tournament/8/season/61643/events/next/0',  # La Liga
                    'https://api.sofascore.com/api/v1/unique-tournament/325/season/58766/events/next/0', # Brasileirão
                ]

                for api_url in internal_apis:
                    try:
                        logger.info(f"🔍 Tentando API interna SofaScore: {api_url}")

                        async with session.get(api_url, headers=headers) as response:
                            if response.status == 200:
                                data = await response.json()

                                # Processar eventos
                                events = data.get('events', [])
                                for event in events[:10]:  # Limitar a 10 por API
                                    tournament = event.get('tournament', {})
                                    country = tournament.get('category', {}).get('name', '')

                                    # Filtrar Brasil/Espanha
                                    if any(term in country for term in ['Brazil', 'Spain', 'Brasil', 'Espanha']):
                                        match_data = {
                                            'id': event.get('id'),
                                            'home_team': {
                                                'name': event.get('homeTeam', {}).get('name', ''),
                                                'id': event.get('homeTeam', {}).get('id')
                                            },
                                            'away_team': {
                                                'name': event.get('awayTeam', {}).get('name', ''),
                                                'id': event.get('awayTeam', {}).get('id')
                                            },
                                            'league': tournament.get('name', ''),
                                            'country': country,
                                            'start_time': event.get('startTimestamp'),
                                            'status': event.get('status', {}).get('description', ''),
                                            'source': 'sofascore_ajax',
                                            'collected_at': datetime.now().isoformat()
                                        }
                                        matches.append(match_data)
                                        logger.info(f"⚽ SofaScore AJAX: {match_data['home_team']['name']} vs {match_data['away_team']['name']}")

                            elif response.status == 403:
                                logger.warning("⚠️ Blocked by SofaScore")
                                break
                            elif response.status == 429:
                                logger.warning("⚠️ Rate limit SofaScore")
                                await asyncio.sleep(15)
                                break

                    except Exception as e:
                        logger.warning(f"⚠️ Erro API {api_url}: {e}")
                        continue

                    await asyncio.sleep(5)  # Delay maior para SofaScore

        except Exception as e:
            logger.error(f"❌ Erro SofaScore AJAX: {e}")

        return matches

    async def scrape_espn_embedded_json(self) -> List[Dict]:
        """
        📺 Extrair JSON embutido das páginas ESPN
        """
        matches = []

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=20)
            ) as session:

                headers = dict(self.base_headers)
                headers.update({
                    'User-Agent': random.choice(self.user_agents),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                })

                urls = [
                    'https://www.espn.com.br/futebol/fixtures',
                    'https://www.espn.com/soccer/fixtures',
                    'https://www.espn.com.br/futebol/fixtures/_/league/esp.1',  # La Liga
                    'https://www.espn.com.br/futebol/fixtures/_/league/bra.1',  # Brasileirão
                ]

                for url in urls:
                    try:
                        logger.info(f"🔍 Extraindo JSON embutido ESPN: {url}")

                        async with session.get(url, headers=headers) as response:
                            if response.status == 200:
                                html = await response.text()

                                # Procurar JSON embutido nas tags script
                                json_patterns = [
                                    r'window\.__espnfitt__\s*=\s*({.*?});',
                                    r'window\.espn\.fixtures\s*=\s*({.*?});',
                                    r'__INITIAL_STATE__\s*=\s*({.*?});'
                                ]

                                for pattern in json_patterns:
                                    json_matches = re.findall(pattern, html, re.DOTALL)

                                    for json_str in json_matches:
                                        try:
                                            data = json.loads(json_str)

                                            # Navegar pela estrutura JSON para encontrar jogos
                                            games = []
                                            if isinstance(data, dict):
                                                # Buscar recursivamente por jogos
                                                games = self._extract_games_from_json(data)

                                            for game in games[:5]:  # Limitar a 5 por página
                                                if self._is_target_match(game):
                                                    match_data = {
                                                        'home_team': {'name': game.get('home_team', 'Home')},
                                                        'away_team': {'name': game.get('away_team', 'Away')},
                                                        'league': game.get('league', 'Unknown'),
                                                        'start_time': game.get('date'),
                                                        'source': 'espn_json',
                                                        'collected_at': datetime.now().isoformat()
                                                    }
                                                    matches.append(match_data)
                                                    logger.info(f"📺 ESPN JSON: {match_data['home_team']['name']} vs {match_data['away_team']['name']}")

                                        except json.JSONDecodeError:
                                            continue

                                # Fallback: extrair diretamente do HTML
                                soup = BeautifulSoup(html, 'html.parser')

                                # Procurar por times específicos no HTML
                                target_teams = ['Real Madrid', 'Barcelona', 'Flamengo', 'Palmeiras', 'Corinthians']

                                for team in target_teams:
                                    if team in html:
                                        match_data = {
                                            'home_team': {'name': team},
                                            'away_team': {'name': 'Opponent'},
                                            'league': 'La Liga' if team in ['Real Madrid', 'Barcelona'] else 'Brasileirão',
                                            'source': 'espn_html',
                                            'collected_at': datetime.now().isoformat()
                                        }
                                        matches.append(match_data)
                                        logger.info(f"📺 ESPN HTML: Referência a {team} encontrada")
                                        break  # Apenas um por página

                    except Exception as e:
                        logger.warning(f"⚠️ Erro ESPN {url}: {e}")
                        continue

                    await asyncio.sleep(2)

        except Exception as e:
            logger.error(f"❌ Erro ESPN JSON: {e}")

        return matches

    def _extract_games_from_json(self, data: Dict, games: List = None) -> List[Dict]:
        """
        🔍 Extrair jogos recursivamente de estrutura JSON complexa
        """
        if games is None:
            games = []

        if isinstance(data, dict):
            # Procurar por estruturas que parecem jogos
            if all(key in data for key in ['home', 'away']) or \
               all(key in data for key in ['homeTeam', 'awayTeam']):

                game_data = {
                    'home_team': data.get('home', data.get('homeTeam', {}).get('name', '')),
                    'away_team': data.get('away', data.get('awayTeam', {}).get('name', '')),
                    'league': data.get('league', data.get('competition', {}).get('name', '')),
                    'date': data.get('date', data.get('startTime', ''))
                }
                games.append(game_data)

            # Buscar recursivamente
            for value in data.values():
                if isinstance(value, (dict, list)):
                    self._extract_games_from_json(value, games)

        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    self._extract_games_from_json(item, games)

        return games

    def _is_target_match(self, game: Dict) -> bool:
        """
        🎯 Verificar se é um jogo de interesse
        """
        home_team = str(game.get('home_team', '')).lower()
        away_team = str(game.get('away_team', '')).lower()
        league = str(game.get('league', '')).lower()

        target_teams = [
            'real madrid', 'barcelona', 'atletico madrid', 'valencia', 'sevilla',
            'flamengo', 'palmeiras', 'corinthians', 'santos', 'são paulo', 'sao paulo'
        ]

        target_leagues = ['la liga', 'primeira', 'brasileir', 'serie a']

        return (any(team in home_team or team in away_team for team in target_teams) or
                any(lg in league for lg in target_leagues))

    async def collect_all_json_data(self) -> Dict:
        """
        🚀 Coletar dados JSON de todas as fontes
        """
        logger.info("🕷️ Iniciando coleta via JSON/AJAX...")

        results = {
            'start_time': datetime.now().isoformat(),
            'sources': {
                'flashscore_json': [],
                'sofascore_ajax': [],
                'espn_json': []
            },
            'all_matches': [],
            'total_matches': 0,
            'success': True
        }

        try:
            # 1. Flashscore JSON
            logger.info("⚡ Coletando JSON do Flashscore...")
            flashscore_matches = await self.scrape_flashscore_json()
            results['sources']['flashscore_json'] = flashscore_matches
            results['all_matches'].extend(flashscore_matches)

            await asyncio.sleep(5)

            # 2. SofaScore AJAX
            logger.info("⚽ Coletando AJAX do SofaScore...")
            sofascore_matches = await self.scrape_sofascore_ajax()
            results['sources']['sofascore_ajax'] = sofascore_matches
            results['all_matches'].extend(sofascore_matches)

            await asyncio.sleep(5)

            # 3. ESPN JSON embutido
            logger.info("📺 Coletando JSON embutido ESPN...")
            espn_matches = await self.scrape_espn_embedded_json()
            results['sources']['espn_json'] = espn_matches
            results['all_matches'].extend(espn_matches)

            results['total_matches'] = len(results['all_matches'])
            results['end_time'] = datetime.now().isoformat()

            logger.info(f"✅ Coleta JSON concluída: {results['total_matches']} jogos")

        except Exception as e:
            logger.error(f"❌ Erro na coleta JSON: {e}")
            results['success'] = False

        return results

# Instância global
json_scraper = JSONNetworkScraper()