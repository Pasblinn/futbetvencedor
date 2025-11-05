#!/usr/bin/env python3
"""
🚀 ULTIMATE FOOTBALL SCRAPER
Implementação final com todas as técnicas anti-detecção
"""

import cloudscraper
import requests
import time
import random
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd
from io import StringIO
import json
from fake_useragent import UserAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UltimateScraper:
    def __init__(self):
        self.ua = UserAgent()
        self.setup_cloudscraper()

    def setup_cloudscraper(self):
        """Setup CloudScraper com configurações otimizadas"""
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            },
            debug=False
        )

        # Headers mais realistas
        self.scraper.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8,es;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'sec-ch-ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        })

    def get_with_fallback(self, url, site_name):
        """Tenta múltiplas estratégias para um site"""
        logger.info(f"🎯 Atacando {site_name}: {url}")

        strategies = [
            ('cloudscraper', self.try_cloudscraper),
            ('direct_requests', self.try_direct_requests),
            ('session_requests', self.try_session_requests)
        ]

        for strategy_name, strategy_func in strategies:
            logger.info(f"🔧 Tentando estratégia: {strategy_name}")

            try:
                result = strategy_func(url, site_name)
                if result['status'] == 'SUCCESS':
                    logger.info(f"✅ SUCESSO com {strategy_name}!")
                    return result

                logger.warning(f"⚠️ {strategy_name} falhou: {result['status']}")

            except Exception as e:
                logger.error(f"❌ Erro em {strategy_name}: {e}")

            # Delay entre tentativas
            time.sleep(random.uniform(3, 6))

        return {'status': 'ALL_FAILED', 'site': site_name}

    def try_cloudscraper(self, url, site_name):
        """CloudScraper - melhor contra Cloudflare"""
        try:
            # Delay aleatório
            time.sleep(random.uniform(2, 5))

            response = self.scraper.get(url, timeout=30)
            logger.info(f"📊 CloudScraper - Status: {response.status_code}, Size: {len(response.content):,}")

            if response.status_code == 200:
                return self.extract_data(response.text, 'cloudscraper', site_name)
            else:
                return {'status': 'HTTP_ERROR', 'code': response.status_code}

        except Exception as e:
            return {'status': 'ERROR', 'error': str(e)}

    def try_direct_requests(self, url, site_name):
        """Requests direto com headers otimizados"""
        try:
            headers = {
                'User-Agent': self.ua.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }

            # Adiciona referer específico por site
            if 'sofascore' in url:
                headers['Referer'] = 'https://www.google.com.br/search?q=sofascore+brasil'
            elif 'fbref' in url:
                headers['Referer'] = 'https://www.google.com/search?q=fbref+serie+a'
            elif 'flashscore' in url:
                headers['Referer'] = 'https://www.google.com.br/'

            time.sleep(random.uniform(3, 7))

            response = requests.get(url, headers=headers, timeout=30)
            logger.info(f"📊 Direct - Status: {response.status_code}, Size: {len(response.content):,}")

            if response.status_code == 200:
                return self.extract_data(response.text, 'direct_requests', site_name)
            else:
                return {'status': 'HTTP_ERROR', 'code': response.status_code}

        except Exception as e:
            return {'status': 'ERROR', 'error': str(e)}

    def try_session_requests(self, url, site_name):
        """Session persistente com cookies"""
        try:
            session = requests.Session()

            # Configurar retry strategy
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[403, 429, 500, 502, 503, 504],
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("http://", adapter)
            session.mount("https://", adapter)

            # Headers de sessão
            session.headers.update({
                'User-Agent': self.ua.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            })

            # Primeiro, acessa a home para pegar cookies
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            home_url = f"https://{domain}/"

            logger.info(f"🍪 Buscando cookies em {home_url}")
            home_response = session.get(home_url, timeout=30)

            time.sleep(random.uniform(2, 4))

            # Agora acessa a URL real
            response = session.get(url, timeout=30)
            logger.info(f"📊 Session - Status: {response.status_code}, Size: {len(response.content):,}")

            if response.status_code == 200:
                return self.extract_data(response.text, 'session_requests', site_name)
            else:
                return {'status': 'HTTP_ERROR', 'code': response.status_code}

        except Exception as e:
            return {'status': 'ERROR', 'error': str(e)}

    def extract_data(self, html_content, method, site_name):
        """Extrai dados do HTML de forma inteligente"""
        try:
            # Limpeza do HTML
            import re
            clean_html = re.sub(r'<script.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            clean_html = re.sub(r'<style.*?</style>', '', clean_html, flags=re.DOTALL | re.IGNORECASE)

            # Verifica se recebeu uma página válida
            if len(html_content) < 1000:
                return {'status': 'SMALL_CONTENT', 'size': len(html_content)}

            # Procura por indicadores de bloqueio
            block_indicators = ['cloudflare', 'ddos protection', 'access denied', 'captcha', 'robot', 'blocked']
            for indicator in block_indicators:
                if indicator.lower() in html_content.lower():
                    return {'status': 'BLOCKED', 'indicator': indicator}

            # Tenta extrair tabelas
            try:
                tables = pd.read_html(StringIO(clean_html))

                if tables and len(tables) > 0:
                    logger.info(f"✅ {method} encontrou {len(tables)} tabelas!")

                    # Filtra tabelas úteis (com pelo menos 3 linhas e 2 colunas)
                    useful_tables = [t for t in tables if len(t) >= 3 and len(t.columns) >= 2]

                    if useful_tables:
                        largest = max(useful_tables, key=len)
                        logger.info(f"📊 Maior tabela útil: {largest.shape}")
                        logger.info(f"📋 Colunas: {list(largest.columns)[:5]}")

                        # Salva dados das primeiras tabelas úteis
                        sample_data = []
                        for i, table in enumerate(useful_tables[:3]):
                            sample_data.append({
                                'index': i,
                                'shape': table.shape,
                                'columns': list(table.columns),
                                'sample': table.head(2).to_dict('records') if len(table) > 0 else []
                            })

                        return {
                            'status': 'SUCCESS',
                            'method': method,
                            'site': site_name,
                            'total_tables': len(tables),
                            'useful_tables': len(useful_tables),
                            'largest_shape': largest.shape,
                            'content_size': len(html_content),
                            'sample_data': sample_data
                        }

            except Exception as table_error:
                logger.warning(f"⚠️ Erro ao extrair tabelas: {table_error}")

            # Se não conseguiu tabelas, verifica se tem conteúdo de futebol
            football_indicators = [
                'team', 'match', 'fixture', 'league', 'tournament', 'série a', 'brasileirão',
                'goal', 'score', 'result', 'position', 'table', 'standing'
            ]

            found_indicators = []
            for indicator in football_indicators:
                if indicator.lower() in html_content.lower():
                    found_indicators.append(indicator)

            if found_indicators:
                logger.info(f"📋 Encontrou conteúdo de futebol: {found_indicators[:5]}")
                return {
                    'status': 'CONTENT_FOUND',
                    'method': method,
                    'site': site_name,
                    'football_indicators': found_indicators[:10],
                    'content_size': len(html_content)
                }

            # Conteúdo genérico
            return {
                'status': 'GENERIC_CONTENT',
                'method': method,
                'site': site_name,
                'content_size': len(html_content)
            }

        except Exception as e:
            return {
                'status': 'EXTRACTION_ERROR',
                'method': method,
                'error': str(e)
            }

def test_football_sites():
    """Testa sites de futebol com scraper ultimate"""

    scraper = UltimateScraper()

    # Sites para testar - URLs mais específicas e simples
    test_sites = [
        {
            'name': 'SofaScore Brasil Serie A',
            'url': 'https://www.sofascore.com/pt/torneio/futebol/brasil/serie-a/325'
        },
        {
            'name': 'FlashScore Brasil',
            'url': 'https://www.flashscore.com.br/futebol/brasil/serie-a/'
        },
        {
            'name': 'ESPN Brasil Serie A',
            'url': 'https://www.espn.com.br/futebol/campeonato/_/liga/bra.1'
        },
        {
            'name': 'UOL Esporte Brasileirão',
            'url': 'https://www.uol.com.br/esporte/futebol/campeonatos/brasileiro/2024/tabela/'
        }
    ]

    logger.info("🚀 ULTIMATE FOOTBALL SCRAPER TEST")
    logger.info("=" * 60)

    results = {}

    for site in test_sites:
        logger.info(f"\n{'=' * 50}")
        result = scraper.get_with_fallback(site['url'], site['name'])
        results[site['name']] = result

        # Delay entre sites
        delay = random.uniform(15, 25)
        logger.info(f"⏱️ Aguardando {delay:.1f}s antes do próximo site...")
        time.sleep(delay)

    # Relatório final
    logger.info("\n" + "=" * 60)
    logger.info("📊 RELATÓRIO FINAL")
    logger.info("=" * 60)

    success_count = 0
    partial_count = 0

    for site_name, result in results.items():
        status = result['status']

        if status == 'SUCCESS':
            success_count += 1
            emoji = "✅"
            details = f"{result['useful_tables']} tabelas úteis, método: {result['method']}"
        elif status in ['CONTENT_FOUND', 'GENERIC_CONTENT']:
            partial_count += 1
            emoji = "⚠️"
            details = f"Conteúdo parcial, método: {result.get('method', 'N/A')}"
        else:
            emoji = "❌"
            details = f"Falhou: {status}"

        logger.info(f"\n{emoji} {site_name}")
        logger.info(f"   Status: {status}")
        logger.info(f"   Detalhes: {details}")

        # Mostra dados de exemplo se houver sucesso
        if status == 'SUCCESS' and 'sample_data' in result:
            for sample in result['sample_data'][:1]:  # Só o primeiro exemplo
                if sample['sample']:
                    logger.info(f"   📊 Exemplo: {sample['sample'][0]}")

    total_sites = len(results)
    logger.info(f"\n🎯 RESUMO:")
    logger.info(f"✅ Sucessos completos: {success_count}/{total_sites} ({success_count/total_sites*100:.1f}%)")
    logger.info(f"⚠️ Sucessos parciais: {partial_count}/{total_sites} ({partial_count/total_sites*100:.1f}%)")
    logger.info(f"🎯 Taxa total de acesso: {(success_count + partial_count)/total_sites*100:.1f}%")

    if success_count > 0:
        logger.info("\n🎉 EXCELENTE! Conseguimos dados estruturados!")
        logger.info("💡 Próximos passos:")
        logger.info("   1. Integrar métodos bem-sucedidos no spider principal")
        logger.info("   2. Configurar rotação automática de estratégias")
        logger.info("   3. Implementar cache inteligente")
    elif partial_count > 0:
        logger.info("\n📈 BOM PROGRESSO! Temos acesso aos sites.")
        logger.info("💡 Próximos passos:")
        logger.info("   1. Melhorar extração de dados não-tabulares")
        logger.info("   2. Implementar parsers específicos por site")
        logger.info("   3. Usar APIs quando disponíveis")
    else:
        logger.info("\n🔧 PRECISAMOS DE MELHORIAS:")
        logger.info("   1. Proxies residenciais premium")
        logger.info("   2. Serviços de resolução de CAPTCHA")
        logger.info("   3. APIs oficiais ou feeds RSS")

if __name__ == '__main__':
    test_football_sites()