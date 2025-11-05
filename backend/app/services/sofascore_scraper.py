"""
⚽ SOFASCORE SCRAPER - Advanced Statistics Service
Coleta estatísticas detalhadas, dados em tempo real e informações de jogos do SofaScore.com
Foco em dados estatísticos avançados e métricas de performance
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

class SofaScoreScraper:
    """
    📊 Scraper avançado para SofaScore.com
    Especializado em estatísticas detalhadas e dados em tempo real
    """

    def __init__(self):
        self.base_url = "https://www.sofascore.com"
        self.api_base = "https://api.sofascore.com/api/v1"
        # Rotação de User-Agents para evitar detecção
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/109.0'
        ]

        self.headers = {
            'User-Agent': self.user_agents[0],  # Será rotacionado
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        self.session = None

    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(ssl=False)
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            timeout=aiohttp.ClientTimeout(total=30),
            connector=connector
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def get_live_matches(self) -> List[Dict]:
        """
        🔴 Obter jogos ao vivo
        """
        try:
            # SofaScore tem uma API não documentada para jogos ao vivo
            url = f"{self.api_base}/sport/football/events/live"
            logger.info(f"🔴 Buscando jogos ao vivo...")

            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"API não disponível, tentando scraping web...")
                    return await self._scrape_live_matches_web()

                data = await response.json()
                matches = []

                if 'events' in data:
                    for event in data['events'][:20]:  # Limitar para performance
                        match_data = await self._process_live_match(event)
                        if match_data:
                            matches.append(match_data)

                logger.info(f"✅ {len(matches)} jogos ao vivo encontrados")
                return matches

        except Exception as e:
            logger.error(f"❌ Erro ao buscar jogos ao vivo: {e}")
            return await self._scrape_live_matches_web()

    async def get_match_statistics(self, match_id: str = None, home_team: str = None, away_team: str = None) -> Dict:
        """
        📈 Obter estatísticas detalhadas de uma partida
        """
        try:
            if not match_id:
                match_id = await self._find_match_id(home_team, away_team)
                if not match_id:
                    return {}

            # Buscar estatísticas da partida
            stats_url = f"{self.api_base}/event/{match_id}/statistics"

            async with self.session.get(stats_url) as response:
                if response.status != 200:
                    return await self._scrape_match_stats_web(home_team, away_team)

                data = await response.json()

                statistics = {
                    'match_id': match_id,
                    'basic_stats': {},
                    'advanced_stats': {},
                    'player_stats': {},
                    'team_comparison': {},
                    'scraped_at': datetime.now().isoformat()
                }

                # Processar estatísticas básicas
                if 'statistics' in data:
                    for period in data['statistics']:
                        if period['period'] == 'ALL':
                            statistics['basic_stats'] = await self._process_basic_stats(period['groups'])

                # Buscar estatísticas avançadas
                advanced_stats = await self._get_advanced_match_stats(match_id)
                statistics['advanced_stats'] = advanced_stats

                return statistics

        except Exception as e:
            logger.error(f"❌ Erro ao buscar estatísticas da partida: {e}")
            return {}

    async def get_team_statistics(self, team_name: str, season_id: str = None) -> Dict:
        """
        🏆 Obter estatísticas completas de um time
        """
        try:
            # Buscar ID do time
            team_id = await self._find_team_id(team_name)
            if not team_id:
                return {}

            # Obter temporada atual se não especificada
            if not season_id:
                season_id = await self._get_current_season(team_id)

            team_stats = {
                'team_name': team_name,
                'team_id': team_id,
                'season_id': season_id,
                'season_stats': {},
                'recent_form': [],
                'player_ratings': {},
                'performance_metrics': {},
                'scraped_at': datetime.now().isoformat()
            }

            # Estatísticas da temporada
            season_url = f"{self.api_base}/team/{team_id}/tournament/{season_id}/statistics"
            async with self.session.get(season_url) as response:
                if response.status == 200:
                    data = await response.json()
                    team_stats['season_stats'] = await self._process_team_season_stats(data)

            # Forma recente (últimos 5 jogos)
            recent_matches = await self._get_team_recent_matches(team_id, 5)
            team_stats['recent_form'] = recent_matches

            # Ratings dos jogadores
            players_url = f"{self.api_base}/team/{team_id}/players"
            async with self.session.get(players_url) as response:
                if response.status == 200:
                    data = await response.json()
                    team_stats['player_ratings'] = await self._process_player_ratings(data)

            return team_stats

        except Exception as e:
            logger.error(f"❌ Erro ao buscar estatísticas do time: {e}")
            return {}

    async def get_player_statistics(self, player_name: str, team_name: str = None) -> Dict:
        """
        👤 Obter estatísticas detalhadas de um jogador
        """
        try:
            player_id = await self._find_player_id(player_name, team_name)
            if not player_id:
                return {}

            player_stats = {
                'player_name': player_name,
                'player_id': player_id,
                'season_stats': {},
                'recent_performances': [],
                'ratings': {},
                'scraped_at': datetime.now().isoformat()
            }

            # Estatísticas da temporada
            stats_url = f"{self.api_base}/player/{player_id}/statistics"
            async with self.session.get(stats_url) as response:
                if response.status == 200:
                    data = await response.json()
                    player_stats['season_stats'] = await self._process_player_season_stats(data)

            return player_stats

        except Exception as e:
            logger.error(f"❌ Erro ao buscar estatísticas do jogador: {e}")
            return {}

    async def get_league_standings(self, league_name: str = "brasileirao") -> Dict:
        """
        🏆 Obter classificação de uma liga
        """
        try:
            # Mapear nomes de ligas para IDs do SofaScore
            league_mapping = {
                'brasileirao': 325,      # Brasileirão Série A
                'premier_league': 17,    # Premier League
                'la_liga': 8,           # La Liga
                'serie_a': 23,          # Serie A
                'bundesliga': 35,       # Bundesliga
                'ligue_1': 34,          # Ligue 1
                'libertadores': 384     # Copa Libertadores
            }

            league_id = league_mapping.get(league_name.lower(), 325)  # Default: Brasileirão

            standings_url = f"{self.api_base}/unique-tournament/{league_id}/season/current/standings/total"

            async with self.session.get(standings_url) as response:
                if response.status != 200:
                    return {}

                data = await response.json()

                standings = {
                    'league_name': league_name,
                    'league_id': league_id,
                    'standings': [],
                    'updated_at': datetime.now().isoformat()
                }

                if 'standings' in data and len(data['standings']) > 0:
                    for row in data['standings'][0]['rows']:
                        team_data = {
                            'position': row['position'],
                            'team_name': row['team']['name'],
                            'team_id': row['team']['id'],
                            'played': row['matches'],
                            'wins': row['wins'],
                            'draws': row['draws'],
                            'losses': row['losses'],
                            'goals_for': row['scoresFor'],
                            'goals_against': row['scoresAgainst'],
                            'goal_difference': row['scoresFor'] - row['scoresAgainst'],
                            'points': row['points']
                        }
                        standings['standings'].append(team_data)

                return standings

        except Exception as e:
            logger.error(f"❌ Erro ao buscar classificação: {e}")
            return {}

    async def _process_live_match(self, event: Dict) -> Optional[Dict]:
        """Processar dados de um jogo ao vivo"""
        try:
            return {
                'match_id': event.get('id'),
                'home_team': {
                    'name': event.get('homeTeam', {}).get('name'),
                    'id': event.get('homeTeam', {}).get('id'),
                    'score': event.get('homeScore', {}).get('current', 0)
                },
                'away_team': {
                    'name': event.get('awayTeam', {}).get('name'),
                    'id': event.get('awayTeam', {}).get('id'),
                    'score': event.get('awayScore', {}).get('current', 0)
                },
                'status': event.get('status', {}).get('description'),
                'minute': event.get('time', {}).get('currentPeriodStartTimestamp'),
                'tournament': event.get('tournament', {}).get('name'),
                'live': True,
                'sofascore_url': f"{self.base_url}/match/{event.get('id')}"
            }
        except Exception as e:
            logger.debug(f"Erro ao processar jogo ao vivo: {e}")
            return None

    async def _process_basic_stats(self, groups: List[Dict]) -> Dict:
        """Processar estatísticas básicas de uma partida"""
        stats = {}

        for group in groups:
            group_name = group.get('groupName', '').lower()

            for stat in group.get('statisticsItems', []):
                stat_name = stat.get('name', '')
                home_value = stat.get('home')
                away_value = stat.get('away')

                stats[stat_name.lower().replace(' ', '_')] = {
                    'home': home_value,
                    'away': away_value
                }

        return stats

    async def _get_advanced_match_stats(self, match_id: str) -> Dict:
        """Obter estatísticas avançadas de uma partida"""
        try:
            # Expected Goals (xG)
            xg_url = f"{self.api_base}/event/{match_id}/graph"
            async with self.session.get(xg_url) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'expected_goals': data.get('graphPoints', []),
                        'momentum': data.get('momentum', [])
                    }
            return {}
        except:
            return {}

    async def _find_team_id(self, team_name: str) -> Optional[str]:
        """Encontrar ID de um time"""
        try:
            search_url = f"{self.api_base}/search/{quote(team_name)}"
            async with self.session.get(search_url) as response:
                if response.status == 200:
                    data = await response.json()
                    for result in data.get('results', []):
                        if result.get('type') == 'team':
                            return str(result.get('entity', {}).get('id'))
            return None
        except:
            return None

    async def _find_match_id(self, home_team: str, away_team: str) -> Optional[str]:
        """Encontrar ID de uma partida"""
        try:
            search_query = f"{home_team} {away_team}"
            search_url = f"{self.api_base}/search/{quote(search_query)}"
            async with self.session.get(search_url) as response:
                if response.status == 200:
                    data = await response.json()
                    for result in data.get('results', []):
                        if result.get('type') == 'event':
                            event = result.get('entity', {})
                            home_name = event.get('homeTeam', {}).get('name', '').lower()
                            away_name = event.get('awayTeam', {}).get('name', '').lower()

                            if (home_team.lower() in home_name or home_name in home_team.lower()) and \
                               (away_team.lower() in away_name or away_name in away_team.lower()):
                                return str(event.get('id'))
            return None
        except:
            return None

    async def _scrape_live_matches_web(self) -> List[Dict]:
        """Fallback: scraping web quando API não está disponível"""
        try:
            url = f"{self.base_url}/football"
            async with self.session.get(url) as response:
                if response.status != 200:
                    return []

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                matches = []
                # Procurar por elementos de jogos ao vivo
                live_elements = soup.find_all(['div', 'article'], class_=re.compile(r'live|match'))

                for element in live_elements[:10]:
                    match_data = await self._extract_match_from_element(element)
                    if match_data:
                        matches.append(match_data)

                return matches

        except Exception as e:
            logger.error(f"❌ Erro no scraping web: {e}")
            return []

    async def _extract_match_from_element(self, element) -> Optional[Dict]:
        """Extrair dados de jogo de um elemento HTML"""
        try:
            text = element.get_text()

            # Procurar por padrões de times e placar
            team_pattern = r'([A-Za-z\s]+)\s+(\d+)\s*-\s*(\d+)\s+([A-Za-z\s]+)'
            match = re.search(team_pattern, text)

            if match:
                return {
                    'home_team': {'name': match.group(1).strip()},
                    'away_team': {'name': match.group(4).strip()},
                    'home_score': int(match.group(2)),
                    'away_score': int(match.group(3)),
                    'live': True,
                    'source': 'sofascore_web'
                }

            return None
        except:
            return None


# Função de integração com o sistema principal
class SofaScoreIntegration:
    """
    🔌 Integração do SofaScore com o sistema principal
    """

    def __init__(self):
        self.scraper = None

    async def enrich_match_data(self, match_data: Dict) -> Dict:
        """Enriquecer dados de partida com estatísticas do SofaScore"""
        async with SofaScoreScraper() as scraper:
            home_team = match_data.get('home_team', {}).get('name')
            away_team = match_data.get('away_team', {}).get('name')

            if home_team and away_team:
                stats = await scraper.get_match_statistics(
                    home_team=home_team,
                    away_team=away_team
                )

                match_data['sofascore_stats'] = stats

            return match_data

    async def get_enhanced_team_data(self, team_name: str) -> Dict:
        """Obter dados enriquecidos de um time"""
        async with SofaScoreScraper() as scraper:
            team_stats = await scraper.get_team_statistics(team_name)

            # Adicionar classificação da liga se for time brasileiro
            if 'brasil' in team_name.lower() or any(word in team_name.lower() for word in ['flamengo', 'palmeiras', 'corinthians', 'santos']):
                standings = await scraper.get_league_standings('brasileirao')
                team_stats['league_standings'] = standings

            return team_stats


# Função de teste
async def test_sofascore_scraper():
    """🧪 Testar o scraper do SofaScore"""

    async with SofaScoreScraper() as scraper:
        print("⚽ TESTANDO SOFASCORE SCRAPER")
        print("=" * 40)

        # Testar jogos ao vivo
        print("🔴 Buscando jogos ao vivo...")
        live_matches = await scraper.get_live_matches()
        print(f"✅ {len(live_matches)} jogos ao vivo encontrados")

        for match in live_matches[:3]:
            home = match.get('home_team', {})
            away = match.get('away_team', {})
            print(f"   🏠 {home.get('name', 'N/A')} {home.get('score', 0)} x {away.get('score', 0)} {away.get('name', 'N/A')}")

        # Testar classificação do Brasileirão
        print("\n🏆 Buscando classificação do Brasileirão...")
        standings = await scraper.get_league_standings('brasileirao')

        if standings and standings.get('standings'):
            print(f"✅ Classificação obtida com {len(standings['standings'])} times")
            for team in standings['standings'][:5]:
                print(f"   {team['position']}º {team['team_name']} - {team['points']} pts")

        # Testar estatísticas de time
        print("\n📊 Testando estatísticas de time...")
        team_stats = await scraper.get_team_statistics("Flamengo")
        if team_stats:
            print(f"✅ Estatísticas de {team_stats.get('team_name')} coletadas")
            season_stats = team_stats.get('season_stats', {})
            if season_stats:
                print(f"   Dados da temporada disponíveis")

if __name__ == "__main__":
    asyncio.run(test_sofascore_scraper())