"""
🕷️ FOOTBALL SPIDER - Multi-Strategy Football Data Scraper
Supports URL-based scraping and competition/season parameters.
Auto-fallback: Scrapy → requests → requests_html → Selenium
"""

import scrapy
import pandas as pd
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Optional, Any
import logging
import time
from datetime import datetime

from ..fetcher import multi_fetcher as fetcher
from ..proxy_manager import proxy_manager
from ..ua_manager import ua_manager


logger = logging.getLogger(__name__)


class FootballSpider(scrapy.Spider):
    name = 'football_spider'
    allowed_domains = []

    # Site-specific configurations
    SITE_CONFIGS = {
        'oddspedia.com': {
            'strategy': ['selenium', 'requests_html'],
            'wait_time': 5,
            'use_proxy': True,
            'table_selectors': ['.odds-table', '.match-table', '.fixture-table'],
            'data_selectors': ['.match-row', '.fixture-row', '.odds-row'],
            'delay': 3
        },
        'fbref.com': {
            'strategy': ['requests_pandas', 'scrapy'],
            'delay': 3,
            'headers_extra': {'Referer': 'https://google.com'},
            'table_selectors': ['table.stats_table', '.sortable', 'table[id*="stats"]'],
            'data_selectors': ['tbody tr', '.stats_row'],
            'wait_time': 2
        },
        'soccerway.com': {
            'strategy': ['requests_html', 'selenium', 'scrapy'],
            'wait_time': 4,
            'use_proxy': True,
            'table_selectors': ['.table-container table', '.matches table', '.standings table'],
            'data_selectors': ['.match', '.team-row', '.fixture'],
            'delay': 4
        },
        'rsssf.com': {
            'strategy': ['requests_pandas', 'scrapy'],
            'delay': 2,
            'table_selectors': ['table', 'pre'],
            'data_selectors': ['tr', 'p'],
            'wait_time': 1
        },
        'github.com': {
            'strategy': ['scrapy', 'requests'],
            'delay': 1,
            'headers_extra': {'Accept': 'application/vnd.github.v3+json'},
            'api_endpoints': ['/repos/{owner}/{repo}/contents/', '/search/repositories'],
            'wait_time': 1
        }
    }

    # Competition mappings
    COMPETITION_URLS = {
        'brasileirao': {
            '2024': 'https://fbref.com/en/comps/24/Serie-A-Stats',
            '2025': 'https://fbref.com/en/comps/24/Serie-A-Stats'
        },
        'premier_league': {
            '2024': 'https://fbref.com/en/comps/9/Premier-League-Stats'
        },
        'la_liga': {
            '2024': 'https://fbref.com/en/comps/12/La-Liga-Stats'
        }
    }

    def __init__(self, url=None, competition=None, season=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.start_urls = []
        self.current_competition = competition
        self.current_season = season

        # Parse arguments
        if url:
            # Single or multiple URLs
            if isinstance(url, str):
                if ',' in url:
                    self.start_urls = [u.strip() for u in url.split(',')]
                else:
                    self.start_urls = [url]
            elif isinstance(url, list):
                self.start_urls = url

        elif competition and season:
            # Competition/season based URLs
            if competition.lower() in self.COMPETITION_URLS:
                comp_data = self.COMPETITION_URLS[competition.lower()]
                if season in comp_data:
                    self.start_urls = [comp_data[season]]
                else:
                    logger.error(f"Season {season} not available for {competition}")
                    raise ValueError(f"Season {season} not available for {competition}")
            else:
                logger.error(f"Competition {competition} not supported")
                raise ValueError(f"Competition {competition} not supported")

        else:
            # Default URLs for testing
            self.start_urls = [
                'https://fbref.com/en/comps/24/Serie-A-Stats',
                'https://en.wikipedia.org/wiki/2024_Campeonato_Brasileiro_Série_A'
            ]

        logger.info(f"Spider initialized with URLs: {self.start_urls}")

        # Set allowed domains from URLs
        for url in self.start_urls:
            domain = urlparse(url).netloc
            if domain and domain not in self.allowed_domains:
                self.allowed_domains.append(domain)

    def start_requests(self):
        """Generate initial requests with site-specific configurations"""
        for url in self.start_urls:
            domain = urlparse(url).netloc
            config = self._get_site_config(domain)

            # Apply site-specific settings
            headers = {
                'User-Agent': ua_manager.get_random_user_agent().get('User-Agent', 'Mozilla/5.0'),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Cache-Control': 'no-cache',
            }

            # Add site-specific headers
            if 'headers_extra' in config:
                headers.update(config['headers_extra'])

            # Set delay
            if hasattr(self, 'download_delay'):
                self.download_delay = config.get('delay', 2)

            meta = {
                'site_config': config,
                'domain': domain,
                'start_time': time.time(),
                'proxy': proxy_manager.get_proxy_sync() if config.get('use_proxy') else None,
                'user_agent': headers['User-Agent']
            }

            yield scrapy.Request(
                url=url,
                headers=headers,
                meta=meta,
                callback=self.parse,
                errback=self.errback_httpbin,
                dont_filter=True
            )

    def parse(self, response):
        """Main parsing method with multi-strategy fallback"""
        domain = response.meta.get('domain')
        config = response.meta.get('site_config', {})
        start_time = response.meta.get('start_time', time.time())

        response_time = (time.time() - start_time) * 1000  # ms

        logger.info(f"Parsing {response.url} (Status: {response.status}, Time: {response_time:.2f}ms)")

        # Extract data using multiple strategies
        tables_data = []

        # Strategy 1: Try direct table parsing
        tables = self._extract_tables_scrapy(response, config)
        if tables:
            tables_data.extend(tables)
            logger.info(f"Found {len(tables)} tables via Scrapy")

        # Strategy 2: If no tables found, try fetcher fallback
        if not tables_data:
            logger.info(f"No tables found via Scrapy, trying fetcher fallback for {response.url}")

            fetch_result = fetcher.fetch_with_fallback(
                url=response.url,
                proxy=response.meta.get('proxy'),
                user_agent=response.meta.get('user_agent'),
                strategy_preference=config.get('strategy', ['scrapy', 'requests_pandas', 'requests_html', 'selenium']),
                wait_time=config.get('wait_time', 3)
            )

            if fetch_result.success and fetch_result.data:
                if isinstance(fetch_result.data, list) and len(fetch_result.data) > 0:
                    # Handle pandas DataFrames from fetcher
                    for i, df in enumerate(fetch_result.data):
                        if isinstance(df, pd.DataFrame) and not df.empty:
                            tables_data.append({
                                'table_name': f'table_{i}',
                                'data': df,
                                'strategy': fetch_result.strategy,
                                'metadata': fetch_result.metadata or {}
                            })

                logger.info(f"Found {len(tables_data)} tables via {fetch_result.strategy}")
            else:
                logger.warning(f"All fetching strategies failed for {response.url}: {fetch_result.error}")

        # Yield results for each table found
        for table_info in tables_data:
            yield {
                'source_url': response.url,
                'source_site': domain,
                'competition': self.current_competition,
                'season': self.current_season,
                'table_name': table_info['table_name'],
                'data': table_info['data'],
                'scraped_at': datetime.now().isoformat(),
                'proxy': response.meta.get('proxy'),
                'user_agent': response.meta.get('user_agent'),
                'strategy': table_info.get('strategy', 'scrapy'),
                'response_time_ms': response_time,
                'status_code': response.status,
                'metadata': table_info.get('metadata', {})
            }

        # Look for additional URLs to follow
        additional_urls = self._find_additional_urls(response, config)
        for url in additional_urls:
            yield response.follow(
                url,
                callback=self.parse,
                meta=response.meta,
                headers=response.request.headers
            )

    def _get_site_config(self, domain: str) -> Dict:
        """Get site-specific configuration"""
        for site_domain, config in self.SITE_CONFIGS.items():
            if site_domain in domain:
                return config

        # Default configuration
        return {
            'strategy': ['scrapy', 'requests_pandas'],
            'delay': 2,
            'wait_time': 3,
            'table_selectors': ['table'],
            'data_selectors': ['tr']
        }

    def _extract_tables_scrapy(self, response, config: Dict) -> List[Dict]:
        """Extract tables using Scrapy selectors"""
        tables_data = []
        selectors = config.get('table_selectors', ['table'])

        for i, selector in enumerate(selectors):
            tables = response.css(selector)

            for j, table in enumerate(tables):
                try:
                    # Try to convert table to pandas DataFrame
                    table_html = table.get()
                    if table_html:
                        df_list = pd.read_html(table_html)
                        if df_list:
                            for k, df in enumerate(df_list):
                                if not df.empty:
                                    tables_data.append({
                                        'table_name': f'table_{i}_{j}_{k}',
                                        'data': df,
                                        'strategy': 'scrapy',
                                        'metadata': {
                                            'selector': selector,
                                            'table_index': j,
                                            'df_index': k
                                        }
                                    })
                except Exception as e:
                    logger.warning(f"Failed to parse table with selector {selector}: {e}")
                    continue

        return tables_data

    def _find_additional_urls(self, response, config: Dict) -> List[str]:
        """Find additional URLs to scrape based on site configuration"""
        additional_urls = []
        domain = urlparse(response.url).netloc

        # Site-specific URL discovery
        if 'fbref.com' in domain:
            # Look for season/competition links
            season_links = response.css('a[href*="/comps/"]::attr(href)').getall()
            additional_urls.extend([urljoin(response.url, link) for link in season_links[:5]])  # Limit to 5

        elif 'oddspedia.com' in domain:
            # Look for match/fixture links
            match_links = response.css('a[href*="/match/"]::attr(href)').getall()
            additional_urls.extend([urljoin(response.url, link) for link in match_links[:10]])  # Limit to 10

        elif 'soccerway.com' in domain:
            # Look for tournament/team links
            team_links = response.css('a[href*="/teams/"]::attr(href)').getall()
            additional_urls.extend([urljoin(response.url, link) for link in team_links[:5]])  # Limit to 5

        return additional_urls[:20]  # Global limit

    def errback_httpbin(self, failure):
        """Handle request failures"""
        logger.error(f"Request failed: {failure.value}")

        request = failure.request
        domain = urlparse(request.url).netloc
        config = self._get_site_config(domain)

        # Try fetcher as fallback for failed requests
        if hasattr(failure, 'response') and failure.response:
            status = failure.response.status
            logger.info(f"HTTP {status} error for {request.url}, trying fetcher fallback")

            fetch_result = fetcher.fetch_with_fallback(
                url=request.url,
                proxy=request.meta.get('proxy'),
                user_agent=request.headers.get('User-Agent'),
                strategy_preference=['requests_html', 'selenium'],
                wait_time=config.get('wait_time', 5)
            )

            if fetch_result.success and fetch_result.data:
                # Convert fetcher result to spider result format
                for i, df in enumerate(fetch_result.data):
                    if isinstance(df, pd.DataFrame) and not df.empty:
                        yield {
                            'source_url': request.url,
                            'source_site': domain,
                            'competition': self.current_competition,
                            'season': self.current_season,
                            'table_name': f'fallback_table_{i}',
                            'data': df,
                            'scraped_at': datetime.now().isoformat(),
                            'proxy': request.meta.get('proxy'),
                            'user_agent': request.headers.get('User-Agent'),
                            'strategy': fetch_result.strategy,
                            'response_time_ms': fetch_result.response_time,
                            'status_code': getattr(failure.response, 'status', None),
                            'metadata': fetch_result.metadata or {'fallback': True}
                        }