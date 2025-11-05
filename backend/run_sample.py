#!/usr/bin/env python3
"""
🚀 FOOTBALL SCRAPER SAMPLE RUNNER
Demonstrates the football spider with fallback strategies against test URLs.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
import time
from datetime import datetime

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('scraper_sample.log')
    ]
)

logger = logging.getLogger(__name__)


class ScraperSampleRunner:
    """Sample runner for football scraper testing"""

    def __init__(self):
        self.base_dir = current_dir
        self.output_dir = self.base_dir / 'scraped_data'
        self.output_dir.mkdir(exist_ok=True)

        # Test URLs - mix of different sites and strategies
        self.test_urls = [
            {
                'url': 'https://en.wikipedia.org/wiki/2024_Campeonato_Brasileiro_Série_A',
                'description': 'Wikipedia - Simple table parsing',
                'expected_strategy': 'scrapy'
            },
            {
                'url': 'https://fbref.com/en/comps/24/Serie-A-Stats',
                'description': 'FBref - Advanced stats tables',
                'expected_strategy': 'requests_pandas'
            },
            {
                'url': 'https://www.soccerway.com/national/brazil/serie-a/2024/regular-season/r78238/',
                'description': 'Soccerway - JS-heavy content',
                'expected_strategy': 'requests_html'
            }
        ]

        # Competition-based tests
        self.competition_tests = [
            {
                'competition': 'brasileirao',
                'season': '2024',
                'description': 'Brasileirão 2024 via competition parameter'
            }
        ]

    def create_sample_config_files(self):
        """Create sample configuration files"""
        logger.info("Creating sample configuration files...")

        # Sample proxies.txt
        proxies_file = self.base_dir / 'proxies.txt'
        if not proxies_file.exists():
            with open(proxies_file, 'w') as f:
                f.write("""# Sample proxy configuration
# Format: protocol://[user:pass@]host:port
# Uncomment and modify with real proxies

# http://proxy1.example.com:8080
# http://user:pass@proxy2.example.com:3128
# socks5://proxy3.example.com:1080

# Free proxies (may not work reliably):
# http://103.149.162.194:80
# http://47.74.152.29:8888
""")
            logger.info(f"Created sample proxies.txt at {proxies_file}")

        # Sample user_agents.txt
        ua_file = self.base_dir / 'user_agents.txt'
        if not ua_file.exists():
            with open(ua_file, 'w') as f:
                f.write("""Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0
Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0
""")
            logger.info(f"Created sample user_agents.txt at {ua_file}")

    def run_scrapy_command(self, command_args: list, description: str) -> bool:
        """Run a scrapy command and return success status"""
        logger.info(f"Running: {description}")
        logger.info(f"Command: scrapy {' '.join(command_args)}")

        start_time = time.time()

        try:
            # Change to football_scraper directory
            os.chdir(self.base_dir / 'football_scraper')

            # Run scrapy command
            cmd = ['scrapy'] + command_args
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            end_time = time.time()
            duration = end_time - start_time

            if result.returncode == 0:
                logger.info(f"✅ SUCCESS: {description} (took {duration:.1f}s)")
                if result.stdout:
                    logger.info(f"Output: {result.stdout[-500:]}")  # Last 500 chars
                return True
            else:
                logger.error(f"❌ FAILED: {description}")
                logger.error(f"Error code: {result.returncode}")
                if result.stderr:
                    logger.error(f"Error output: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error(f"⏱️ TIMEOUT: {description} (exceeded 5 minutes)")
            return False
        except Exception as e:
            logger.error(f"💥 EXCEPTION: {description} - {e}")
            return False
        finally:
            # Change back to original directory
            os.chdir(self.base_dir)

    def test_url_based_scraping(self):
        """Test URL-based scraping"""
        logger.info("=" * 60)
        logger.info("🌐 TESTING URL-BASED SCRAPING")
        logger.info("=" * 60)

        results = []

        for test in self.test_urls:
            url = test['url']
            description = test['description']

            # Run spider with single URL
            success = self.run_scrapy_command([
                'crawl', 'football_spider',
                '-a', f'url={url}',
                '-s', 'FEED_FORMAT=jsonlines',
                '-s', f'FEED_URI=../scraped_data/{int(time.time())}_single.jsonl'
            ], f"Single URL: {description}")

            results.append({'test': description, 'success': success})
            time.sleep(2)  # Brief pause between tests

        return results

    def test_multiple_urls(self):
        """Test multiple URL scraping"""
        logger.info("=" * 60)
        logger.info("🔗 TESTING MULTIPLE URL SCRAPING")
        logger.info("=" * 60)

        # Combine first 2 test URLs
        urls = [test['url'] for test in self.test_urls[:2]]
        url_string = ','.join(urls)

        success = self.run_scrapy_command([
            'crawl', 'football_spider',
            '-a', f'url={url_string}',
            '-s', 'FEED_FORMAT=jsonlines',
            '-s', f'FEED_URI=../scraped_data/{int(time.time())}_multiple.jsonl'
        ], "Multiple URLs test")

        return [{'test': 'Multiple URLs', 'success': success}]

    def test_competition_based_scraping(self):
        """Test competition-based scraping"""
        logger.info("=" * 60)
        logger.info("🏆 TESTING COMPETITION-BASED SCRAPING")
        logger.info("=" * 60)

        results = []

        for test in self.competition_tests:
            competition = test['competition']
            season = test['season']
            description = test['description']

            success = self.run_scrapy_command([
                'crawl', 'football_spider',
                '-a', f'competition={competition}',
                '-a', f'season={season}',
                '-s', 'FEED_FORMAT=jsonlines',
                '-s', f'FEED_URI=../scraped_data/{int(time.time())}_competition.jsonl'
            ], description)

            results.append({'test': description, 'success': success})

        return results

    def test_fallback_strategies(self):
        """Test fallback strategies with a challenging URL"""
        logger.info("=" * 60)
        logger.info("🔄 TESTING FALLBACK STRATEGIES")
        logger.info("=" * 60)

        # Use a URL that will likely require fallback strategies
        challenging_url = 'https://www.oddspedia.com/football'

        success = self.run_scrapy_command([
            'crawl', 'football_spider',
            '-a', f'url={challenging_url}',
            '-s', 'FEED_FORMAT=jsonlines',
            '-s', f'FEED_URI=../scraped_data/{int(time.time())}_fallback.jsonl',
            '-s', 'DOWNLOAD_DELAY=3',
            '-s', 'CONCURRENT_REQUESTS=1'
        ], "Fallback strategies test (Oddspedia)")

        return [{'test': 'Fallback strategies', 'success': success}]

    def check_output_files(self):
        """Check generated output files"""
        logger.info("=" * 60)
        logger.info("📁 CHECKING OUTPUT FILES")
        logger.info("=" * 60)

        output_files = list(self.output_dir.glob('*.jsonl'))
        output_files.extend(list(self.output_dir.glob('*.csv')))
        output_files.extend(list(self.output_dir.glob('*.parquet')))

        if output_files:
            logger.info(f"Found {len(output_files)} output files:")
            for file in sorted(output_files):
                file_size = file.stat().st_size
                logger.info(f"  📄 {file.name} ({file_size:,} bytes)")

            # Try to read a sample JSONL file
            jsonl_files = [f for f in output_files if f.suffix == '.jsonl']
            if jsonl_files:
                sample_file = jsonl_files[0]
                try:
                    with open(sample_file, 'r') as f:
                        lines = f.readlines()
                    logger.info(f"Sample file {sample_file.name} has {len(lines)} records")
                    if lines:
                        logger.info(f"Sample record keys: {list(eval(lines[0]).keys())}")
                except Exception as e:
                    logger.warning(f"Could not read sample file: {e}")
        else:
            logger.warning("No output files found!")

        return len(output_files) > 0

    def run_all_tests(self):
        """Run all sample tests"""
        logger.info("🚀 STARTING FOOTBALL SCRAPER SAMPLE TESTS")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        logger.info(f"Output directory: {self.output_dir}")

        # Create sample config files
        self.create_sample_config_files()

        # Run all test categories
        all_results = []

        # URL-based tests
        url_results = self.test_url_based_scraping()
        all_results.extend(url_results)

        # Multiple URL test
        multi_results = self.test_multiple_urls()
        all_results.extend(multi_results)

        # Competition-based tests
        comp_results = self.test_competition_based_scraping()
        all_results.extend(comp_results)

        # Fallback strategy tests
        fallback_results = self.test_fallback_strategies()
        all_results.extend(fallback_results)

        # Check output files
        has_output = self.check_output_files()

        # Summary
        logger.info("=" * 60)
        logger.info("📊 SAMPLE TEST SUMMARY")
        logger.info("=" * 60)

        successful_tests = sum(1 for result in all_results if result['success'])
        total_tests = len(all_results)

        logger.info(f"Tests passed: {successful_tests}/{total_tests}")
        logger.info(f"Output files generated: {'Yes' if has_output else 'No'}")

        for result in all_results:
            status = "✅" if result['success'] else "❌"
            logger.info(f"  {status} {result['test']}")

        if successful_tests > 0:
            logger.info("\n🎉 Sample tests completed! Check scraped_data/ directory for results.")
        else:
            logger.warning("\n⚠️ No tests passed. Check logs and configuration.")

        return successful_tests, total_tests, has_output


def main():
    """Main entry point"""
    runner = ScraperSampleRunner()
    success_count, total_count, has_output = runner.run_all_tests()

    # Exit code based on results
    if success_count > 0:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure


if __name__ == '__main__':
    main()