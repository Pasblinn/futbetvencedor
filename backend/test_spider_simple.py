#!/usr/bin/env python3
"""
🧪 Test Spider - Direct Testing of Individual Sites
"""

import requests
import pandas as pd
import logging
import time
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_site_access(url, site_name):
    """Test if we can access a site and extract tables"""
    logger.info(f"🔍 Testing {site_name}: {url}")

    try:
        # Basic headers to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

        start_time = time.time()
        response = requests.get(url, headers=headers, timeout=30)
        response_time = time.time() - start_time

        logger.info(f"📊 {site_name} Status: {response.status_code}, Time: {response_time:.2f}s")

        if response.status_code == 200:
            # Try to extract tables using pandas
            try:
                from io import StringIO
                tables = pd.read_html(StringIO(response.text))
                logger.info(f"✅ {site_name} SUCCESS: Found {len(tables)} tables")

                # Show sample of largest table
                if tables:
                    largest_table = max(tables, key=len)
                    logger.info(f"📋 Largest table shape: {largest_table.shape}")
                    logger.info(f"📋 Columns: {list(largest_table.columns)[:5]}...")

                return {
                    'status': 'SUCCESS',
                    'tables_found': len(tables),
                    'response_time': response_time,
                    'status_code': response.status_code,
                    'content_size': len(response.text),
                    'sample_table_shape': largest_table.shape if tables else None
                }

            except Exception as table_error:
                logger.warning(f"⚠️ {site_name} No tables found: {table_error}")
                return {
                    'status': 'NO_TABLES',
                    'error': str(table_error),
                    'response_time': response_time,
                    'status_code': response.status_code,
                    'content_size': len(response.text)
                }
        else:
            logger.error(f"❌ {site_name} HTTP Error: {response.status_code}")
            return {
                'status': 'HTTP_ERROR',
                'status_code': response.status_code,
                'response_time': response_time,
                'error': f"HTTP {response.status_code}"
            }

    except requests.exceptions.Timeout:
        logger.error(f"⏰ {site_name} TIMEOUT (>30s)")
        return {'status': 'TIMEOUT', 'error': 'Request timeout'}

    except requests.exceptions.ConnectionError as e:
        logger.error(f"🔌 {site_name} CONNECTION ERROR: {e}")
        return {'status': 'CONNECTION_ERROR', 'error': str(e)}

    except Exception as e:
        logger.error(f"💥 {site_name} UNEXPECTED ERROR: {e}")
        return {'status': 'ERROR', 'error': str(e)}

def main():
    """Test major football sites"""
    test_sites = [
        {
            'name': 'FBref Brasileirão',
            'url': 'https://fbref.com/en/comps/24/Serie-A-Stats',
            'expected_strategy': 'requests_pandas'
        },
        {
            'name': 'FBref Premier League',
            'url': 'https://fbref.com/en/comps/9/Premier-League-Stats',
            'expected_strategy': 'requests_pandas'
        },
        {
            'name': 'Wikipedia Brasileirão',
            'url': 'https://en.wikipedia.org/wiki/2024_Campeonato_Brasileiro_S%C3%A9rie_A',
            'expected_strategy': 'requests_pandas'
        },
        {
            'name': 'Oddspedia Football',
            'url': 'https://oddspedia.com/football',
            'expected_strategy': 'selenium'
        },
        {
            'name': 'Soccerway Brazil',
            'url': 'https://www.soccerway.com/national/brazil/serie-a/2024/regular-season/r78238/',
            'expected_strategy': 'requests_html'
        }
    ]

    logger.info("🚀 Starting football sites accessibility test...")
    logger.info(f"⏰ Test started at: {datetime.now().isoformat()}")

    results = {}

    for site in test_sites:
        logger.info(f"\n{'='*60}")
        result = test_site_access(site['url'], site['name'])
        result['expected_strategy'] = site['expected_strategy']
        results[site['name']] = result

        # Wait between requests to be respectful
        time.sleep(3)

    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("📊 SUMMARY RESULTS:")
    logger.info(f"{'='*60}")

    success_count = 0
    for site_name, result in results.items():
        status_emoji = "✅" if result['status'] == 'SUCCESS' else "⚠️" if result['status'] == 'NO_TABLES' else "❌"
        logger.info(f"{status_emoji} {site_name:<25} {result['status']:<15} ({result.get('tables_found', 0)} tables)")
        if result['status'] == 'SUCCESS':
            success_count += 1

    logger.info(f"\n🎯 Success Rate: {success_count}/{len(test_sites)} sites ({success_count/len(test_sites)*100:.1f}%)")

    # Recommendations
    logger.info(f"\n💡 RECOMMENDATIONS:")
    failed_sites = [name for name, result in results.items() if result['status'] != 'SUCCESS']
    if failed_sites:
        logger.info("🔧 Sites requiring special handling:")
        for site in failed_sites:
            result = results[site]
            logger.info(f"   • {site}: {result['status']} - Try {result['expected_strategy']} strategy")
    else:
        logger.info("🎉 All sites accessible with basic requests!")

if __name__ == '__main__':
    main()