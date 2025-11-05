"""
🛡️ ADVANCED BYPASSING SCRAPER - Scraper Avançado com Bypass de Proteções
Implementa técnicas avançadas para contornar bloqueios:
- Headers rotativos realistas
- Proxies e delays inteligentes
- Sites alternativos
- Parsing HTML robusto
- Técnicas anti-detecção
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
import base64

logger = logging.getLogger(__name__)

class AdvancedBypassScraper:
    """
    🚀 Scraper avançado com técnicas de bypass
    """

    def __init__(self):
        # Headers muito realistas baseados em navegadores reais
        self.realistic_headers = [
            {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,pt;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-CH-UA': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'Sec-CH-UA-Mobile': '?0',
                'Sec-CH-UA-Platform': '"Windows"'
            },
            {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            },
            {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
        ]

    async def scrape_with_bypass_techniques(self) -> Dict:
        """
        🛡️ Scraping com técnicas avançadas de bypass
        """
        logger.info("🛡️ INICIANDO SCRAPING AVANÇADO COM BYPASS...")

        results = {
            'start_time': datetime.now().isoformat(),
            'sources': {
                'alternative_sources': [],
                'google_search_results': [],
                'cached_pages': [],
                'rss_feeds': []
            },
            'all_matches': [],
            'total_matches': 0,
            'success': True
        }

        try:
            # 1. Fontes alternativas mais abertas
            logger.info("🌐 Tentando fontes alternativas...")
            alt_matches = await self._scrape_alternative_sources()
            results['sources']['alternative_sources'] = alt_matches
            results['all_matches'].extend(alt_matches)

            await asyncio.sleep(3)

            # 2. Resultados do Google (páginas públicas)
            logger.info("🔍 Buscando resultados públicos do Google...")
            google_matches = await self._scrape_google_results()
            results['sources']['google_search_results'] = google_matches
            results['all_matches'].extend(google_matches)

            await asyncio.sleep(3)

            # 3. Páginas em cache e feeds RSS
            logger.info("📡 Coletando feeds RSS e páginas em cache...")
            rss_matches = await self._scrape_rss_feeds()
            results['sources']['rss_feeds'] = rss_matches
            results['all_matches'].extend(rss_matches)

            await asyncio.sleep(3)

            # 4. Sites de notícias esportivas (mais abertos)
            logger.info("📰 Coletando de sites de notícias esportivas...")
            news_matches = await self._scrape_sports_news()
            results['sources']['sports_news'] = news_matches
            results['all_matches'].extend(news_matches)

            results['total_matches'] = len(results['all_matches'])
            results['end_time'] = datetime.now().isoformat()

            logger.info(f"✅ SCRAPING AVANÇADO: {results['total_matches']} jogos coletados")

        except Exception as e:
            logger.error(f"❌ Erro no scraping avançado: {e}")
            results['success'] = False

        return results

    async def _scrape_alternative_sources(self) -> List[Dict]:
        """
        🌐 Fontes alternativas mais abertas
        """
        matches = []

        alternative_sites = [
            # Sites de notícias esportivas (geralmente mais abertos)
            'https://www.goal.com/en/fixtures',
            'https://www.espn.com/soccer/fixtures',
            'https://www.skysports.com/football/fixtures',
            'https://www.bbc.com/sport/football/fixtures',

            # Sites oficiais de ligas (às vezes têm dados públicos)
            'https://www.laliga.com/en-GB/fixtures',
            'https://www.premierleague.com/fixtures',

            # Sites brasileiros
            'https://www.globoesporte.globo.com/futebol/brasileirao-serie-a/',
            'https://www.lance.com.br/brasileirao/',
        ]

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=20)
            ) as session:

                for site_url in alternative_sites:
                    try:
                        headers = random.choice(self.realistic_headers).copy()

                        # Adicionar referer realista
                        if 'goal.com' in site_url:
                            headers['Referer'] = 'https://www.google.com/'
                        elif 'espn.com' in site_url:
                            headers['Referer'] = 'https://www.espn.com/'

                        logger.info(f"🔍 Tentando fonte alternativa: {site_url}")

                        async with session.get(site_url, headers=headers) as response:
                            if response.status == 200:
                                html = await response.text()
                                soup = BeautifulSoup(html, 'html.parser')

                                # Buscar padrões comuns de jogos
                                match_patterns = [
                                    # Padrões de texto com "vs", "x", "-"
                                    r'([A-Z][a-z]+(?: [A-Z][a-z]+)*)\s+(?:vs\.?|x|-)\s+([A-Z][a-z]+(?: [A-Z][a-z]+)*)',
                                    # Times conhecidos
                                    r'(Real Madrid|Barcelona|Manchester United|Liverpool|Arsenal|Chelsea|Flamengo|Palmeiras|Corinthians)',
                                ]

                                for pattern in match_patterns:
                                    pattern_matches = re.findall(pattern, html, re.IGNORECASE)

                                    for match in pattern_matches[:5]:  # Limitar a 5 por padrão
                                        if isinstance(match, tuple) and len(match) >= 2:
                                            home_team = match[0].strip()
                                            away_team = match[1].strip()
                                        else:
                                            home_team = str(match).strip()
                                            away_team = "Opponent"

                                        if home_team and away_team and home_team != away_team:
                                            match_data = {
                                                'home_team': {'name': home_team},
                                                'away_team': {'name': away_team},
                                                'tournament': self._detect_league_from_site(site_url),
                                                'source': f'alternative_{self._get_site_name(site_url)}',
                                                'collected_at': datetime.now().isoformat()
                                            }
                                            matches.append(match_data)
                                            logger.info(f"🌐 {self._get_site_name(site_url)}: {home_team} vs {away_team}")

                                # Buscar por elementos estruturados também
                                fixture_elements = soup.find_all(['div', 'li', 'tr'], class_=lambda x: x and any(term in x.lower() for term in ['fixture', 'match', 'game', 'event']))

                                for element in fixture_elements[:8]:
                                    try:
                                        text = element.get_text()
                                        # Procurar por padrão "Team1 vs Team2" ou similar
                                        vs_match = re.search(r'([A-Z][a-zA-Z\s]+?)\s+(?:vs\.?|x|-)\s+([A-Z][a-zA-Z\s]+)', text)
                                        if vs_match:
                                            home_team = vs_match.group(1).strip()
                                            away_team = vs_match.group(2).strip()

                                            if len(home_team) > 3 and len(away_team) > 3:  # Filtrar nomes muito curtos
                                                match_data = {
                                                    'home_team': {'name': home_team},
                                                    'away_team': {'name': away_team},
                                                    'tournament': self._detect_league_from_site(site_url),
                                                    'source': f'structured_{self._get_site_name(site_url)}',
                                                    'collected_at': datetime.now().isoformat()
                                                }
                                                matches.append(match_data)

                                    except Exception:
                                        continue

                            elif response.status == 403:
                                logger.warning(f"⚠️ Bloqueado: {site_url}")
                            else:
                                logger.warning(f"⚠️ Status {response.status}: {site_url}")

                    except Exception as e:
                        logger.warning(f"⚠️ Erro {site_url}: {e}")
                        continue

                    await asyncio.sleep(random.uniform(2, 4))  # Delay aleatório

        except Exception as e:
            logger.error(f"❌ Erro fontes alternativas: {e}")

        return matches

    async def _scrape_google_results(self) -> List[Dict]:
        """
        🔍 Buscar resultados públicos do Google sobre jogos de hoje
        """
        matches = []

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=15)
            ) as session:

                # Queries de busca específicas
                today = datetime.now().strftime('%Y-%m-%d')
                search_queries = [
                    f'Real Madrid vs Barcelona {today}',
                    f'football matches today {today}',
                    f'soccer fixtures {today}',
                    'Flamengo Palmeiras hoje',
                    'La Liga matches today'
                ]

                for query in search_queries:
                    try:
                        # Google Search (cuidadoso para não ser bloqueado)
                        encoded_query = quote(query)
                        google_url = f'https://www.google.com/search?q={encoded_query}&hl=en&gl=us'

                        headers = random.choice(self.realistic_headers).copy()
                        headers['Referer'] = 'https://www.google.com/'

                        logger.info(f"🔍 Google search: {query}")

                        async with session.get(google_url, headers=headers) as response:
                            if response.status == 200:
                                html = await response.text()

                                # Extrair snippets que mencionem jogos
                                # Google snippets geralmente têm formato "Team1 vs Team2"
                                vs_matches = re.findall(r'([A-Z][a-zA-Z\s]+?)\s+vs\.?\s+([A-Z][a-zA-Z\s]+)', html, re.IGNORECASE)

                                for home_team, away_team in vs_matches[:3]:  # Máximo 3 por busca
                                    if len(home_team) > 3 and len(away_team) > 3:
                                        match_data = {
                                            'home_team': {'name': home_team.strip()},
                                            'away_team': {'name': away_team.strip()},
                                            'tournament': 'Google Search Result',
                                            'source': 'google_search',
                                            'search_query': query,
                                            'collected_at': datetime.now().isoformat()
                                        }
                                        matches.append(match_data)
                                        logger.info(f"🔍 Google: {home_team} vs {away_team}")

                    except Exception as e:
                        logger.warning(f"⚠️ Google search error: {e}")
                        continue

                    await asyncio.sleep(random.uniform(3, 6))  # Delay maior para Google

        except Exception as e:
            logger.error(f"❌ Erro Google results: {e}")

        return matches

    async def _scrape_rss_feeds(self) -> List[Dict]:
        """
        📡 Coletar feeds RSS de sites esportivos
        """
        matches = []

        rss_feeds = [
            'https://www.espn.com/espn/rss/soccer/news',
            'https://www.goal.com/feeds/news',
            'https://www.skysports.com/rss/football',
            'https://globoesporte.globo.com/rss/futebol/',
        ]

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=15)
            ) as session:

                for rss_url in rss_feeds:
                    try:
                        headers = random.choice(self.realistic_headers).copy()
                        headers['Accept'] = 'application/rss+xml, application/xml, text/xml'

                        logger.info(f"📡 RSS Feed: {rss_url}")

                        async with session.get(rss_url, headers=headers) as response:
                            if response.status == 200:
                                xml_content = await response.text()

                                # Parse XML/RSS
                                soup = BeautifulSoup(xml_content, 'xml')

                                # Buscar itens RSS
                                items = soup.find_all('item')

                                for item in items[:10]:  # Máximo 10 por feed
                                    try:
                                        title = item.find('title')
                                        if title:
                                            title_text = title.get_text()

                                            # Procurar padrões de jogos no título
                                            vs_match = re.search(r'([A-Z][a-zA-Z\s]+?)\s+(?:vs\.?|x|-)\s+([A-Z][a-zA-Z\s]+)', title_text)
                                            if vs_match:
                                                home_team = vs_match.group(1).strip()
                                                away_team = vs_match.group(2).strip()

                                                match_data = {
                                                    'home_team': {'name': home_team},
                                                    'away_team': {'name': away_team},
                                                    'tournament': 'RSS Feed',
                                                    'source': f'rss_{self._get_site_name(rss_url)}',
                                                    'title': title_text,
                                                    'collected_at': datetime.now().isoformat()
                                                }
                                                matches.append(match_data)
                                                logger.info(f"📡 RSS: {home_team} vs {away_team}")

                                    except Exception:
                                        continue

                    except Exception as e:
                        logger.warning(f"⚠️ RSS error {rss_url}: {e}")
                        continue

                    await asyncio.sleep(2)

        except Exception as e:
            logger.error(f"❌ Erro RSS feeds: {e}")

        return matches

    async def _scrape_sports_news(self) -> List[Dict]:
        """
        📰 Sites de notícias esportivas (geralmente mais abertos)
        """
        matches = []

        news_sites = [
            'https://www.marca.com/futbol/primera-division.html',
            'https://as.com/futbol/primera/',
            'https://www.sport.es/es/futbol/',
            'https://www.ole.com.ar/futbol/',
            'https://www.lance.com.br/futebol/',
        ]

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=20)
            ) as session:

                for news_url in news_sites:
                    try:
                        headers = random.choice(self.realistic_headers).copy()

                        # Adicionar referers realistas baseados no país
                        if any(domain in news_url for domain in ['marca.com', 'as.com', 'sport.es']):
                            headers['Accept-Language'] = 'es-ES,es;q=0.9,en;q=0.8'
                        elif 'ole.com.ar' in news_url:
                            headers['Accept-Language'] = 'es-AR,es;q=0.9'
                        elif 'lance.com.br' in news_url:
                            headers['Accept-Language'] = 'pt-BR,pt;q=0.9'

                        logger.info(f"📰 Notícias: {news_url}")

                        async with session.get(news_url, headers=headers) as response:
                            if response.status == 200:
                                html = await response.text()

                                # Times específicos para procurar
                                target_teams = [
                                    'Real Madrid', 'Barcelona', 'Atlético Madrid', 'Valencia', 'Sevilla',
                                    'Flamengo', 'Palmeiras', 'Corinthians', 'Santos', 'São Paulo',
                                    'Manchester United', 'Manchester City', 'Liverpool', 'Arsenal', 'Chelsea'
                                ]

                                for team in target_teams:
                                    if team in html:
                                        # Procurar contexto ao redor do nome do time
                                        team_pattern = rf'({team})\s+(?:vs\.?|x|-|contra)\s+([A-Z][a-zA-Z\s]+)|([A-Z][a-zA-Z\s]+)\s+(?:vs\.?|x|-|contra)\s+({team})'
                                        context_matches = re.finditer(team_pattern, html, re.IGNORECASE)

                                        for match in context_matches:
                                            groups = match.groups()
                                            if groups[0] and groups[1]:  # Team vs Opponent
                                                home_team = groups[0].strip()
                                                away_team = groups[1].strip()
                                            elif groups[2] and groups[3]:  # Opponent vs Team
                                                home_team = groups[2].strip()
                                                away_team = groups[3].strip()
                                            else:
                                                continue

                                            if len(away_team) > 3 and home_team != away_team:
                                                match_data = {
                                                    'home_team': {'name': home_team},
                                                    'away_team': {'name': away_team},
                                                    'tournament': self._detect_league_from_site(news_url),
                                                    'source': f'news_{self._get_site_name(news_url)}',
                                                    'collected_at': datetime.now().isoformat()
                                                }
                                                matches.append(match_data)
                                                logger.info(f"📰 {self._get_site_name(news_url)}: {home_team} vs {away_team}")
                                                break  # Um jogo por time por site

                            elif response.status == 403:
                                logger.warning(f"⚠️ Bloqueado: {news_url}")
                            else:
                                logger.warning(f"⚠️ Status {response.status}: {news_url}")

                    except Exception as e:
                        logger.warning(f"⚠️ Erro news {news_url}: {e}")
                        continue

                    await asyncio.sleep(random.uniform(3, 5))

        except Exception as e:
            logger.error(f"❌ Erro sports news: {e}")

        return matches

    def _detect_league_from_site(self, url: str) -> str:
        """Detectar liga pela URL do site"""
        url_lower = url.lower()

        if any(term in url_lower for term in ['laliga', 'primera', 'marca', 'as.com', 'sport.es']):
            return 'La Liga'
        elif any(term in url_lower for term in ['premier', 'england', 'sky']):
            return 'Premier League'
        elif any(term in url_lower for term in ['brasileiro', 'brasil', 'globo', 'lance']):
            return 'Brasileirão'
        elif any(term in url_lower for term in ['serie-a', 'italy']):
            return 'Serie A'
        elif 'goal.com' in url_lower or 'espn.com' in url_lower:
            return 'International'

        return 'Unknown League'

    def _get_site_name(self, url: str) -> str:
        """Extrair nome do site da URL"""
        import urllib.parse
        domain = urllib.parse.urlparse(url).netloc
        return domain.replace('www.', '').split('.')[0]

# Instância global
advanced_scraper = AdvancedBypassScraper()