"""
⚽ API-FOOTBALL SERVICE (api-sports.io)
Serviço de integração com a API-Football v3 (https://v3.football.api-sports.io)
API com rate limit muito mais alto e dados mais abrangentes

Rate Limits:
- Free Plan: 100 requests/day
- Basic Plan: 1000 requests/day
- Pro Plan: 10000+ requests/day

Dados Disponíveis:
- 900+ ligas de futebol mundial
- Estatísticas detalhadas de partidas
- Dados de jogadores e times
- Odds de múltiplas casas de apostas
- Eventos ao vivo e lineups
"""

import httpx
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from app.core.config import settings
from app.core.redis import redis_client
import json
import logging

logger = logging.getLogger(__name__)

class APIFootballService:
    """Serviço para integração com API-Football (api-sports.io)"""

    def __init__(self):
        self.base_url = "https://v3.football.api-sports.io"
        self.api_key = settings.API_SPORTS_KEY
        self.headers = {
            "x-apisports-key": self.api_key,
            "Content-Type": "application/json"
        }
        self.cache_ttl = 300  # 5 minutes
        self.rate_limit_delay = 1.0  # Delay entre requests (ajustável)

    async def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Fazer requisição à API com tratamento de erros e rate limiting"""
        try:
            # Aguardar para respeitar rate limit
            await asyncio.sleep(self.rate_limit_delay)

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/{endpoint}",
                    headers=self.headers,
                    params=params or {}
                )

                if response.status_code == 200:
                    data = response.json()

                    # Verificar se a resposta foi bem-sucedida
                    if data.get('response') is not None:
                        return data
                    else:
                        logger.error(f"API retornou erro: {data.get('errors', 'Unknown error')}")
                        return {'response': [], 'errors': data.get('errors', [])}

                elif response.status_code == 429:
                    logger.warning("Rate limit atingido!")
                    return {'response': [], 'errors': ['Rate limit exceeded']}

                else:
                    logger.error(f"Erro na API: {response.status_code} - {response.text}")
                    return {'response': [], 'errors': [f'HTTP {response.status_code}']}

        except Exception as e:
            logger.error(f"Erro ao fazer requisição: {e}")
            return {'response': [], 'errors': [str(e)]}

    async def get_leagues(self, country: str = None, season: int = None) -> List[Dict]:
        """
        Obter ligas disponíveis

        Args:
            country: Código do país (ex: "Brazil", "England", "Spain")
            season: Ano da temporada (ex: 2024, 2025)
        """
        cache_key = f"api_football:leagues:{country}:{season}"
        cached_data = await redis_client.get(cache_key)

        if cached_data:
            return json.loads(cached_data)

        params = {}
        if country:
            params['country'] = country
        if season:
            params['season'] = season

        result = await self._make_request('leagues', params)
        leagues = result.get('response', [])

        await redis_client.setex(cache_key, 3600, json.dumps(leagues))  # Cache 1h
        return leagues

    async def get_fixtures_by_league(
        self,
        league_id: int,
        season: int,
        date_from: str = None,
        date_to: str = None
    ) -> List[Dict]:
        """
        Obter partidas de uma liga específica

        Args:
            league_id: ID da liga (ex: 71 para Brasileirão Série A)
            season: Ano da temporada (ex: 2024)
            date_from: Data inicial (YYYY-MM-DD)
            date_to: Data final (YYYY-MM-DD)
        """
        cache_key = f"api_football:fixtures:{league_id}:{season}:{date_from}:{date_to}"
        cached_data = await redis_client.get(cache_key)

        if cached_data:
            return json.loads(cached_data)

        params = {
            'league': league_id,
            'season': season
        }

        if date_from:
            params['from'] = date_from
        if date_to:
            params['to'] = date_to

        result = await self._make_request('fixtures', params)
        fixtures = result.get('response', [])

        # Cache maior para jogos finalizados
        cache_time = 3600 if fixtures else 300
        await redis_client.setex(cache_key, cache_time, json.dumps(fixtures))

        return fixtures

    async def get_fixtures_by_date(self, date: str, league_ids: List[int] = None) -> List[Dict]:
        """
        🎯 MÉTODO OTIMIZADO: Obter TODOS os fixtures de uma data específica

        Busca todos os jogos de uma data e filtra pelas ligas desejadas.
        ECONOMIA MÁXIMA DE API: 1 request por dia em vez de 1 request por liga por dia

        Args:
            date: Data no formato YYYY-MM-DD
            league_ids: Lista de IDs das ligas para filtrar (opcional)

        Returns:
            Lista de fixtures filtrados pelas ligas
        """
        cache_key = f"api_football:fixtures_by_date:{date}"
        cached_data = await redis_client.get(cache_key)

        if cached_data:
            all_fixtures = json.loads(cached_data)
        else:
            # Buscar TODOS os fixtures da data
            params = {'date': date}
            result = await self._make_request('fixtures', params)
            all_fixtures = result.get('response', [])

            # Cache por 1 hora (jogos futuros) ou 24h (jogos do passado)
            is_past = datetime.strptime(date, '%Y-%m-%d').date() < datetime.now().date()
            cache_time = 86400 if is_past else 3600
            await redis_client.setex(cache_key, cache_time, json.dumps(all_fixtures))

            logger.info(f"📥 API Request: Buscados {len(all_fixtures)} fixtures para {date}")

        # Filtrar pelas ligas desejadas (se especificado)
        if league_ids:
            filtered_fixtures = [
                f for f in all_fixtures
                if f.get('league', {}).get('id') in league_ids
            ]
            logger.info(f"🎯 Filtrados {len(filtered_fixtures)}/{len(all_fixtures)} fixtures para ligas selecionadas")
            return filtered_fixtures

        return all_fixtures

    async def get_live_fixtures(self, league_ids: List[int] = None) -> List[Dict]:
        """
        🔴 MÉTODO OTIMIZADO: Obter TODOS os fixtures AO VIVO agora

        Busca todos os jogos que estão acontecendo AGORA e filtra pelas ligas desejadas.
        NÃO USA CACHE (sempre busca dados frescos)

        Args:
            league_ids: Lista de IDs das ligas para filtrar (opcional)

        Returns:
            Lista de fixtures ao vivo filtrados
        """
        # Buscar TODOS os fixtures ao vivo (sem cache para ter dados frescos)
        params = {'live': 'all'}
        result = await self._make_request('fixtures', params)
        all_live_fixtures = result.get('response', [])

        logger.info(f"🔴 {len(all_live_fixtures)} jogos AO VIVO no momento")

        # Filtrar pelas ligas desejadas (se especificado)
        if league_ids:
            filtered_fixtures = [
                f for f in all_live_fixtures
                if f.get('league', {}).get('id') in league_ids
            ]
            logger.info(f"🎯 {len(filtered_fixtures)}/{len(all_live_fixtures)} jogos ao vivo das ligas selecionadas")
            return filtered_fixtures

        return all_live_fixtures

    async def get_fixture_by_id(self, fixture_id: int) -> Dict:
        """
        Obter um fixture específico por ID (usado para atualizar jogos ao vivo)

        Args:
            fixture_id: ID do fixture

        Returns:
            Dados do fixture
        """
        params = {'id': fixture_id}
        result = await self._make_request('fixtures', params)
        fixtures = result.get('response', [])

        return fixtures[0] if fixtures else {}

    async def get_fixture_details(self, fixture_id: int) -> Dict:
        """
        Obter detalhes completos de uma partida específica

        Args:
            fixture_id: ID da partida
        """
        cache_key = f"api_football:fixture_details:{fixture_id}"
        cached_data = await redis_client.get(cache_key)

        if cached_data:
            return json.loads(cached_data)

        result = await self._make_request('fixtures', {'id': fixture_id})
        fixture_data = result.get('response', [])
        fixture = fixture_data[0] if fixture_data else {}

        # Cache permanente para jogos finalizados
        is_finished = fixture.get('fixture', {}).get('status', {}).get('short') == 'FT'
        cache_time = 86400 if is_finished else 300

        await redis_client.setex(cache_key, cache_time, json.dumps(fixture))
        return fixture

    async def get_fixture_statistics(self, fixture_id: int) -> List[Dict]:
        """
        Obter estatísticas detalhadas de uma partida

        Args:
            fixture_id: ID da partida
        """
        cache_key = f"api_football:fixture_stats:{fixture_id}"
        cached_data = await redis_client.get(cache_key)

        if cached_data:
            return json.loads(cached_data)

        result = await self._make_request('fixtures/statistics', {'fixture': fixture_id})
        stats = result.get('response', [])

        await redis_client.setex(cache_key, 3600, json.dumps(stats))
        return stats

    async def get_team_statistics(
        self,
        team_id: int,
        league_id: int,
        season: int
    ) -> Dict:
        """
        Obter estatísticas de um time em uma temporada específica

        Args:
            team_id: ID do time
            league_id: ID da liga
            season: Ano da temporada
        """
        cache_key = f"api_football:team_stats:{team_id}:{league_id}:{season}"
        cached_data = await redis_client.get(cache_key)

        if cached_data:
            return json.loads(cached_data)

        params = {
            'team': team_id,
            'league': league_id,
            'season': season
        }

        result = await self._make_request('teams/statistics', params)
        stats_data = result.get('response', {})

        await redis_client.setex(cache_key, 1800, json.dumps(stats_data))  # Cache 30min
        return stats_data

    async def get_head_to_head(self, team1_id: int, team2_id: int, last: int = 10) -> List[Dict]:
        """
        Obter histórico de confrontos diretos entre dois times

        Args:
            team1_id: ID do primeiro time
            team2_id: ID do segundo time
            last: Número de jogos recentes (padrão: 10)
        """
        cache_key = f"api_football:h2h:{team1_id}:{team2_id}:{last}"
        cached_data = await redis_client.get(cache_key)

        if cached_data:
            return json.loads(cached_data)

        params = {
            'h2h': f"{team1_id}-{team2_id}",
            'last': last
        }

        result = await self._make_request('fixtures/headtohead', params)
        h2h_fixtures = result.get('response', [])

        await redis_client.setex(cache_key, 3600, json.dumps(h2h_fixtures))
        return h2h_fixtures

    async def get_odds(self, fixture_id: int) -> List[Dict]:
        """
        Obter odds de casas de apostas para uma partida

        Args:
            fixture_id: ID da partida
        """
        cache_key = f"api_football:odds:{fixture_id}"
        cached_data = await redis_client.get(cache_key)

        if cached_data:
            return json.loads(cached_data)

        result = await self._make_request('odds', {'fixture': fixture_id})
        odds = result.get('response', [])

        # Cache curto para odds (variam muito)
        await redis_client.setex(cache_key, 180, json.dumps(odds))  # 3 min
        return odds

    async def get_standings(self, league_id: int, season: int) -> List[Dict]:
        """
        Obter tabela de classificação

        Args:
            league_id: ID da liga
            season: Ano da temporada
        """
        cache_key = f"api_football:standings:{league_id}:{season}"
        cached_data = await redis_client.get(cache_key)

        if cached_data:
            return json.loads(cached_data)

        params = {
            'league': league_id,
            'season': season
        }

        result = await self._make_request('standings', params)
        standings = result.get('response', [])

        await redis_client.setex(cache_key, 1800, json.dumps(standings))
        return standings

    async def collect_brazilian_leagues_data(self, season: int = 2024) -> Dict:
        """
        Coletar dados das principais ligas brasileiras

        Ligas principais:
        - Brasileirão Série A (ID: 71)
        - Brasileirão Série B (ID: 72)
        - Copa Libertadores (ID: 13)
        - Copa Sul-Americana (ID: 11)
        """
        brazilian_leagues = {
            'brasileirao_a': 71,
            'brasileirao_b': 72,
            'libertadores': 13,
            'sul_americana': 11
        }

        results = {
            'season': season,
            'leagues': {},
            'total_matches': 0,
            'errors': []
        }

        for league_name, league_id in brazilian_leagues.items():
            try:
                logger.info(f"Coletando dados de {league_name} (ID: {league_id})...")

                # Obter fixtures da liga
                fixtures = await self.get_fixtures_by_league(
                    league_id=league_id,
                    season=season
                )

                # Filtrar apenas jogos finalizados
                finished_fixtures = [
                    f for f in fixtures
                    if f.get('fixture', {}).get('status', {}).get('short') == 'FT'
                ]

                results['leagues'][league_name] = {
                    'league_id': league_id,
                    'total_fixtures': len(fixtures),
                    'finished_fixtures': len(finished_fixtures),
                    'fixtures': finished_fixtures
                }

                results['total_matches'] += len(finished_fixtures)

                logger.info(f"✅ {league_name}: {len(finished_fixtures)} jogos finalizados coletados")

                # Respeitar rate limit
                await asyncio.sleep(self.rate_limit_delay)

            except Exception as e:
                error_msg = f"Erro ao coletar {league_name}: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)

        return results

    async def collect_major_european_leagues_data(self, season: int = 2024) -> Dict:
        """
        Coletar dados das principais ligas europeias

        Ligas principais:
        - Premier League (ID: 39)
        - La Liga (ID: 140)
        - Bundesliga (ID: 78)
        - Serie A (ID: 135)
        - Ligue 1 (ID: 61)
        - Champions League (ID: 2)
        """
        european_leagues = {
            'premier_league': 39,
            'la_liga': 140,
            'bundesliga': 78,
            'serie_a': 135,
            'ligue_1': 61,
            'champions_league': 2
        }

        results = {
            'season': season,
            'leagues': {},
            'total_matches': 0,
            'errors': []
        }

        for league_name, league_id in european_leagues.items():
            try:
                logger.info(f"Coletando dados de {league_name} (ID: {league_id})...")

                # Obter fixtures da liga
                fixtures = await self.get_fixtures_by_league(
                    league_id=league_id,
                    season=season
                )

                # Filtrar apenas jogos finalizados
                finished_fixtures = [
                    f for f in fixtures
                    if f.get('fixture', {}).get('status', {}).get('short') == 'FT'
                ]

                results['leagues'][league_name] = {
                    'league_id': league_id,
                    'total_fixtures': len(fixtures),
                    'finished_fixtures': len(finished_fixtures),
                    'fixtures': finished_fixtures
                }

                results['total_matches'] += len(finished_fixtures)

                logger.info(f"✅ {league_name}: {len(finished_fixtures)} jogos finalizados coletados")

                # Respeitar rate limit
                await asyncio.sleep(self.rate_limit_delay)

            except Exception as e:
                error_msg = f"Erro ao coletar {league_name}: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)

        return results

    async def get_enriched_fixture_data(self, fixture_id: int) -> Dict:
        """
        Obter dados enriquecidos de uma partida (fixture + statistics + odds)

        Args:
            fixture_id: ID da partida
        """
        try:
            # Buscar dados em paralelo
            fixture_task = self.get_fixture_details(fixture_id)
            stats_task = self.get_fixture_statistics(fixture_id)
            odds_task = self.get_odds(fixture_id)

            fixture, statistics, odds = await asyncio.gather(
                fixture_task,
                stats_task,
                odds_task,
                return_exceptions=True
            )

            return {
                'fixture': fixture if not isinstance(fixture, Exception) else {},
                'statistics': statistics if not isinstance(statistics, Exception) else [],
                'odds': odds if not isinstance(odds, Exception) else [],
                'enriched_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Erro ao enriquecer dados da partida {fixture_id}: {e}")
            return {'error': str(e)}

    async def get_injuries(
        self,
        league_id: int = None,
        season: int = None,
        team_id: int = None,
        fixture_id: int = None,
        timezone: str = "America/Sao_Paulo"
    ) -> List[Dict]:
        """
        Obter lesões de jogadores

        Args:
            league_id: ID da liga (ex: 71 para Brasileirão Série A)
            season: Ano da temporada (ex: 2025)
            team_id: ID do time para filtrar lesões específicas
            fixture_id: ID da partida para lesões específicas
            timezone: Timezone (default: America/Sao_Paulo)

        Returns:
            Lista de lesões com informações de jogador, time, tipo e status
        """
        cache_key = f"api_football:injuries:{league_id}:{season}:{team_id}:{fixture_id}"
        cached_data = await redis_client.get(cache_key)

        if cached_data:
            return json.loads(cached_data)

        params = {'timezone': timezone}
        if league_id:
            params['league'] = league_id
        if season:
            params['season'] = season
        if team_id:
            params['team'] = team_id
        if fixture_id:
            params['fixture'] = fixture_id

        result = await self._make_request('injuries', params)
        injuries = result.get('response', [])

        # Cache por 12 horas (injuries não mudam com frequência)
        await redis_client.setex(cache_key, 43200, json.dumps(injuries))
        return injuries
