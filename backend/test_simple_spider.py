#!/usr/bin/env python3
"""
🧪 Simple Spider Test
Test basic functionality without complex async operations
"""

import scrapy
from scrapy.crawler import CrawlerProcess
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class SimpleFootballSpider(scrapy.Spider):
    name = 'simple_test'
    allowed_domains = ['en.wikipedia.org']
    start_urls = ['https://en.wikipedia.org/wiki/2024_Campeonato_Brasileiro_Série_A']

    def parse(self, response):
        logger.info(f"Parsing {response.url}")

        # Extract tables using pandas
        try:
            tables = pd.read_html(response.text)
            logger.info(f"Found {len(tables)} tables via pandas")

            for i, table in enumerate(tables):
                if not table.empty and len(table) > 3:  # Skip tiny tables
                    yield {
                        'source_url': response.url,
                        'table_index': i,
                        'table_shape': table.shape,
                        'table_columns': list(table.columns),
                        'sample_data': table.head(3).to_dict('records'),
                        'strategy': 'pandas'
                    }

        except Exception as e:
            logger.error(f"Failed to extract tables: {e}")

        # Also try CSS selectors
        tables_css = response.css('table')
        logger.info(f"Found {len(tables_css)} tables via CSS")

        for i, table in enumerate(tables_css[:3]):  # Limit to first 3
            yield {
                'source_url': response.url,
                'table_index': f'css_{i}',
                'table_text': table.get()[:500] + '...',  # First 500 chars
                'strategy': 'css_selector'
            }


if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Run spider
    process = CrawlerProcess({
        'FEED_FORMAT': 'jsonlines',
        'FEED_URI': 'simple_test_output.jsonl',
        'LOG_LEVEL': 'INFO'
    })

    process.crawl(SimpleFootballSpider)
    process.start()