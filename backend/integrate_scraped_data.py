#!/usr/bin/env python3
"""
🔗 INTEGRATION SCRIPT - Scraped Data + Existing ML Pipeline
Enriches existing match data with scraped team statistics for better ML predictions.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScrapedDataIntegrator:
    """Integrates scraped team statistics with existing match data"""

    def __init__(self):
        # Team name mapping for consistency
        self.team_mappings = {
            'RB Bragantino': 'Red Bull Bragantino',
            'Bragantino': 'Red Bull Bragantino'
        }

    def load_scraped_features(self, features_path: str) -> pd.DataFrame:
        """Load and process scraped team statistics"""
        logger.info(f"Loading scraped features from {features_path}")

        features_df = pd.read_parquet(features_path)

        # Clean team names
        features_df['team_clean'] = features_df['equipevde'].str.replace(r'\s*\([^)]*\)', '', regex=True)

        # Apply team name mappings
        features_df['team_clean'] = features_df['team_clean'].replace(self.team_mappings)

        # Select relevant statistics
        team_stats = features_df[[
            'team_clean', 'pts', 'v', 'e', 'd', 'gp', 'gc', 'sg', 'pos'
        ]].rename(columns={
            'team_clean': 'team',
            'pts': 'points',
            'v': 'wins',
            'e': 'draws',
            'd': 'losses',
            'gp': 'goals_for',
            'gc': 'goals_against',
            'sg': 'goal_diff',
            'pos': 'position'
        })

        # Convert goal_diff to numeric, handling + and − symbols
        team_stats['goal_diff'] = (
            team_stats['goal_diff']
            .astype(str)
            .str.replace('+', '', regex=False)
            .str.replace('−', '-', regex=False)  # Unicode minus to ASCII
            .astype(float)
        )

        # Calculate additional metrics
        team_stats['matches_played'] = team_stats['wins'] + team_stats['draws'] + team_stats['losses']
        team_stats['win_rate'] = team_stats['wins'] / team_stats['matches_played']
        team_stats['goals_per_match'] = team_stats['goals_for'] / team_stats['matches_played']
        team_stats['conceded_per_match'] = team_stats['goals_against'] / team_stats['matches_played']
        team_stats['points_per_match'] = team_stats['points'] / team_stats['matches_played']

        logger.info(f"Processed {len(team_stats)} team statistics")
        return team_stats

    def enrich_match_data(
        self,
        matches_df: pd.DataFrame,
        team_stats: pd.DataFrame
    ) -> pd.DataFrame:
        """Enrich match data with team statistics"""
        logger.info("Enriching match data with scraped statistics...")

        enriched_df = matches_df.copy()

        # Merge home team stats
        home_stats = team_stats.add_suffix('_home')
        enriched_df = enriched_df.merge(
            home_stats,
            left_on='home_team',
            right_on='team_home',
            how='left'
        ).drop(columns=['team_home'])

        # Merge away team stats
        away_stats = team_stats.add_suffix('_away')
        enriched_df = enriched_df.merge(
            away_stats,
            left_on='away_team',
            right_on='team_away',
            how='left'
        ).drop(columns=['team_away'])

        # Calculate match-specific features
        enriched_df['position_diff'] = enriched_df['position_home'] - enriched_df['position_away']
        enriched_df['points_diff'] = enriched_df['points_home'] - enriched_df['points_away']
        enriched_df['goal_diff_diff'] = enriched_df['goal_diff_home'] - enriched_df['goal_diff_away']
        enriched_df['win_rate_diff'] = enriched_df['win_rate_home'] - enriched_df['win_rate_away']
        enriched_df['form_diff'] = enriched_df['points_per_match_home'] - enriched_df['points_per_match_away']

        # Calculate team strength indicators
        enriched_df['home_strength'] = (
            enriched_df['win_rate_home'] * 0.4 +
            enriched_df['points_per_match_home'] / 3 * 0.3 +  # Normalize to 0-1
            enriched_df['goals_per_match_home'] / 3 * 0.2 +   # Assume max ~3 goals
            (21 - enriched_df['position_home']) / 20 * 0.1    # Position strength (inverted)
        )

        enriched_df['away_strength'] = (
            enriched_df['win_rate_away'] * 0.4 +
            enriched_df['points_per_match_away'] / 3 * 0.3 +
            enriched_df['goals_per_match_away'] / 3 * 0.2 +
            (21 - enriched_df['position_away']) / 20 * 0.1
        )

        enriched_df['strength_diff'] = enriched_df['home_strength'] - enriched_df['away_strength']

        logger.info(f"Enriched dataset shape: {enriched_df.shape}")
        logger.info(f"New features added: {enriched_df.shape[1] - matches_df.shape[1]}")

        return enriched_df

    def validate_integration(self, enriched_df: pd.DataFrame) -> Dict:
        """Validate the integration results"""
        validation_report = {
            'total_matches': len(enriched_df),
            'matches_with_home_stats': enriched_df['points_home'].notna().sum(),
            'matches_with_away_stats': enriched_df['points_away'].notna().sum(),
            'missing_home_stats': enriched_df['points_home'].isna().sum(),
            'missing_away_stats': enriched_df['points_away'].isna().sum(),
            'feature_count': enriched_df.shape[1],
            'new_feature_names': [
                col for col in enriched_df.columns
                if any(suffix in col for suffix in ['_home', '_away', '_diff'])
            ]
        }

        logger.info("🔍 INTEGRATION VALIDATION:")
        logger.info(f"  ✅ Total matches: {validation_report['total_matches']}")
        logger.info(f"  ✅ Home team stats coverage: {validation_report['matches_with_home_stats']}/{validation_report['total_matches']} ({validation_report['matches_with_home_stats']/validation_report['total_matches']*100:.1f}%)")
        logger.info(f"  ✅ Away team stats coverage: {validation_report['matches_with_away_stats']}/{validation_report['total_matches']} ({validation_report['matches_with_away_stats']/validation_report['total_matches']*100:.1f}%)")
        logger.info(f"  📊 Total features: {validation_report['feature_count']}")

        if validation_report['missing_home_stats'] > 0 or validation_report['missing_away_stats'] > 0:
            logger.warning(f"  ⚠️  Missing stats - Home: {validation_report['missing_home_stats']}, Away: {validation_report['missing_away_stats']}")

        return validation_report

def main():
    """Main integration pipeline"""
    integrator = ScrapedDataIntegrator()

    # Load scraped team statistics
    team_stats = integrator.load_scraped_features('classification_ml/features.parquet')

    # Load existing match data
    logger.info("Loading existing match data...")
    matches_df = pd.read_csv('brasileirao_2024_matches_clean.csv')

    # Enrich match data
    enriched_df = integrator.enrich_match_data(matches_df, team_stats)

    # Validate integration
    validation_report = integrator.validate_integration(enriched_df)

    # Save enriched dataset
    output_path = 'brasileirao_2024_matches_enriched.csv'
    enriched_df.to_csv(output_path, index=False)
    logger.info(f"💾 Saved enriched dataset: {output_path}")

    # Save team statistics separately
    team_stats_path = 'team_statistics_scraped.csv'
    team_stats.to_csv(team_stats_path, index=False)
    logger.info(f"💾 Saved team statistics: {team_stats_path}")

    logger.info("✅ Integration completed successfully!")

    return enriched_df, validation_report

if __name__ == '__main__':
    enriched_df, report = main()