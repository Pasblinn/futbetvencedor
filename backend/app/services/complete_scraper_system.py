"""
🌐 COMPLETE SCRAPER SYSTEM - Sistema Completo de Scraping
Implementa scraping para TODOS os principais sites de futebol:
- SofaScore (JSON interceptado)
- Flashscore (XHR/AJAX)
- Transfermarkt (HTML + dados históricos)
- WhoScored (xG e estatísticas avançadas)
- FBref (tabelas HTML organizadas)
- Soccerway (confrontos e histórico)
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
from urllib.parse import urljoin, quote, urlparse
import time

logger = logging.getLogger(__name__)

class CompleteScraper:
    """
    🚀 Sistema completo de scraping para todos os sites principais
    """

    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0'
        ]

        self.request_delays = {
            'sofascore': 3,
            'flashscore': 4,
            'transfermarkt': 5,
            'whoscored': 6,
            'fbref': 3,
            'soccerway': 4
        }

    async def scrape_all_sites(self) -> Dict:
        """
        🎯 Scraping completo de todos os sites
        """
        logger.info("🌐 INICIANDO SCRAPING COMPLETO DE TODOS OS SITES...")

        results = {
            'start_time': datetime.now().isoformat(),
            'sites': {
                'sofascore': {'matches': [], 'errors': []},
                'flashscore': {'matches': [], 'errors': []},
                'transfermarkt': {'matches': [], 'errors': []},
                'whoscored': {'matches': [], 'errors': []},
                'fbref': {'matches': [], 'errors': []},
                'soccerway': {'matches': [], 'errors': []}
            },
            'all_matches': [],
            'total_matches': 0,
            'success': True
        }

        try:
            # 1. SofaScore - JSON interceptado
            logger.info("⚽ SCRAPING SOFASCORE (JSON)...")
            sofascore_data = await self._scrape_sofascore()
            results['sites']['sofascore'] = sofascore_data
            results['all_matches'].extend(sofascore_data['matches'])

            await asyncio.sleep(self.request_delays['sofascore'])

            # 2. Flashscore - XHR/AJAX
            logger.info("⚡ SCRAPING FLASHSCORE (AJAX)...")
            flashscore_data = await self._scrape_flashscore()
            results['sites']['flashscore'] = flashscore_data
            results['all_matches'].extend(flashscore_data['matches'])

            await asyncio.sleep(self.request_delays['flashscore'])

            # 3. Transfermarkt - HTML + dados históricos
            logger.info("💰 SCRAPING TRANSFERMARKT (HTML)...")
            transfermarkt_data = await self._scrape_transfermarkt()
            results['sites']['transfermarkt'] = transfermarkt_data
            results['all_matches'].extend(transfermarkt_data['matches'])

            await asyncio.sleep(self.request_delays['transfermarkt'])

            # 4. WhoScored - xG e estatísticas
            logger.info("🎯 SCRAPING WHOSCORED (xG)...")
            whoscored_data = await self._scrape_whoscored()
            results['sites']['whoscored'] = whoscored_data
            results['all_matches'].extend(whoscored_data['matches'])

            await asyncio.sleep(self.request_delays['whoscored'])

            # 5. FBref - tabelas HTML
            logger.info("📊 SCRAPING FBREF (TABELAS)...")
            fbref_data = await self._scrape_fbref()
            results['sites']['fbref'] = fbref_data
            results['all_matches'].extend(fbref_data['matches'])

            await asyncio.sleep(self.request_delays['fbref'])

            # 6. Soccerway - confrontos e histórico
            logger.info("🏆 SCRAPING SOCCERWAY (HISTÓRICO)...")
            soccerway_data = await self._scrape_soccerway()
            results['sites']['soccerway'] = soccerway_data
            results['all_matches'].extend(soccerway_data['matches'])

            results['total_matches'] = len(results['all_matches'])
            results['end_time'] = datetime.now().isoformat()

            logger.info(f"✅ SCRAPING COMPLETO: {results['total_matches']} jogos de {len(results['sites'])} sites")

        except Exception as e:
            logger.error(f"❌ Erro no scraping completo: {e}")
            results['success'] = False

        return results

    async def _scrape_sofascore(self) -> Dict:
        """
        ⚽ SofaScore - Interceptar JSON das requisições internas
        """
        result = {'matches': [], 'errors': []}

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:

                headers = {
                    'User-Agent': random.choice(self.user_agents),
                    'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
                    'Referer': 'https://www.sofascore.com/',
                    'Origin': 'https://www.sofascore.com',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-site'
                }

                today = datetime.now().strftime('%Y-%m-%d')

                # URLs das APIs internas do SofaScore
                api_endpoints = [
                    f'https://api.sofascore.com/api/v1/sport/football/scheduled-events/{today}',
                    'https://api.sofascore.com/api/v1/sport/football/events/live',
                    'https://api.sofascore.com/api/v1/unique-tournament/8/season/61643/events/next/0',   # La Liga 2024/25
                    'https://api.sofascore.com/api/v1/unique-tournament/325/season/58766/events/next/0', # Brasileirão 2024
                    'https://api.sofascore.com/api/v1/unique-tournament/17/season/61627/events/next/0',  # Premier League
                ]

                for endpoint in api_endpoints:
                    try:
                        logger.info(f"🔍 SofaScore API: {endpoint}")

                        async with session.get(endpoint, headers=headers) as response:
                            if response.status == 200:
                                data = await response.json()
                                events = data.get('events', [])

                                logger.info(f"📊 SofaScore: {len(events)} eventos encontrados")

                                for event in events[:15]:  # Limitar para não sobrecarregar
                                    tournament = event.get('tournament', {})
                                    category = tournament.get('category', {})
                                    country = category.get('name', '')

                                    # Filtrar países de interesse
                                    if any(term in country.lower() for term in ['spain', 'brazil', 'england', 'espanha', 'brasil']):
                                        match_data = {
                                            'id': event.get('id'),
                                            'home_team': {
                                                'id': event.get('homeTeam', {}).get('id'),
                                                'name': event.get('homeTeam', {}).get('name', ''),
                                                'shortName': event.get('homeTeam', {}).get('shortName', '')
                                            },
                                            'away_team': {
                                                'id': event.get('awayTeam', {}).get('id'),
                                                'name': event.get('awayTeam', {}).get('name', ''),
                                                'shortName': event.get('awayTeam', {}).get('shortName', '')
                                            },
                                            'tournament': tournament.get('name', ''),
                                            'country': country,
                                            'start_timestamp': event.get('startTimestamp'),
                                            'status': event.get('status', {}).get('description', ''),
                                            'round_info': event.get('roundInfo', {}),
                                            'source': 'sofascore_json',
                                            'collected_at': datetime.now().isoformat()
                                        }

                                        # Adicionar score se disponível
                                        if 'homeScore' in event and 'awayScore' in event:
                                            match_data['score'] = {
                                                'home': event.get('homeScore', {}).get('display'),
                                                'away': event.get('awayScore', {}).get('display')
                                            }

                                        result['matches'].append(match_data)
                                        logger.info(f"⚽ SofaScore: {match_data['home_team']['name']} vs {match_data['away_team']['name']} ({country})")

                            elif response.status == 403:
                                logger.warning("⚠️ SofaScore: Acesso bloqueado (403)")
                                result['errors'].append(f"403 Forbidden: {endpoint}")
                                break
                            elif response.status == 429:
                                logger.warning("⚠️ SofaScore: Rate limit (429)")
                                result['errors'].append(f"Rate limit: {endpoint}")
                                await asyncio.sleep(10)
                                break
                            else:
                                result['errors'].append(f"HTTP {response.status}: {endpoint}")

                    except Exception as e:
                        result['errors'].append(f"Erro {endpoint}: {str(e)}")
                        continue

                    await asyncio.sleep(2)  # Pausa entre endpoints

        except Exception as e:
            logger.error(f"❌ Erro SofaScore: {e}")
            result['errors'].append(str(e))

        return result

    async def _scrape_flashscore(self) -> Dict:
        """
        ⚡ Flashscore - XHR/AJAX interceptado
        """
        result = {'matches': [], 'errors': []}

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=25)
            ) as session:

                headers = {
                    'User-Agent': random.choice(self.user_agents),
                    'Accept': '*/*',
                    'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
                    'Referer': 'https://www.flashscore.com.br/',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Cache-Control': 'no-cache'
                }

                # URLs das APIs do Flashscore (descobertas via Network tab)
                flashscore_apis = [
                    'https://d.flashscore.com.br/x/feed/f_1_0_8_pt-br_1',  # Feed principal
                    'https://d.flashscore.com.br/x/feed/f_1_0_2_pt-br_1',  # Feed alternativo
                    'https://www.flashscore.com.br/res/feed/d-A-fp-1-',     # Feed direto
                    'https://d.flashscore.com.br/x/feed/df_st_1_pt-br',     # Standings
                ]

                for api_url in flashscore_apis:
                    try:
                        logger.info(f"🔍 Flashscore Feed: {api_url}")

                        async with session.get(api_url, headers=headers) as response:
                            if response.status == 200:
                                content = await response.text()

                                # Flashscore usa formato proprietário, extrair com regex
                                # Procurar por padrões de times
                                team_patterns = [
                                    r'(Real Madrid|Barcelona|Atletico Madrid|Valencia|Sevilla)',
                                    r'(Flamengo|Palmeiras|Corinthians|Santos|São Paulo|Sao Paulo)',
                                    r'(Manchester United|Liverpool|Arsenal|Chelsea|Manchester City)'
                                ]

                                matches_found = []
                                for pattern in team_patterns:
                                    teams = re.findall(pattern, content, re.IGNORECASE)
                                    matches_found.extend(teams)

                                # Processar times encontrados
                                for i in range(0, len(matches_found), 2):
                                    if i + 1 < len(matches_found):
                                        match_data = {
                                            'home_team': {'name': matches_found[i]},
                                            'away_team': {'name': matches_found[i + 1]},
                                            'tournament': self._detect_league_from_team(matches_found[i]),
                                            'source': 'flashscore_xhr',
                                            'collected_at': datetime.now().isoformat()
                                        }
                                        result['matches'].append(match_data)
                                        logger.info(f"⚡ Flashscore: {match_data['home_team']['name']} vs {match_data['away_team']['name']}")

                                # Também procurar por dados JSON embebidos
                                json_matches = re.findall(r'\{[^{}]*"home"[^{}]*\}', content)
                                for json_str in json_matches[:5]:  # Limitar a 5
                                    try:
                                        match_json = json.loads(json_str)
                                        if 'home' in match_json and 'away' in match_json:
                                            match_data = {
                                                'home_team': {'name': match_json['home']},
                                                'away_team': {'name': match_json['away']},
                                                'source': 'flashscore_json',
                                                'collected_at': datetime.now().isoformat()
                                            }
                                            result['matches'].append(match_data)
                                    except:
                                        continue

                            else:
                                result['errors'].append(f"HTTP {response.status}: {api_url}")

                    except Exception as e:
                        result['errors'].append(f"Erro {api_url}: {str(e)}")
                        continue

                    await asyncio.sleep(3)

        except Exception as e:
            logger.error(f"❌ Erro Flashscore: {e}")
            result['errors'].append(str(e))

        return result

    async def _scrape_transfermarkt(self) -> Dict:
        """
        💰 Transfermarkt - HTML + dados históricos
        """
        result = {'matches': [], 'errors': []}

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:

                headers = {
                    'User-Agent': random.choice(self.user_agents),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9,pt;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive'
                }

                # URLs do Transfermarkt para ligas principais
                transfermarkt_urls = [
                    'https://www.transfermarkt.com/primera-division/spieltag/wettbewerb/ES1',  # La Liga
                    'https://www.transfermarkt.com/campeonato-brasileiro-serie-a/spieltag/wettbewerb/BRA1',  # Brasileirão
                    'https://www.transfermarkt.com/premier-league/spieltag/wettbewerb/GB1',   # Premier League
                ]

                for url in transfermarkt_urls:
                    try:
                        logger.info(f"🔍 Transfermarkt: {url}")

                        async with session.get(url, headers=headers) as response:
                            if response.status == 200:
                                html = await response.text()
                                soup = BeautifulSoup(html, 'html.parser')

                                # Transfermarkt usa tabelas bem estruturadas
                                match_tables = soup.find_all('table', class_=['items'])

                                for table in match_tables:
                                    rows = table.find_all('tr')

                                    for row in rows[1:11]:  # Pular header, pegar 10 jogos
                                        try:
                                            cells = row.find_all(['td', 'th'])

                                            if len(cells) >= 3:
                                                # Extrair times dos links
                                                team_links = row.find_all('a', href=lambda x: x and '/verein/' in x)

                                                if len(team_links) >= 2:
                                                    home_team = team_links[0].get_text(strip=True)
                                                    away_team = team_links[1].get_text(strip=True)

                                                    # Detectar liga pela URL
                                                    league = 'Unknown'
                                                    if 'primera-division' in url:
                                                        league = 'La Liga'
                                                    elif 'brasileiro' in url:
                                                        league = 'Brasileirão'
                                                    elif 'premier-league' in url:
                                                        league = 'Premier League'

                                                    match_data = {
                                                        'home_team': {'name': home_team},
                                                        'away_team': {'name': away_team},
                                                        'tournament': league,
                                                        'source': 'transfermarkt_html',
                                                        'collected_at': datetime.now().isoformat()
                                                    }

                                                    # Tentar extrair data/hora
                                                    date_cell = row.find('td', class_=['zentriert'])
                                                    if date_cell:
                                                        match_data['date_info'] = date_cell.get_text(strip=True)

                                                    result['matches'].append(match_data)
                                                    logger.info(f"💰 Transfermarkt: {home_team} vs {away_team} ({league})")

                                        except Exception as e:
                                            continue

                            else:
                                result['errors'].append(f"HTTP {response.status}: {url}")

                    except Exception as e:
                        result['errors'].append(f"Erro {url}: {str(e)}")
                        continue

                    await asyncio.sleep(5)  # Respeitar rate limit do Transfermarkt

        except Exception as e:
            logger.error(f"❌ Erro Transfermarkt: {e}")
            result['errors'].append(str(e))

        return result

    async def _scrape_whoscored(self) -> Dict:
        """
        🎯 WhoScored - xG e estatísticas avançadas
        """
        result = {'matches': [], 'errors': []}

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=35)
            ) as session:

                headers = {
                    'User-Agent': random.choice(self.user_agents),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Cache-Control': 'no-cache'
                }

                whoscored_urls = [
                    'https://www.whoscored.com/Regions/206/Tournaments/4/Spain-LaLiga',
                    'https://www.whoscored.com/Regions/31/Tournaments/95/Brazil-Serie-A',
                    'https://www.whoscored.com/Regions/252/Tournaments/2/England-Premier-League',
                ]

                for url in whoscored_urls:
                    try:
                        logger.info(f"🔍 WhoScored: {url}")

                        async with session.get(url, headers=headers) as response:
                            if response.status == 200:
                                html = await response.text()

                                # WhoScored frequentemente tem JSON embutido
                                json_patterns = [
                                    r'var\s+matchCentreData\s*=\s*(\{.*?\});',
                                    r'var\s+fixtureData\s*=\s*(\[.*?\]);',
                                    r'DataStore\.prime\([\'"]tournament[\'"],\s*(\{.*?\})\);'
                                ]

                                for pattern in json_patterns:
                                    matches = re.findall(pattern, html, re.DOTALL)
                                    for match_str in matches:
                                        try:
                                            data = json.loads(match_str)

                                            if isinstance(data, dict):
                                                # Processar dados de match
                                                if 'home' in data and 'away' in data:
                                                    match_data = {
                                                        'home_team': {
                                                            'name': data['home'].get('name', ''),
                                                            'id': data['home'].get('teamId')
                                                        },
                                                        'away_team': {
                                                            'name': data['away'].get('name', ''),
                                                            'id': data['away'].get('teamId')
                                                        },
                                                        'tournament': self._detect_league_from_url(url),
                                                        'xg_home': data['home'].get('xG'),
                                                        'xg_away': data['away'].get('xG'),
                                                        'source': 'whoscored_json',
                                                        'collected_at': datetime.now().isoformat()
                                                    }
                                                    result['matches'].append(match_data)
                                                    logger.info(f"🎯 WhoScored: {match_data['home_team']['name']} vs {match_data['away_team']['name']}")

                                            elif isinstance(data, list):
                                                # Processar lista de fixtures
                                                for fixture in data[:10]:
                                                    if isinstance(fixture, dict) and 'teams' in fixture:
                                                        teams = fixture['teams']
                                                        if len(teams) >= 2:
                                                            match_data = {
                                                                'home_team': {'name': teams[0].get('name', '')},
                                                                'away_team': {'name': teams[1].get('name', '')},
                                                                'tournament': self._detect_league_from_url(url),
                                                                'source': 'whoscored_fixtures',
                                                                'collected_at': datetime.now().isoformat()
                                                            }
                                                            result['matches'].append(match_data)

                                        except json.JSONDecodeError:
                                            continue

                                # Fallback: HTML scraping
                                soup = BeautifulSoup(html, 'html.parser')
                                fixture_divs = soup.find_all('div', class_=['fixture', 'match-report'])

                                for div in fixture_divs[:5]:
                                    try:
                                        team_links = div.find_all('a', href=lambda x: x and '/Teams/' in x)
                                        if len(team_links) >= 2:
                                            home_team = team_links[0].get_text(strip=True)
                                            away_team = team_links[1].get_text(strip=True)

                                            match_data = {
                                                'home_team': {'name': home_team},
                                                'away_team': {'name': away_team},
                                                'tournament': self._detect_league_from_url(url),
                                                'source': 'whoscored_html',
                                                'collected_at': datetime.now().isoformat()
                                            }
                                            result['matches'].append(match_data)
                                            logger.info(f"🎯 WhoScored HTML: {home_team} vs {away_team}")

                                    except Exception as e:
                                        continue

                            else:
                                result['errors'].append(f"HTTP {response.status}: {url}")

                    except Exception as e:
                        result['errors'].append(f"Erro {url}: {str(e)}")
                        continue

                    await asyncio.sleep(6)  # WhoScored é mais lento

        except Exception as e:
            logger.error(f"❌ Erro WhoScored: {e}")
            result['errors'].append(str(e))

        return result

    async def _scrape_fbref(self) -> Dict:
        """
        📊 FBref - tabelas HTML organizadas
        """
        result = {'matches': [], 'errors': []}

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=25)
            ) as session:

                headers = {
                    'User-Agent': random.choice(self.user_agents),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                }

                fbref_urls = [
                    'https://fbref.com/en/comps/12/La-Liga-Stats',
                    'https://fbref.com/en/comps/24/Serie-A-Stats',
                    'https://fbref.com/en/comps/9/Premier-League-Stats',
                    'https://fbref.com/en/comps/11/Ligue-1-Stats',
                ]

                for url in fbref_urls:
                    try:
                        logger.info(f"🔍 FBref: {url}")

                        async with session.get(url, headers=headers) as response:
                            if response.status == 200:
                                html = await response.text()
                                soup = BeautifulSoup(html, 'html.parser')

                                # FBref tem tabelas muito bem organizadas
                                tables = soup.find_all('table')

                                for table in tables:
                                    # Procurar tabelas de fixtures/resultados
                                    if any(term in table.get_text().lower() for term in ['fixture', 'result', 'match', 'score']):
                                        tbody = table.find('tbody')
                                        if tbody:
                                            rows = tbody.find_all('tr')

                                            for row in rows[:12]:  # Limitar a 12 por tabela
                                                try:
                                                    cells = row.find_all(['td', 'th'])

                                                    if len(cells) >= 6:
                                                        # FBref geralmente tem: Date, Home, Score, Away, etc
                                                        home_cell = None
                                                        away_cell = None

                                                        # Procurar células com links de times
                                                        for i, cell in enumerate(cells):
                                                            team_link = cell.find('a', href=lambda x: x and '/squads/' in x)
                                                            if team_link:
                                                                if home_cell is None:
                                                                    home_cell = team_link
                                                                elif away_cell is None:
                                                                    away_cell = team_link
                                                                    break

                                                        if home_cell and away_cell:
                                                            home_team = home_cell.get_text(strip=True)
                                                            away_team = away_cell.get_text(strip=True)

                                                            match_data = {
                                                                'home_team': {'name': home_team},
                                                                'away_team': {'name': away_team},
                                                                'tournament': self._detect_league_from_url(url),
                                                                'source': 'fbref_table',
                                                                'collected_at': datetime.now().isoformat()
                                                            }

                                                            # Tentar extrair score
                                                            score_patterns = [r'(\d+)[–-](\d+)', r'(\d+)\s*[–-]\s*(\d+)']
                                                            row_text = row.get_text()
                                                            for pattern in score_patterns:
                                                                score_match = re.search(pattern, row_text)
                                                                if score_match:
                                                                    match_data['score'] = {
                                                                        'home': int(score_match.group(1)),
                                                                        'away': int(score_match.group(2))
                                                                    }
                                                                    break

                                                            result['matches'].append(match_data)
                                                            logger.info(f"📊 FBref: {home_team} vs {away_team}")

                                                except Exception as e:
                                                    continue

                            else:
                                result['errors'].append(f"HTTP {response.status}: {url}")

                    except Exception as e:
                        result['errors'].append(f"Erro {url}: {str(e)}")
                        continue

                    await asyncio.sleep(3)

        except Exception as e:
            logger.error(f"❌ Erro FBref: {e}")
            result['errors'].append(str(e))

        return result

    async def _scrape_soccerway(self) -> Dict:
        """
        🏆 Soccerway - confrontos e histórico
        """
        result = {'matches': [], 'errors': []}

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=25)
            ) as session:

                headers = {
                    'User-Agent': random.choice(self.user_agents),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                }

                soccerway_urls = [
                    'https://int.soccerway.com/national/spain/primera-division/',
                    'https://int.soccerway.com/national/brazil/serie-a/',
                    'https://int.soccerway.com/national/england/premier-league/',
                ]

                for url in soccerway_urls:
                    try:
                        logger.info(f"🔍 Soccerway: {url}")

                        async with session.get(url, headers=headers) as response:
                            if response.status == 200:
                                html = await response.text()
                                soup = BeautifulSoup(html, 'html.parser')

                                # Soccerway usa divs específicos para jogos
                                match_containers = soup.find_all(['div', 'tr'], class_=lambda x: x and any(term in x.lower() for term in ['match', 'fixture', 'game']))

                                for container in match_containers[:10]:
                                    try:
                                        # Procurar links de times
                                        team_links = container.find_all('a', href=lambda x: x and '/team/' in x)

                                        if len(team_links) >= 2:
                                            home_team = team_links[0].get_text(strip=True)
                                            away_team = team_links[1].get_text(strip=True)

                                            match_data = {
                                                'home_team': {'name': home_team},
                                                'away_team': {'name': away_team},
                                                'tournament': self._detect_league_from_url(url),
                                                'source': 'soccerway_html',
                                                'collected_at': datetime.now().isoformat()
                                            }

                                            # Tentar extrair horário/data
                                            time_elem = container.find(['span', 'div'], class_=lambda x: x and 'time' in x.lower())
                                            if time_elem:
                                                match_data['time_info'] = time_elem.get_text(strip=True)

                                            result['matches'].append(match_data)
                                            logger.info(f"🏆 Soccerway: {home_team} vs {away_team}")

                                    except Exception as e:
                                        continue

                            else:
                                result['errors'].append(f"HTTP {response.status}: {url}")

                    except Exception as e:
                        result['errors'].append(f"Erro {url}: {str(e)}")
                        continue

                    await asyncio.sleep(4)

        except Exception as e:
            logger.error(f"❌ Erro Soccerway: {e}")
            result['errors'].append(str(e))

        return result

    def _detect_league_from_team(self, team_name: str) -> str:
        """Detectar liga pelo nome do time"""
        team_lower = team_name.lower()

        spanish_teams = ['real madrid', 'barcelona', 'atletico', 'valencia', 'sevilla']
        brazilian_teams = ['flamengo', 'palmeiras', 'corinthians', 'santos', 'são paulo', 'sao paulo']
        english_teams = ['manchester', 'liverpool', 'arsenal', 'chelsea', 'tottenham']

        if any(team in team_lower for team in spanish_teams):
            return 'La Liga'
        elif any(team in team_lower for team in brazilian_teams):
            return 'Brasileirão'
        elif any(team in team_lower for team in english_teams):
            return 'Premier League'

        return 'Unknown League'

    def _detect_league_from_url(self, url: str) -> str:
        """Detectar liga pela URL"""
        url_lower = url.lower()

        if any(term in url_lower for term in ['laliga', 'primera', 'spain']):
            return 'La Liga'
        elif any(term in url_lower for term in ['brasileiro', 'brazil', 'serie-a']):
            return 'Brasileirão'
        elif any(term in url_lower for term in ['premier', 'england']):
            return 'Premier League'
        elif any(term in url_lower for term in ['serie-a', 'italy']):
            return 'Serie A'
        elif any(term in url_lower for term in ['ligue', 'france']):
            return 'Ligue 1'

        return 'Unknown League'

# Instância global
complete_scraper = CompleteScraper()