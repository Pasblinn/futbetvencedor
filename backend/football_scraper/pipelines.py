"""
📊 SCRAPY PIPELINES - Data Processing and Export Pipelines
Handles data cleaning, normalization, metadata addition, and multi-format export.
Outputs to CSV, JSONL, and Parquet formats with comprehensive metadata.
"""

import json
import logging
import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem

logger = logging.getLogger(__name__)

class DataCleaningPipeline:
    """
    🧹 Data Cleaning and Normalization Pipeline
    Cleans and normalizes scraped data before export
    """

    def __init__(self):
        self.processed_items = 0
        self.dropped_items = 0

    def process_item(self, item, spider):
        """Clean and normalize item data"""
        adapter = ItemAdapter(item)

        try:
            # Clean string fields
            for field_name, value in adapter.items():
                if isinstance(value, str):
                    # Strip whitespace
                    cleaned_value = value.strip()

                    # Remove multiple spaces
                    cleaned_value = ' '.join(cleaned_value.split())

                    # Handle empty strings
                    if not cleaned_value:
                        cleaned_value = None

                    adapter[field_name] = cleaned_value

                elif isinstance(value, list):
                    # Clean list items
                    cleaned_list = []
                    for list_item in value:
                        if isinstance(list_item, str):
                            cleaned_item = list_item.strip()
                            if cleaned_item:
                                cleaned_list.append(cleaned_item)
                        else:
                            cleaned_list.append(list_item)
                    adapter[field_name] = cleaned_list

            # Convert numeric strings to numbers
            numeric_fields = ['home_score', 'away_score', 'home_odds', 'draw_odds', 'away_odds',
                            'possession_home', 'possession_away', 'shots_home', 'shots_away']

            for field in numeric_fields:
                if field in adapter and adapter[field] is not None:
                    try:
                        value = adapter[field]
                        if isinstance(value, str):
                            # Remove non-numeric characters except decimal point
                            numeric_value = ''.join(char for char in value if char.isdigit() or char == '.')
                            if numeric_value:
                                adapter[field] = float(numeric_value) if '.' in numeric_value else int(numeric_value)
                    except (ValueError, TypeError):
                        logger.warning(f"Could not convert {field} to numeric: {adapter[field]}")

            # Standardize team names
            team_fields = ['home_team', 'away_team']
            for field in team_fields:
                if field in adapter and adapter[field]:
                    adapter[field] = self._standardize_team_name(adapter[field])

            # Validate required fields
            required_fields = ['source_url', 'scraped_at']
            for field in required_fields:
                if field not in adapter or adapter[field] is None:
                    logger.error(f"Missing required field {field} in item from {spider.name}")
                    raise DropItem(f"Missing required field: {field}")

            self.processed_items += 1
            return item

        except DropItem:
            self.dropped_items += 1
            raise
        except Exception as e:
            logger.error(f"Error processing item in DataCleaningPipeline: {e}")
            self.dropped_items += 1
            raise DropItem(f"Error processing item: {e}")

    def _standardize_team_name(self, team_name: str) -> str:
        """Standardize team name format"""
        if not team_name:
            return team_name

        # Common standardizations
        standardizations = {
            # Brazilian teams
            'Athletico Paranaense': 'Athletico-PR',
            'Atletico Paranaense': 'Athletico-PR',
            'Atletico Mineiro': 'Atlético-MG',
            'Atletico MG': 'Atlético-MG',
            'Sao Paulo': 'São Paulo',
            'Sao Paulo FC': 'São Paulo',
            'Red Bull Bragantino': 'Bragantino',
            'RB Bragantino': 'Bragantino',
            'Vasco da Gama': 'Vasco',
            'Flamengo RJ': 'Flamengo',
            'Fluminense FC': 'Fluminense',
            'Palmeiras SP': 'Palmeiras',

            # International teams (examples)
            'Manchester United': 'Man United',
            'Manchester City': 'Man City',
            'Real Madrid CF': 'Real Madrid',
            'FC Barcelona': 'Barcelona',
            'Bayern Munich': 'Bayern München',
            'Borussia Dortmund': 'Dortmund',
            'Paris Saint-Germain': 'PSG',
            'Juventus FC': 'Juventus',
            'AC Milan': 'Milan',
            'Inter Milan': 'Inter',
        }

        return standardizations.get(team_name, team_name)

    def close_spider(self, spider):
        """Log pipeline statistics"""
        logger.info(f"DataCleaningPipeline processed {self.processed_items} items, "
                   f"dropped {self.dropped_items} items")

class MetadataPipeline:
    """
    📝 Metadata Addition Pipeline
    Adds comprehensive metadata to each scraped item
    """

    def __init__(self):
        self.start_time = datetime.now()

    def open_spider(self, spider):
        """Initialize pipeline for spider"""
        self.spider_start_time = datetime.now()

    def process_item(self, item, spider):
        """Add metadata to item"""
        adapter = ItemAdapter(item)

        # Add spider metadata
        if 'spider_name' not in adapter:
            adapter['spider_name'] = spider.name

        # Add timestamps if not present
        if 'scraped_at' not in adapter:
            adapter['scraped_at'] = datetime.now().isoformat()

        # Add source site from URL
        if 'source_url' in adapter and 'source_site' not in adapter:
            url = adapter['source_url']
            if 'oddspedia.com' in url:
                adapter['source_site'] = 'oddspedia'
            elif 'fbref.com' in url:
                adapter['source_site'] = 'fbref'
            elif 'soccerway.com' in url:
                adapter['source_site'] = 'soccerway'
            elif 'rsssf.com' in url:
                adapter['source_site'] = 'rsssf'
            elif 'github.com' in url and 'openfootball' in url:
                adapter['source_site'] = 'openfootball'
            else:
                adapter['source_site'] = 'unknown'

        # Add scraping metadata from request meta
        request_meta = getattr(spider, 'current_request_meta', {})

        if 'proxy_info' in request_meta:
            proxy_info = request_meta['proxy_info']
            adapter['proxy_used'] = proxy_info.url
            adapter['proxy_country'] = proxy_info.country
        else:
            adapter['proxy_used'] = None

        if 'user_agent_info' in request_meta:
            ua_info = request_meta['user_agent_info']
            adapter['user_agent'] = ua_info.get('User-Agent', 'unknown')
        else:
            adapter['user_agent'] = 'unknown'

        # Add scrape strategy
        if request_meta.get('use_selenium', False):
            adapter['scrape_strategy'] = 'selenium'
        elif request_meta.get('use_requests_html', False):
            adapter['scrape_strategy'] = 'requests_html'
        else:
            adapter['scrape_strategy'] = 'scrapy'

        # Add response time if available
        adapter['response_time_ms'] = request_meta.get('response_time_ms', 0)

        # Generate item hash for deduplication
        item_hash = self._generate_item_hash(adapter)
        adapter['item_hash'] = item_hash

        return item

    def _generate_item_hash(self, adapter: ItemAdapter) -> str:
        """Generate unique hash for item"""
        # Use key fields to generate hash
        key_fields = ['source_url', 'home_team', 'away_team', 'match_date']

        hash_string = ''
        for field in key_fields:
            if field in adapter and adapter[field] is not None:
                hash_string += str(adapter[field])

        return hashlib.md5(hash_string.encode()).hexdigest()

class ExportPipeline:
    """
    📤 Multi-Format Export Pipeline
    Exports data to CSV, JSONL, and Parquet formats with metadata
    """

    def __init__(self, output_dir: str = 'scraped_data'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # File handles
        self.jsonl_file = None
        self.csv_data = []
        self.items_processed = 0

        # Metadata tracking
        self.start_time = datetime.now()
        self.source_sites = set()
        self.competitions = set()
        self.seasons = set()

    def open_spider(self, spider):
        """Initialize export files"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # JSONL file
        jsonl_path = self.output_dir / f'data_{spider.name}_{timestamp}.jsonl'
        self.jsonl_file = open(jsonl_path, 'w', encoding='utf-8')

        # Store paths for later use
        self.current_timestamp = timestamp
        self.current_spider = spider.name

        logger.info(f"ExportPipeline initialized for {spider.name}")
        logger.info(f"JSONL output: {jsonl_path}")

    def process_item(self, item, spider):
        """Export item to all formats"""
        adapter = ItemAdapter(item)

        try:
            # Convert to dict
            item_dict = dict(adapter)

            # Write to JSONL
            json_line = json.dumps(item_dict, ensure_ascii=False, default=str)
            self.jsonl_file.write(json_line + '\n')
            self.jsonl_file.flush()

            # Add to CSV data
            self.csv_data.append(item_dict)

            # Update metadata tracking
            if 'source_site' in item_dict:
                self.source_sites.add(item_dict['source_site'])

            if 'competition' in item_dict:
                self.competitions.add(item_dict['competition'])

            if 'season' in item_dict:
                self.seasons.add(item_dict['season'])

            self.items_processed += 1

            if self.items_processed % 100 == 0:
                logger.info(f"Exported {self.items_processed} items")

            return item

        except Exception as e:
            logger.error(f"Error exporting item: {e}")
            return item

    def close_spider(self, spider):
        """Finalize exports and generate metadata"""
        try:
            # Close JSONL file
            if self.jsonl_file:
                self.jsonl_file.close()

            # Export to CSV
            if self.csv_data:
                csv_path = self.output_dir / f'data_{self.current_spider}_{self.current_timestamp}.csv'
                df = pd.DataFrame(self.csv_data)
                df.to_csv(csv_path, index=False, encoding='utf-8')
                logger.info(f"CSV exported: {csv_path}")

                # Export to Parquet
                parquet_path = self.output_dir / f'data_{self.current_spider}_{self.current_timestamp}.parquet'
                df.to_parquet(parquet_path, index=False, engine='pyarrow')
                logger.info(f"Parquet exported: {parquet_path}")

            # Create unified files
            self._create_unified_files()

            # Generate metadata
            self._generate_metadata_file()

            logger.info(f"ExportPipeline completed. Processed {self.items_processed} items")

        except Exception as e:
            logger.error(f"Error closing ExportPipeline: {e}")

    def _create_unified_files(self):
        """Create unified data.jsonl and data.parquet files"""
        try:
            # Combine all JSONL files
            unified_jsonl_path = self.output_dir / 'data.jsonl'
            all_data = []

            # Read all individual files
            for file_path in self.output_dir.glob('data_*.jsonl'):
                if file_path.name != 'data.jsonl':  # Skip the unified file itself
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            if line.strip():
                                all_data.append(json.loads(line))

            # Write unified JSONL
            if all_data:
                with open(unified_jsonl_path, 'w', encoding='utf-8') as f:
                    for item in all_data:
                        json_line = json.dumps(item, ensure_ascii=False, default=str)
                        f.write(json_line + '\n')

                # Create unified Parquet
                unified_parquet_path = self.output_dir / 'data.parquet'
                df_unified = pd.DataFrame(all_data)
                df_unified.to_parquet(unified_parquet_path, index=False, engine='pyarrow')

                logger.info(f"Unified files created: {unified_jsonl_path}, {unified_parquet_path}")

        except Exception as e:
            logger.error(f"Error creating unified files: {e}")

    def _generate_metadata_file(self):
        """Generate comprehensive metadata file"""
        try:
            end_time = datetime.now()
            duration = (end_time - self.start_time).total_seconds()

            # Calculate file sizes and hashes
            files_info = {}
            for file_path in self.output_dir.glob('data*.{jsonl,csv,parquet}'):
                if file_path.exists():
                    file_size = file_path.stat().st_size

                    # Calculate file hash
                    with open(file_path, 'rb') as f:
                        file_hash = hashlib.md5(f.read()).hexdigest()

                    files_info[file_path.name] = {
                        'size_bytes': file_size,
                        'size_mb': round(file_size / (1024 * 1024), 2),
                        'md5_hash': file_hash
                    }

            metadata = {
                'dataset_version': '1.0.0',
                'generated_at': end_time.isoformat(),
                'scraping_started': self.start_time.isoformat(),
                'scraping_duration_seconds': round(duration, 2),
                'total_items': self.items_processed,
                'source_sites': sorted(list(self.source_sites)),
                'competitions': sorted(list(self.competitions)),
                'seasons': sorted(list(self.seasons)),
                'files': files_info,
                'scraping_stats': {
                    'spider_name': self.current_spider,
                    'items_per_second': round(self.items_processed / duration, 2) if duration > 0 else 0,
                }
            }

            # Write metadata
            metadata_path = self.output_dir / 'metadata.json'
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            logger.info(f"Metadata generated: {metadata_path}")

        except Exception as e:
            logger.error(f"Error generating metadata: {e}")

class ValidationPipeline:
    """
    ✅ Data Validation Pipeline
    Validates scraped data quality and generates validation reports
    """

    def __init__(self):
        self.validation_errors = []
        self.validation_warnings = []
        self.items_validated = 0

    def process_item(self, item, spider):
        """Validate item data"""
        adapter = ItemAdapter(item)
        errors = []
        warnings = []

        # Required field validation
        required_fields = ['source_url', 'scraped_at']
        for field in required_fields:
            if field not in adapter or adapter[field] is None:
                errors.append(f"Missing required field: {field}")

        # Data type validation
        if 'home_score' in adapter and adapter['home_score'] is not None:
            if not isinstance(adapter['home_score'], (int, float)):
                warnings.append(f"home_score should be numeric, got {type(adapter['home_score'])}")

        # Data range validation
        if 'possession_home' in adapter and adapter['possession_home'] is not None:
            possession = adapter['possession_home']
            if isinstance(possession, (int, float)) and not (0 <= possession <= 100):
                warnings.append(f"possession_home outside valid range (0-100): {possession}")

        # Logical validation
        if 'home_team' in adapter and 'away_team' in adapter:
            if adapter['home_team'] == adapter['away_team']:
                errors.append("home_team and away_team cannot be the same")

        # Record validation results
        if errors:
            self.validation_errors.extend(errors)
            logger.error(f"Validation errors for item: {errors}")

        if warnings:
            self.validation_warnings.extend(warnings)
            logger.warning(f"Validation warnings for item: {warnings}")

        self.items_validated += 1
        return item

    def close_spider(self, spider):
        """Generate validation report"""
        try:
            report = {
                'validation_completed_at': datetime.now().isoformat(),
                'items_validated': self.items_validated,
                'total_errors': len(self.validation_errors),
                'total_warnings': len(self.validation_warnings),
                'error_rate': len(self.validation_errors) / max(self.items_validated, 1),
                'warning_rate': len(self.validation_warnings) / max(self.items_validated, 1),
                'errors': self.validation_errors[:50],  # First 50 errors
                'warnings': self.validation_warnings[:50],  # First 50 warnings
            }

            # Write validation report
            output_dir = Path('scraped_data')
            report_path = output_dir / 'validation_report.json'

            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            logger.info(f"Validation report generated: {report_path}")
            logger.info(f"Validation summary: {self.items_validated} items, "
                       f"{len(self.validation_errors)} errors, {len(self.validation_warnings)} warnings")

        except Exception as e:
            logger.error(f"Error generating validation report: {e}")