"""
🏁 FINISHED MATCHES COLLECTOR - Coletor de jogos finalizados
Foca em coletar jogos já finalizados com resultados para treinar ML
Prioridade: Brasil e Espanha
"""

import asyncio
import httpx
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import os

from app.services.api_sports_collector import api_sports_collector
from app.services.free_apis_collector import free_apis_collector

logger = logging.getLogger(__name__)

class FinishedMatchesCollector:
    """
    🏁 Coletor especializado em jogos finalizados para ML
    """

    def __init__(self):
        self.api_key = os.getenv('API_SPORTS_KEY')
        self.base_url = "https://v3.football.api-sports.io"

        self.headers = {
            'X-RapidAPI-Key': self.api_key,
            'X-RapidAPI-Host': 'v3.football.api-sports.io'
        }

        # Ligas prioritárias com resultados históricos
        self.target_leagues = {
            'brasileirao': {
                'id': 71,
                'name': 'Brasileirão Série A',
                'country': 'Brazil',
                'season': 2024,
                'priority': 1
            },
            'la_liga': {
                'id': 140,
                'name': 'La Liga',
                'country': 'Spain',
                'season': 2024,
                'priority': 2
            },
            'premier_league': {
                'id': 39,
                'name': 'Premier League',
                'country': 'England',
                'season': 2024,
                'priority': 3
            },
            'serie_a': {
                'id': 135,
                'name': 'Serie A',
                'country': 'Italy',
                'season': 2024,
                'priority': 4
            },
            'bundesliga': {
                'id': 78,
                'name': 'Bundesliga',
                'country': 'Germany',
                'season': 2024,
                'priority': 5
            }
        }

    async def collect_finished_matches_for_ml(self, target_finished_matches: int = 100) -> Dict:
        """
        🏁 Coletar jogos finalizados para treinar ML
        """
        logger.info(f"🏁 COLETANDO JOGOS FINALIZADOS PARA ML - Meta: {target_finished_matches}")

        results = {
            'start_time': datetime.now().isoformat(),
            'target_matches': target_finished_matches,
            'leagues': {},
            'all_finished_matches': [],
            'total_finished': 0,
            'success': True
        }

        try:
            # Coletar por liga em ordem de prioridade
            for league_key, league_info in sorted(self.target_leagues.items(),
                                                key=lambda x: x[1]['priority']):

                if results['total_finished'] >= target_finished_matches:
                    break

                logger.info(f"🏆 Coletando jogos finalizados: {league_info['name']}")

                # 1. API-Sports (melhor fonte para resultados)
                api_sports_matches = await self._get_finished_matches_api_sports(league_info)

                # 2. Football-Data.org (backup)
                football_data_matches = await self._get_finished_matches_football_data(league_key)

                # 3. SportDB (backup)
                sportdb_matches = await self._get_finished_matches_sportdb(league_info)

                # Combinar e filtrar apenas finalizados
                all_league_matches = api_sports_matches + football_data_matches + sportdb_matches
                finished_matches = self._filter_finished_matches(all_league_matches)

                results['leagues'][league_key] = {
                    'league_info': league_info,
                    'finished_matches': finished_matches,
                    'count': len(finished_matches)
                }

                results['all_finished_matches'].extend(finished_matches)
                results['total_finished'] = len(results['all_finished_matches'])

                logger.info(f"✅ {league_info['name']}: {len(finished_matches)} jogos finalizados")

                # Rate limiting
                await asyncio.sleep(2)

        except Exception as e:
            logger.error(f"❌ Erro coletando jogos finalizados: {e}")
            results['success'] = False

        results['end_time'] = datetime.now().isoformat()
        logger.info(f"🏁 COLETA FINALIZADA: {results['total_finished']} jogos com resultados")

        return results

    async def _get_finished_matches_api_sports(self, league_info: Dict) -> List[Dict]:
        """
        🔑 Buscar jogos finalizados via API-Sports
        """
        matches = []

        try:
            if not self.api_key:
                return matches

            # Buscar jogos das últimas 4 semanas
            end_date = datetime.now()
            start_date = end_date - timedelta(weeks=4)

            url = f"{self.base_url}/fixtures"
            params = {
                'league': league_info['id'],
                'season': league_info['season'],
                'status': 'FT',  # Full Time
                'from': start_date.strftime('%Y-%m-%d'),
                'to': end_date.strftime('%Y-%m-%d')
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=self.headers, params=params)

                if response.status_code == 200:
                    data = response.json()

                    for fixture in data.get('response', [])[:25]:  # Máximo 25 por liga
                        try:
                            match_data = self._parse_api_sports_finished_fixture(fixture)
                            if match_data:
                                matches.append(match_data)
                        except Exception as e:
                            logger.warning(f"⚠️ Erro processando fixture finalizado: {e}")

                elif response.status_code == 429:
                    logger.warning("⚠️ API-Sports: Rate limit atingido")
                else:
                    logger.warning(f"⚠️ API-Sports status {response.status_code}")

        except Exception as e:
            logger.error(f"❌ Erro API-Sports jogos finalizados: {e}")

        return matches

    async def _get_finished_matches_football_data(self, league_key: str) -> List[Dict]:
        """
        ⚽ Buscar jogos finalizados via Football-Data.org
        """
        matches = []

        try:
            # Mapear chaves para códigos Football-Data
            league_codes = {
                'brasileirao': 'BSA',  # Se disponível
                'la_liga': 'PD',
                'premier_league': 'PL',
                'serie_a': 'SA',
                'bundesliga': 'BL1'
            }

            league_code = league_codes.get(league_key)
            if not league_code or not os.getenv('FOOTBALL_DATA_API_KEY'):
                return matches

            headers = {
                'X-Auth-Token': os.getenv('FOOTBALL_DATA_API_KEY')
            }

            base_url = "https://api.football-data.org/v4"
            url = f"{base_url}/competitions/{league_code}/matches"

            params = {
                'status': 'FINISHED',
                'limit': 20
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers, params=params)

                if response.status_code == 200:
                    data = response.json()

                    for match in data.get('matches', []):
                        try:
                            if match['status'] == 'FINISHED' and match['score']['fullTime']['home'] is not None:
                                match_data = {
                                    'home_team': {'name': match['homeTeam']['name']},
                                    'away_team': {'name': match['awayTeam']['name']},
                                    'tournament': match['competition']['name'],
                                    'match_date': match['utcDate'],
                                    'status': 'FINISHED',
                                    'home_score': match['score']['fullTime']['home'],
                                    'away_score': match['score']['fullTime']['away'],
                                    'source': 'football_data_finished',
                                    'match_id': match['id'],
                                    'collected_at': datetime.now().isoformat()
                                }
                                matches.append(match_data)
                        except Exception as e:
                            logger.warning(f"⚠️ Erro processando match Football-Data: {e}")

        except Exception as e:
            logger.error(f"❌ Erro Football-Data jogos finalizados: {e}")

        return matches

    async def _get_finished_matches_sportdb(self, league_info: Dict) -> List[Dict]:
        """
        🏟️ Buscar jogos finalizados via SportDB
        """
        matches = []

        try:
            # SportDB tem dados históricos limitados mas são úteis
            base_url = "https://www.thesportsdb.com/api/v1/json/3"

            # Mapear para IDs SportDB (aproximados)
            sportdb_league_ids = {
                71: '4351',   # Brasileirão (aproximado)
                140: '4335',  # La Liga
                39: '4328',   # Premier League
                135: '4332',  # Serie A
                78: '4331'    # Bundesliga
            }

            league_id = sportdb_league_ids.get(league_info['id'])
            if not league_id:
                return matches

            url = f"{base_url}/eventsseason.php"
            params = {
                'id': league_id,
                's': '2023-2024'
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)

                if response.status_code == 200:
                    data = response.json()

                    for event in data.get('events', [])[:15]:  # Máximo 15
                        try:
                            # Verificar se jogo foi finalizado
                            if (event.get('intHomeScore') is not None and
                                event.get('intAwayScore') is not None and
                                event.get('strStatus') == 'Match Finished'):

                                match_data = {
                                    'home_team': {'name': event.get('strHomeTeam')},
                                    'away_team': {'name': event.get('strAwayTeam')},
                                    'tournament': event.get('strLeague', league_info['name']),
                                    'match_date': event.get('dateEvent'),
                                    'status': 'FINISHED',
                                    'home_score': int(event.get('intHomeScore')),
                                    'away_score': int(event.get('intAwayScore')),
                                    'source': 'sportdb_finished',
                                    'match_id': event.get('idEvent'),
                                    'collected_at': datetime.now().isoformat()
                                }
                                matches.append(match_data)

                        except Exception as e:
                            logger.warning(f"⚠️ Erro processando event SportDB: {e}")

        except Exception as e:
            logger.error(f"❌ Erro SportDB jogos finalizados: {e}")

        return matches

    def _parse_api_sports_finished_fixture(self, fixture: Dict) -> Optional[Dict]:
        """
        🔄 Converter fixture finalizado da API-Sports
        """
        try:
            # Verificar se realmente está finalizado com resultados
            if (fixture['fixture']['status']['short'] != 'FT' or
                fixture['goals']['home'] is None or
                fixture['goals']['away'] is None):
                return None

            home_team = fixture['teams']['home']['name']
            away_team = fixture['teams']['away']['name']
            league_name = fixture['league']['name']

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
                'status': 'FINISHED',
                'home_score': fixture['goals']['home'],
                'away_score': fixture['goals']['away'],
                'venue': fixture['fixture']['venue']['name'] if fixture['fixture']['venue'] else None,
                'referee': fixture['fixture']['referee'],
                'source': 'api_sports_finished',
                'match_id': fixture['fixture']['id'],
                'collected_at': datetime.now().isoformat()
            }

            # Adicionar estatísticas se disponíveis
            if 'statistics' in fixture:
                match_data['statistics'] = fixture['statistics']

            return match_data

        except Exception as e:
            logger.error(f"❌ Erro parsing fixture finalizado: {e}")
            return None

    def _filter_finished_matches(self, matches: List[Dict]) -> List[Dict]:
        """
        🔍 Filtrar apenas jogos realmente finalizados
        """
        finished_matches = []

        for match in matches:
            try:
                # Verificar critérios para ML
                if (match.get('status') == 'FINISHED' and
                    match.get('home_score') is not None and
                    match.get('away_score') is not None and
                    match.get('home_team', {}).get('name') and
                    match.get('away_team', {}).get('name')):

                    finished_matches.append(match)

            except Exception as e:
                logger.warning(f"⚠️ Erro filtrando jogo: {e}")
                continue

        # Remover duplicatas baseado nos times
        seen = set()
        unique_matches = []

        for match in finished_matches:
            match_key = f"{match['home_team']['name']}_{match['away_team']['name']}_{match.get('match_date', '')}"
            if match_key not in seen:
                seen.add(match_key)
                unique_matches.append(match)

        return unique_matches

    def get_ml_training_summary(self, finished_matches: List[Dict]) -> Dict:
        """
        📊 Gerar resumo dos dados para ML
        """
        summary = {
            'total_matches': len(finished_matches),
            'leagues': {},
            'teams': set(),
            'score_patterns': {
                'home_wins': 0,
                'away_wins': 0,
                'draws': 0
            },
            'avg_goals_per_match': 0,
            'data_quality': {
                'complete_scores': 0,
                'missing_data': 0
            }
        }

        total_goals = 0

        for match in finished_matches:
            try:
                # Contabilizar liga
                league = match.get('tournament', 'Unknown')
                if league not in summary['leagues']:
                    summary['leagues'][league] = 0
                summary['leagues'][league] += 1

                # Contabilizar times
                summary['teams'].add(match['home_team']['name'])
                summary['teams'].add(match['away_team']['name'])

                # Analisar resultados
                home_score = match['home_score']
                away_score = match['away_score']

                if home_score > away_score:
                    summary['score_patterns']['home_wins'] += 1
                elif away_score > home_score:
                    summary['score_patterns']['away_wins'] += 1
                else:
                    summary['score_patterns']['draws'] += 1

                total_goals += home_score + away_score
                summary['data_quality']['complete_scores'] += 1

            except Exception as e:
                summary['data_quality']['missing_data'] += 1

        # Calcular médias
        if summary['total_matches'] > 0:
            summary['avg_goals_per_match'] = total_goals / summary['total_matches']

        summary['teams'] = len(summary['teams'])

        return summary

# Instância global
finished_matches_collector = FinishedMatchesCollector()