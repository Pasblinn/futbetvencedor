"""
🌍 MASSIVE DATA COLLECTOR - Coleta massiva de dados de futebol
Testa múltiplos sites para extrair o máximo de dados possível
Sites alvo: FBref, RSSSF, OpenFootball, Soccerway, Wikipedia
"""

import asyncio
import time
from advanced_table_scraper import AdvancedTableScraper
import os

class MassiveDataCollector:
    """
    🌍 Coletor massivo de dados de futebol
    """

    def __init__(self):
        self.scraper = AdvancedTableScraper()
        self.all_results = []

        # URLs organizadas por site e tipo
        self.target_sites = {
            'fbref': {
                'name': 'FBref - Football Reference',
                'urls': [
                    'https://fbref.com/en/comps/24/Serie-A-Stats',  # Brasileirão
                    'https://fbref.com/en/comps/24/schedule/Serie-A-Scores-and-Fixtures',  # Resultados Brasileirão
                    'https://fbref.com/en/comps/12/La-Liga-Stats',  # La Liga
                    'https://fbref.com/en/comps/12/schedule/La-Liga-Scores-and-Fixtures',  # Resultados La Liga
                    'https://fbref.com/en/comps/9/Premier-League-Stats',  # Premier League
                    'https://fbref.com/en/comps/9/schedule/Premier-League-Scores-and-Fixtures',  # Resultados Premier League
                    'https://fbref.com/en/comps/11/Serie-A-Stats',  # Serie A Italia
                    'https://fbref.com/en/comps/11/schedule/Serie-A-Scores-and-Fixtures',  # Resultados Serie A
                ]
            },
            'rsssf': {
                'name': 'RSSSF - Rec.Sport.Soccer Statistics Foundation',
                'urls': [
                    'https://www.rsssf.com/tablesbr/bra2024.html',  # Brasileirão 2024
                    'https://www.rsssf.com/tablesbr/bra2023.html',  # Brasileirão 2023
                    'https://www.rsssf.com/tabless/spain2024.html',  # La Liga 2024
                    'https://www.rsssf.com/tablese/eng2024.html',  # Premier League 2024
                    'https://www.rsssf.com/tablesi/ital2024.html',  # Serie A 2024
                ]
            },
            'soccerway': {
                'name': 'Soccerway International',
                'urls': [
                    'https://int.soccerway.com/national/brazil/serie-a/2024/regular-season/r72171/',  # Brasileirão 2024
                    'https://int.soccerway.com/national/spain/primera-division/2024-2025/regular-season/r85424/',  # La Liga 2024-25
                    'https://int.soccerway.com/national/england/premier-league/2024-2025/regular-season/r85362/',  # Premier 2024-25
                    'https://int.soccerway.com/national/italy/serie-a/2024-2025/regular-season/r85364/',  # Serie A 2024-25
                ]
            },
            'wikipedia': {
                'name': 'Wikipedia - Campeonatos e Temporadas',
                'urls': [
                    'https://pt.wikipedia.org/wiki/Campeonato_Brasileiro_de_Futebol_de_2024_-_Série_A',  # Brasileirão 2024
                    'https://pt.wikipedia.org/wiki/Campeonato_Brasileiro_de_Futebol_de_2023_-_Série_A',  # Brasileirão 2023
                    'https://en.wikipedia.org/wiki/2024–25_La_Liga',  # La Liga 2024-25
                    'https://en.wikipedia.org/wiki/2024–25_Premier_League',  # Premier League 2024-25
                    'https://en.wikipedia.org/wiki/2024–25_Serie_A',  # Serie A 2024-25
                ]
            },
            'transfermarkt': {
                'name': 'Transfermarkt (sites alternativos)',
                'urls': [
                    'https://www.transfermarkt.com.br/campeonato-brasileiro-serie-a/spielplan/wettbewerb/BRA1/saison_id/2024',  # Jogos Brasileirão
                    'https://www.transfermarkt.com/primera-division/spielplan/wettbewerb/ES1/saison_id/2024',  # Jogos La Liga
                    'https://www.transfermarkt.com/premier-league/spielplan/wettbewerb/GB1/saison_id/2024',  # Jogos Premier
                    'https://www.transfermarkt.com/serie-a/spielplan/wettbewerb/IT1/saison_id/2024',  # Jogos Serie A
                ]
            },
            'globoesporte': {
                'name': 'Globo Esporte (fonte brasileira)',
                'urls': [
                    'https://globoesporte.globo.com/futebol/brasileirao-serie-a/',  # Brasileirão principal
                    'https://globoesporte.globo.com/futebol/brasileirao-serie-a/tabela/',  # Tabela Brasileirão
                ]
            }
        }

    def print_header(self, text: str):
        """Imprimir cabeçalho formatado"""
        print("\n" + "="*80)
        print(f"🌍 {text}")
        print("="*80)

    def print_site_header(self, site_name: str, site_key: str):
        """Imprimir cabeçalho do site"""
        print(f"\n🎯 SITE: {site_name} ({site_key.upper()})")
        print("-" * 60)

    async def test_site_urls(self, site_key: str, site_info: dict) -> dict:
        """
        Testar todas as URLs de um site específico
        """
        site_results = {
            'site': site_key,
            'name': site_info['name'],
            'total_urls': len(site_info['urls']),
            'successful_urls': 0,
            'failed_urls': 0,
            'total_tables': 0,
            'total_files': 0,
            'url_results': []
        }

        self.print_site_header(site_info['name'], site_key)

        for i, url in enumerate(site_info['urls'], 1):
            print(f"\n📄 URL {i}/{len(site_info['urls'])}: {url}")

            try:
                # Delay entre requests para evitar bloqueios
                if i > 1:
                    delay = 3
                    print(f"⏳ Aguardando {delay}s...")
                    await asyncio.sleep(delay)

                # Fazer scraping
                result = self.scraper.scrape_url(url)

                # Processar resultado
                if result['success']:
                    site_results['successful_urls'] += 1
                    site_results['total_tables'] += result['tables_found']
                    site_results['total_files'] += len(result['files_saved'])

                    print(f"✅ SUCESSO! Método: {result['method_used']}")
                    print(f"   📊 Tabelas: {result['tables_found']} | 💾 Arquivos: {len(result['files_saved'])}")

                    if result['files_saved']:
                        for file in result['files_saved'][:3]:  # Mostrar apenas os primeiros 3
                            print(f"   📁 {os.path.basename(file)}")
                        if len(result['files_saved']) > 3:
                            print(f"   📁 ... e mais {len(result['files_saved'])-3} arquivos")
                else:
                    site_results['failed_urls'] += 1
                    print(f"❌ FALHA: {result.get('error', 'Erro desconhecido')}")

                site_results['url_results'].append({
                    'url': url,
                    'success': result['success'],
                    'method_used': result.get('method_used'),
                    'tables_found': result.get('tables_found', 0),
                    'files_saved': len(result.get('files_saved', [])),
                    'error': result.get('error')
                })

            except Exception as e:
                site_results['failed_urls'] += 1
                print(f"❌ ERRO GERAL: {e}")
                site_results['url_results'].append({
                    'url': url,
                    'success': False,
                    'error': str(e)
                })

        return site_results

    async def collect_all_data(self):
        """
        Coletar dados de todos os sites
        """
        self.print_header("COLETA MASSIVA DE DADOS DE FUTEBOL")
        print("🎯 Sites alvo: FBref, RSSSF, Soccerway, Wikipedia, Transfermarkt, Globo Esporte")
        print("🕷️ Estratégias: requests → requests-html → selenium")
        print("⏱️ Tempo estimado: 5-10 minutos")

        start_time = time.time()
        all_site_results = []

        for site_key, site_info in self.target_sites.items():
            try:
                site_results = await self.test_site_urls(site_key, site_info)
                all_site_results.append(site_results)

                # Resumo do site
                print(f"\n📊 RESUMO {site_key.upper()}:")
                print(f"   ✅ Sucessos: {site_results['successful_urls']}/{site_results['total_urls']}")
                print(f"   📊 Total de tabelas: {site_results['total_tables']}")
                print(f"   💾 Total de arquivos: {site_results['total_files']}")

            except Exception as e:
                print(f"❌ ERRO NO SITE {site_key}: {e}")
                continue

        # Relatório final
        self.print_final_report(all_site_results, start_time)
        return all_site_results

    def print_final_report(self, all_results: list, start_time: float):
        """
        Imprimir relatório final da coleta
        """
        end_time = time.time()
        duration = end_time - start_time

        self.print_header("RELATÓRIO FINAL DA COLETA MASSIVA")

        # Estatísticas gerais
        total_urls = sum(r['total_urls'] for r in all_results)
        total_successful = sum(r['successful_urls'] for r in all_results)
        total_tables = sum(r['total_tables'] for r in all_results)
        total_files = sum(r['total_files'] for r in all_results)

        print(f"⏱️ TEMPO TOTAL: {duration/60:.1f} minutos")
        print(f"📊 ESTATÍSTICAS GERAIS:")
        print(f"   🌐 URLs testadas: {total_urls}")
        print(f"   ✅ URLs com sucesso: {total_successful}")
        print(f"   📈 Taxa de sucesso: {(total_successful/total_urls*100):.1f}%")
        print(f"   📊 Total de tabelas extraídas: {total_tables}")
        print(f"   💾 Total de arquivos salvos: {total_files}")

        print(f"\n📋 DETALHES POR SITE:")
        for result in all_results:
            if result['total_files'] > 0:
                print(f"   🎯 {result['name']}: {result['successful_urls']}/{result['total_urls']} URLs | {result['total_tables']} tabelas | {result['total_files']} arquivos")

        # Listar arquivos salvos
        csv_files = [f for f in os.listdir('scraped_tables/') if f.endswith('.csv')]
        print(f"\n📁 ARQUIVOS COLETADOS ({len(csv_files)} total):")

        # Agrupar por site
        sites_found = {}
        for file in csv_files:
            site = file.split('_')[0]
            if site not in sites_found:
                sites_found[site] = []
            sites_found[site].append(file)

        for site, files in sites_found.items():
            print(f"   📂 {site}: {len(files)} arquivos")
            for file in files[:3]:  # Mostrar primeiros 3
                print(f"      📄 {file}")
            if len(files) > 3:
                print(f"      📄 ... e mais {len(files)-3} arquivos")

        print(f"\n🎉 COLETA CONCLUÍDA!")
        print(f"📁 Todos os dados salvos em: ./scraped_tables/")

async def main():
    """Função principal"""
    collector = MassiveDataCollector()
    results = await collector.collect_all_data()

    # Sugestão do próximo passo
    print(f"\n🚀 PRÓXIMO PASSO:")
    print(f"Execute: python3 train_ml_models.py")

if __name__ == "__main__":
    asyncio.run(main())