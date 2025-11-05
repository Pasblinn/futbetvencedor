"""
🏆 FBREF EASY SCRAPER - Coletor simples FBref com pandas
Usa pandas.read_html() para coletar tabelas facilmente
Foco em dados históricos das últimas temporadas
"""

import asyncio
import pandas as pd
import requests
import logging
from typing import Dict, List, Optional
from datetime import datetime
import time
import random

logger = logging.getLogger(__name__)

class FBrefEasyScraper:
    """
    🏆 Scraper simples e eficaz para FBref
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

        # URLs das principais ligas com resultados
        self.league_urls = {
            'la_liga_2023': 'https://fbref.com/en/comps/12/2023-2024/schedule/2023-2024-La-Liga-Fixtures',
            'premier_league_2023': 'https://fbref.com/en/comps/9/2023-2024/schedule/2023-2024-Premier-League-Fixtures',
            'serie_a_2023': 'https://fbref.com/en/comps/11/2023-2024/schedule/2023-2024-Serie-A-Fixtures',
            'bundesliga_2023': 'https://fbref.com/en/comps/20/2023-2024/schedule/2023-2024-Bundesliga-Fixtures',

            # Temporadas anteriores (mais dados históricos)
            'la_liga_2022': 'https://fbref.com/en/comps/12/2022-2023/schedule/2022-2023-La-Liga-Fixtures',
            'premier_league_2022': 'https://fbref.com/en/comps/9/2022-2023/schedule/2022-2023-Premier-League-Fixtures',
            'serie_a_2022': 'https://fbref.com/en/comps/11/2022-2023/schedule/2022-2023-Serie-A-Fixtures',
            'bundesliga_2022': 'https://fbref.com/en/comps/20/2022-2023/schedule/2022-2023-Bundesliga-Fixtures',
        }

    def scrape_fbref_results(self, max_leagues: int = 4) -> Dict:
        """
        🏆 Coletar resultados do FBref usando pandas
        """
        logger.info("🏆 INICIANDO COLETA FBREF COM PANDAS...")

        results = {
            'start_time': datetime.now().isoformat(),
            'leagues_data': {},
            'all_matches': [],
            'total_matches': 0,
            'success': True
        }

        try:
            league_count = 0
            for league_key, url in self.league_urls.items():
                if league_count >= max_leagues:
                    break

                logger.info(f"🏆 Processando {league_key}...")

                try:
                    # Usar pandas para ler tabelas HTML
                    league_matches = self._scrape_league_with_pandas(url, league_key)

                    if league_matches:
                        results['leagues_data'][league_key] = {
                            'url': url,
                            'matches': league_matches,
                            'count': len(league_matches)
                        }

                        results['all_matches'].extend(league_matches)
                        logger.info(f"✅ {league_key}: {len(league_matches)} jogos coletados")
                        league_count += 1

                    else:
                        logger.warning(f"⚠️ {league_key}: Nenhum jogo coletado")

                except Exception as e:
                    logger.error(f"❌ Erro {league_key}: {e}")
                    continue

                # Rate limiting gentil
                time.sleep(random.uniform(2, 4))

        except Exception as e:
            logger.error(f"❌ Erro geral FBref: {e}")
            results['success'] = False

        results['total_matches'] = len(results['all_matches'])
        results['end_time'] = datetime.now().isoformat()

        logger.info(f"🏆 FBREF CONCLUÍDO: {results['total_matches']} jogos coletados")
        return results

    def _scrape_league_with_pandas(self, url: str, league_key: str) -> List[Dict]:
        """
        📊 Usar pandas.read_html() para coletar uma liga
        """
        matches = []

        try:
            # Ler todas as tabelas da página
            tables = pd.read_html(url, header=0)

            logger.info(f"📊 {league_key}: {len(tables)} tabelas encontradas")

            # Procurar a tabela de fixtures/resultados
            for i, table in enumerate(tables):
                try:
                    # Verificar se a tabela tem estrutura de resultados
                    if self._is_results_table(table):
                        logger.info(f"📊 Usando tabela {i} como tabela de resultados")

                        # Processar cada linha da tabela
                        for index, row in table.iterrows():
                            try:
                                match_data = self._parse_table_row(row, league_key)
                                if match_data:
                                    matches.append(match_data)
                            except Exception as e:
                                continue

                        break  # Usar apenas a primeira tabela válida

                except Exception as e:
                    logger.warning(f"⚠️ Erro processando tabela {i}: {e}")
                    continue

        except Exception as e:
            logger.error(f"❌ Erro pandas.read_html {url}: {e}")

        return matches

    def _is_results_table(self, table: pd.DataFrame) -> bool:
        """
        🔍 Verificar se a tabela contém resultados de jogos
        """
        try:
            # Converter nomes das colunas para string e verificar estrutura
            columns = [str(col).lower() for col in table.columns]

            # Procurar por colunas típicas de resultados
            result_indicators = [
                'score', 'result', 'home', 'away', 'date',
                'wk', 'round', 'match', 'fixture'
            ]

            # Verificar se tem pelo menos 2 indicadores
            matches = sum(1 for indicator in result_indicators
                         if any(indicator in col for col in columns))

            # Verificar se tem dados suficientes
            has_enough_rows = len(table) > 10
            has_enough_cols = len(table.columns) >= 5

            return matches >= 2 and has_enough_rows and has_enough_cols

        except Exception:
            return False

    def _parse_table_row(self, row: pd.Series, league_key: str) -> Optional[Dict]:
        """
        📝 Processar uma linha da tabela de resultados
        """
        try:
            # Converter série para dict para facilitar acesso
            row_dict = row.to_dict()
            row_values = [str(val) for val in row_dict.values() if pd.notna(val)]

            # Procurar padrões nas colunas
            home_team = None
            away_team = None
            home_score = None
            away_score = None
            match_date = None

            # Tentar diferentes estratégias de parsing
            for i, val in enumerate(row_values):
                val_str = str(val).strip()

                # Procurar por placar (formato: "2–1", "1-0", etc.)
                if '–' in val_str or '-' in val_str:
                    score_parts = val_str.replace('–', '-').split('-')
                    if len(score_parts) == 2:
                        try:
                            home_score = int(score_parts[0].strip())
                            away_score = int(score_parts[1].strip())
                        except ValueError:
                            continue

                # Procurar por nomes de times
                elif (len(val_str) > 3 and
                      not val_str.isdigit() and
                      not any(char in val_str for char in ['/', ':', '(', ')']) and
                      val_str not in ['nan', 'NaN', 'None']):

                    if home_team is None:
                        home_team = val_str
                    elif away_team is None and val_str != home_team:
                        away_team = val_str

                # Procurar por data
                elif (len(val_str) >= 8 and
                      any(char in val_str for char in ['-', '/', '.']) and
                      any(char.isdigit() for char in val_str)):
                    match_date = val_str

            # Verificar se temos dados suficientes
            if (home_team and away_team and
                home_score is not None and away_score is not None):

                match_data = {
                    'home_team': {'name': home_team},
                    'away_team': {'name': away_team},
                    'tournament': self._get_league_name(league_key),
                    'home_score': home_score,
                    'away_score': away_score,
                    'status': 'FINISHED',
                    'match_date': match_date,
                    'source': 'fbref_pandas',
                    'collected_at': datetime.now().isoformat()
                }

                logger.info(f"📊 FBref: {home_team} {home_score}-{away_score} {away_team}")
                return match_data

        except Exception as e:
            logger.warning(f"⚠️ Erro parsing row: {e}")

        return None

    def _get_league_name(self, league_key: str) -> str:
        """
        🏆 Mapear chave para nome da liga
        """
        league_names = {
            'la_liga_2023': 'La Liga 2023-24',
            'la_liga_2022': 'La Liga 2022-23',
            'premier_league_2023': 'Premier League 2023-24',
            'premier_league_2022': 'Premier League 2022-23',
            'serie_a_2023': 'Serie A 2023-24',
            'serie_a_2022': 'Serie A 2022-23',
            'bundesliga_2023': 'Bundesliga 2023-24',
            'bundesliga_2022': 'Bundesliga 2022-23'
        }
        return league_names.get(league_key, 'FBref League')

    def get_training_summary(self, matches: List[Dict]) -> Dict:
        """
        📈 Gerar resumo dos dados coletados
        """
        if not matches:
            return {'error': 'No matches to analyze'}

        summary = {
            'total_matches': len(matches),
            'leagues': {},
            'teams': set(),
            'results_distribution': {
                'home_wins': 0,
                'away_wins': 0,
                'draws': 0
            },
            'goals_stats': {
                'total_goals': 0,
                'avg_goals_per_match': 0,
                'highest_scoring': None,
                'lowest_scoring': None
            }
        }

        total_goals = 0
        highest_goals = 0
        lowest_goals = float('inf')

        for match in matches:
            try:
                # Liga
                league = match.get('tournament', 'Unknown')
                if league not in summary['leagues']:
                    summary['leagues'][league] = 0
                summary['leagues'][league] += 1

                # Times
                summary['teams'].add(match['home_team']['name'])
                summary['teams'].add(match['away_team']['name'])

                # Resultados
                home_score = match['home_score']
                away_score = match['away_score']

                if home_score > away_score:
                    summary['results_distribution']['home_wins'] += 1
                elif away_score > home_score:
                    summary['results_distribution']['away_wins'] += 1
                else:
                    summary['results_distribution']['draws'] += 1

                # Gols
                match_goals = home_score + away_score
                total_goals += match_goals

                if match_goals > highest_goals:
                    highest_goals = match_goals
                    summary['goals_stats']['highest_scoring'] = f"{match['home_team']['name']} {home_score}-{away_score} {match['away_team']['name']}"

                if match_goals < lowest_goals:
                    lowest_goals = match_goals
                    summary['goals_stats']['lowest_scoring'] = f"{match['home_team']['name']} {home_score}-{away_score} {match['away_team']['name']}"

            except Exception as e:
                continue

        # Finalizações
        summary['teams'] = len(summary['teams'])
        summary['goals_stats']['total_goals'] = total_goals
        if summary['total_matches'] > 0:
            summary['goals_stats']['avg_goals_per_match'] = total_goals / summary['total_matches']

        return summary

# Instância global
fbref_easy_scraper = FBrefEasyScraper()