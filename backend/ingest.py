#!/usr/bin/env python3
"""
🔄 ML DATA INGESTION SERVICE
Converts scraped data (JSONL/Parquet) into ML-ready features for training.

Input: raw_data/ (data.jsonl, data.parquet from scraper)
Output: ml_ready/ (features.parquet, labels.parquet, metadata.json)
"""

import json
import logging
import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import argparse
import sys

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import numpy as np
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from sklearn.impute import SimpleImputer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MLDataIngestor:
    """Converts scraped football data into ML-ready features"""

    def __init__(self, config: Dict = None):
        self.config = config or self._default_config()

        # Field mappings for different data sources
        self.field_mappings = {
            'fbref': {
                'Home': 'home_team',
                'Away': 'away_team',
                'xG': 'xg_home',
                'xG.1': 'xg_away',
                'Score': 'score',
                'Date': 'match_date'
            },
            'oddspedia': {
                'homeTeam': 'home_team',
                'awayTeam': 'away_team',
                'homeOdds': 'odds_home',
                'awayOdds': 'odds_away',
                'drawOdds': 'odds_draw'
            },
            'soccerway': {
                'Home team': 'home_team',
                'Away team': 'away_team',
                'Result': 'result'
            },
            'wikipedia': {
                'Home team': 'home_team',
                'Away team': 'away_team',
                'Score': 'score'
            }
        }

        # Initialize encoders
        self.label_encoders = {}
        self.imputers = {}

    def _default_config(self) -> Dict:
        """Default configuration for data ingestion"""
        return {
            'missing_threshold': 0.8,  # Drop columns with >80% missing
            'categorical_encoding': 'label',  # 'label' or 'onehot'
            'numerical_imputation': 'median',  # 'mean', 'median', 'mode'
            'categorical_imputation': 'most_frequent',
            'date_format': '%Y-%m-%d',
            'output_partitioning': ['competition', 'season'],
            'min_matches_per_team': 5,  # Minimum matches for team statistics
            'feature_windows': [5, 10],  # Rolling windows for form features
        }

    def ingest_and_prepare(
        self,
        path_raw_dir: str,
        path_out_dir: str,
        config: Dict = None
    ) -> Dict:
        """
        Main ingestion pipeline

        Args:
            path_raw_dir: Path to raw scraped data
            path_out_dir: Path to output ML-ready data
            config: Configuration overrides

        Returns:
            Dict with processing results and metadata
        """
        if config:
            self.config.update(config)

        raw_dir = Path(path_raw_dir)
        out_dir = Path(path_out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Starting ML data ingestion: {raw_dir} -> {out_dir}")

        # Step 1: Load raw data
        raw_data = self._load_raw_data(raw_dir)
        if raw_data.empty:
            raise ValueError("No data found in raw directory")

        logger.info(f"Loaded {len(raw_data)} raw records from {raw_dir}")

        # Step 2: Clean and normalize
        cleaned_data = self._clean_and_normalize(raw_data)
        logger.info(f"Cleaned data: {len(cleaned_data)} records")

        # Step 3: Feature engineering
        features_df = self._engineer_features(cleaned_data)
        logger.info(f"Engineered features: {len(features_df)} records, {len(features_df.columns)} features")

        # Step 4: Generate labels (if possible)
        labels_df = self._generate_labels(features_df)

        # Step 5: Split features and labels
        final_features = features_df.drop(columns=[col for col in ['result', 'winner', 'home_goals', 'away_goals']
                                                  if col in features_df.columns])

        # Step 6: Save results
        metadata = self._save_results(final_features, labels_df, out_dir, raw_data)

        logger.info(f"✅ Ingestion complete! Generated {len(final_features)} feature records")
        return metadata

    def _load_raw_data(self, raw_dir: Path) -> pd.DataFrame:
        """Load raw data from JSONL and Parquet files"""
        all_data = []

        # Load JSONL files
        jsonl_files = list(raw_dir.glob('*.jsonl'))
        for jsonl_file in jsonl_files:
            logger.info(f"Loading JSONL: {jsonl_file}")
            try:
                records = []
                with open(jsonl_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            records.append(json.loads(line.strip()))

                if records:
                    df = pd.json_normalize(records)
                    all_data.append(df)
                    logger.info(f"Loaded {len(df)} records from {jsonl_file}")
            except Exception as e:
                logger.warning(f"Failed to load {jsonl_file}: {e}")

        # Load Parquet files
        parquet_files = list(raw_dir.glob('*.parquet'))
        for parquet_file in parquet_files:
            logger.info(f"Loading Parquet: {parquet_file}")
            try:
                df = pd.read_parquet(parquet_file)
                all_data.append(df)
                logger.info(f"Loaded {len(df)} records from {parquet_file}")
            except Exception as e:
                logger.warning(f"Failed to load {parquet_file}: {e}")

        if not all_data:
            return pd.DataFrame()

        # Combine all data
        combined_df = pd.concat(all_data, ignore_index=True, sort=False)
        return combined_df

    def _clean_and_normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and normalize scraped data"""
        logger.info("Cleaning and normalizing data...")

        # Handle nested data structures
        if 'data' in df.columns:
            expanded_data = []
            for idx, row in df.iterrows():
                if isinstance(row['data'], pd.DataFrame):
                    # Flatten DataFrame data
                    data_df = row['data'].copy()
                    # Add metadata from parent row
                    for col in ['source_url', 'competition', 'season', 'scraped_at']:
                        if col in row:
                            data_df[col] = row[col]
                    expanded_data.append(data_df)
                elif isinstance(row['data'], dict):
                    # Handle dictionary data
                    data_dict = row['data'].copy()
                    # Add metadata
                    for col in ['source_url', 'competition', 'season', 'scraped_at']:
                        if col in row:
                            data_dict[col] = row[col]
                    expanded_data.append(pd.DataFrame([data_dict]))

            if expanded_data:
                df = pd.concat(expanded_data, ignore_index=True, sort=False)

        # Handle Wikipedia table structure (rows column contains list of dicts)
        elif 'rows' in df.columns and 'columns' in df.columns:
            expanded_data = []
            for idx, row in df.iterrows():
                if isinstance(row['rows'], list) and len(row['rows']) > 0:
                    # Convert rows list to DataFrame
                    rows_df = pd.DataFrame(row['rows'])

                    # Add metadata from parent row
                    for col in ['source_url', 'source_site', 'competition', 'season', 'table_name', 'scraped_at', 'strategy']:
                        if col in row and pd.notna(row[col]):
                            rows_df[col] = row[col]

                    expanded_data.append(rows_df)

            if expanded_data:
                df = pd.concat(expanded_data, ignore_index=True, sort=False)

        # Column name normalization
        df.columns = df.columns.str.lower().str.replace(' ', '_').str.replace('[^a-z0-9_]', '', regex=True)

        # Apply field mappings based on source
        df = self._apply_field_mappings(df)

        # Data type conversions
        df = self._convert_data_types(df)

        # Remove rows with too many missing values
        missing_threshold = len(df.columns) * (1 - self.config['missing_threshold'])
        df = df.dropna(thresh=missing_threshold)

        # Drop columns with too many missing values
        missing_cols = df.isnull().sum()
        cols_to_drop = missing_cols[missing_cols > len(df) * self.config['missing_threshold']].index
        if len(cols_to_drop) > 0:
            logger.info(f"Dropping columns with >80% missing: {list(cols_to_drop)}")
            df = df.drop(columns=cols_to_drop)

        return df

    def _apply_field_mappings(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply source-specific field mappings"""
        if 'source_site' not in df.columns:
            return df

        for site, mappings in self.field_mappings.items():
            site_mask = df['source_site'].str.contains(site, na=False)
            if site_mask.any():
                logger.info(f"Applying {site} field mappings to {site_mask.sum()} records")
                for old_col, new_col in mappings.items():
                    if old_col in df.columns:
                        df.loc[site_mask, new_col] = df.loc[site_mask, old_col]

        return df

    def _convert_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert data types appropriately"""
        # Date columns
        date_cols = [col for col in df.columns if any(keyword in col.lower()
                     for keyword in ['date', 'time', 'scraped_at'])]

        for col in date_cols:
            try:
                df[col] = pd.to_datetime(df[col], errors='coerce')
            except Exception as e:
                logger.warning(f"Failed to convert {col} to datetime: {e}")

        # Numeric columns (goals, odds, ratings, etc.)
        numeric_patterns = ['goal', 'xg', 'odd', 'rating', 'point', 'win', 'draw', 'loss']
        for col in df.columns:
            if any(pattern in col.lower() for pattern in numeric_patterns):
                try:
                    # Handle percentage values
                    if df[col].dtype == 'object':
                        df[col] = df[col].astype(str).str.replace('%', '').str.replace('$', '')
                    df[col] = pd.to_numeric(df[col], errors='coerce')

                    # Convert percentages to decimals
                    if col.lower().endswith('_pct') or '%' in str(df[col].iloc[0]):
                        df[col] = df[col] / 100.0

                except Exception as e:
                    logger.warning(f"Failed to convert {col} to numeric: {e}")

        return df

    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engineer ML features from cleaned data"""
        logger.info("Engineering ML features...")

        features_list = []

        # Group by match or team
        if all(col in df.columns for col in ['home_team', 'away_team']):
            # Match-based features
            features_list.append(self._create_match_features(df))
        elif 'team' in df.columns:
            # Team-based features
            features_list.append(self._create_team_features(df))
        else:
            # Generic features
            features_list.append(self._create_generic_features(df))

        # Combine all features
        if features_list:
            final_features = pd.concat(features_list, ignore_index=True, sort=False)
        else:
            final_features = df.copy()

        # Add derived features
        final_features = self._add_derived_features(final_features)

        # Handle categorical encoding
        final_features = self._encode_categorical_features(final_features)

        # Handle missing values
        final_features = self._impute_missing_values(final_features)

        return final_features

    def _create_match_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create features for match-based data"""
        logger.info("Creating match-based features...")

        match_features = []

        for idx, row in df.iterrows():
            if pd.isna(row.get('home_team')) or pd.isna(row.get('away_team')):
                continue

            feature_dict = {
                'id': str(uuid.uuid4()),
                'source_url': row.get('source_url', ''),
                'competition': row.get('competition', 'unknown'),
                'season': row.get('season', 'unknown'),
                'home_team': row['home_team'],
                'away_team': row['away_team'],
                'match_date': row.get('match_date', datetime.now()),
                'home': True,  # For home team record
                'scraped_at': row.get('scraped_at', datetime.now()),
                'proxy': row.get('proxy', ''),
                'user_agent': row.get('user_agent', ''),
                'strategy': row.get('strategy', 'unknown')
            }

            # Extract match result if available
            if 'score' in row and pd.notna(row['score']):
                score = str(row['score'])
                if '-' in score or ':' in score:
                    try:
                        separator = '-' if '-' in score else ':'
                        home_goals, away_goals = map(int, score.split(separator))
                        feature_dict.update({
                            'goals_for': home_goals,
                            'goals_against': away_goals,
                            'result': 'W' if home_goals > away_goals else 'D' if home_goals == away_goals else 'L'
                        })
                    except ValueError:
                        pass

            # Extract xG if available
            for xg_col in ['xg_home', 'xg', 'expected_goals']:
                if xg_col in row and pd.notna(row[xg_col]):
                    feature_dict['xg'] = float(row[xg_col])
                    break

            # Extract odds if available
            for odds_col in ['odds_home', 'home_odds', '1']:
                if odds_col in row and pd.notna(row[odds_col]):
                    feature_dict['odds'] = float(row[odds_col])
                    break

            match_features.append(feature_dict)

            # Create away team record
            away_feature_dict = feature_dict.copy()
            away_feature_dict.update({
                'id': str(uuid.uuid4()),
                'team': row['away_team'],
                'opponent': row['home_team'],
                'home': False
            })

            if 'goals_for' in feature_dict:
                away_feature_dict.update({
                    'goals_for': feature_dict['goals_against'],
                    'goals_against': feature_dict['goals_for'],
                    'result': 'L' if feature_dict['result'] == 'W' else 'W' if feature_dict['result'] == 'L' else 'D'
                })

            # Away xG
            for xg_col in ['xg_away', 'xg_a', 'expected_goals_away']:
                if xg_col in row and pd.notna(row[xg_col]):
                    away_feature_dict['xg'] = float(row[xg_col])
                    break

            # Away odds
            for odds_col in ['odds_away', 'away_odds', '2']:
                if odds_col in row and pd.notna(row[odds_col]):
                    away_feature_dict['odds'] = float(row[odds_col])
                    break

            match_features.append(away_feature_dict)

        return pd.DataFrame(match_features)

    def _create_team_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create features for team-based data"""
        logger.info("Creating team-based features...")

        team_features = []

        for idx, row in df.iterrows():
            feature_dict = {
                'id': str(uuid.uuid4()),
                'source_url': row.get('source_url', ''),
                'competition': row.get('competition', 'unknown'),
                'season': row.get('season', 'unknown'),
                'team': row.get('team', 'unknown'),
                'scraped_at': row.get('scraped_at', datetime.now())
            }

            # Add all numeric columns as features
            for col in df.columns:
                if pd.api.types.is_numeric_dtype(df[col]) and col not in feature_dict:
                    val = row.get(col, np.nan)
                    # Handle list values by converting to string or taking first element
                    if isinstance(val, list):
                        val = val[0] if len(val) > 0 else np.nan
                    feature_dict[col] = val

            team_features.append(feature_dict)

        return pd.DataFrame(team_features)

    def _create_generic_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create generic features when structure is unknown"""
        logger.info("Creating generic features...")

        features = df.copy()

        # Add ID if missing
        if 'id' not in features.columns:
            features['id'] = [str(uuid.uuid4()) for _ in range(len(features))]

        # Handle list values in all columns
        for col in features.columns:
            if features[col].apply(lambda x: isinstance(x, list)).any():
                features[col] = features[col].apply(
                    lambda x: x[0] if isinstance(x, list) and len(x) > 0 else (str(x) if isinstance(x, list) else x)
                )

        return features

    def _add_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add derived statistical features"""
        if len(df) == 0:
            return df

        # Team-level statistics
        if 'team' in df.columns:
            df = self._add_team_statistics(df)

        # Match-level statistics
        if all(col in df.columns for col in ['home_team', 'away_team']):
            df = self._add_match_statistics(df)

        return df

    def _add_team_statistics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add team-level statistical features"""
        logger.info("Adding team statistics...")

        if 'goals_for' in df.columns and 'goals_against' in df.columns:
            # Calculate team stats
            team_stats = df.groupby('team').agg({
                'goals_for': ['mean', 'std', 'sum'],
                'goals_against': ['mean', 'std', 'sum'],
                'result': lambda x: (x == 'W').mean() if 'result' in df.columns else 0
            }).round(3)

            team_stats.columns = ['goals_for_avg', 'goals_for_std', 'goals_for_total',
                                'goals_against_avg', 'goals_against_std', 'goals_against_total',
                                'win_rate']

            # Form indicators
            for window in self.config['feature_windows']:
                if len(df) >= window:
                    form_stats = df.groupby('team').apply(
                        lambda x: self._calculate_form(x, window)
                    ).reset_index(drop=True)

                    form_df = pd.DataFrame(form_stats.tolist())
                    form_df['team'] = form_stats.index

                    df = df.merge(form_df, on='team', how='left', suffixes=('', f'_last_{window}'))

            # Merge team stats back
            df = df.merge(team_stats, on='team', how='left')

        return df

    def _add_match_statistics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add match-level statistical features"""
        logger.info("Adding match statistics...")

        # Home/Away splits
        if 'home' in df.columns:
            df['home_advantage'] = df['home'].astype(int)

        return df

    def _calculate_form(self, team_data: pd.DataFrame, window: int) -> Dict:
        """Calculate form statistics for a team"""
        if len(team_data) < window:
            return {}

        recent = team_data.tail(window)

        form_dict = {}

        if 'result' in recent.columns:
            results = recent['result'].tolist()
            form_dict[f'form_last_{window}'] = ''.join(results)
            form_dict[f'wins_last_{window}'] = results.count('W')
            form_dict[f'draws_last_{window}'] = results.count('D')
            form_dict[f'losses_last_{window}'] = results.count('L')

        if 'goals_for' in recent.columns:
            form_dict[f'goals_for_avg_last_{window}'] = recent['goals_for'].mean()
            form_dict[f'goals_against_avg_last_{window}'] = recent['goals_against'].mean()

        return form_dict

    def _encode_categorical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Encode categorical features"""
        categorical_cols = df.select_dtypes(include=['object']).columns
        categorical_cols = [col for col in categorical_cols
                          if col not in ['id', 'source_url', 'scraped_at', 'proxy', 'user_agent']]

        if self.config['categorical_encoding'] == 'label':
            for col in categorical_cols:
                if col not in self.label_encoders:
                    self.label_encoders[col] = LabelEncoder()

                # Handle NaN values
                non_null_mask = df[col].notna()
                if non_null_mask.any():
                    df.loc[non_null_mask, f'{col}_encoded'] = self.label_encoders[col].fit_transform(
                        df.loc[non_null_mask, col].astype(str)
                    )

        return df

    def _impute_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Impute missing values"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        categorical_cols = df.select_dtypes(include=['object']).columns

        # Numeric imputation
        if len(numeric_cols) > 0:
            if 'numeric' not in self.imputers:
                self.imputers['numeric'] = SimpleImputer(strategy=self.config['numerical_imputation'])

            df[numeric_cols] = self.imputers['numeric'].fit_transform(df[numeric_cols])

        # Categorical imputation
        if len(categorical_cols) > 0:
            if 'categorical' not in self.imputers:
                self.imputers['categorical'] = SimpleImputer(strategy=self.config['categorical_imputation'])

            df[categorical_cols] = self.imputers['categorical'].fit_transform(df[categorical_cols])

        return df

    def _generate_labels(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate labels from features if possible"""
        labels_data = []

        if 'result' in df.columns:
            for idx, row in df.iterrows():
                label_dict = {
                    'id': row.get('id', str(uuid.uuid4())),
                    'result': row['result']
                }

                # Binary classification labels
                if row['result'] == 'W':
                    label_dict.update({'win': 1, 'draw': 0, 'loss': 0})
                elif row['result'] == 'D':
                    label_dict.update({'win': 0, 'draw': 1, 'loss': 0})
                elif row['result'] == 'L':
                    label_dict.update({'win': 0, 'draw': 0, 'loss': 1})

                labels_data.append(label_dict)

        return pd.DataFrame(labels_data) if labels_data else pd.DataFrame()

    def _save_results(
        self,
        features_df: pd.DataFrame,
        labels_df: pd.DataFrame,
        out_dir: Path,
        raw_data: pd.DataFrame
    ) -> Dict:
        """Save processed results and generate metadata"""

        # Save features
        features_path = out_dir / 'features.parquet'
        features_df.to_parquet(features_path, index=False)
        logger.info(f"Saved features: {features_path} ({len(features_df)} records)")

        # Save labels if available
        labels_path = None
        if not labels_df.empty:
            labels_path = out_dir / 'labels.parquet'
            labels_df.to_parquet(labels_path, index=False)
            logger.info(f"Saved labels: {labels_path} ({len(labels_df)} records)")

        # Generate validation report
        validation_report = self._generate_validation_report(features_df, labels_df)

        # Save validation report
        validation_path = out_dir / 'validation_report.json'
        with open(validation_path, 'w') as f:
            json.dump(validation_report, f, indent=2, default=str)

        # Generate metadata
        metadata = {
            'dataset_version': '1.0.0',
            'generated_at': datetime.now().isoformat(),
            'num_feature_records': len(features_df),
            'num_label_records': len(labels_df) if not labels_df.empty else 0,
            'num_features': len(features_df.columns),
            'source_sites': raw_data['source_site'].unique().tolist() if 'source_site' in raw_data.columns else [],
            'competitions': raw_data['competition'].unique().tolist() if 'competition' in raw_data.columns else [],
            'seasons': raw_data['season'].unique().tolist() if 'season' in raw_data.columns else [],
            'scraped_range': {
                'min': raw_data['scraped_at'].min() if 'scraped_at' in raw_data.columns else None,
                'max': raw_data['scraped_at'].max() if 'scraped_at' in raw_data.columns else None
            },
            'file_hashes': {
                'features': self._calculate_file_hash(features_path),
                'labels': self._calculate_file_hash(labels_path) if labels_path else None
            },
            'config': self.config,
            'validation_report': validation_report
        }

        # Save metadata
        metadata_path = out_dir / 'metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)

        logger.info(f"Saved metadata: {metadata_path}")

        return metadata

    def _generate_validation_report(self, features_df: pd.DataFrame, labels_df: pd.DataFrame) -> Dict:
        """Generate validation report"""
        report = {
            'features': {
                'total_records': len(features_df),
                'total_features': len(features_df.columns),
                'missing_values': features_df.isnull().sum().to_dict(),
                'data_types': features_df.dtypes.astype(str).to_dict(),
                'numeric_features': features_df.select_dtypes(include=[np.number]).columns.tolist(),
                'categorical_features': features_df.select_dtypes(include=['object']).columns.tolist()
            }
        }

        if not labels_df.empty:
            report['labels'] = {
                'total_records': len(labels_df),
                'label_distribution': labels_df['result'].value_counts().to_dict() if 'result' in labels_df.columns else {}
            }

        # Validation checks
        report['validation_checks'] = {
            'has_required_fields': all(field in features_df.columns for field in ['id']),
            'no_duplicate_ids': features_df['id'].nunique() == len(features_df) if 'id' in features_df.columns else False,
            'consistent_record_count': len(features_df) == len(labels_df) if not labels_df.empty else True
        }

        return report

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate file hash for versioning"""
        if not file_path or not file_path.exists():
            return None

        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()


def main():
    """CLI interface for the ML ingestion service"""
    parser = argparse.ArgumentParser(description='Football ML Data Ingestion Service')
    parser.add_argument('--input', required=True, help='Input raw data directory')
    parser.add_argument('--output', required=True, help='Output ML-ready data directory')
    parser.add_argument('--config', help='JSON configuration file path')

    args = parser.parse_args()

    # Load config if provided
    config = {}
    if args.config and Path(args.config).exists():
        with open(args.config) as f:
            config = json.load(f)

    # Run ingestion
    try:
        ingestor = MLDataIngestor(config)
        metadata = ingestor.ingest_and_prepare(args.input, args.output, config)

        logger.info("✅ ML data ingestion completed successfully!")
        logger.info(f"Features: {metadata['num_feature_records']} records")
        logger.info(f"Labels: {metadata['num_label_records']} records")
        logger.info(f"Output: {args.output}")

        sys.exit(0)

    except Exception as e:
        logger.error(f"❌ Ingestion failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()