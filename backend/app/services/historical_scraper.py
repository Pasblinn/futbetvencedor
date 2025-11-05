"""
📜 HISTORICAL SCRAPER - Scraper de dados históricos
Coleta dados antigos sem preocupação com rate limits
Foco em resultados de temporadas passadas para ML
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

logger = logging.getLogger(__name__)

class HistoricalScraper:
    """
    📜 Scraper especializado em dados históricos
    """

    def __init__(self):
        # Headers rotativos para evitar detecção
        self.headers_pool = [
            {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,pt-BR;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive'
            },
            {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,pt;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br'
            }
        ]

        # Sites com dados históricos abertos
        self.historical_sources = {
            'fbref_historical': {
                'base_url': 'https://fbref.com',
                'leagues': {
                    'la_liga': '/en/comps/12/2023-2024/schedule/2023-2024-La-Liga-Fixtures',
                    'premier_league': '/en/comps/9/2023-2024/schedule/2023-2024-Premier-League-Fixtures',
                    'serie_a': '/en/comps/11/2023-2024/schedule/2023-2024-Serie-A-Fixtures',
                    'bundesliga': '/en/comps/20/2023-2024/schedule/2023-2024-Bundesliga-Fixtures'
                }
            },
            'wikipedia_results': {
                'base_url': 'https://en.wikipedia.org',
                'leagues': {
                    'la_liga': '/wiki/2023%E2%80%9324_La_Liga',
                    'premier_league': '/wiki/2023%E2%80%9324_Premier_League',
                    'brasileirao': '/wiki/2023_Campeonato_Brasileiro_S%C3%A9rie_A'
                }
            },
            'github_datasets': {
                'base_url': 'https://raw.githubusercontent.com',
                'sources': [
                    '/openfootball/football.json/master/2023-24/es.1.json',  # La Liga
                    '/openfootball/football.json/master/2023-24/en.1.json',  # Premier League
                    '/openfootball/football.json/master/2023-24/de.1.json',  # Bundesliga
                    '/openfootball/football.json/master/2023-24/it.1.json'   # Serie A
                ]
            }
        }

    async def scrape_historical_data(self, target_matches: int = 200) -> Dict:
        """
        📜 Coletar dados históricos de múltiplas fontes
        """
        logger.info(f"📜 INICIANDO SCRAPING HISTÓRICO - Meta: {target_matches} jogos")

        results = {
            'start_time': datetime.now().isoformat(),
            'sources': {},
            'all_historical_matches': [],
            'total_matches': 0,
            'success': True
        }

        try:
            # 1. FBref (dados estruturados)
            logger.info("📊 Coletando dados do FBref...")
            fbref_matches = await self._scrape_fbref_historical()
            results['sources']['fbref'] = fbref_matches
            results['all_historical_matches'].extend(fbref_matches)

            await asyncio.sleep(3)

            # 2. GitHub datasets (JSON estruturado)
            logger.info("📂 Coletando datasets GitHub...")
            github_matches = await self._scrape_github_datasets()
            results['sources']['github'] = github_matches
            results['all_historical_matches'].extend(github_matches)

            await asyncio.sleep(2)

            # 3. Wikipedia (backup com resultados)
            logger.info("📖 Coletando dados da Wikipedia...")
            wiki_matches = await self._scrape_wikipedia_results()
            results['sources']['wikipedia'] = wiki_matches
            results['all_historical_matches'].extend(wiki_matches)

            # 4. Filtrar e remover duplicatas
            unique_matches = self._remove_duplicates(results['all_historical_matches'])
            results['all_historical_matches'] = unique_matches
            results['total_matches'] = len(unique_matches)

        except Exception as e:
            logger.error(f"❌ Erro no scraping histórico: {e}")
            results['success'] = False

        results['end_time'] = datetime.now().isoformat()
        logger.info(f"📜 SCRAPING HISTÓRICO CONCLUÍDO: {results['total_matches']} jogos únicos")

        return results

    async def _scrape_fbref_historical(self) -> List[Dict]:
        """
        📊 Coletar dados históricos do FBref
        """
        matches = []

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:

                for league_key, url_path in self.historical_sources['fbref_historical']['leagues'].items():
                    try:
                        full_url = self.historical_sources['fbref_historical']['base_url'] + url_path
                        headers = random.choice(self.headers_pool)

                        logger.info(f"📊 FBref - {league_key}: {full_url}")

                        async with session.get(full_url, headers=headers) as response:
                            if response.status == 200:
                                html = await response.text()
                                soup = BeautifulSoup(html, 'html.parser')

                                # Procurar tabelas de resultados
                                tables = soup.find_all('table', {'class': 'stats_table'})

                                for table in tables:
                                    rows = table.find_all('tr')

                                    for row in rows[1:]:  # Skip header
                                        try:
                                            cells = row.find_all(['td', 'th'])
                                            if len(cells) >= 8:  # Estrutura mínima esperada

                                                # Tentar extrair informações
                                                date_cell = cells[1] if len(cells) > 1 else None
                                                home_cell = cells[3] if len(cells) > 3 else None
                                                score_cell = cells[4] if len(cells) > 4 else None
                                                away_cell = cells[5] if len(cells) > 5 else None

                                                if home_cell and away_cell and score_cell:
                                                    home_team = home_cell.get_text().strip()
                                                    away_team = away_cell.get_text().strip()
                                                    score_text = score_cell.get_text().strip()

                                                    # Parse do placar
                                                    score_match = re.search(r'(\d+)[-–](\d+)', score_text)
                                                    if score_match and home_team and away_team:
                                                        home_score = int(score_match.group(1))
                                                        away_score = int(score_match.group(2))

                                                        match_data = {
                                                            'home_team': {'name': home_team},
                                                            'away_team': {'name': away_team},
                                                            'tournament': self._get_league_name(league_key),
                                                            'home_score': home_score,
                                                            'away_score': away_score,
                                                            'status': 'FINISHED',
                                                            'source': 'fbref_historical',
                                                            'collected_at': datetime.now().isoformat()
                                                        }

                                                        if date_cell:
                                                            match_data['match_date'] = date_cell.get_text().strip()

                                                        matches.append(match_data)
                                                        logger.info(f"📊 FBref: {home_team} {home_score}-{away_score} {away_team}")

                                        except Exception as e:
                                            continue

                            else:
                                logger.warning(f"⚠️ FBref status {response.status}: {full_url}")

                    except Exception as e:
                        logger.warning(f"⚠️ Erro FBref {league_key}: {e}")
                        continue

                    await asyncio.sleep(random.uniform(2, 4))

        except Exception as e:
            logger.error(f"❌ Erro geral FBref: {e}")

        return matches

    async def _scrape_github_datasets(self) -> List[Dict]:
        """
        📂 Coletar datasets JSON do GitHub
        """
        matches = []

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:

                for dataset_path in self.historical_sources['github_datasets']['sources']:
                    try:
                        full_url = self.historical_sources['github_datasets']['base_url'] + dataset_path
                        headers = random.choice(self.headers_pool)

                        logger.info(f"📂 GitHub dataset: {dataset_path}")

                        async with session.get(full_url, headers=headers) as response:
                            if response.status == 200:
                                data = await response.json()

                                # Estrutura OpenFootball
                                if 'rounds' in data:
                                    league_name = data.get('name', 'GitHub Dataset')

                                    for round_data in data['rounds']:
                                        for match in round_data.get('matches', []):
                                            try:
                                                team1 = match.get('team1')
                                                team2 = match.get('team2')
                                                score = match.get('score')

                                                if team1 and team2 and score:
                                                    # Parse do score
                                                    if 'ft' in score:
                                                        ft_score = score['ft']
                                                        if len(ft_score) == 2:
                                                            match_data = {
                                                                'home_team': {'name': team1},
                                                                'away_team': {'name': team2},
                                                                'tournament': league_name,
                                                                'home_score': ft_score[0],
                                                                'away_score': ft_score[1],
                                                                'status': 'FINISHED',
                                                                'match_date': match.get('date'),
                                                                'source': 'github_openfootball',
                                                                'collected_at': datetime.now().isoformat()
                                                            }

                                                            matches.append(match_data)
                                                            logger.info(f"📂 GitHub: {team1} {ft_score[0]}-{ft_score[1]} {team2}")

                                            except Exception as e:
                                                continue

                            else:
                                logger.warning(f"⚠️ GitHub status {response.status}: {dataset_path}")

                    except Exception as e:
                        logger.warning(f"⚠️ Erro GitHub dataset {dataset_path}: {e}")
                        continue

                    await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"❌ Erro geral GitHub: {e}")

        return matches

    async def _scrape_wikipedia_results(self) -> List[Dict]:
        """
        📖 Coletar resultados da Wikipedia
        """
        matches = []

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=25)) as session:

                for league_key, url_path in self.historical_sources['wikipedia_results']['leagues'].items():
                    try:
                        full_url = self.historical_sources['wikipedia_results']['base_url'] + url_path
                        headers = random.choice(self.headers_pool)

                        logger.info(f"📖 Wikipedia - {league_key}: {url_path}")

                        async with session.get(full_url, headers=headers) as response:
                            if response.status == 200:
                                html = await response.text()
                                soup = BeautifulSoup(html, 'html.parser')

                                # Procurar tabelas com resultados
                                tables = soup.find_all('table', class_=lambda x: x and 'wikitable' in x)

                                for table in tables:
                                    rows = table.find_all('tr')

                                    for row in rows:
                                        try:
                                            cells = row.find_all(['td', 'th'])
                                            row_text = row.get_text()

                                            # Procurar padrões de resultados
                                            result_patterns = [
                                                r'([A-Z][a-zA-Z\s]+?)\s+(\d+)[–-](\d+)\s+([A-Z][a-zA-Z\s]+)',
                                                r'([A-Z][a-zA-Z\s]+?)\s+vs\.?\s+([A-Z][a-zA-Z\s]+)\s+(\d+)[–-](\d+)'
                                            ]

                                            for pattern in result_patterns:
                                                match_result = re.search(pattern, row_text)
                                                if match_result:
                                                    if len(match_result.groups()) == 4:
                                                        team1, score1, score2, team2 = match_result.groups()
                                                    else:
                                                        continue

                                                    if team1 and team2 and score1.isdigit() and score2.isdigit():
                                                        match_data = {
                                                            'home_team': {'name': team1.strip()},
                                                            'away_team': {'name': team2.strip()},
                                                            'tournament': self._get_league_name(league_key),
                                                            'home_score': int(score1),
                                                            'away_score': int(score2),
                                                            'status': 'FINISHED',
                                                            'source': 'wikipedia_historical',
                                                            'collected_at': datetime.now().isoformat()
                                                        }

                                                        matches.append(match_data)
                                                        logger.info(f"📖 Wiki: {team1} {score1}-{score2} {team2}")
                                                        break

                                        except Exception as e:
                                            continue

                    except Exception as e:
                        logger.warning(f"⚠️ Erro Wikipedia {league_key}: {e}")
                        continue

                    await asyncio.sleep(random.uniform(3, 5))

        except Exception as e:
            logger.error(f"❌ Erro geral Wikipedia: {e}")

        return matches

    def _remove_duplicates(self, matches: List[Dict]) -> List[Dict]:
        """
        🔄 Remover jogos duplicados
        """
        seen = set()
        unique_matches = []

        for match in matches:
            try:
                home_team = match['home_team']['name'].lower().strip()
                away_team = match['away_team']['name'].lower().strip()
                match_key = f"{home_team}_{away_team}_{match.get('home_score')}_{match.get('away_score')}"

                if match_key not in seen:
                    seen.add(match_key)
                    unique_matches.append(match)

            except Exception:
                continue

        return unique_matches

    def _get_league_name(self, league_key: str) -> str:
        """Mapear chave para nome da liga"""
        league_names = {
            'la_liga': 'La Liga',
            'premier_league': 'Premier League',
            'serie_a': 'Serie A',
            'bundesliga': 'Bundesliga',
            'brasileirao': 'Brasileirão'
        }
        return league_names.get(league_key, 'Historical League')

# Instância global
historical_scraper = HistoricalScraper()