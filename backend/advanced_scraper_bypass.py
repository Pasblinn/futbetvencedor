#!/usr/bin/env python3
"""
💪 ADVANCED SCRAPER BYPASS - Anti-Bot Circumvention
Implementa as melhores técnicas para contornar bloqueios 403
"""

import requests
import time
import random
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from io import StringIO
import fake_useragent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedScraper:
    def __init__(self):
        self.session = requests.Session()
        self.setup_session()

    def setup_session(self):
        """Configura sessão com máxima compatibilidade"""

        # User-Agents rotativos mais realistas
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
        ]

        # Headers mais realistas
        self.base_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }

        # Retry strategy
        retry_strategy = Retry(
            total=5,
            backoff_factor=2,
            status_forcelist=[403, 429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Timeout configurations
        self.session.timeout = 30

    def get_random_headers(self, referer=None):
        """Gera headers aleatórios realistas"""
        headers = self.base_headers.copy()
        headers['User-Agent'] = random.choice(self.user_agents)

        if referer:
            headers['Referer'] = referer

        # Adiciona variações aleatórias
        if random.random() > 0.5:
            headers['Cache-Control'] = 'no-cache'

        if random.random() > 0.7:
            headers['Pragma'] = 'no-cache'

        return headers

    def scrape_with_requests(self, url, max_attempts=3):
        """Scraping avançado com requests"""
        logger.info(f"🔥 Tentando {url} com requests avançado...")

        for attempt in range(max_attempts):
            try:
                # Delay aleatório
                time.sleep(random.uniform(2, 5))

                headers = self.get_random_headers()

                # Primeira requisição para pegar cookies
                logger.info(f"📡 Tentativa {attempt + 1}: Fazendo requisição inicial...")
                response = self.session.get(url, headers=headers)

                logger.info(f"📊 Status: {response.status_code}, Size: {len(response.content)}")

                if response.status_code == 403:
                    logger.warning("🚫 Status 403, tentando com headers diferentes...")

                    # Tenta com headers de browser real
                    headers.update({
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Referer': 'https://www.google.com/',
                        'Origin': 'https://www.google.com'
                    })

                    time.sleep(random.uniform(3, 7))
                    response = self.session.get(url, headers=headers)
                    logger.info(f"📊 Retry Status: {response.status_code}")

                if response.status_code == 200:
                    logger.info("✅ Sucesso com requests!")
                    return self.extract_tables(response.text, 'requests')

            except Exception as e:
                logger.error(f"❌ Erro na tentativa {attempt + 1}: {e}")
                if attempt < max_attempts - 1:
                    time.sleep(random.uniform(5, 10))

        return {'status': 'FAILED', 'method': 'requests'}

    def scrape_with_undetected_chrome(self, url):
        """Scraping com undetected-chromedriver (mais eficaz)"""
        logger.info(f"🤖 Tentando {url} com undetected Chrome...")

        try:
            options = uc.ChromeOptions()

            # Configurações anti-detecção
            options.add_argument('--no-first-run --no-service-autorun --password-store=basic')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-extensions')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-infobars')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-browser-side-navigation')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-features=VizDisplayCompositor')
            options.add_argument('--window-size=1920,1080')

            # Headless mode (opcional)
            options.add_argument('--headless=new')

            driver = uc.Chrome(options=options, version_main=None)

            try:
                logger.info("📡 Navegando para a URL...")
                driver.get(url)

                # Espera página carregar
                time.sleep(random.uniform(5, 8))

                # Scroll para simular comportamento humano
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
                time.sleep(2)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                time.sleep(2)

                html_content = driver.page_source

                if len(html_content) < 1000:
                    logger.warning("⚠️ Conteúdo muito pequeno recebido")
                    return {'status': 'SMALL_CONTENT', 'method': 'undetected_chrome'}

                logger.info(f"📊 Conteúdo obtido: {len(html_content)} chars")

                return self.extract_tables(html_content, 'undetected_chrome')

            finally:
                driver.quit()

        except Exception as e:
            logger.error(f"💥 Erro com undetected Chrome: {e}")
            return {'status': 'ERROR', 'method': 'undetected_chrome', 'error': str(e)}

    def extract_tables(self, html_content, method):
        """Extrai tabelas do HTML"""
        try:
            # Remove scripts que podem interferir
            import re
            clean_html = re.sub(r'<script.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)

            # Tenta extrair tabelas
            tables = pd.read_html(StringIO(clean_html), attrs={'class': None})

            if tables:
                logger.info(f"✅ {method.upper()} SUCCESS: {len(tables)} tabelas encontradas!")

                # Mostra info da maior tabela
                largest = max(tables, key=len)
                logger.info(f"📋 Maior tabela: {largest.shape}")

                if len(largest.columns) > 0:
                    logger.info(f"📋 Colunas: {list(largest.columns)[:5]}...")

                # Salva sample
                sample_data = []
                for i, table in enumerate(tables[:3]):  # Primeiras 3 tabelas
                    if len(table) > 2:  # Só tabelas com dados
                        sample_data.append({
                            'table_index': i,
                            'shape': table.shape,
                            'columns': list(table.columns),
                            'sample_rows': table.head(2).to_dict('records')
                        })

                return {
                    'status': 'SUCCESS',
                    'method': method,
                    'tables_count': len(tables),
                    'largest_table_shape': largest.shape,
                    'sample_data': sample_data,
                    'content_size': len(html_content)
                }
            else:
                # Procura por indicadores de conteúdo
                indicators = ['table', 'fixture', 'match', 'team', 'league', 'position', 'pts', 'goal']
                found_indicators = [ind for ind in indicators if ind.lower() in html_content.lower()]

                if found_indicators:
                    logger.info(f"📋 Encontrou indicadores de futebol: {found_indicators}")
                    return {
                        'status': 'CONTENT_FOUND',
                        'method': method,
                        'indicators': found_indicators,
                        'content_size': len(html_content)
                    }
                else:
                    return {
                        'status': 'NO_TABLES',
                        'method': method,
                        'content_size': len(html_content)
                    }

        except Exception as e:
            logger.error(f"❌ Erro ao extrair tabelas: {e}")

            # Mesmo assim tenta buscar conteúdo relevante
            if any(term in html_content.lower() for term in ['football', 'soccer', 'league', 'team']):
                return {
                    'status': 'CONTENT_PARTIAL',
                    'method': method,
                    'error': str(e),
                    'content_size': len(html_content)
                }

            return {
                'status': 'EXTRACTION_ERROR',
                'method': method,
                'error': str(e)
            }

def test_blocked_sites():
    """Testa sites que estavam bloqueados"""

    scraper = AdvancedScraper()

    test_sites = [
        {
            'name': 'SofaScore Brasil',
            'url': 'https://www.sofascore.com/tournament/football/brazil/serie-a/325',
        },
        {
            'name': 'FBref Brasileirão',
            'url': 'https://fbref.com/en/comps/24/Serie-A-Stats',
        },
        {
            'name': 'Oddspedia Football',
            'url': 'https://oddspedia.com/football/brazil/serie-a',
        },
        {
            'name': 'FlashScore Brasil',
            'url': 'https://www.flashscore.com.br/futebol/brasil/serie-a/',
        }
    ]

    logger.info("🚀 TESTE AVANÇADO DE SITES BLOQUEADOS")
    logger.info("="*60)

    results = {}

    for site in test_sites:
        logger.info(f"\n🎯 Testando {site['name']}...")
        logger.info("-" * 40)

        # Método 1: Requests avançado
        result_requests = scraper.scrape_with_requests(site['url'])

        # Método 2: Undetected Chrome (só se requests falhar)
        if result_requests['status'] != 'SUCCESS':
            logger.info("🔄 Requests falhou, tentando undetected Chrome...")
            result_chrome = scraper.scrape_with_undetected_chrome(site['url'])
        else:
            result_chrome = {'status': 'SKIPPED', 'method': 'undetected_chrome'}

        results[site['name']] = {
            'requests': result_requests,
            'undetected_chrome': result_chrome,
            'url': site['url']
        }

        # Delay entre sites
        time.sleep(random.uniform(10, 15))

    # Resumo
    logger.info("\n" + "="*60)
    logger.info("📊 RESULTADOS FINAIS")
    logger.info("="*60)

    success_count = 0
    total_tests = 0

    for site_name, results_site in results.items():
        total_tests += 2  # requests + chrome

        req_status = results_site['requests']['status']
        chrome_status = results_site['undetected_chrome']['status']

        # Verifica sucessos
        req_success = req_status in ['SUCCESS', 'CONTENT_FOUND', 'CONTENT_PARTIAL']
        chrome_success = chrome_status in ['SUCCESS', 'CONTENT_FOUND', 'CONTENT_PARTIAL', 'SKIPPED']

        if req_success:
            success_count += 1
        if chrome_success and chrome_status != 'SKIPPED':
            success_count += 1

        # Status visual
        req_emoji = "✅" if req_success else "❌"
        chrome_emoji = "✅" if chrome_success else "❌" if chrome_status != 'SKIPPED' else "⏭️"

        logger.info(f"\n🏟️ {site_name}:")
        logger.info(f"   {req_emoji} Requests: {req_status}")
        logger.info(f"   {chrome_emoji} Chrome: {chrome_status}")

        # Mostra dados se sucesso
        for method, result in [('requests', results_site['requests']), ('chrome', results_site['undetected_chrome'])]:
            if result['status'] == 'SUCCESS':
                logger.info(f"      📊 {method}: {result.get('tables_count', 0)} tabelas, {result.get('content_size', 0):,} chars")

    success_rate = success_count / total_tests * 100 if total_tests > 0 else 0
    logger.info(f"\n🎯 Taxa de Sucesso Total: {success_count}/{total_tests} ({success_rate:.1f}%)")

    if success_count > 0:
        logger.info("✅ SUCESSO! Alguns métodos funcionaram!")
    else:
        logger.info("❌ Todos os métodos falharam. Pode ser necessário:")
        logger.info("   • Proxies residenciais premium")
        logger.info("   • Serviços de resolução de CAPTCHA")
        logger.info("   • Rotação de IP mais frequente")

if __name__ == '__main__':
    # Instala dependências necessárias
    try:
        import undetected_chromedriver
        import fake_useragent
    except ImportError:
        logger.error("📦 Instale as dependências: pip install undetected-chromedriver fake-useragent")
        exit(1)

    test_blocked_sites()