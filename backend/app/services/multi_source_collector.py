"""
🌐 MULTI-SOURCE DATA COLLECTOR
Coletor integrado que combina dados de múltiplas fontes:
- APIs oficiais (Football-Data.org + The Odds API)
- Web scraping (Oddspedia.com + SofaScore.com)
- Armazenamento unificado no banco de dados
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from app.services.football_data_service import FootballDataService
from app.services.odds_service import OddsService
from app.services.oddspedia_scraper import OddspediaScraper
from app.services.sofascore_scraper import SofaScoreScraper, SofaScoreIntegration
from app.core.database import get_db_session
from app.models.team import Team
from app.models.match import Match
from app.models.odds import Odds

logger = logging.getLogger(__name__)

class MultiSourceCollector:
    """
    🔄 Coletor de dados multi-fonte
    Combina APIs oficiais e web scraping para máxima cobertura de dados
    """

    def __init__(self):
        # Serviços de API
        self.football_api = FootballDataService()
        self.odds_api = OddsService()

        # Configurações de coleta
        self.collection_config = {
            'use_apis': True,           # Usar APIs oficiais
            'use_oddspedia': True,      # Usar scraping Oddspedia
            'use_sofascore': True,      # Usar scraping SofaScore
            'rate_limit_delay': 3.0,    # Delay entre requests
            'max_retries': 2,           # Máximo de tentativas
            'timeout_seconds': 30       # Timeout por request
        }

        # Integração SofaScore
        self.sofascore_integration = SofaScoreIntegration()

    async def collect_comprehensive_data(self) -> Dict:
        """
        🎯 Coleta completa de dados de todas as fontes
        """
        logger.info("🌐 Iniciando coleta multi-fonte de dados...")

        results = {
            'start_time': datetime.now().isoformat(),
            'sources': {
                'official_apis': {'teams': 0, 'matches': 0, 'odds': 0, 'errors': []},
                'oddspedia': {'matches': 0, 'odds': 0, 'errors': []},
                'sofascore': {'live_matches': 0, 'statistics': 0, 'standings': 0, 'errors': []}
            },
            'totals': {'teams': 0, 'matches': 0, 'odds': 0, 'enhanced_data': 0},
            'errors': []
        }

        try:
            # 1. Coletar dados das APIs oficiais
            if self.collection_config['use_apis']:
                logger.info("📡 Coletando dados das APIs oficiais...")
                api_results = await self._collect_from_apis()
                results['sources']['official_apis'] = api_results

            # 2. Coletar dados do Oddspedia
            if self.collection_config['use_oddspedia']:
                logger.info("🕷️ Coletando dados do Oddspedia...")
                oddspedia_results = await self._collect_from_oddspedia()
                results['sources']['oddspedia'] = oddspedia_results

            # 3. Coletar dados do SofaScore
            if self.collection_config['use_sofascore']:
                logger.info("⚽ Coletando dados do SofaScore...")
                sofascore_results = await self._collect_from_sofascore()
                results['sources']['sofascore'] = sofascore_results

            # 4. Consolidar e armazenar dados
            logger.info("💾 Consolidando e armazenando dados...")
            consolidation_results = await self._consolidate_and_store(results)
            results['totals'] = consolidation_results

            results['end_time'] = datetime.now().isoformat()
            results['success'] = True

            logger.info(f"✅ Coleta multi-fonte concluída: {results['totals']}")

        except Exception as e:
            logger.error(f"❌ Erro na coleta multi-fonte: {e}")
            results['errors'].append(str(e))
            results['success'] = False

        return results

    async def _collect_from_apis(self) -> Dict:
        """Coletar dados das APIs oficiais"""
        api_results = {'teams': 0, 'matches': 0, 'odds': 0, 'errors': []}

        try:
            # Coletar jogos de hoje e próximos dias
            today = datetime.now().strftime('%Y-%m-%d')
            next_week = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')

            # Ligas prioritárias (ajustado para evitar rate limits)
            priority_leagues = ['PL', 'PD', 'BSA']  # Premier, La Liga, Brasileirão

            for league in priority_leagues:
                try:
                    await asyncio.sleep(self.collection_config['rate_limit_delay'])

                    # Buscar jogos da liga
                    matches = await self.football_api.get_matches_by_competition(
                        league, today, next_week
                    )

                    api_results['matches'] += len(matches)
                    logger.info(f"   📅 {league}: {len(matches)} jogos coletados")

                    # Para cada jogo, tentar obter odds
                    for match in matches[:5]:  # Limitar para evitar rate limit
                        try:
                            home_team = match.get('homeTeam', {}).get('name', '')
                            away_team = match.get('awayTeam', {}).get('name', '')

                            if home_team and away_team:
                                odds_data = await self.odds_api.get_match_odds(
                                    home_team=home_team,
                                    away_team=away_team
                                )

                                if odds_data:
                                    api_results['odds'] += 1

                        except Exception as e:
                            api_results['errors'].append(f"Erro ao buscar odds: {str(e)}")

                except Exception as e:
                    api_results['errors'].append(f"Erro na liga {league}: {str(e)}")

        except Exception as e:
            api_results['errors'].append(f"Erro geral nas APIs: {str(e)}")

        return api_results

    async def _collect_from_oddspedia(self) -> Dict:
        """Coletar dados do Oddspedia"""
        oddspedia_results = {'matches': 0, 'odds': 0, 'errors': []}

        try:
            async with OddspediaScraper() as scraper:
                # Buscar jogos de hoje
                matches = await scraper.get_football_matches_today()
                oddspedia_results['matches'] = len(matches)

                # Para alguns jogos, buscar odds detalhadas
                for match in matches[:3]:  # Limitar para não sobrecarregar
                    try:
                        if 'match_url' in match:
                            odds_data = await scraper.get_match_odds(match_url=match['match_url'])
                            if odds_data:
                                oddspedia_results['odds'] += 1

                        await asyncio.sleep(2)  # Rate limiting

                    except Exception as e:
                        oddspedia_results['errors'].append(f"Erro ao buscar odds: {str(e)}")

        except Exception as e:
            oddspedia_results['errors'].append(f"Erro no Oddspedia: {str(e)}")

        return oddspedia_results

    async def _collect_from_sofascore(self) -> Dict:
        """Coletar dados do SofaScore"""
        sofascore_results = {'live_matches': 0, 'statistics': 0, 'standings': 0, 'errors': []}

        try:
            async with SofaScoreScraper() as scraper:
                # Buscar jogos ao vivo
                live_matches = await scraper.get_live_matches()
                sofascore_results['live_matches'] = len(live_matches)

                # Buscar classificação do Brasileirão
                standings = await scraper.get_league_standings('brasileirao')
                if standings and standings.get('standings'):
                    sofascore_results['standings'] = len(standings['standings'])

                # Buscar estatísticas de alguns times importantes
                important_teams = ['Flamengo', 'Palmeiras', 'Manchester United', 'Real Madrid']

                for team in important_teams:
                    try:
                        team_stats = await scraper.get_team_statistics(team)
                        if team_stats:
                            sofascore_results['statistics'] += 1

                        await asyncio.sleep(2)  # Rate limiting

                    except Exception as e:
                        sofascore_results['errors'].append(f"Erro estatísticas {team}: {str(e)}")

        except Exception as e:
            sofascore_results['errors'].append(f"Erro no SofaScore: {str(e)}")

        return sofascore_results

    async def _consolidate_and_store(self, results: Dict) -> Dict:
        """Consolidar dados de todas as fontes e armazenar no banco"""
        consolidation_results = {'teams': 0, 'matches': 0, 'odds': 0, 'enhanced_data': 0}

        try:
            with get_db_session() as db:
                # Contar dados já existentes
                existing_teams = db.query(Team).count()
                existing_matches = db.query(Match).count()
                existing_odds = db.query(Odds).count()

                logger.info(f"📊 Dados existentes: {existing_teams} times, {existing_matches} jogos, {existing_odds} odds")

                # Aqui você pode implementar a lógica de consolidação e armazenamento
                # Por enquanto, vamos apenas reportar os totais

                consolidation_results = {
                    'teams': existing_teams,
                    'matches': existing_matches,
                    'odds': existing_odds,
                    'enhanced_data': (
                        results['sources']['oddspedia']['matches'] +
                        results['sources']['sofascore']['live_matches'] +
                        results['sources']['sofascore']['statistics']
                    )
                }

        except Exception as e:
            logger.error(f"❌ Erro na consolidação: {e}")

        return consolidation_results

    async def enhance_existing_matches(self) -> Dict:
        """
        ✨ Enriquecer jogos existentes no banco com dados adicionais
        """
        logger.info("✨ Enriquecendo dados de jogos existentes...")

        enhancement_results = {'enhanced_matches': 0, 'errors': []}

        try:
            with get_db_session() as db:
                # Buscar jogos futuros ou em andamento
                upcoming_matches = db.query(Match).filter(
                    Match.match_date >= datetime.now(),
                    Match.status.in_(['SCHEDULED', 'LIVE'])
                ).limit(10).all()

                for match in upcoming_matches:
                    try:
                        # Enriquecer com dados do SofaScore
                        match_data = {
                            'home_team': {'name': match.home_team.name if match.home_team else ''},
                            'away_team': {'name': match.away_team.name if match.away_team else ''}
                        }

                        enhanced_data = await self.sofascore_integration.enrich_match_data(match_data)

                        if enhanced_data.get('sofascore_stats'):
                            # Aqui você pode salvar os dados enriquecidos
                            # Por exemplo, em uma nova tabela ou como JSON no campo match_data
                            enhancement_results['enhanced_matches'] += 1

                        await asyncio.sleep(1)  # Rate limiting

                    except Exception as e:
                        enhancement_results['errors'].append(f"Erro ao enriquecer jogo {match.id}: {str(e)}")

        except Exception as e:
            enhancement_results['errors'].append(f"Erro geral no enhancement: {str(e)}")

        logger.info(f"✨ Enhancement concluído: {enhancement_results['enhanced_matches']} jogos enriquecidos")
        return enhancement_results

    async def get_live_data_update(self) -> Dict:
        """
        🔴 Atualização rápida de dados ao vivo
        """
        logger.info("🔴 Atualizando dados ao vivo...")

        live_update = {'live_matches': [], 'updated_odds': [], 'errors': []}

        try:
            # Dados ao vivo do SofaScore
            async with SofaScoreScraper() as scraper:
                live_matches = await scraper.get_live_matches()
                live_update['live_matches'] = live_matches

            # Odds atualizadas do Oddspedia
            async with OddspediaScraper() as scraper:
                today_matches = await scraper.get_football_matches_today()

                for match in today_matches[:5]:  # Limitar para performance
                    if 'odds' in match:
                        live_update['updated_odds'].append(match['odds'])

        except Exception as e:
            live_update['errors'].append(f"Erro na atualização ao vivo: {str(e)}")

        return live_update


# Função de teste
async def test_multi_source_collector():
    """🧪 Testar o coletor multi-fonte"""

    collector = MultiSourceCollector()

    print("🌐 TESTANDO COLETOR MULTI-FONTE")
    print("=" * 50)

    # Teste de coleta completa
    print("🔄 Executando coleta completa...")
    results = await collector.collect_comprehensive_data()

    print(f"\n📊 RESULTADOS DA COLETA:")
    print(f"APIs Oficiais: {results['sources']['official_apis']['matches']} jogos, {results['sources']['official_apis']['odds']} odds")
    print(f"Oddspedia: {results['sources']['oddspedia']['matches']} jogos, {results['sources']['oddspedia']['odds']} odds")
    print(f"SofaScore: {results['sources']['sofascore']['live_matches']} ao vivo, {results['sources']['sofascore']['statistics']} estatísticas")

    # Teste de dados ao vivo
    print("\n🔴 Testando dados ao vivo...")
    live_data = await collector.get_live_data_update()
    print(f"Jogos ao vivo: {len(live_data['live_matches'])}")
    print(f"Odds atualizadas: {len(live_data['updated_odds'])}")

    if results['errors']:
        print(f"\n⚠️ Erros encontrados: {len(results['errors'])}")

if __name__ == "__main__":
    asyncio.run(test_multi_source_collector())