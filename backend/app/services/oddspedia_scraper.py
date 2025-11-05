"""
🕷️ ODDSPEDIA SCRAPER - Web Scraping Service
Coleta dados de odds, estatísticas e informações de jogos do Oddspedia.com
Complementa os dados das APIs oficiais com informações adicionais
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from urllib.parse import urljoin, quote
import logging

logger = logging.getLogger(__name__)

class OddspediaScraper:
    """
    🔍 Scraper para dados do Oddspedia.com
    Coleta odds, estatísticas e informações de partidas
    """

    def __init__(self):
        self.base_url = "https://oddspedia.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.session = None

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def get_football_matches_today(self) -> List[Dict]:
        """
        📅 Obter jogos de futebol de hoje
        """
        try:
            url = f"{self.base_url}/football"
            logger.info(f"🔍 Buscando jogos de hoje em: {url}")

            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.error(f"❌ Erro HTTP {response.status}")
                    return []

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                matches = []

                # Procurar por containers de jogos
                match_containers = soup.find_all(['div', 'article'], class_=re.compile(r'match|game|fixture'))

                for container in match_containers[:10]:  # Limitar para evitar sobrecarga
                    match_data = await self._extract_match_data(container)
                    if match_data:
                        matches.append(match_data)

                logger.info(f"✅ Extraídos {len(matches)} jogos do Oddspedia")
                return matches

        except Exception as e:
            logger.error(f"❌ Erro ao buscar jogos: {e}")
            return []

    async def get_match_odds(self, match_url: str = None, team1: str = None, team2: str = None) -> Dict:
        """
        💰 Obter odds de uma partida específica
        """
        try:
            if match_url:
                url = urljoin(self.base_url, match_url)
            else:
                # Buscar por URL da partida usando nomes dos times
                url = await self._find_match_url(team1, team2)
                if not url:
                    return {}

            logger.info(f"💰 Buscando odds em: {url}")

            async with self.session.get(url) as response:
                if response.status != 200:
                    return {}

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                odds_data = {
                    'match_url': url,
                    'bookmakers': [],
                    'main_odds': {},
                    'over_under': {},
                    'both_teams_score': {},
                    'scraped_at': datetime.now().isoformat()
                }

                # Extrair odds principais (1X2)
                odds_data['main_odds'] = await self._extract_main_odds(soup)

                # Extrair over/under
                odds_data['over_under'] = await self._extract_over_under_odds(soup)

                # Extrair ambas marcam
                odds_data['both_teams_score'] = await self._extract_btts_odds(soup)

                # Extrair casas de apostas disponíveis
                odds_data['bookmakers'] = await self._extract_bookmakers(soup)

                return odds_data

        except Exception as e:
            logger.error(f"❌ Erro ao buscar odds: {e}")
            return {}

    async def get_team_statistics(self, team_name: str) -> Dict:
        """
        📊 Obter estatísticas de um time
        """
        try:
            # Buscar página do time
            search_url = f"{self.base_url}/search?q={quote(team_name)}"

            async with self.session.get(search_url) as response:
                if response.status != 200:
                    return {}

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                stats = {
                    'team_name': team_name,
                    'recent_form': [],
                    'season_stats': {},
                    'h2h_tendency': {},
                    'scraped_at': datetime.now().isoformat()
                }

                # Extrair forma recente
                stats['recent_form'] = await self._extract_team_form(soup)

                # Extrair estatísticas da temporada
                stats['season_stats'] = await self._extract_season_stats(soup)

                return stats

        except Exception as e:
            logger.error(f"❌ Erro ao buscar estatísticas do time: {e}")
            return {}

    async def _extract_match_data(self, container) -> Optional[Dict]:
        """Extrair dados de uma partida do HTML"""
        try:
            match_data = {}

            # Buscar times
            teams = container.find_all(text=re.compile(r'[A-Za-z\s]{3,}'))
            if len(teams) >= 2:
                match_data['home_team'] = teams[0].strip()
                match_data['away_team'] = teams[1].strip()

            # Buscar horário
            time_element = container.find(text=re.compile(r'\d{2}:\d{2}'))
            if time_element:
                match_data['time'] = time_element.strip()

            # Buscar liga
            league_element = container.find('span', class_=re.compile(r'league|competition'))
            if league_element:
                match_data['league'] = league_element.get_text().strip()

            # Buscar odds básicas
            odds_elements = container.find_all(text=re.compile(r'\d+\.\d+'))
            if len(odds_elements) >= 3:
                match_data['odds'] = {
                    'home': float(odds_elements[0]),
                    'draw': float(odds_elements[1]),
                    'away': float(odds_elements[2])
                }

            # Buscar URL da partida
            link = container.find('a')
            if link and link.get('href'):
                match_data['match_url'] = link['href']

            return match_data if len(match_data) > 2 else None

        except Exception as e:
            logger.debug(f"Erro ao extrair dados da partida: {e}")
            return None

    async def _extract_main_odds(self, soup: BeautifulSoup) -> Dict:
        """Extrair odds principais (1X2)"""
        try:
            odds = {}

            # Padrões comuns para odds 1X2
            odds_containers = soup.find_all(['div', 'span'], class_=re.compile(r'odds|bet|outcome'))

            for container in odds_containers:
                text = container.get_text()
                # Procurar por padrões de odds (ex: 2.50, 3.20, 1.85)
                odds_matches = re.findall(r'\b\d+\.\d{2}\b', text)
                if len(odds_matches) >= 3:
                    odds = {
                        'home': float(odds_matches[0]),
                        'draw': float(odds_matches[1]),
                        'away': float(odds_matches[2])
                    }
                    break

            return odds

        except Exception as e:
            logger.debug(f"Erro ao extrair odds principais: {e}")
            return {}

    async def _extract_over_under_odds(self, soup: BeautifulSoup) -> Dict:
        """Extrair odds over/under"""
        try:
            ou_odds = {}

            # Procurar seções de over/under
            ou_sections = soup.find_all(text=re.compile(r'over|under|o/u', re.IGNORECASE))

            for section in ou_sections:
                parent = section.parent
                if parent:
                    odds_text = parent.get_text()
                    # Procurar padrões como "Over 2.5: 1.85" ou "Under 2.5: 2.10"
                    over_match = re.search(r'over\s*2\.5.*?(\d+\.\d+)', odds_text, re.IGNORECASE)
                    under_match = re.search(r'under\s*2\.5.*?(\d+\.\d+)', odds_text, re.IGNORECASE)

                    if over_match:
                        ou_odds['over_2_5'] = float(over_match.group(1))
                    if under_match:
                        ou_odds['under_2_5'] = float(under_match.group(1))

            return ou_odds

        except Exception as e:
            logger.debug(f"Erro ao extrair odds over/under: {e}")
            return {}

    async def _extract_btts_odds(self, soup: BeautifulSoup) -> Dict:
        """Extrair odds de ambas marcam"""
        try:
            btts_odds = {}

            # Procurar seções de "both teams score" ou "ambas marcam"
            btts_sections = soup.find_all(text=re.compile(r'both.*score|btts|ambas.*marcam', re.IGNORECASE))

            for section in btts_sections:
                parent = section.parent
                if parent:
                    odds_text = parent.get_text()
                    # Procurar odds para sim/não
                    yes_match = re.search(r'yes.*?(\d+\.\d+)|sim.*?(\d+\.\d+)', odds_text, re.IGNORECASE)
                    no_match = re.search(r'no.*?(\d+\.\d+)|não.*?(\d+\.\d+)', odds_text, re.IGNORECASE)

                    if yes_match:
                        btts_odds['yes'] = float(yes_match.group(1) or yes_match.group(2))
                    if no_match:
                        btts_odds['no'] = float(no_match.group(1) or no_match.group(2))

            return btts_odds

        except Exception as e:
            logger.debug(f"Erro ao extrair odds BTTS: {e}")
            return {}

    async def _extract_bookmakers(self, soup: BeautifulSoup) -> List[str]:
        """Extrair lista de casas de apostas disponíveis"""
        try:
            bookmakers = []

            # Procurar logos ou nomes de casas de apostas
            bookmaker_elements = soup.find_all(['img', 'span', 'div'], alt=re.compile(r'bet|bookmaker'))

            for element in bookmaker_elements:
                if element.get('alt'):
                    bookmakers.append(element['alt'])
                elif element.get_text():
                    text = element.get_text().strip()
                    if len(text) < 20 and any(word in text.lower() for word in ['bet', 'casino', 'sport']):
                        bookmakers.append(text)

            return list(set(bookmakers))  # Remover duplicatas

        except Exception as e:
            logger.debug(f"Erro ao extrair bookmakers: {e}")
            return []

    async def _extract_team_form(self, soup: BeautifulSoup) -> List[str]:
        """Extrair forma recente do time (W/L/D)"""
        try:
            form = []

            # Procurar indicadores de forma (W, L, D ou V, E, D)
            form_elements = soup.find_all(text=re.compile(r'[WLD]{5}|[VED]{5}'))

            for element in form_elements:
                form_text = element.strip()
                if len(form_text) == 5 and all(c in 'WLDVED' for c in form_text):
                    form = list(form_text)
                    break

            return form

        except Exception as e:
            logger.debug(f"Erro ao extrair forma do time: {e}")
            return []

    async def _extract_season_stats(self, soup: BeautifulSoup) -> Dict:
        """Extrair estatísticas da temporada"""
        try:
            stats = {}

            # Procurar por números que podem ser estatísticas
            stat_patterns = {
                'goals_for': r'goals.*for.*?(\d+)',
                'goals_against': r'goals.*against.*?(\d+)',
                'wins': r'wins.*?(\d+)',
                'draws': r'draws.*?(\d+)',
                'losses': r'losses.*?(\d+)'
            }

            page_text = soup.get_text().lower()

            for stat_name, pattern in stat_patterns.items():
                match = re.search(pattern, page_text)
                if match:
                    stats[stat_name] = int(match.group(1))

            return stats

        except Exception as e:
            logger.debug(f"Erro ao extrair estatísticas da temporada: {e}")
            return {}

    async def _find_match_url(self, team1: str, team2: str) -> Optional[str]:
        """Encontrar URL de uma partida específica"""
        try:
            search_query = f"{team1} vs {team2}"
            search_url = f"{self.base_url}/search?q={quote(search_query)}"

            async with self.session.get(search_url) as response:
                if response.status != 200:
                    return None

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                # Procurar links para partidas
                match_links = soup.find_all('a', href=re.compile(r'/football/'))

                for link in match_links:
                    href = link.get('href')
                    text = link.get_text().lower()

                    if (team1.lower() in text and team2.lower() in text) or ('vs' in text):
                        return href

                return None

        except Exception as e:
            logger.debug(f"Erro ao buscar URL da partida: {e}")
            return None


# Função de teste e uso
async def test_oddspedia_scraper():
    """🧪 Testar o scraper do Oddspedia"""

    async with OddspediaScraper() as scraper:
        print("🕷️ TESTANDO ODDSPEDIA SCRAPER")
        print("=" * 40)

        # Testar jogos de hoje
        print("📅 Buscando jogos de hoje...")
        matches = await scraper.get_football_matches_today()
        print(f"✅ Encontrados {len(matches)} jogos")

        for i, match in enumerate(matches[:3], 1):
            print(f"\n🎯 Jogo {i}:")
            print(f"   🏠 {match.get('home_team', 'N/A')}")
            print(f"   🏃 {match.get('away_team', 'N/A')}")
            print(f"   ⏰ {match.get('time', 'N/A')}")
            print(f"   🏆 {match.get('league', 'N/A')}")
            if 'odds' in match:
                odds = match['odds']
                print(f"   💰 Odds: {odds.get('home', 'N/A')} | {odds.get('draw', 'N/A')} | {odds.get('away', 'N/A')}")

        # Testar estatísticas de time
        if matches:
            first_match = matches[0]
            team_name = first_match.get('home_team')
            if team_name:
                print(f"\n📊 Buscando estatísticas de {team_name}...")
                stats = await scraper.get_team_statistics(team_name)
                if stats:
                    print(f"   ✅ Estatísticas coletadas")
                    print(f"   📈 Forma: {stats.get('recent_form', [])}")
                    season_stats = stats.get('season_stats', {})
                    if season_stats:
                        print(f"   ⚽ Gols pró: {season_stats.get('goals_for', 'N/A')}")
                        print(f"   🥅 Gols contra: {season_stats.get('goals_against', 'N/A')}")

if __name__ == "__main__":
    asyncio.run(test_oddspedia_scraper())