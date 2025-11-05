"""
🔄 FETCHER MODULE - Multi-Strategy Data Fetching System
Implements multiple fetching strategies with automatic fallback:
1. Scrapy (primary)
2. requests + pandas.read_html
3. requests_html (JS rendering)
4. Selenium headless (fallback final)
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from pathlib import Path
import pandas as pd
import requests
from bs4 import BeautifulSoup
from requests_html import HTMLSession
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from .proxy_manager import proxy_manager
from .ua_manager import ua_manager
from .retry_backoff import retry_manager

logger = logging.getLogger(__name__)

class FetchResult:
    """Container for fetch results"""
    def __init__(
        self,
        success: bool,
        data: Any = None,
        strategy: str = None,
        response_time: float = 0.0,
        status_code: int = None,
        error: str = None,
        metadata: Dict = None
    ):
        self.success = success
        self.data = data
        self.strategy = strategy
        self.response_time = response_time
        self.status_code = status_code
        self.error = error
        self.metadata = metadata or {}
        self.timestamp = datetime.now()

class BaseFetcher:
    """Base class for all fetchers"""

    def __init__(self, name: str):
        self.name = name
        self.success_count = 0
        self.failure_count = 0
        self.total_response_time = 0.0

    async def fetch(self, url: str, **kwargs) -> FetchResult:
        """Fetch data from URL - to be implemented by subclasses"""
        raise NotImplementedError

    def get_stats(self) -> Dict:
        """Get fetcher statistics"""
        total_requests = self.success_count + self.failure_count
        return {
            'name': self.name,
            'total_requests': total_requests,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'success_rate': self.success_count / max(total_requests, 1),
            'avg_response_time': self.total_response_time / max(self.success_count, 1)
        }

class ScrapyFetcher(BaseFetcher):
    """
    🕷️ Scrapy-based fetcher (primary strategy)
    Uses Scrapy's robust downloading system
    """

    def __init__(self):
        super().__init__("scrapy")

    async def fetch(self, url: str, **kwargs) -> FetchResult:
        """Fetch using Scrapy downloader"""
        start_time = time.time()

        try:
            # This would integrate with Scrapy's downloader
            # For now, we'll use requests as a placeholder
            # In a full Scrapy integration, this would use the Scrapy engine

            headers = ua_manager.get_random_headers()
            proxy = await proxy_manager.get_proxy()

            proxies = None
            if proxy:
                proxies = {
                    'http': proxy.formatted_proxy,
                    'https': proxy.formatted_proxy
                }

            response = requests.get(
                url,
                headers=headers,
                proxies=proxies,
                timeout=30,
                allow_redirects=True
            )

            response_time = time.time() - start_time

            if response.status_code == 200:
                self.success_count += 1
                self.total_response_time += response_time

                # Parse tables if HTML
                tables = []
                if 'text/html' in response.headers.get('content-type', ''):
                    try:
                        tables = pd.read_html(response.text)
                    except ValueError:
                        pass  # No tables found

                return FetchResult(
                    success=True,
                    data={
                        'html': response.text,
                        'tables': tables,
                        'headers': dict(response.headers)
                    },
                    strategy=self.name,
                    response_time=response_time,
                    status_code=response.status_code,
                    metadata={
                        'url': url,
                        'proxy_used': proxy.url if proxy else None,
                        'user_agent': headers.get('User-Agent')
                    }
                )
            else:
                self.failure_count += 1
                return FetchResult(
                    success=False,
                    strategy=self.name,
                    response_time=response_time,
                    status_code=response.status_code,
                    error=f"HTTP {response.status_code}"
                )

        except Exception as e:
            self.failure_count += 1
            response_time = time.time() - start_time

            return FetchResult(
                success=False,
                strategy=self.name,
                response_time=response_time,
                error=str(e)
            )

class RequestsPandasFetcher(BaseFetcher):
    """
    📊 Requests + pandas.read_html fetcher
    Good for simple HTML tables
    """

    def __init__(self):
        super().__init__("requests_pandas")
        self.session = requests.Session()

    async def fetch(self, url: str, **kwargs) -> FetchResult:
        """Fetch using requests + pandas"""
        start_time = time.time()

        try:
            headers = ua_manager.get_random_headers()
            proxy = await proxy_manager.get_proxy()

            # Update session headers
            self.session.headers.update(headers)

            # Set proxy
            if proxy:
                self.session.proxies = {
                    'http': proxy.formatted_proxy,
                    'https': proxy.formatted_proxy
                }

            response = self.session.get(url, timeout=30)
            response_time = time.time() - start_time

            if response.status_code == 200:
                # Try to extract tables with pandas
                tables = []
                try:
                    tables = pd.read_html(
                        response.text,
                        match=kwargs.get('table_match'),
                        attrs=kwargs.get('table_attrs'),
                        encoding='utf-8'
                    )
                    logger.info(f"Found {len(tables)} tables in {url}")
                except ValueError:
                    logger.warning(f"No tables found in {url}")

                self.success_count += 1
                self.total_response_time += response_time

                return FetchResult(
                    success=True,
                    data={
                        'html': response.text,
                        'tables': tables,
                        'headers': dict(response.headers)
                    },
                    strategy=self.name,
                    response_time=response_time,
                    status_code=response.status_code,
                    metadata={
                        'url': url,
                        'proxy_used': proxy.url if proxy else None,
                        'tables_found': len(tables)
                    }
                )
            else:
                self.failure_count += 1
                return FetchResult(
                    success=False,
                    strategy=self.name,
                    response_time=response_time,
                    status_code=response.status_code,
                    error=f"HTTP {response.status_code}"
                )

        except Exception as e:
            self.failure_count += 1
            response_time = time.time() - start_time

            return FetchResult(
                success=False,
                strategy=self.name,
                response_time=response_time,
                error=str(e)
            )

class RequestsHtmlFetcher(BaseFetcher):
    """
    🌐 requests-html fetcher with JS rendering
    Good for JavaScript-heavy sites
    """

    def __init__(self):
        super().__init__("requests_html")
        self.session = HTMLSession()

    async def fetch(self, url: str, **kwargs) -> FetchResult:
        """Fetch using requests-html"""
        start_time = time.time()

        try:
            headers = ua_manager.get_random_headers()
            proxy = await proxy_manager.get_proxy()

            # Set proxy
            if proxy:
                self.session.proxies = {
                    'http': proxy.formatted_proxy,
                    'https': proxy.formatted_proxy
                }

            # Make request
            response = self.session.get(url, headers=headers, timeout=30)

            # Render JavaScript if needed
            if kwargs.get('render_js', True):
                response.html.render(
                    timeout=20,
                    keep_page=False,
                    scrolldown=kwargs.get('scrolldown', 1)
                )

            response_time = time.time() - start_time

            if response.status_code == 200:
                # Extract tables from rendered HTML
                tables = []
                try:
                    tables = pd.read_html(
                        response.html.html,
                        match=kwargs.get('table_match'),
                        attrs=kwargs.get('table_attrs')
                    )
                except ValueError:
                    pass

                self.success_count += 1
                self.total_response_time += response_time

                return FetchResult(
                    success=True,
                    data={
                        'html': response.html.html,
                        'text': response.html.text,
                        'tables': tables,
                        'links': list(response.html.links),
                        'headers': dict(response.headers)
                    },
                    strategy=self.name,
                    response_time=response_time,
                    status_code=response.status_code,
                    metadata={
                        'url': url,
                        'proxy_used': proxy.url if proxy else None,
                        'js_rendered': kwargs.get('render_js', True),
                        'tables_found': len(tables)
                    }
                )
            else:
                self.failure_count += 1
                return FetchResult(
                    success=False,
                    strategy=self.name,
                    response_time=response_time,
                    status_code=response.status_code,
                    error=f"HTTP {response.status_code}"
                )

        except Exception as e:
            self.failure_count += 1
            response_time = time.time() - start_time

            return FetchResult(
                success=False,
                strategy=self.name,
                response_time=response_time,
                error=str(e)
            )

class SeleniumFetcher(BaseFetcher):
    """
    🤖 Selenium headless fetcher (final fallback)
    Most robust but slowest option
    """

    def __init__(self):
        super().__init__("selenium")
        self.driver = None

    def _get_driver(self):
        """Get or create Selenium driver"""
        if self.driver is None:
            try:
                options = Options()
                options.add_argument('--headless')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-gpu')
                options.add_argument('--disable-web-security')
                options.add_argument('--allow-running-insecure-content')
                options.add_argument('--disable-extensions')
                options.add_argument('--disable-plugins')
                options.add_argument('--disable-images')
                options.add_argument('--window-size=1920,1080')

                self.driver = webdriver.Chrome(
                    ChromeDriverManager().install(),
                    options=options
                )

                # Set timeouts
                self.driver.implicitly_wait(10)
                self.driver.set_page_load_timeout(30)

            except Exception as e:
                logger.error(f"Failed to create Selenium driver: {e}")
                raise

        return self.driver

    async def fetch(self, url: str, **kwargs) -> FetchResult:
        """Fetch using Selenium"""
        start_time = time.time()

        try:
            driver = self._get_driver()

            # Set User-Agent (limited support in Selenium)
            headers = ua_manager.get_random_headers()
            user_agent = headers['User-Agent']

            driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                'userAgent': user_agent
            })

            # Navigate to page
            driver.get(url)

            # Wait for page to load
            wait_time = kwargs.get('wait_time', 3)
            time.sleep(wait_time)

            # Wait for specific elements if specified
            if 'wait_for_selector' in kwargs:
                wait = WebDriverWait(driver, 10)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, kwargs['wait_for_selector'])))

            # Scroll if needed
            if kwargs.get('scroll_down', False):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

            # Get page source
            html = driver.page_source

            response_time = time.time() - start_time

            # Extract tables
            tables = []
            try:
                tables = pd.read_html(
                    html,
                    match=kwargs.get('table_match'),
                    attrs=kwargs.get('table_attrs')
                )
            except ValueError:
                pass

            self.success_count += 1
            self.total_response_time += response_time

            return FetchResult(
                success=True,
                data={
                    'html': html,
                    'tables': tables,
                    'title': driver.title,
                    'current_url': driver.current_url
                },
                strategy=self.name,
                response_time=response_time,
                status_code=200,
                metadata={
                    'url': url,
                    'final_url': driver.current_url,
                    'user_agent': user_agent,
                    'tables_found': len(tables),
                    'wait_time': wait_time
                }
            )

        except Exception as e:
            self.failure_count += 1
            response_time = time.time() - start_time

            return FetchResult(
                success=False,
                strategy=self.name,
                response_time=response_time,
                error=str(e)
            )

    def close(self):
        """Clean up Selenium driver"""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
            except Exception as e:
                logger.error(f"Error closing Selenium driver: {e}")

class MultiFetcher:
    """
    🔄 Multi-Strategy Fetcher
    Tries different strategies with automatic fallback
    """

    def __init__(self):
        self.strategies = [
            ScrapyFetcher(),
            RequestsPandasFetcher(),
            RequestsHtmlFetcher(),
            SeleniumFetcher()
        ]
        self.strategy_stats = {}

    async def fetch(
        self,
        url: str,
        strategies: Optional[List[str]] = None,
        **kwargs
    ) -> FetchResult:
        """
        Fetch data using multiple strategies with fallback

        Args:
            url: URL to fetch
            strategies: List of strategy names to try (in order)
            **kwargs: Additional arguments for fetchers
        """
        # Filter strategies if specified
        if strategies:
            available_strategies = [s for s in self.strategies if s.name in strategies]
        else:
            available_strategies = self.strategies

        last_error = None

        for strategy in available_strategies:
            logger.info(f"Trying {strategy.name} for {url}")

            try:
                result = await strategy.fetch(url, **kwargs)

                if result.success:
                    logger.info(f"Successfully fetched {url} using {strategy.name} "
                              f"in {result.response_time:.2f}s")
                    return result
                else:
                    logger.warning(f"{strategy.name} failed for {url}: {result.error}")
                    last_error = result.error

            except Exception as e:
                logger.error(f"{strategy.name} raised exception for {url}: {e}")
                last_error = str(e)

        # All strategies failed
        return FetchResult(
            success=False,
            error=f"All strategies failed. Last error: {last_error}",
            metadata={'url': url, 'strategies_tried': [s.name for s in available_strategies]}
        )

    def get_stats(self) -> Dict:
        """Get statistics for all strategies"""
        return {
            'strategies': [strategy.get_stats() for strategy in self.strategies],
            'total_requests': sum(s.success_count + s.failure_count for s in self.strategies),
            'overall_success_rate': (
                sum(s.success_count for s in self.strategies) /
                max(sum(s.success_count + s.failure_count for s in self.strategies), 1)
            )
        }

    def fetch_with_fallback(
        self,
        url: str,
        proxy: Optional[str] = None,
        user_agent: Optional[str] = None,
        strategy_preference: Optional[List[str]] = None,
        **kwargs
    ) -> FetchResult:
        """
        Synchronous version of fetch for use in Scrapy spiders
        """
        import asyncio

        # Use existing event loop if available, otherwise create new one
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, we need to run in a thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self.fetch(url, strategies=strategy_preference, proxy=proxy, user_agent=user_agent, **kwargs)
                    )
                    return future.result()
            else:
                return loop.run_until_complete(
                    self.fetch(url, strategies=strategy_preference, proxy=proxy, user_agent=user_agent, **kwargs)
                )
        except RuntimeError:
            # No event loop, create new one
            return asyncio.run(
                self.fetch(url, strategies=strategy_preference, proxy=proxy, user_agent=user_agent, **kwargs)
            )

    def close(self):
        """Clean up all fetchers"""
        for strategy in self.strategies:
            if hasattr(strategy, 'close'):
                strategy.close()

# Global multi-fetcher instance
multi_fetcher = MultiFetcher()