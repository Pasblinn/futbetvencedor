"""
🇧🇷🇪🇸 BRAZILIAN & SPANISH FOOTBALL COLLECTOR
Coletor especializado para futebol brasileiro e espanhol
Combina APIs limitadas com scraping para evitar rate limits
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import json
import random

logger = logging.getLogger(__name__)

class BrazilianSpanishCollector:
    """
    🎯 Coletor otimizado para futebol brasileiro e espanhol
    Evita rate limits usando scraping inteligente
    """

    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]

        # Configurações específicas para Brasil e Espanha
        self.leagues_config = {
            'brazil': {
                'serie_a': {
                    'name': 'Brasileirão Série A',
                    'sofascore_id': 325,
                    'api_code': 'BSA',
                    'priority': 1
                },
                'serie_b': {
                    'name': 'Brasileirão Série B',
                    'sofascore_id': 390,
                    'api_code': 'BSB',
                    'priority': 2
                },
                'copa_brasil': {
                    'name': 'Copa do Brasil',
                    'sofascore_id': 384,
                    'api_code': 'CDB',
                    'priority': 3
                }
            },
            'spain': {
                'la_liga': {
                    'name': 'La Liga',
                    'sofascore_id': 8,
                    'api_code': 'PD',
                    'priority': 1
                },
                'segunda': {
                    'name': 'Segunda División',
                    'sofascore_id': 9,
                    'api_code': 'SD',
                    'priority': 2
                },
                'copa_del_rey': {
                    'name': 'Copa del Rey',
                    'sofascore_id': 16,
                    'api_code': 'CDR',
                    'priority': 3
                }
            }
        }

    async def collect_brazilian_spanish_data(self) -> Dict:
        """
        🎯 Coleta otimizada para Brasil e Espanha
        """
        logger.info("🇧🇷🇪🇸 Iniciando coleta Brasil/Espanha...")

        results = {
            'start_time': datetime.now().isoformat(),
            'brazil': {'teams': 0, 'matches': 0, 'odds': 0, 'errors': []},
            'spain': {'teams': 0, 'matches': 0, 'odds': 0, 'errors': []},
            'total_matches': 0,
            'success': True,
            'errors': []
        }

        try:
            # Coleta dados do Brasil
            logger.info("🇧🇷 Coletando dados do futebol brasileiro...")
            brazil_data = await self._collect_brazil_data()
            results['brazil'] = brazil_data

            # Pausa para evitar rate limit
            await asyncio.sleep(5)

            # Coleta dados da Espanha
            logger.info("🇪🇸 Coletando dados do futebol espanhol...")
            spain_data = await self._collect_spain_data()
            results['spain'] = spain_data

            results['total_matches'] = brazil_data['matches'] + spain_data['matches']
            results['end_time'] = datetime.now().isoformat()

            logger.info(f"✅ Coleta concluída: {results['total_matches']} jogos")

        except Exception as e:
            logger.error(f"❌ Erro na coleta Brasil/Espanha: {e}")
            results['errors'].append(str(e))
            results['success'] = False

        return results

    async def _collect_brazil_data(self) -> Dict:
        """🇧🇷 Coletar dados específicos do Brasil"""
        results = {'teams': 0, 'matches': 0, 'odds': 0, 'errors': []}

        try:
            async with aiohttp.ClientSession(
                headers={'User-Agent': random.choice(self.user_agents)},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:

                # Brasileirão Série A (prioridade 1)
                serie_a_matches = await self._scrape_sofascore_league(
                    session,
                    self.leagues_config['brazil']['serie_a']['sofascore_id'],
                    'Brasileirão Série A'
                )
                results['matches'] += len(serie_a_matches)

                # Pausa entre requests
                await asyncio.sleep(3)

                # Copa do Brasil (prioridade 3, se ainda não atingiu rate limit)
                try:
                    copa_matches = await self._scrape_sofascore_league(
                        session,
                        self.leagues_config['brazil']['copa_brasil']['sofascore_id'],
                        'Copa do Brasil'
                    )
                    results['matches'] += len(copa_matches)
                except Exception as e:
                    results['errors'].append(f"Copa do Brasil: {str(e)}")

        except Exception as e:
            logger.error(f"❌ Erro na coleta Brasil: {e}")
            results['errors'].append(str(e))

        return results

    async def _collect_spain_data(self) -> Dict:
        """🇪🇸 Coletar dados específicos da Espanha"""
        results = {'teams': 0, 'matches': 0, 'odds': 0, 'errors': []}

        try:
            async with aiohttp.ClientSession(
                headers={'User-Agent': random.choice(self.user_agents)},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:

                # La Liga (prioridade 1)
                la_liga_matches = await self._scrape_sofascore_league(
                    session,
                    self.leagues_config['spain']['la_liga']['sofascore_id'],
                    'La Liga'
                )
                results['matches'] += len(la_liga_matches)

                # Pausa entre requests
                await asyncio.sleep(3)

                # Copa del Rey (prioridade 3, se ainda não atingiu rate limit)
                try:
                    copa_matches = await self._scrape_sofascore_league(
                        session,
                        self.leagues_config['spain']['copa_del_rey']['sofascore_id'],
                        'Copa del Rey'
                    )
                    results['matches'] += len(copa_matches)
                except Exception as e:
                    results['errors'].append(f"Copa del Rey: {str(e)}")

        except Exception as e:
            logger.error(f"❌ Erro na coleta Espanha: {e}")
            results['errors'].append(str(e))

        return results

    async def _scrape_sofascore_league(self, session: aiohttp.ClientSession, league_id: int, league_name: str) -> List[Dict]:
        """
        🏆 Scraping de uma liga específica do SofaScore
        """
        matches = []

        try:
            # URL da API não documentada do SofaScore - vamos tentar múltiplas abordagens
            today = datetime.now().strftime('%Y-%m-%d')

            # Abordagem 1: Eventos agendados para hoje
            url1 = f"https://api.sofascore.com/api/v1/sport/football/scheduled-events/{today}"

            # Abordagem 2: Eventos da liga específica
            url2 = f"https://api.sofascore.com/api/v1/unique-tournament/{league_id}/season/2024/events/next/0"

            # Abordagem 3: Eventos de hoje por categoria
            urls_to_try = [url1, url2]

            for url in urls_to_try:
                try:
                    logger.info(f"🔍 Tentando URL: {url}")
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            logger.info(f"📊 Dados recebidos: {len(str(data))} caracteres")

                            # Processar eventos
                            events = data.get('events', [])
                            if not events and 'tournament' in str(data):
                                # Pode ser que os eventos estejam em outra estrutura
                                events = data.get('tournamentEvents', {}).get('events', [])

                            logger.info(f"🎯 {len(events)} eventos encontrados")

                            for event in events:
                                tournament = event.get('tournament', {})
                                tournament_id = tournament.get('id')
                                tournament_name = tournament.get('name', league_name)

                                # Filtrar por liga específica ou por país
                                is_target_league = (
                                    tournament_id == league_id or
                                    'La Liga' in tournament_name or
                                    'Primera' in tournament_name or
                                    'Brasileir' in tournament_name or
                                    'Serie A' in tournament_name or
                                    'Copa' in tournament_name
                                )

                                if is_target_league:
                                    match_data = self._process_sofascore_match(event, tournament_name)
                                    if match_data:
                                        matches.append(match_data)
                                        logger.info(f"⚽ Jogo encontrado: {match_data['home_team']['name']} vs {match_data['away_team']['name']}")

                        elif response.status == 429:
                            logger.warning(f"⚠️ Rate limit atingido para {league_name}")
                            await asyncio.sleep(10)  # Pausa maior em caso de rate limit
                            break
                        else:
                            logger.warning(f"⚠️ Status {response.status} para {url}")

                except Exception as e:
                    logger.warning(f"⚠️ Erro ao buscar {url}: {e}")
                    continue

                # Pausa entre URLs
                await asyncio.sleep(3)

            logger.info(f"✅ {len(matches)} jogos coletados de {league_name}")

        except Exception as e:
            logger.error(f"❌ Erro no scraping de {league_name}: {e}")

        return matches

    def _process_sofascore_match(self, event: Dict, league_name: str) -> Optional[Dict]:
        """
        🔄 Processar dados de uma partida do SofaScore
        """
        try:
            return {
                'id': event.get('id'),
                'league': league_name,
                'home_team': {
                    'id': event.get('homeTeam', {}).get('id'),
                    'name': event.get('homeTeam', {}).get('name'),
                    'shortName': event.get('homeTeam', {}).get('shortName')
                },
                'away_team': {
                    'id': event.get('awayTeam', {}).get('id'),
                    'name': event.get('awayTeam', {}).get('name'),
                    'shortName': event.get('awayTeam', {}).get('shortName')
                },
                'start_time': event.get('startTimestamp'),
                'status': event.get('status', {}).get('description'),
                'score': event.get('homeScore', {}).get('display', 0) if event.get('homeScore') else None,
                'away_score': event.get('awayScore', {}).get('display', 0) if event.get('awayScore') else None,
                'source': 'sofascore',
                'collected_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.warning(f"⚠️ Erro ao processar partida: {e}")
            return None

    async def get_todays_matches(self) -> List[Dict]:
        """
        📅 Obter todos os jogos de hoje (Brasil e Espanha)
        """
        todays_matches = []

        try:
            async with aiohttp.ClientSession(
                headers={'User-Agent': random.choice(self.user_agents)},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:

                today = datetime.now().strftime('%Y-%m-%d')

                # URL para jogos de hoje
                urls_to_try = [
                    f"https://api.sofascore.com/api/v1/sport/football/scheduled-events/{today}",
                    "https://api.sofascore.com/api/v1/sport/football/events/live"
                ]

                for url in urls_to_try:
                    try:
                        logger.info(f"🔍 Buscando jogos em: {url}")
                        async with session.get(url) as response:
                            if response.status == 200:
                                data = await response.json()
                                events = data.get('events', [])

                                logger.info(f"📊 {len(events)} eventos encontrados")

                                for event in events:
                                    tournament = event.get('tournament', {})
                                    country = tournament.get('category', {}).get('name', '')
                                    tournament_name = tournament.get('name', '')

                                    # Filtrar jogos brasileiros e espanhóis
                                    is_target_match = (
                                        'Brazil' in country or 'Brasil' in country or
                                        'Spain' in country or 'España' in country or
                                        'Espanha' in country or
                                        'La Liga' in tournament_name or
                                        'Primera' in tournament_name or
                                        'Brasileir' in tournament_name or
                                        'Serie A' in tournament_name and 'Brazil' in str(event) or
                                        'Real Madrid' in str(event) or
                                        'Barcelona' in str(event) or
                                        'Atletico' in str(event)
                                    )

                                    if is_target_match:
                                        match_data = self._process_sofascore_match(event, tournament_name)
                                        if match_data:
                                            # Verificar se é jogo ao vivo
                                            status = event.get('status', {})
                                            match_data['is_live'] = status.get('type') == 'inprogress'
                                            match_data['country'] = country

                                            todays_matches.append(match_data)
                                            logger.info(f"⚽ Jogo encontrado: {match_data['home_team']['name']} vs {match_data['away_team']['name']} ({country})")

                            elif response.status == 429:
                                logger.warning(f"⚠️ Rate limit atingido")
                                await asyncio.sleep(10)
                                break
                            else:
                                logger.warning(f"⚠️ Status {response.status} para {url}")

                    except Exception as e:
                        logger.warning(f"⚠️ Erro ao buscar {url}: {e}")
                        continue

                    # Pausa entre URLs
                    await asyncio.sleep(3)

                logger.info(f"✅ {len(todays_matches)} jogos de hoje encontrados")

        except Exception as e:
            logger.error(f"❌ Erro ao buscar jogos de hoje: {e}")

        return todays_matches

    async def get_live_brazilian_matches(self) -> List[Dict]:
        """
        🔴 Obter jogos brasileiros ao vivo
        """
        live_matches = []

        try:
            all_matches = await self.get_todays_matches()

            # Filtrar apenas jogos ao vivo do Brasil
            for match in all_matches:
                if match.get('is_live') and ('Brazil' in match.get('country', '') or 'Brasil' in match.get('country', '')):
                    live_matches.append(match)

            logger.info(f"🔴 {len(live_matches)} jogos brasileiros ao vivo")

        except Exception as e:
            logger.error(f"❌ Erro ao buscar jogos ao vivo: {e}")

        return live_matches

    async def get_league_standings(self, league_id: int, league_name: str) -> Dict:
        """
        📊 Obter classificação de uma liga
        """
        try:
            async with aiohttp.ClientSession(
                headers={'User-Agent': random.choice(self.user_agents)},
                timeout=aiohttp.ClientTimeout(total=20)
            ) as session:

                # URL para classificação do SofaScore
                current_season = datetime.now().year
                url = f"https://api.sofascore.com/api/v1/unique-tournament/{league_id}/season/{current_season}/standings/total"

                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()

                        standings = []
                        for row in data.get('standings', [{}])[0].get('rows', []):
                            team_data = {
                                'position': row.get('position'),
                                'team': {
                                    'id': row.get('team', {}).get('id'),
                                    'name': row.get('team', {}).get('name')
                                },
                                'points': row.get('points'),
                                'played': row.get('played'),
                                'wins': row.get('wins'),
                                'draws': row.get('draws'),
                                'losses': row.get('losses'),
                                'goals_for': row.get('scoresFor'),
                                'goals_against': row.get('scoresAgainst'),
                                'goal_difference': row.get('scoresFor', 0) - row.get('scoresAgainst', 0)
                            }
                            standings.append(team_data)

                        logger.info(f"📊 Classificação de {league_name} coletada: {len(standings)} times")

                        return {
                            'league': league_name,
                            'standings': standings,
                            'updated_at': datetime.now().isoformat()
                        }

        except Exception as e:
            logger.error(f"❌ Erro ao coletar classificação de {league_name}: {e}")

        return {'league': league_name, 'standings': [], 'error': str(e)}

# Instância global
brazilian_spanish_collector = BrazilianSpanishCollector()