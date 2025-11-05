"""
🎯 PROFESSIONAL SCRAPER - Sites profissionais de dados esportivos
Foca nos melhores sites para coleta de dados de futebol:
- Sofascore (JSON API calls)
- Flashscore (XHR/JSON endpoints)
- FBref (HTML tables)
- Transfermarkt (structured data)
- WhoScored (match statistics)
- Soccerway (fixtures & results)
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
import time

logger = logging.getLogger(__name__)

class ProfessionalScraper:
    """
    🎯 Scraper profissional para sites de dados esportivos
    """

    def __init__(self):
        self.session = None

        # Headers realistas para cada site
        self.site_headers = {
            'sofascore': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Origin': 'https://www.sofascore.com',
                'Referer': 'https://www.sofascore.com/',
                'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"'
            },
            'flashscore': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': 'https://www.flashscore.com/'
            },
            'fbref': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': 'https://fbref.com/'
            }
        }

    async def scrape_professional_sources(self) -> Dict:
        """
        🎯 Coleta de dados dos melhores sites profissionais
        """
        logger.info("🎯 INICIANDO SCRAPING PROFISSIONAL...")

        results = {
            'start_time': datetime.now().isoformat(),
            'sources': {},
            'all_matches': [],
            'total_matches': 0,
            'success': True
        }

        # Timeout para toda a operação
        timeout = aiohttp.ClientTimeout(total=60)

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                self.session = session

                # 1. Sofascore (melhor fonte)
                logger.info("⚽ Coletando Sofascore...")
                sofascore_matches = await self._scrape_sofascore()
                results['sources']['sofascore'] = sofascore_matches
                results['all_matches'].extend(sofascore_matches)
                await asyncio.sleep(3)

                # 2. FBref (dados históricos confiáveis)
                logger.info("📊 Coletando FBref...")
                fbref_matches = await self._scrape_fbref()
                results['sources']['fbref'] = fbref_matches
                results['all_matches'].extend(fbref_matches)
                await asyncio.sleep(3)

                # 3. Flashscore (livescores)
                logger.info("⚡ Coletando Flashscore...")
                flashscore_matches = await self._scrape_flashscore()
                results['sources']['flashscore'] = flashscore_matches
                results['all_matches'].extend(flashscore_matches)
                await asyncio.sleep(3)

                # 4. Soccerway (fixtures organizados)
                logger.info("🌐 Coletando Soccerway...")
                soccerway_matches = await self._scrape_soccerway()
                results['sources']['soccerway'] = soccerway_matches
                results['all_matches'].extend(soccerway_matches)

        except Exception as e:
            logger.error(f"❌ Erro no scraping profissional: {e}")
            results['success'] = False

        results['total_matches'] = len(results['all_matches'])
        results['end_time'] = datetime.now().isoformat()

        logger.info(f"✅ SCRAPING PROFISSIONAL: {results['total_matches']} jogos coletados")
        return results

    async def _scrape_sofascore(self) -> List[Dict]:
        """
        ⚽ Sofascore - JSON API calls (melhor fonte)
        """
        matches = []

        try:
            # Endpoints Sofascore conhecidos
            today = datetime.now().strftime('%Y-%m-%d')

            sofascore_endpoints = [
                # Matches de hoje
                f'https://api.sofascore.com/api/v1/sport/football/scheduled-events/{today}',
                # Top leagues events
                'https://api.sofascore.com/api/v1/sport/football/events/live',
                # Próximos jogos principais
                'https://api.sofascore.com/api/v1/sport/football/events/next',
            ]

            headers = self.site_headers['sofascore']

            for endpoint in sofascore_endpoints:
                try:
                    logger.info(f"🔍 Sofascore endpoint: {endpoint}")

                    async with self.session.get(endpoint, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()

                            # Processar eventos/jogos
                            events = []
                            if 'events' in data:
                                events = data['events']
                            elif 'scheduledEvents' in data:
                                events = data['scheduledEvents']
                            elif isinstance(data, list):
                                events = data

                            for event in events[:10]:  # Limite por endpoint
                                try:
                                    if 'homeTeam' in event and 'awayTeam' in event:
                                        home_team = event['homeTeam'].get('name', 'Unknown')
                                        away_team = event['awayTeam'].get('name', 'Unknown')

                                        match_data = {
                                            'home_team': {'name': home_team},
                                            'away_team': {'name': away_team},
                                            'tournament': event.get('tournament', {}).get('name', 'Unknown'),
                                            'startTime': event.get('startTimestamp'),
                                            'status': event.get('status', {}).get('type', 'scheduled'),
                                            'source': 'sofascore_api',
                                            'match_id': event.get('id'),
                                            'collected_at': datetime.now().isoformat()
                                        }

                                        matches.append(match_data)
                                        logger.info(f"⚽ Sofascore: {home_team} vs {away_team}")

                                except Exception as e:
                                    logger.warning(f"⚠️ Erro processando evento Sofascore: {e}")
                                    continue

                        elif response.status == 403:
                            logger.warning(f"⚠️ Sofascore bloqueado: {endpoint}")
                        else:
                            logger.warning(f"⚠️ Sofascore status {response.status}: {endpoint}")

                except Exception as e:
                    logger.warning(f"⚠️ Erro endpoint Sofascore {endpoint}: {e}")
                    continue

                await asyncio.sleep(2)  # Rate limiting

        except Exception as e:
            logger.error(f"❌ Erro Sofascore: {e}")

        return matches

    async def _scrape_fbref(self) -> List[Dict]:
        """
        📊 FBref - HTML tables com dados estruturados
        """
        matches = []

        try:
            headers = self.site_headers['fbref']

            # URLs principais do FBref
            fbref_urls = [
                'https://fbref.com/en/comps/9/schedule/Premier-League-Fixtures',
                'https://fbref.com/en/comps/12/schedule/La-Liga-Fixtures',
                'https://fbref.com/en/comps/11/schedule/Serie-A-Fixtures',
                'https://fbref.com/en/comps/20/schedule/Bundesliga-Fixtures',
                'https://fbref.com/en/matches/',  # Página geral de jogos
            ]

            for url in fbref_urls:
                try:
                    logger.info(f"📊 FBref: {url}")

                    async with self.session.get(url, headers=headers) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')

                            # Procurar tabelas de fixtures
                            tables = soup.find_all('table', {'class': ['stats_table', 'min_width']})

                            for table in tables:
                                rows = table.find_all('tr')

                                for row in rows[1:15]:  # Skip header, limite 15
                                    try:
                                        cells = row.find_all(['td', 'th'])
                                        if len(cells) >= 6:  # Estrutura mínima esperada

                                            # Buscar times nas células
                                            home_team = None
                                            away_team = None

                                            for cell in cells:
                                                text = cell.get_text().strip()
                                                links = cell.find_all('a')

                                                # Se tem link, provavelmente é time
                                                if links and len(text) > 2:
                                                    if home_team is None:
                                                        home_team = text
                                                    elif away_team is None:
                                                        away_team = text
                                                        break

                                            if home_team and away_team and home_team != away_team:
                                                match_data = {
                                                    'home_team': {'name': home_team},
                                                    'away_team': {'name': away_team},
                                                    'tournament': self._detect_league_from_url(url),
                                                    'source': 'fbref_table',
                                                    'collected_at': datetime.now().isoformat()
                                                }

                                                matches.append(match_data)
                                                logger.info(f"📊 FBref: {home_team} vs {away_team}")

                                    except Exception:
                                        continue

                        elif response.status == 403:
                            logger.warning(f"⚠️ FBref bloqueado: {url}")
                        else:
                            logger.warning(f"⚠️ FBref status {response.status}: {url}")

                except Exception as e:
                    logger.warning(f"⚠️ Erro FBref {url}: {e}")
                    continue

                await asyncio.sleep(3)  # Rate limiting mais conservador

        except Exception as e:
            logger.error(f"❌ Erro FBref: {e}")

        return matches

    async def _scrape_flashscore(self) -> List[Dict]:
        """
        ⚡ Flashscore - XHR/JSON endpoints
        """
        matches = []

        try:
            headers = self.site_headers['flashscore']

            # Endpoints Flashscore conhecidos (podem mudar)
            base_url = 'https://www.flashscore.com'

            # Página principal para buscar dados
            main_urls = [
                'https://www.flashscore.com/',
                'https://www.flashscore.com/football/',
                'https://www.flashscore.com/football/england/premier-league/',
                'https://www.flashscore.com/football/spain/laliga/',
            ]

            for url in main_urls:
                try:
                    logger.info(f"⚡ Flashscore: {url}")

                    async with self.session.get(url, headers=headers) as response:
                        if response.status == 200:
                            html = await response.text()

                            # Buscar dados JSON embarcados
                            json_patterns = [
                                r'window\._initial_state\s*=\s*({.+?});',
                                r'window\.__INITIAL_STATE__\s*=\s*({.+?});',
                                r'"events":\s*(\[.+?\])',
                                r'"fixtures":\s*(\[.+?\])'
                            ]

                            for pattern in json_patterns:
                                json_matches = re.finditer(pattern, html, re.DOTALL)

                                for json_match in json_matches:
                                    try:
                                        json_str = json_match.group(1)
                                        data = json.loads(json_str)

                                        # Processar estrutura de dados
                                        events = []
                                        if isinstance(data, list):
                                            events = data
                                        elif isinstance(data, dict):
                                            if 'events' in data:
                                                events = data['events']
                                            elif 'fixtures' in data:
                                                events = data['fixtures']

                                        for event in events[:8]:  # Limite por padrão
                                            if isinstance(event, dict):
                                                home_name = event.get('home_name') or event.get('homeTeam', {}).get('name')
                                                away_name = event.get('away_name') or event.get('awayTeam', {}).get('name')

                                                if home_name and away_name:
                                                    match_data = {
                                                        'home_team': {'name': home_name},
                                                        'away_team': {'name': away_name},
                                                        'tournament': event.get('tournament_name', 'Flashscore'),
                                                        'source': 'flashscore_json',
                                                        'collected_at': datetime.now().isoformat()
                                                    }

                                                    matches.append(match_data)
                                                    logger.info(f"⚡ Flashscore: {home_name} vs {away_name}")

                                    except json.JSONDecodeError:
                                        continue
                                    except Exception as e:
                                        logger.warning(f"⚠️ Erro JSON Flashscore: {e}")
                                        continue

                            # Buscar também por padrões HTML
                            soup = BeautifulSoup(html, 'html.parser')

                            # Classes típicas do Flashscore
                            match_elements = soup.find_all(['div', 'tr'], class_=lambda x: x and any(term in x.lower() for term in ['event', 'match', 'fixture', 'game']))

                            for element in match_elements[:10]:
                                try:
                                    text = element.get_text()
                                    # Procurar padrão de times
                                    teams_match = re.search(r'([A-Z][a-zA-Z\s]+?)\s+(?:vs\.?|x|-)\s+([A-Z][a-zA-Z\s]+)', text)

                                    if teams_match:
                                        home_team = teams_match.group(1).strip()
                                        away_team = teams_match.group(2).strip()

                                        if len(home_team) > 3 and len(away_team) > 3:
                                            match_data = {
                                                'home_team': {'name': home_team},
                                                'away_team': {'name': away_team},
                                                'tournament': 'Flashscore HTML',
                                                'source': 'flashscore_html',
                                                'collected_at': datetime.now().isoformat()
                                            }

                                            matches.append(match_data)
                                            logger.info(f"⚡ Flashscore HTML: {home_team} vs {away_team}")

                                except Exception:
                                    continue

                        elif response.status == 403:
                            logger.warning(f"⚠️ Flashscore bloqueado: {url}")
                        else:
                            logger.warning(f"⚠️ Flashscore status {response.status}: {url}")

                except Exception as e:
                    logger.warning(f"⚠️ Erro Flashscore {url}: {e}")
                    continue

                await asyncio.sleep(4)  # Rate limiting

        except Exception as e:
            logger.error(f"❌ Erro Flashscore: {e}")

        return matches

    async def _scrape_soccerway(self) -> List[Dict]:
        """
        🌐 Soccerway - Fixtures organizados
        """
        matches = []

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': 'https://int.soccerway.com/'
            }

            soccerway_urls = [
                'https://int.soccerway.com/matches/',
                'https://int.soccerway.com/national/england/premier-league/20232024/regular-season/fixtures/',
                'https://int.soccerway.com/national/spain/primera-division/20232024/regular-season/fixtures/',
                'https://int.soccerway.com/national/italy/serie-a/20232024/regular-season/fixtures/',
            ]

            for url in soccerway_urls:
                try:
                    logger.info(f"🌐 Soccerway: {url}")

                    async with self.session.get(url, headers=headers) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')

                            # Procurar tabelas de matches
                            tables = soup.find_all('table', class_=lambda x: x and 'matches' in x.lower())

                            if not tables:
                                # Buscar por outras estruturas
                                tables = soup.find_all('table')

                            for table in tables:
                                rows = table.find_all('tr')

                                for row in rows[:15]:  # Limite por tabela
                                    try:
                                        # Procurar links de times
                                        team_links = row.find_all('a', href=lambda x: x and '/team/' in x)

                                        if len(team_links) >= 2:
                                            home_team = team_links[0].get_text().strip()
                                            away_team = team_links[1].get_text().strip()

                                            if home_team and away_team and home_team != away_team:
                                                match_data = {
                                                    'home_team': {'name': home_team},
                                                    'away_team': {'name': away_team},
                                                    'tournament': self._detect_league_from_url(url),
                                                    'source': 'soccerway',
                                                    'collected_at': datetime.now().isoformat()
                                                }

                                                matches.append(match_data)
                                                logger.info(f"🌐 Soccerway: {home_team} vs {away_team}")

                                    except Exception:
                                        continue

                        elif response.status == 403:
                            logger.warning(f"⚠️ Soccerway bloqueado: {url}")
                        else:
                            logger.warning(f"⚠️ Soccerway status {response.status}: {url}")

                except Exception as e:
                    logger.warning(f"⚠️ Erro Soccerway {url}: {e}")
                    continue

                await asyncio.sleep(3)

        except Exception as e:
            logger.error(f"❌ Erro Soccerway: {e}")

        return matches

    def _detect_league_from_url(self, url: str) -> str:
        """Detectar liga pela URL"""
        url_lower = url.lower()

        if any(term in url_lower for term in ['premier-league', 'england']):
            return 'Premier League'
        elif any(term in url_lower for term in ['la-liga', 'laliga', 'spain', 'primera']):
            return 'La Liga'
        elif any(term in url_lower for term in ['serie-a', 'italy']):
            return 'Serie A'
        elif any(term in url_lower for term in ['bundesliga', 'germany']):
            return 'Bundesliga'
        elif any(term in url_lower for term in ['ligue-1', 'france']):
            return 'Ligue 1'

        return 'International'

# Instância global
professional_scraper = ProfessionalScraper()