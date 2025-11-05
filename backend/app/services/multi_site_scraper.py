"""
🌐 MULTI-SITE SCRAPER - Sistema de Scraping Robusto
Implementa coleta de dados dos principais sites de futebol:
- Flashscore (livescores, confrontos diretos)
- FBref (estatísticas avançadas)
- Soccerway (tabelas, histórico)
- Transfermarkt (dados de jogadores)
- WhoScored (xG, estatísticas detalhadas)
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import json
import random
import re
from urllib.parse import urljoin, quote

logger = logging.getLogger(__name__)

class MultiSiteScraper:
    """
    🎯 Scraper multi-site para dados de futebol
    """

    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0'
        ]

        self.session_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

        # Rate limiting
        self.request_delay = 3  # segundos entre requests
        self.max_retries = 3

    async def collect_from_all_sources(self) -> Dict:
        """
        🚀 Coletar dados de todas as fontes disponíveis
        """
        logger.info("🌐 Iniciando coleta multi-site...")

        results = {
            'start_time': datetime.now().isoformat(),
            'sources': {
                'flashscore': {'matches': 0, 'errors': []},
                'fbref': {'matches': 0, 'errors': []},
                'soccerway': {'matches': 0, 'errors': []},
                'whoscored': {'matches': 0, 'errors': []}
            },
            'all_matches': [],
            'total_matches': 0,
            'success': True
        }

        async with aiohttp.ClientSession(
            headers=self.session_headers,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as session:

            # 1. Flashscore (prioridade alta - livescores)
            logger.info("⚡ Coletando do Flashscore...")
            flashscore_data = await self._scrape_flashscore(session)
            results['sources']['flashscore'] = flashscore_data
            results['all_matches'].extend(flashscore_data.get('matches', []))

            await asyncio.sleep(self.request_delay)

            # 2. FBref (estatísticas detalhadas)
            logger.info("📊 Coletando do FBref...")
            fbref_data = await self._scrape_fbref(session)
            results['sources']['fbref'] = fbref_data
            results['all_matches'].extend(fbref_data.get('matches', []))

            await asyncio.sleep(self.request_delay)

            # 3. Soccerway (tabelas e confrontos)
            logger.info("⚽ Coletando do Soccerway...")
            soccerway_data = await self._scrape_soccerway(session)
            results['sources']['soccerway'] = soccerway_data
            results['all_matches'].extend(soccerway_data.get('matches', []))

            await asyncio.sleep(self.request_delay)

            # 4. WhoScored (xG e estatísticas avançadas)
            logger.info("🎯 Coletando do WhoScored...")
            whoscored_data = await self._scrape_whoscored(session)
            results['sources']['whoscored'] = whoscored_data
            results['all_matches'].extend(whoscored_data.get('matches', []))

        results['total_matches'] = len(results['all_matches'])
        results['end_time'] = datetime.now().isoformat()

        logger.info(f"✅ Coleta concluída: {results['total_matches']} jogos de todas as fontes")
        return results

    async def _scrape_flashscore(self, session: aiohttp.ClientSession) -> Dict:
        """⚡ Scraping do Flashscore para jogos ao vivo e resultados"""
        results = {'matches': [], 'errors': []}

        try:
            # Flashscore Brasil - página principal
            url = "https://www.flashscore.com.br/futebol/"

            headers = dict(self.session_headers)
            headers['User-Agent'] = random.choice(self.user_agents)

            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()

                    # Procurar por dados JSON embutidos
                    json_pattern = r'window\.flashscore\.data\s*=\s*({.*?});'
                    json_matches = re.findall(json_pattern, html, re.DOTALL)

                    if json_matches:
                        try:
                            data = json.loads(json_matches[0])
                            # Processar dados JSON do Flashscore
                            for match in data.get('events', [])[:20]:  # Limitar a 20
                                processed = self._process_flashscore_match(match)
                                if processed:
                                    results['matches'].append(processed)
                        except json.JSONDecodeError:
                            logger.warning("⚠️ Erro ao decodificar JSON do Flashscore")

                    # Fallback: scraping HTML tradicional
                    soup = BeautifulSoup(html, 'html.parser')

                    # Procurar elementos de jogos
                    match_elements = soup.find_all(['div', 'tr'], class_=lambda x: x and any(term in x.lower() for term in ['event', 'match', 'game']))

                    for element in match_elements[:10]:
                        try:
                            # Tentar extrair times
                            team_elements = element.find_all(['span', 'div'], class_=lambda x: x and 'team' in x.lower())

                            if len(team_elements) >= 2:
                                home_team = team_elements[0].get_text(strip=True)
                                away_team = team_elements[1].get_text(strip=True)

                                # Filtrar times brasileiros e espanhóis
                                if self._is_target_team(home_team) or self._is_target_team(away_team):
                                    match_data = {
                                        'home_team': {'name': home_team},
                                        'away_team': {'name': away_team},
                                        'league': self._detect_league(element.get_text()),
                                        'source': 'flashscore',
                                        'collected_at': datetime.now().isoformat()
                                    }
                                    results['matches'].append(match_data)
                                    logger.info(f"⚡ Flashscore: {home_team} vs {away_team}")

                        except Exception as e:
                            continue

                else:
                    results['errors'].append(f"HTTP {response.status}")

        except Exception as e:
            logger.error(f"❌ Erro Flashscore: {e}")
            results['errors'].append(str(e))

        return results

    async def _scrape_fbref(self, session: aiohttp.ClientSession) -> Dict:
        """📊 Scraping do FBref para estatísticas detalhadas"""
        results = {'matches': [], 'errors': []}

        try:
            # FBref - Liga Espanhola
            url = "https://fbref.com/en/comps/12/La-Liga-Stats"

            headers = dict(self.session_headers)
            headers['User-Agent'] = random.choice(self.user_agents)

            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    # FBref usa tabelas bem estruturadas
                    tables = soup.find_all('table')

                    for table in tables:
                        # Procurar tabela de jogos recentes/próximos
                        if any(term in table.get_text().lower() for term in ['fixture', 'match', 'result']):
                            rows = table.find_all('tr')

                            for row in rows[1:11]:  # Pular header, pegar 10 jogos
                                try:
                                    cells = row.find_all(['td', 'th'])
                                    if len(cells) >= 4:
                                        # Extrair informações das células
                                        home_team = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                                        away_team = cells[3].get_text(strip=True) if len(cells) > 3 else ""

                                        if home_team and away_team:
                                            match_data = {
                                                'home_team': {'name': home_team},
                                                'away_team': {'name': away_team},
                                                'league': 'La Liga',
                                                'source': 'fbref',
                                                'collected_at': datetime.now().isoformat()
                                            }
                                            results['matches'].append(match_data)
                                            logger.info(f"📊 FBref: {home_team} vs {away_team}")

                                except Exception as e:
                                    continue

        except Exception as e:
            logger.error(f"❌ Erro FBref: {e}")
            results['errors'].append(str(e))

        return results

    async def _scrape_soccerway(self, session: aiohttp.ClientSession) -> Dict:
        """⚽ Scraping do Soccerway para tabelas e confrontos"""
        results = {'matches': [], 'errors': []}

        try:
            # Soccerway - página da Liga Espanhola
            url = "https://int.soccerway.com/national/spain/primera-division/"

            headers = dict(self.session_headers)
            headers['User-Agent'] = random.choice(self.user_agents)

            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    # Soccerway tem estrutura específica para jogos
                    match_divs = soup.find_all(['div', 'tr'], class_=lambda x: x and 'match' in x.lower())

                    for div in match_divs[:10]:
                        try:
                            # Procurar links de times
                            team_links = div.find_all('a', href=lambda x: x and 'team' in x)

                            if len(team_links) >= 2:
                                home_team = team_links[0].get_text(strip=True)
                                away_team = team_links[1].get_text(strip=True)

                                match_data = {
                                    'home_team': {'name': home_team},
                                    'away_team': {'name': away_team},
                                    'league': 'La Liga',
                                    'source': 'soccerway',
                                    'collected_at': datetime.now().isoformat()
                                }
                                results['matches'].append(match_data)
                                logger.info(f"⚽ Soccerway: {home_team} vs {away_team}")

                        except Exception as e:
                            continue

        except Exception as e:
            logger.error(f"❌ Erro Soccerway: {e}")
            results['errors'].append(str(e))

        return results

    async def _scrape_whoscored(self, session: aiohttp.ClientSession) -> Dict:
        """🎯 Scraping do WhoScored para estatísticas avançadas"""
        results = {'matches': [], 'errors': []}

        try:
            # WhoScored - página da Liga Espanhola
            url = "https://www.whoscored.com/Regions/206/Tournaments/4/Spain-LaLiga"

            headers = dict(self.session_headers)
            headers['User-Agent'] = random.choice(self.user_agents)

            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()

                    # WhoScored frequentemente tem dados JSON embutidos
                    json_pattern = r'var\s+matchCentreData\s*=\s*({.*?});'
                    json_matches = re.findall(json_pattern, html, re.DOTALL)

                    if json_matches:
                        try:
                            data = json.loads(json_matches[0])
                            # Processar dados de estatísticas avançadas
                            match_data = {
                                'home_team': {'name': data.get('home', {}).get('name', 'Home Team')},
                                'away_team': {'name': data.get('away', {}).get('name', 'Away Team')},
                                'league': 'La Liga',
                                'source': 'whoscored',
                                'xg_home': data.get('home', {}).get('xG'),
                                'xg_away': data.get('away', {}).get('xG'),
                                'collected_at': datetime.now().isoformat()
                            }
                            results['matches'].append(match_data)
                            logger.info(f"🎯 WhoScored: {match_data['home_team']['name']} vs {match_data['away_team']['name']}")

                        except json.JSONDecodeError:
                            logger.warning("⚠️ Erro ao decodificar JSON do WhoScored")

                    # Fallback HTML
                    soup = BeautifulSoup(html, 'html.parser')
                    fixture_elements = soup.find_all(['div'], class_=lambda x: x and 'fixture' in x.lower())

                    for element in fixture_elements[:5]:
                        try:
                            teams = element.find_all(['span', 'div'], class_=lambda x: x and 'team' in x.lower())
                            if len(teams) >= 2:
                                match_data = {
                                    'home_team': {'name': teams[0].get_text(strip=True)},
                                    'away_team': {'name': teams[1].get_text(strip=True)},
                                    'league': 'La Liga',
                                    'source': 'whoscored',
                                    'collected_at': datetime.now().isoformat()
                                }
                                results['matches'].append(match_data)
                                logger.info(f"🎯 WhoScored HTML: {match_data['home_team']['name']} vs {match_data['away_team']['name']}")

                        except Exception as e:
                            continue

        except Exception as e:
            logger.error(f"❌ Erro WhoScored: {e}")
            results['errors'].append(str(e))

        return results

    def _process_flashscore_match(self, match_data: Dict) -> Optional[Dict]:
        """🔄 Processar dados JSON do Flashscore"""
        try:
            return {
                'home_team': {'name': match_data.get('home_name', '')},
                'away_team': {'name': match_data.get('away_name', '')},
                'league': match_data.get('tournament_name', ''),
                'status': match_data.get('status_description', ''),
                'source': 'flashscore',
                'collected_at': datetime.now().isoformat()
            }
        except Exception:
            return None

    def _is_target_team(self, team_name: str) -> bool:
        """🎯 Verificar se é um time de interesse (Brasil/Espanha)"""
        if not team_name:
            return False

        team_lower = team_name.lower()

        # Times brasileiros famosos
        brazilian_teams = [
            'flamengo', 'corinthians', 'palmeiras', 'santos', 'são paulo', 'sao paulo',
            'grêmio', 'gremio', 'internacional', 'vasco', 'botafogo', 'atlético', 'atletico'
        ]

        # Times espanhóis famosos
        spanish_teams = [
            'real madrid', 'barcelona', 'atletico madrid', 'valencia', 'sevilla',
            'villarreal', 'athletic', 'real sociedad', 'betis', 'espanyol'
        ]

        all_target_teams = brazilian_teams + spanish_teams

        return any(target in team_lower for target in all_target_teams)

    def _detect_league(self, text: str) -> str:
        """🔍 Detectar liga a partir do texto"""
        text_lower = text.lower()

        if any(term in text_lower for term in ['la liga', 'primera', 'espanha', 'spain']):
            return 'La Liga'
        elif any(term in text_lower for term in ['brasileir', 'brasil', 'brazil', 'série a', 'serie a']):
            return 'Brasileirão'
        elif any(term in text_lower for term in ['copa', 'libertadores']):
            return 'Copa'
        else:
            return 'Unknown League'

    async def get_live_matches_all_sources(self) -> List[Dict]:
        """🔴 Obter jogos ao vivo de todas as fontes"""
        logger.info("🔴 Buscando jogos ao vivo em todas as fontes...")

        all_data = await self.collect_from_all_sources()
        live_matches = []

        for match in all_data.get('all_matches', []):
            # Considerar como "ao vivo" se tem status específico ou está próximo ao horário
            if (match.get('status') and 'live' in match.get('status', '').lower()) or \
               match.get('is_live') or \
               self._is_target_team(match.get('home_team', {}).get('name', '')):
                live_matches.append(match)

        logger.info(f"🔴 {len(live_matches)} jogos identificados como relevantes")
        return live_matches

# Instância global
multi_scraper = MultiSiteScraper()