"""
🔄 MULTI-API ADAPTER
Adaptador para unificar dados de múltiplas APIs em formato padrão para ML

Compatível com:
- Football-Data.org (API atual - rate limit baixo)
- API-Football (api-sports.io - rate limit alto)
"""

from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MultiAPIAdapter:
    """Adaptador para normalizar dados de diferentes APIs"""

    @staticmethod
    def normalize_fixture_from_api_football(fixture_data: Dict) -> Dict:
        """
        Normalizar fixture da API-Football para formato padrão

        API-Football format:
        {
            "fixture": {...},
            "league": {...},
            "teams": {"home": {...}, "away": {...}},
            "goals": {"home": 2, "away": 1},
            "score": {...}
        }

        Padrão format (Football-Data.org):
        {
            "id": "...",
            "utcDate": "...",
            "status": "...",
            "homeTeam": {...},
            "awayTeam": {...},
            "score": {...}
        }
        """
        try:
            fixture_info = fixture_data.get('fixture', {})
            teams = fixture_data.get('teams', {})
            goals = fixture_data.get('goals', {})
            league = fixture_data.get('league', {})
            score = fixture_data.get('score', {})

            # Mapear status
            status_map = {
                'FT': 'FINISHED',
                'NS': 'SCHEDULED',
                'LIVE': 'IN_PLAY',
                '1H': 'IN_PLAY',
                '2H': 'IN_PLAY',
                'HT': 'IN_PLAY',
                'PST': 'POSTPONED',
                'CANC': 'CANCELLED',
                'ABD': 'ABANDONED'
            }

            api_status = fixture_info.get('status', {}).get('short', 'NS')
            normalized_status = status_map.get(api_status, 'SCHEDULED')

            return {
                'id': str(fixture_info.get('id', '')),
                'utcDate': fixture_info.get('date', ''),
                'status': normalized_status,
                'matchday': league.get('round', ''),
                'stage': 'REGULAR_SEASON',
                'competition': {
                    'id': str(league.get('id', '')),
                    'name': league.get('name', ''),
                    'code': league.get('country', ''),
                    'emblem': league.get('logo', '')
                },
                'homeTeam': {
                    'id': str(teams.get('home', {}).get('id', '')),
                    'name': teams.get('home', {}).get('name', ''),
                    'shortName': teams.get('home', {}).get('name', ''),
                    'crest': teams.get('home', {}).get('logo', '')
                },
                'awayTeam': {
                    'id': str(teams.get('away', {}).get('id', '')),
                    'name': teams.get('away', {}).get('name', ''),
                    'shortName': teams.get('away', {}).get('name', ''),
                    'crest': teams.get('away', {}).get('logo', '')
                },
                'score': {
                    'winner': MultiAPIAdapter._determine_winner(goals),
                    'fullTime': {
                        'home': goals.get('home'),
                        'away': goals.get('away')
                    },
                    'halfTime': {
                        'home': score.get('halftime', {}).get('home'),
                        'away': score.get('halftime', {}).get('away')
                    }
                },
                # Metadados de origem
                '_source_api': 'api-football',
                '_original_id': fixture_info.get('id')
            }

        except Exception as e:
            logger.error(f"Erro ao normalizar fixture: {e}")
            return {}

    @staticmethod
    def _determine_winner(goals: Dict) -> Optional[str]:
        """Determinar vencedor baseado nos gols"""
        home_goals = goals.get('home')
        away_goals = goals.get('away')

        if home_goals is None or away_goals is None:
            return None

        if home_goals > away_goals:
            return 'HOME_TEAM'
        elif away_goals > home_goals:
            return 'AWAY_TEAM'
        else:
            return 'DRAW'

    @staticmethod
    def extract_advanced_statistics(statistics: List[Dict]) -> Dict:
        """
        Extrair estatísticas avançadas do formato API-Football

        statistics format:
        [
            {
                "team": {"id": 127, "name": "Flamengo", ...},
                "statistics": [
                    {"type": "Shots on Goal", "value": 5},
                    {"type": "Possession", "value": "65%"},
                    ...
                ]
            }
        ]
        """
        try:
            stats_dict = {'home': {}, 'away': {}}

            if len(statistics) >= 2:
                home_stats = statistics[0].get('statistics', [])
                away_stats = statistics[1].get('statistics', [])

                # Mapear estatísticas
                for stat in home_stats:
                    stat_type = stat.get('type', '')
                    value = stat.get('value')

                    # Converter valores
                    if isinstance(value, str):
                        value = value.replace('%', '')
                        try:
                            value = float(value) if value else 0
                        except:
                            value = 0

                    stats_dict['home'][stat_type] = value

                for stat in away_stats:
                    stat_type = stat.get('type', '')
                    value = stat.get('value')

                    if isinstance(value, str):
                        value = value.replace('%', '')
                        try:
                            value = float(value) if value else 0
                        except:
                            value = 0

                    stats_dict['away'][stat_type] = value

            return stats_dict

        except Exception as e:
            logger.error(f"Erro ao extrair estatísticas: {e}")
            return {'home': {}, 'away': {}}

    @staticmethod
    def convert_api_football_to_training_format(fixtures: List[Dict]) -> List[Dict]:
        """
        Converter lista de fixtures da API-Football para formato de treinamento

        Args:
            fixtures: Lista de fixtures da API-Football

        Returns:
            Lista normalizada no formato padrão
        """
        normalized_fixtures = []

        for fixture in fixtures:
            normalized = MultiAPIAdapter.normalize_fixture_from_api_football(fixture)

            if normalized and normalized.get('status') == 'FINISHED':
                normalized_fixtures.append(normalized)

        logger.info(f"Convertidos {len(normalized_fixtures)} fixtures para formato de treinamento")
        return normalized_fixtures

    @staticmethod
    def is_valid_for_training(fixture: Dict) -> bool:
        """
        Verificar se fixture tem dados suficientes para treinamento

        Args:
            fixture: Fixture normalizado

        Returns:
            True se válido para treinamento
        """
        required_fields = [
            'id',
            'utcDate',
            'status',
            'homeTeam',
            'awayTeam',
            'score'
        ]

        # Verificar campos obrigatórios
        if not all(fixture.get(field) for field in required_fields):
            return False

        # Verificar se tem placar
        score = fixture.get('score', {})
        full_time = score.get('fullTime', {})

        if full_time.get('home') is None or full_time.get('away') is None:
            return False

        # Verificar se está finalizado
        if fixture.get('status') != 'FINISHED':
            return False

        return True

    @staticmethod
    def merge_fixtures_from_multiple_sources(
        fixtures_list: List[List[Dict]]
    ) -> List[Dict]:
        """
        Mesclar fixtures de múltiplas fontes removendo duplicatas

        Args:
            fixtures_list: Lista de listas de fixtures de diferentes fontes

        Returns:
            Lista mesclada sem duplicatas
        """
        seen_matches = set()
        merged_fixtures = []

        for fixtures in fixtures_list:
            for fixture in fixtures:
                # Criar chave única baseada em times e data
                home_team = fixture.get('homeTeam', {}).get('name', '')
                away_team = fixture.get('awayTeam', {}).get('name', '')
                match_date = fixture.get('utcDate', '')

                if not all([home_team, away_team, match_date]):
                    continue

                # Extrair apenas a data (sem hora)
                try:
                    date_only = match_date.split('T')[0]
                except:
                    date_only = match_date

                match_key = f"{home_team}_{away_team}_{date_only}"

                if match_key not in seen_matches:
                    seen_matches.add(match_key)
                    merged_fixtures.append(fixture)

        logger.info(f"Mesclados {len(merged_fixtures)} fixtures únicos de {sum(len(f) for f in fixtures_list)} totais")
        return merged_fixtures

    @staticmethod
    def get_league_id_mapping() -> Dict:
        """
        Mapeamento de IDs de ligas entre diferentes APIs

        Returns:
            Dict com mapeamento {league_name: {api_name: league_id}}
        """
        return {
            'brasileirao_a': {
                'football_data': 'BSA',
                'api_football': 71
            },
            'brasileirao_b': {
                'football_data': 'BSB',
                'api_football': 72
            },
            'libertadores': {
                'football_data': 'CL',
                'api_football': 13
            },
            'sul_americana': {
                'football_data': 'CSA',
                'api_football': 11
            },
            'premier_league': {
                'football_data': 'PL',
                'api_football': 39
            },
            'la_liga': {
                'football_data': 'PD',
                'api_football': 140
            },
            'bundesliga': {
                'football_data': 'BL1',
                'api_football': 78
            },
            'serie_a': {
                'football_data': 'SA',
                'api_football': 135
            },
            'ligue_1': {
                'football_data': 'FL1',
                'api_football': 61
            },
            'champions_league': {
                'football_data': 'CL',
                'api_football': 2
            }
        }
