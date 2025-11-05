#!/usr/bin/env python3
"""
📊 COLETOR DE DADOS - API-FOOTBALL (PLANO PRO)
Script otimizado para coletar dados em massa para treinamento de ML

Plano: Pro - 7500 requests/day
Status atual: 121 requests usados (disponível: 7379)

Estratégia de coleta:
1. Brasileirão Série A (completo temporada 2024)
2. Brasileirão Série B (completo temporada 2024)
3. Copa Libertadores 2024
4. Copa Sul-Americana 2024
5. Premier League 2024
6. La Liga 2024
7. Bundesliga 2024
8. Serie A (Italia) 2024

Com estatísticas detalhadas para cada partida finalizada!
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import json
import logging

sys.path.insert(0, str(Path(__file__).parent))

from app.services.api_football_service import APIFootballService
from app.services.multi_api_adapter import MultiAPIAdapter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataCollector:
    """Coletor otimizado de dados para ML"""

    def __init__(self):
        self.service = APIFootballService()
        self.adapter = MultiAPIAdapter()
        self.service.rate_limit_delay = 0.5  # Com plano Pro podemos ser mais rápidos

        # Ligas prioritárias com IDs corretos
        self.leagues = {
            'brasileirao_a': {'id': 71, 'name': 'Brasileirão Série A', 'priority': 1},
            'brasileirao_b': {'id': 72, 'name': 'Brasileirão Série B', 'priority': 2},
            'libertadores': {'id': 13, 'name': 'Copa Libertadores', 'priority': 3},
            'sul_americana': {'id': 11, 'name': 'Copa Sul-Americana', 'priority': 4},
            'premier_league': {'id': 39, 'name': 'Premier League', 'priority': 5},
            'la_liga': {'id': 140, 'name': 'La Liga', 'priority': 6},
            'bundesliga': {'id': 78, 'name': 'Bundesliga', 'priority': 7},
            'serie_a': {'id': 135, 'name': 'Serie A (Italia)', 'priority': 8}
        }

        self.results = {
            'collection_start': datetime.now().isoformat(),
            'leagues': {},
            'totals': {
                'fixtures_collected': 0,
                'fixtures_with_stats': 0,
                'valid_for_training': 0
            },
            'requests_used': 0
        }

    async def collect_league_data(self, league_key: str, league_info: dict, season: int = 2024):
        """
        Coletar dados completos de uma liga

        Args:
            league_key: Chave da liga (ex: 'brasileirao_a')
            league_info: Info da liga (id, name, priority)
            season: Ano da temporada
        """
        league_id = league_info['id']
        league_name = league_info['name']

        print(f"\n{'='*60}")
        print(f"🏆 Coletando: {league_name} ({season})")
        print(f"{'='*60}")

        try:
            # 1. Obter todas as fixtures da liga
            print(f"📦 Buscando fixtures da temporada {season}...")
            fixtures = await self.service.get_fixtures_by_league(
                league_id=league_id,
                season=season
            )

            self.results['requests_used'] += 1

            # Filtrar apenas finalizados
            finished_fixtures = [
                f for f in fixtures
                if f.get('fixture', {}).get('status', {}).get('short') == 'FT'
            ]

            print(f"✅ {len(finished_fixtures)} partidas finalizadas encontradas")

            # 2. Coletar estatísticas de cada partida (apenas se não tiver muitas)
            enriched_fixtures = []

            # Limitar estatísticas detalhadas para economizar requests se necessário
            max_detailed_stats = 100 if league_info['priority'] <= 4 else 50

            for idx, fixture in enumerate(finished_fixtures[:max_detailed_stats]):
                fixture_id = fixture.get('fixture', {}).get('id')

                if idx % 10 == 0:
                    print(f"   📊 Coletando estatísticas... [{idx}/{len(finished_fixtures[:max_detailed_stats])}]")

                try:
                    # Buscar estatísticas detalhadas
                    statistics = await self.service.get_fixture_statistics(fixture_id)
                    self.results['requests_used'] += 1

                    # Adicionar estatísticas ao fixture
                    fixture_with_stats = {
                        **fixture,
                        'detailed_statistics': statistics,
                        'has_detailed_stats': True
                    }

                    enriched_fixtures.append(fixture_with_stats)
                    self.results['totals']['fixtures_with_stats'] += 1

                    # Pequeno delay para não sobrecarregar
                    await asyncio.sleep(0.1)

                except Exception as e:
                    logger.warning(f"Erro ao buscar stats da fixture {fixture_id}: {e}")
                    enriched_fixtures.append({**fixture, 'has_detailed_stats': False})

            # Adicionar fixtures sem stats detalhadas (para ter mais dados)
            for fixture in finished_fixtures[max_detailed_stats:]:
                enriched_fixtures.append({**fixture, 'has_detailed_stats': False})

            # 3. Normalizar fixtures
            normalized_fixtures = []
            for fixture in enriched_fixtures:
                normalized = self.adapter.normalize_fixture_from_api_football(fixture)

                if normalized and self.adapter.is_valid_for_training(normalized):
                    # Adicionar estatísticas detalhadas se disponíveis
                    if fixture.get('has_detailed_stats'):
                        normalized['statistics'] = self.adapter.extract_advanced_statistics(
                            fixture.get('detailed_statistics', [])
                        )

                    normalized_fixtures.append(normalized)
                    self.results['totals']['valid_for_training'] += 1

            self.results['totals']['fixtures_collected'] += len(normalized_fixtures)

            # 4. Salvar dados da liga
            output_dir = Path('app/ml/data/api_football')
            output_dir.mkdir(parents=True, exist_ok=True)

            league_file = output_dir / f"{league_key}_{season}.json"
            with open(league_file, 'w') as f:
                json.dump(normalized_fixtures, f, indent=2, default=str)

            print(f"💾 Dados salvos: {league_file}")
            print(f"✅ {len(normalized_fixtures)} fixtures válidos para treinamento")

            self.results['leagues'][league_key] = {
                'league_id': league_id,
                'league_name': league_name,
                'season': season,
                'total_fixtures': len(fixtures),
                'finished_fixtures': len(finished_fixtures),
                'enriched_with_stats': sum(1 for f in enriched_fixtures if f.get('has_detailed_stats')),
                'valid_for_training': len(normalized_fixtures),
                'data_file': str(league_file)
            }

            return True

        except Exception as e:
            logger.error(f"Erro ao coletar {league_name}: {e}")
            self.results['leagues'][league_key] = {
                'error': str(e)
            }
            return False

    async def run_collection(self, max_leagues: int = None):
        """
        Executar coleta completa

        Args:
            max_leagues: Limite de ligas para coletar (None = todas)
        """
        print("🚀"*30)
        print("INICIANDO COLETA DE DADOS EM MASSA")
        print("API-Football v3 (Plano Pro - 7500 req/day)")
        print("🚀"*30)

        # Ordenar ligas por prioridade
        sorted_leagues = sorted(
            self.leagues.items(),
            key=lambda x: x[1]['priority']
        )

        # Limitar se necessário
        if max_leagues:
            sorted_leagues = sorted_leagues[:max_leagues]

        # Coletar cada liga
        for league_key, league_info in sorted_leagues:
            success = await self.collect_league_data(league_key, league_info)

            if not success:
                logger.warning(f"⚠️ Falha ao coletar {league_info['name']}")

            # Status de requests
            print(f"\n📊 Requests usados nesta execução: ~{self.results['requests_used']}")

        # Resumo final
        print("\n" + "="*60)
        print("📊 RESUMO DA COLETA")
        print("="*60)

        print(f"\n✅ Ligas coletadas: {len([l for l in self.results['leagues'].values() if 'error' not in l])}")
        print(f"⚽ Total de fixtures: {self.results['totals']['fixtures_collected']}")
        print(f"📊 Fixtures com estatísticas: {self.results['totals']['fixtures_with_stats']}")
        print(f"🎓 Fixtures válidos para ML: {self.results['totals']['valid_for_training']}")
        print(f"📡 Requests aproximados: {self.results['requests_used']}")

        print("\nDetalhes por liga:")
        for league_key, league_data in self.results['leagues'].items():
            if 'error' not in league_data:
                print(f"   ✅ {league_data['league_name']}:")
                print(f"      - Finalizados: {league_data['finished_fixtures']}")
                print(f"      - Com stats: {league_data['enriched_with_stats']}")
                print(f"      - Válidos: {league_data['valid_for_training']}")
            else:
                print(f"   ❌ {league_key}: {league_data['error']}")

        # Salvar resumo
        summary_file = Path('app/ml/data/api_football/collection_summary.json')
        summary_file.parent.mkdir(parents=True, exist_ok=True)

        with open(summary_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)

        print(f"\n📄 Resumo salvo em: {summary_file}")

        print("\n" + "="*60)
        print("🎉 COLETA CONCLUÍDA COM SUCESSO!")
        print("="*60)

async def main():
    """Função principal"""
    import argparse

    parser = argparse.ArgumentParser(description='Coletor de dados API-Football')
    parser.add_argument('--max-leagues', type=int, default=None,
                       help='Número máximo de ligas para coletar (padrão: todas)')
    parser.add_argument('--test', action='store_true',
                       help='Modo teste: coleta apenas Brasileirão Série A')

    args = parser.parse_args()

    collector = DataCollector()

    if args.test:
        print("🧪 MODO TESTE: Coletando apenas Brasileirão Série A")
        await collector.collect_league_data('brasileirao_a', collector.leagues['brasileirao_a'])
    else:
        await collector.run_collection(max_leagues=args.max_leagues)

if __name__ == "__main__":
    asyncio.run(main())
