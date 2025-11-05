#!/usr/bin/env python3
"""
📅 DAILY DATA COLLECTOR - Automated daily scraping from public sources
Collects data from government/public sources with low security restrictions
Designed for daily cron job execution: 0 6 * * * python daily_data_collector.py
"""

import asyncio
import aiohttp
import pandas as pd
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import time
import random
import hashlib
from bs4 import BeautifulSoup
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/daily_collector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DailyDataCollector:
    """Automated daily data collection from public sources"""

    def __init__(self):
        self.session = None
        self.collected_data = []
        self.sources = self._configure_sources()
        self.output_dir = Path("daily_data")
        self.output_dir.mkdir(exist_ok=True)

        # Ensure logs directory exists
        Path("logs").mkdir(exist_ok=True)

    def _configure_sources(self) -> Dict:
        """Configure public data sources with low security restrictions"""
        return {
            'wikipedia_pt': {
                'name': 'Wikipedia Portuguese',
                'urls': [
                    'https://pt.wikipedia.org/wiki/Campeonato_Brasileiro_de_Futebol_de_2024_-_Série_A',
                    'https://pt.wikipedia.org/wiki/Campeonato_Brasileiro_de_Futebol_de_2025_-_Série_A'
                ],
                'rate_limit': 2.0,  # seconds between requests
                'priority': 'high',
                'success_rate': 0.95
            },
            'wikipedia_en': {
                'name': 'Wikipedia English',
                'urls': [
                    'https://en.wikipedia.org/wiki/2024_Campeonato_Brasileiro_Série_A',
                    'https://en.wikipedia.org/wiki/2025_Campeonato_Brasileiro_Série_A'
                ],
                'rate_limit': 2.0,
                'priority': 'high',
                'success_rate': 0.95
            },
            'rsssf': {
                'name': 'RSSSF - Rec.Sport.Soccer Statistics Foundation',
                'urls': [
                    'https://www.rsssf.com/tablesbr/bra2024.html',
                    'https://www.rsssf.com/tablesbr/bra2025.html'
                ],
                'rate_limit': 3.0,  # More conservative for RSSSF
                'priority': 'medium',
                'success_rate': 0.80
            },
            'wikidata': {
                'name': 'Wikidata SPARQL',
                'urls': [
                    'https://query.wikidata.org/sparql'
                ],
                'rate_limit': 5.0,  # Very conservative for SPARQL endpoint
                'priority': 'low',
                'success_rate': 0.70,
                'sparql_queries': [
                    self._get_brazilian_teams_query(),
                    self._get_recent_matches_query()
                ]
            },
            'football_data_org': {
                'name': 'football-data.org API',
                'urls': [
                    'https://api.football-data.org/v4/competitions/BSA/standings',
                    'https://api.football-data.org/v4/competitions/BSA/matches'
                ],
                'rate_limit': 60.0,  # API rate limit
                'priority': 'medium',
                'success_rate': 0.85,
                'headers': {
                    'X-Auth-Token': 'your_api_key_here'  # Would need registration
                }
            }
        }

    def _get_brazilian_teams_query(self) -> str:
        """SPARQL query for Brazilian football teams"""
        return """
        SELECT DISTINCT ?team ?teamLabel ?league ?leagueLabel WHERE {
          ?team wdt:P31 wd:Q476028 ;
                wdt:P17 wd:Q155 .
          OPTIONAL { ?team wdt:P118 ?league . }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "pt,en" . }
        }
        LIMIT 50
        """

    def _get_recent_matches_query(self) -> str:
        """SPARQL query for recent matches"""
        return """
        SELECT DISTINCT ?match ?matchLabel ?home ?homeLabel ?away ?awayLabel ?date WHERE {
          ?match wdt:P31 wd:Q16466 ;
                 wdt:P1268 ?home ;
                 wdt:P1269 ?away ;
                 wdt:P585 ?date .
          ?home wdt:P17 wd:Q155 .
          ?away wdt:P17 wd:Q155 .
          FILTER (?date >= "2024-01-01T00:00:00Z"^^xsd:dateTime)
          SERVICE wikibase:label { bd:serviceParam wikibase:language "pt,en" . }
        }
        ORDER BY DESC(?date)
        LIMIT 100
        """

    async def collect_daily_data(self):
        """Main daily data collection routine"""
        logger.info("🚀 Starting daily data collection")
        start_time = datetime.now()

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Football Analytics Bot 1.0 (Educational Research)',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
        ) as session:
            self.session = session

            # Collect from sources in priority order
            high_priority = [k for k, v in self.sources.items() if v['priority'] == 'high']
            medium_priority = [k for k, v in self.sources.items() if v['priority'] == 'medium']
            low_priority = [k for k, v in self.sources.items() if v['priority'] == 'low']

            for sources_batch in [high_priority, medium_priority, low_priority]:
                await self._collect_from_sources(sources_batch)

        # Process collected data
        await self._process_and_save_data()

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info(f"✅ Daily collection completed in {duration:.1f}s")
        logger.info(f"📊 Collected {len(self.collected_data)} data entries")

        return self.collected_data

    async def _collect_from_sources(self, source_keys: List[str]):
        """Collect data from a batch of sources"""
        tasks = []
        for source_key in source_keys:
            source = self.sources[source_key]
            if source_key == 'wikidata':
                task = self._collect_wikidata(source_key, source)
            elif source_key == 'football_data_org':
                task = self._collect_api_data(source_key, source)
            else:
                task = self._collect_web_data(source_key, source)
            tasks.append(task)

        # Execute tasks with controlled concurrency
        for task in tasks:
            try:
                await task
            except Exception as e:
                logger.error(f"Error collecting from source: {e}")

            # Rate limiting between sources
            await asyncio.sleep(1)

    async def _collect_web_data(self, source_key: str, source: Dict):
        """Collect data from web sources (Wikipedia, RSSSF)"""
        logger.info(f"🌐 Collecting from {source['name']}")

        for url in source['urls']:
            try:
                await asyncio.sleep(source['rate_limit'])

                async with self.session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()

                        # Extract tables from HTML
                        tables = self._extract_tables_from_html(content, url)

                        for table_data in tables:
                            self.collected_data.append({
                                'source': source_key,
                                'source_url': url,
                                'collected_at': datetime.now().isoformat(),
                                'data_type': 'table',
                                'data': table_data
                            })

                        logger.info(f"✅ {url}: {len(tables)} tables extracted")
                    else:
                        logger.warning(f"⚠️ {url}: HTTP {response.status}")

            except Exception as e:
                logger.error(f"❌ Error collecting {url}: {e}")

    async def _collect_wikidata(self, source_key: str, source: Dict):
        """Collect data from Wikidata SPARQL endpoint"""
        logger.info(f"🔍 Collecting from {source['name']}")

        for query in source['sparql_queries']:
            try:
                await asyncio.sleep(source['rate_limit'])

                params = {
                    'query': query,
                    'format': 'json'
                }

                async with self.session.get(source['urls'][0], params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        self.collected_data.append({
                            'source': source_key,
                            'source_url': source['urls'][0],
                            'collected_at': datetime.now().isoformat(),
                            'data_type': 'sparql',
                            'query': query[:100] + '...',
                            'data': data['results']['bindings']
                        })

                        logger.info(f"✅ SPARQL query: {len(data['results']['bindings'])} results")
                    else:
                        logger.warning(f"⚠️ SPARQL endpoint: HTTP {response.status}")

            except Exception as e:
                logger.error(f"❌ Error with SPARQL query: {e}")

    async def _collect_api_data(self, source_key: str, source: Dict):
        """Collect data from API endpoints"""
        logger.info(f"🔌 Collecting from {source['name']}")

        headers = source.get('headers', {})

        for url in source['urls']:
            try:
                await asyncio.sleep(source['rate_limit'])

                async with self.session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()

                        self.collected_data.append({
                            'source': source_key,
                            'source_url': url,
                            'collected_at': datetime.now().isoformat(),
                            'data_type': 'api',
                            'data': data
                        })

                        logger.info(f"✅ {url}: API data collected")
                    else:
                        logger.warning(f"⚠️ {url}: HTTP {response.status}")

            except Exception as e:
                logger.error(f"❌ Error collecting API {url}: {e}")

    def _extract_tables_from_html(self, html: str, url: str) -> List[Dict]:
        """Extract tables from HTML content"""
        soup = BeautifulSoup(html, 'html.parser')
        tables = soup.find_all('table')

        extracted_tables = []

        for i, table in enumerate(tables):
            try:
                # Convert table to pandas DataFrame
                df = pd.read_html(str(table))[0]

                if len(df) > 2 and len(df.columns) > 2:  # Only meaningful tables
                    table_data = {
                        'table_index': i,
                        'rows': len(df),
                        'columns': len(df.columns),
                        'column_names': df.columns.tolist(),
                        'data': df.to_dict('records')
                    }

                    # Add table caption if available
                    caption = table.find('caption')
                    if caption:
                        table_data['caption'] = caption.get_text().strip()

                    extracted_tables.append(table_data)

            except Exception as e:
                logger.debug(f"Could not process table {i}: {e}")

        return extracted_tables

    async def _process_and_save_data(self):
        """Process and save collected data"""
        if not self.collected_data:
            logger.warning("⚠️ No data collected")
            return

        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Save raw collected data
        raw_file = self.output_dir / f"daily_raw_{timestamp}.json"
        with open(raw_file, 'w', encoding='utf-8') as f:
            json.dump(self.collected_data, f, ensure_ascii=False, indent=2)

        logger.info(f"💾 Raw data saved: {raw_file}")

        # Process for ML pipeline
        processed_file = self.output_dir / f"daily_processed_{timestamp}.jsonl"
        await self._convert_for_ml_pipeline(processed_file)

        # Run ML ingestion if enabled
        await self._trigger_ml_pipeline(processed_file)

    async def _convert_for_ml_pipeline(self, output_file: Path):
        """Convert collected data to ML pipeline format"""
        ml_ready_data = []

        for entry in self.collected_data:
            if entry['data_type'] == 'table' and 'data' in entry:
                for table in entry['data']:
                    if 'data' in table and len(table['data']) > 0:
                        # Convert to JSONL format expected by ingest.py
                        ml_entry = {
                            'source_url': entry['source_url'],
                            'source_site': entry['source'],
                            'competition': 'brasileirao',  # Could be detected
                            'season': '2024',  # Could be detected from URL
                            'table_name': f"{entry['source']}_{table.get('table_index', 0)}",
                            'scraped_at': entry['collected_at'],
                            'strategy': 'daily_collector',
                            'columns': table.get('column_names', []),
                            'rows': table['data'],
                            'total_rows': len(table['data'])
                        }
                        ml_ready_data.append(ml_entry)

        # Save as JSONL for ML pipeline
        with open(output_file, 'w', encoding='utf-8') as f:
            for entry in ml_ready_data:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')

        logger.info(f"🔧 ML-ready data saved: {output_file} ({len(ml_ready_data)} entries)")

    async def _trigger_ml_pipeline(self, data_file: Path):
        """Trigger ML pipeline if new data is significant"""
        if len(self.collected_data) < 5:  # Not enough new data
            logger.info("ℹ️ Insufficient new data for ML pipeline")
            return

        try:
            # Create temporary directory for ML processing
            temp_dir = Path("temp_daily_ml")
            temp_dir.mkdir(exist_ok=True)

            # Copy data file to temp directory
            temp_file = temp_dir / data_file.name
            temp_file.write_text(data_file.read_text())

            # Run ML ingestion pipeline
            logger.info("🤖 Triggering ML pipeline...")
            result = subprocess.run([
                'python', 'ingest.py',
                '--input', str(temp_dir),
                '--output', f'ml_daily_{datetime.now().strftime("%Y%m%d")}'
            ], capture_output=True, text=True, cwd=Path.cwd())

            if result.returncode == 0:
                logger.info("✅ ML pipeline completed successfully")

                # Trigger retraining if enough new data
                await self._check_retrain_trigger()
            else:
                logger.error(f"❌ ML pipeline failed: {result.stderr}")

        except Exception as e:
            logger.error(f"❌ Error triggering ML pipeline: {e}")

    async def _check_retrain_trigger(self):
        """Check if model retraining should be triggered"""
        # Simple heuristic: retrain weekly or with significant data changes
        last_training = self._get_last_training_date()

        if not last_training or (datetime.now() - last_training).days >= 7:
            logger.info("🔄 Triggering ML model retraining")

            try:
                result = subprocess.run([
                    'python', 'train_ml_enriched.py'
                ], capture_output=True, text=True, cwd=Path.cwd())

                if result.returncode == 0:
                    logger.info("✅ Model retraining completed")
                    self._update_last_training_date()
                else:
                    logger.error(f"❌ Model retraining failed: {result.stderr}")

            except Exception as e:
                logger.error(f"❌ Error during retraining: {e}")

    def _get_last_training_date(self) -> Optional[datetime]:
        """Get the date of last model training"""
        try:
            metadata_file = Path("models/enriched_brasileirao/metadata_enriched.joblib")
            if metadata_file.exists():
                import joblib
                metadata = joblib.load(metadata_file)
                return datetime.fromisoformat(metadata['training_date'])
        except:
            pass
        return None

    def _update_last_training_date(self):
        """Update the last training date"""
        try:
            training_log = Path("logs/last_training.txt")
            training_log.write_text(datetime.now().isoformat())
        except Exception as e:
            logger.error(f"Could not update training date: {e}")

async def main():
    """Main entry point for daily collection"""
    collector = DailyDataCollector()

    try:
        data = await collector.collect_daily_data()

        # Generate summary report
        print("\n📊 DAILY COLLECTION SUMMARY")
        print("=" * 50)
        print(f"🕐 Completed at: {datetime.now()}")
        print(f"📈 Data entries: {len(data)}")

        source_counts = {}
        for entry in data:
            source = entry['source']
            source_counts[source] = source_counts.get(source, 0) + 1

        print("📋 By source:")
        for source, count in source_counts.items():
            print(f"  {source}: {count}")

        print("✅ Daily collection completed successfully!")

    except Exception as e:
        logger.error(f"❌ Daily collection failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())