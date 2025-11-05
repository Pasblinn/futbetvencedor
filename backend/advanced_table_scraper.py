"""
🕷️ ADVANCED TABLE SCRAPER - Scraper robusto para contornar bloqueios
Implementa múltiplas estratégias para extrair tabelas de sites de futebol
Contorna 403, 401, 404, 500 com fallbacks inteligentes
"""

import requests
import pandas as pd
import time
import random
import os
import re
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse
import warnings
warnings.filterwarnings('ignore')

# Tentar importar bibliotecas opcionais
try:
    from requests_html import HTMLSession
    HAS_REQUESTS_HTML = True
except ImportError:
    HAS_REQUESTS_HTML = False
    print("⚠️ requests-html não instalado. Use: pip install requests-html")

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service
    HAS_SELENIUM = True
except ImportError:
    HAS_SELENIUM = False
    print("⚠️ selenium não instalado. Use: pip install selenium webdriver-manager")

class AdvancedTableScraper:
    """
    🕷️ Scraper avançado com múltiplas estratégias anti-bloqueio
    """

    def __init__(self, use_proxies: bool = False):
        """
        Inicializar scraper com configurações

        Args:
            use_proxies: Se deve usar proxies (implementação futura)
        """
        self.use_proxies = use_proxies
        self.session = requests.Session()

        # Lista de User-Agents populares para rotação
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:90.0) Gecko/20100101 Firefox/90.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:90.0) Gecko/20100101 Firefox/90.0'
        ]

        # Headers padrão que simulam navegador real
        self.base_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8,en-US;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Chromium";v="91", " Not;A Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1'
        }

        # Configurar diretório de saída
        self.output_dir = "scraped_tables"
        os.makedirs(self.output_dir, exist_ok=True)

    def get_random_headers(self, referer: Optional[str] = None) -> Dict[str, str]:
        """
        Gerar headers aleatórios para simular navegador real

        Args:
            referer: URL de referência opcional

        Returns:
            Dicionário com headers
        """
        headers = self.base_headers.copy()
        headers['User-Agent'] = random.choice(self.user_agents)

        if referer:
            headers['Referer'] = referer

        return headers

    def fetch_with_requests(self, url: str, retries: int = 3) -> Optional[str]:
        """
        Estratégia 1: Requests simples com headers e retry

        Args:
            url: URL alvo
            retries: Número de tentativas

        Returns:
            HTML da página ou None se falhar
        """
        print(f"🌐 Tentativa 1: requests simples para {url}")

        for attempt in range(retries):
            try:
                headers = self.get_random_headers()

                # Delay aleatório entre tentativas
                if attempt > 0:
                    delay = random.uniform(2, 5)
                    print(f"⏳ Aguardando {delay:.1f}s antes da tentativa {attempt + 1}")
                    time.sleep(delay)

                response = self.session.get(
                    url,
                    headers=headers,
                    timeout=30,
                    allow_redirects=True
                )

                print(f"📡 Status Code: {response.status_code}")

                if response.status_code == 200:
                    print("✅ Sucesso com requests simples!")
                    return response.text

                elif response.status_code in [403, 401]:
                    print(f"🚫 Bloqueado ({response.status_code}), tentando novamente...")
                    continue

                elif response.status_code in [404]:
                    print("❌ Página não encontrada (404)")
                    return None

                elif response.status_code in [500, 502, 503]:
                    print(f"🔥 Erro do servidor ({response.status_code}), tentando novamente...")
                    continue

                else:
                    print(f"⚠️ Status inesperado: {response.status_code}")
                    continue

            except requests.exceptions.RequestException as e:
                print(f"❌ Erro na requisição: {e}")
                continue

        print("❌ Falha em todas as tentativas com requests")
        return None

    def fetch_with_requests_html(self, url: str) -> Optional[str]:
        """
        Estratégia 2: requests-html com renderização JavaScript

        Args:
            url: URL alvo

        Returns:
            HTML renderizado ou None se falhar
        """
        if not HAS_REQUESTS_HTML:
            print("⚠️ requests-html não disponível, pulando...")
            return None

        print(f"🚀 Tentativa 2: requests-html com JS para {url}")

        try:
            session = HTMLSession()

            headers = self.get_random_headers()
            for key, value in headers.items():
                session.headers[key] = value

            r = session.get(url, timeout=30)
            print(f"📡 Status Code: {r.status_code}")

            if r.status_code == 200:
                # Renderizar JavaScript
                print("🔄 Renderizando JavaScript...")
                r.html.render(timeout=20, wait=2)
                print("✅ Sucesso com requests-html!")
                return r.html.html

        except Exception as e:
            print(f"❌ Erro com requests-html: {e}")

        return None

    def fetch_with_selenium(self, url: str) -> Optional[str]:
        """
        Estratégia 3: Selenium com Chrome headless (último recurso)

        Args:
            url: URL alvo

        Returns:
            HTML da página ou None se falhar
        """
        if not HAS_SELENIUM:
            print("⚠️ selenium não disponível, pulando...")
            return None

        print(f"🤖 Tentativa 3: Selenium headless para {url}")

        driver = None
        try:
            # Configurar Chrome headless
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument(f'--user-agent={random.choice(self.user_agents)}')

            # Usar webdriver-manager para gerenciar ChromeDriver automaticamente
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.get(url)

            # Aguardar carregamento
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Aguardar possíveis tabelas carregarem
            time.sleep(3)

            html = driver.page_source
            print("✅ Sucesso com Selenium!")
            return html

        except Exception as e:
            print(f"❌ Erro com Selenium: {e}")
            return None

        finally:
            if driver:
                driver.quit()

    def extract_tables_from_html(self, html: str, url: str) -> List[Tuple[pd.DataFrame, str]]:
        """
        Extrair todas as tabelas do HTML usando pandas

        Args:
            html: HTML da página
            url: URL original (para contexto)

        Returns:
            Lista de tuplas (DataFrame, nome_da_tabela)
        """
        print("📊 Extraindo tabelas com pandas...")

        tables_found = []

        try:
            # Tentar extrair tabelas com pandas
            tables = pd.read_html(html, header=0)
            print(f"🎯 Encontradas {len(tables)} tabelas")

            for i, table in enumerate(tables):
                # Gerar nome da tabela
                table_name = f"table_{i+1}"

                # Tentar encontrar título da tabela no HTML
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html, 'html.parser')

                    # Procurar por títulos próximos às tabelas
                    table_tags = soup.find_all('table')
                    if i < len(table_tags):
                        table_tag = table_tags[i]

                        # Buscar título em elementos anteriores
                        for sibling in table_tag.find_all_previous(['h1', 'h2', 'h3', 'h4', 'caption']):
                            if sibling.get_text().strip():
                                title = sibling.get_text().strip()
                                # Limpar título para nome de arquivo
                                title = re.sub(r'[^\w\s-]', '', title)
                                title = re.sub(r'[-\s]+', '_', title)
                                table_name = title[:50] if title else table_name
                                break

                except ImportError:
                    print("⚠️ BeautifulSoup não disponível para melhor detecção de títulos")
                except Exception as e:
                    print(f"⚠️ Erro ao extrair título da tabela: {e}")

                tables_found.append((table, table_name))

        except ValueError as e:
            print(f"❌ Nenhuma tabela encontrada: {e}")
        except Exception as e:
            print(f"❌ Erro ao extrair tabelas: {e}")

        return tables_found

    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Limpar DataFrame removendo multi-índices e espaços

        Args:
            df: DataFrame original

        Returns:
            DataFrame limpo
        """
        # Copiar DataFrame
        cleaned_df = df.copy()

        # Remover multi-índices das colunas
        if isinstance(cleaned_df.columns, pd.MultiIndex):
            # Concatenar níveis do multi-índice
            cleaned_df.columns = [
                '_'.join(str(col).strip() for col in column if str(col) != 'nan')
                for column in cleaned_df.columns
            ]

        # Limpar nomes das colunas
        cleaned_df.columns = [
            re.sub(r'\s+', '_', str(col).strip().replace(' ', '_'))
            for col in cleaned_df.columns
        ]

        # Remover colunas completamente vazias
        cleaned_df = cleaned_df.dropna(axis=1, how='all')

        # Remover linhas completamente vazias
        cleaned_df = cleaned_df.dropna(axis=0, how='all')

        return cleaned_df

    def save_tables_to_csv(self, tables: List[Tuple[pd.DataFrame, str]], url: str) -> List[str]:
        """
        Salvar tabelas em arquivos CSV

        Args:
            tables: Lista de tuplas (DataFrame, nome)
            url: URL original

        Returns:
            Lista de arquivos salvos
        """
        saved_files = []

        # Gerar prefixo baseado na URL
        domain = urlparse(url).netloc.replace('www.', '').replace('.', '_')
        timestamp = int(time.time())

        for i, (table, table_name) in enumerate(tables):
            try:
                # Limpar DataFrame
                cleaned_table = self.clean_dataframe(table)

                if cleaned_table.empty:
                    print(f"⚠️ Tabela {i+1} está vazia após limpeza, pulando...")
                    continue

                # Gerar nome do arquivo
                filename = f"{domain}_{table_name}_{timestamp}.csv"
                filepath = os.path.join(self.output_dir, filename)

                # Salvar CSV
                cleaned_table.to_csv(filepath, index=False, encoding='utf-8')
                print(f"💾 Salvo: {filename} ({len(cleaned_table)} linhas, {len(cleaned_table.columns)} colunas)")

                saved_files.append(filepath)

            except Exception as e:
                print(f"❌ Erro salvando tabela {i+1}: {e}")
                continue

        return saved_files

    def scrape_url(self, url: str) -> Dict:
        """
        Método principal para fazer scraping de uma URL

        Args:
            url: URL alvo

        Returns:
            Dicionário com resultados do scraping
        """
        print(f"🕷️ INICIANDO SCRAPING AVANÇADO")
        print(f"🎯 URL: {url}")
        print("=" * 70)

        result = {
            'url': url,
            'success': False,
            'method_used': None,
            'tables_found': 0,
            'files_saved': [],
            'error': None
        }

        html = None

        # Estratégia 1: Requests simples
        html = self.fetch_with_requests(url)
        if html:
            result['method_used'] = 'requests'

        # Estratégia 2: requests-html se a primeira falhar
        if not html:
            html = self.fetch_with_requests_html(url)
            if html:
                result['method_used'] = 'requests_html'

        # Estratégia 3: Selenium se as outras falharem
        if not html:
            html = self.fetch_with_selenium(url)
            if html:
                result['method_used'] = 'selenium'

        # Se conseguimos HTML, extrair tabelas
        if html:
            try:
                tables = self.extract_tables_from_html(html, url)
                result['tables_found'] = len(tables)

                if tables:
                    saved_files = self.save_tables_to_csv(tables, url)
                    result['files_saved'] = saved_files
                    result['success'] = True

                    print(f"\n🎉 SUCESSO!")
                    print(f"📊 Tabelas encontradas: {len(tables)}")
                    print(f"💾 Arquivos salvos: {len(saved_files)}")
                    for file in saved_files:
                        print(f"  📁 {os.path.basename(file)}")

                else:
                    result['error'] = "Nenhuma tabela encontrada na página"
                    print("❌ Nenhuma tabela encontrada na página")

            except Exception as e:
                result['error'] = f"Erro ao processar HTML: {e}"
                print(f"❌ Erro ao processar HTML: {e}")

        else:
            result['error'] = "Falha em todas as estratégias de scraping"
            print("❌ FALHA: Todas as estratégias falharam")

        return result

def main():
    """
    Função principal interativa
    """
    print("🕷️ ADVANCED TABLE SCRAPER")
    print("=" * 50)
    print("Scraper robusto que contorna bloqueios 403, 401, 404, 500")
    print("Estratégias: requests → requests-html → selenium")
    print("=" * 50)

    # Solicitar URL do usuário
    url = input("\n🌐 Digite a URL para fazer scraping: ").strip()

    if not url:
        print("❌ URL não fornecida!")
        return

    # Adicionar http:// se necessário
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    # Perguntar sobre proxies (futura implementação)
    use_proxies = input("\n🔄 Usar proxies? (y/n) [n]: ").strip().lower() == 'y'

    # Inicializar scraper
    scraper = AdvancedTableScraper(use_proxies=use_proxies)

    # Executar scraping
    print(f"\n🚀 Iniciando scraping...")
    result = scraper.scrape_url(url)

    # Mostrar resultado final
    print("\n" + "=" * 70)
    print("📋 RESULTADO FINAL:")
    print(f"✅ Sucesso: {result['success']}")
    print(f"🛠️ Método usado: {result['method_used']}")
    print(f"📊 Tabelas encontradas: {result['tables_found']}")
    print(f"💾 Arquivos salvos: {len(result['files_saved'])}")

    if result['error']:
        print(f"❌ Erro: {result['error']}")

    print(f"📁 Arquivos salvos em: {scraper.output_dir}/")

if __name__ == "__main__":
    main()