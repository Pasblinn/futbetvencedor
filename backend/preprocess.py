#!/usr/bin/env python3
"""
🔧 FEATURE ENGINEERING PIPELINE
Advanced feature engineering for football analytics ML models.
Focuses on creating meaningful features from scraped football data.
"""

import numpy as np
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FootballFeatureEngineer:
    """Advanced feature engineering for football data"""

    def __init__(self, config: Dict = None):
        self.config = config or self._default_config()

    def _default_config(self) -> Dict:
        """Default configuration for feature engineering"""
        return {
            'form_windows': [3, 5, 10],  # Recent form analysis windows
            'rolling_windows': [5, 10, 15],  # Rolling statistics windows
            'head_to_head_limit': 10,  # Max head-to-head matches to consider
            'season_weight_decay': 0.1,  # Weight decay for historical seasons
            'min_matches_threshold': 3,  # Minimum matches for reliable stats
            'elo_k_factor': 32,  # ELO rating K-factor
            'home_advantage': 0.1,  # Home advantage factor
            'position_weights': {  # Position-based feature weights
                'GK': 0.1, 'DEF': 0.7, 'MID': 0.8, 'ATT': 1.0
            }
        }

    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Main feature engineering pipeline

        Args:
            df: Input DataFrame with football data

        Returns:
            DataFrame with engineered features
        """
        logger.info(f"Starting feature engineering for {len(df)} records...")

        if len(df) == 0:
            return df

        # Create a copy to avoid modifying original
        features_df = df.copy()

        # Basic preprocessing
        features_df = self._preprocess_basic_fields(features_df)

        # Team-level features
        features_df = self._engineer_team_features(features_df)

        # Match-level features
        features_df = self._engineer_match_features(features_df)

        # Temporal features
        features_df = self._engineer_temporal_features(features_df)

        # Advanced statistical features
        features_df = self._engineer_advanced_features(features_df)

        # ELO ratings
        features_df = self._engineer_elo_ratings(features_df)

        # Head-to-head features
        features_df = self._engineer_head_to_head_features(features_df)

        # Form and momentum features
        features_df = self._engineer_form_features(features_df)

        # Market/odds features
        features_df = self._engineer_market_features(features_df)

        logger.info(f"Feature engineering completed. Output: {len(features_df)} records, {len(features_df.columns)} features")

        return features_df

    def _preprocess_basic_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """Preprocess and standardize basic fields"""
        logger.info("Preprocessing basic fields...")

        # Ensure required columns exist
        required_cols = ['team', 'competition', 'season']
        for col in required_cols:
            if col not in df.columns:
                df[col] = 'unknown'

        # Standardize team names
        if 'team' in df.columns:
            df['team'] = df['team'].str.strip().str.title()

        # Parse match dates
        if 'match_date' in df.columns:
            df['match_date'] = pd.to_datetime(df['match_date'], errors='coerce')
            df['match_date'] = df['match_date'].fillna(datetime.now())

        # Create team-season identifiers
        df['team_season'] = df['team'] + '_' + df['season'].astype(str)

        # Home/Away indicator
        if 'home' not in df.columns:
            df['home'] = True  # Default assumption

        return df

    def _engineer_team_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engineer team-level statistical features"""
        logger.info("Engineering team features...")

        if 'team' not in df.columns:
            return df

        # Basic team statistics
        team_stats = self._calculate_team_statistics(df)
        df = df.merge(team_stats, on='team', how='left', suffixes=('', '_team'))

        # Seasonal team performance
        if 'season' in df.columns:
            seasonal_stats = self._calculate_seasonal_statistics(df)
            df = df.merge(seasonal_stats, on=['team', 'season'], how='left', suffixes=('', '_season'))

        # Home/Away splits
        home_away_stats = self._calculate_home_away_splits(df)
        df = df.merge(home_away_stats, on=['team', 'home'], how='left', suffixes=('', '_venue'))

        return df

    def _engineer_match_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engineer match-level features"""
        logger.info("Engineering match features...")

        # Match context features
        df = self._add_match_context_features(df)

        # Competition features
        df = self._add_competition_features(df)

        # Referee features (if available)
        if 'referee' in df.columns:
            df = self._add_referee_features(df)

        return df

    def _engineer_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engineer time-based features"""
        logger.info("Engineering temporal features...")

        if 'match_date' not in df.columns:
            return df

        # Day of week
        df['day_of_week'] = df['match_date'].dt.dayofweek
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)

        # Month and season period
        df['month'] = df['match_date'].dt.month
        df['quarter'] = df['match_date'].dt.quarter

        # Days since last match
        if 'team' in df.columns:
            df = df.sort_values(['team', 'match_date'])
            df['days_since_last_match'] = df.groupby('team')['match_date'].diff().dt.days

        return df

    def _engineer_advanced_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engineer advanced statistical features"""
        logger.info("Engineering advanced features...")

        # Rolling statistics
        for window in self.config['rolling_windows']:
            df = self._add_rolling_statistics(df, window)

        # Momentum indicators
        df = self._add_momentum_indicators(df)

        # Performance ratios and efficiency metrics
        df = self._add_efficiency_metrics(df)

        return df

    def _engineer_elo_ratings(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engineer ELO rating system"""
        logger.info("Engineering ELO ratings...")

        if not all(col in df.columns for col in ['team', 'match_date']):
            return df

        # Initialize ELO ratings
        elo_ratings = {}
        df = df.sort_values(['match_date', 'team'])

        elo_history = []

        for idx, row in df.iterrows():
            team = row['team']
            date = row['match_date']

            # Initialize team ELO if not exists
            if team not in elo_ratings:
                elo_ratings[team] = 1500  # Standard starting ELO

            current_elo = elo_ratings[team]

            # Update ELO based on match result if available
            if 'result' in row and pd.notna(row['result']):
                opponent = row.get('opponent', 'unknown')
                if opponent != 'unknown' and opponent in elo_ratings:
                    opponent_elo = elo_ratings[opponent]

                    # Calculate expected score
                    expected_score = 1 / (1 + 10 ** ((opponent_elo - current_elo) / 400))

                    # Actual score
                    actual_score = 1 if row['result'] == 'W' else 0.5 if row['result'] == 'D' else 0

                    # Update ELO
                    new_elo = current_elo + self.config['elo_k_factor'] * (actual_score - expected_score)
                    elo_ratings[team] = new_elo

            elo_history.append({
                'index': idx,
                'team': team,
                'elo_rating': current_elo,
                'date': date
            })

        # Merge ELO ratings back
        elo_df = pd.DataFrame(elo_history).set_index('index')
        df['elo_rating'] = elo_df['elo_rating']

        return df

    def _engineer_head_to_head_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engineer head-to-head historical features"""
        logger.info("Engineering head-to-head features...")

        if not all(col in df.columns for col in ['team', 'opponent']):
            # Try to infer opponent from match structure
            if all(col in df.columns for col in ['home_team', 'away_team']):
                df['opponent'] = df.apply(
                    lambda x: x['away_team'] if x['team'] == x['home_team'] else x['home_team'],
                    axis=1
                )
            else:
                return df

        # Calculate head-to-head statistics
        h2h_features = []

        for idx, row in df.iterrows():
            team = row['team']
            opponent = row['opponent']

            if pd.isna(opponent) or opponent == 'unknown':
                h2h_features.append({})
                continue

            # Filter historical matches between these teams
            h2h_matches = df[
                ((df['team'] == team) & (df['opponent'] == opponent)) |
                ((df['team'] == opponent) & (df['opponent'] == team))
            ]

            if 'match_date' in df.columns and pd.notna(row['match_date']):
                h2h_matches = h2h_matches[h2h_matches['match_date'] < row['match_date']]

            h2h_matches = h2h_matches.tail(self.config['head_to_head_limit'])

            # Calculate H2H statistics
            h2h_stats = self._calculate_h2h_statistics(h2h_matches, team, opponent)
            h2h_features.append(h2h_stats)

        # Convert to DataFrame and merge
        h2h_df = pd.DataFrame(h2h_features)
        df = pd.concat([df, h2h_df], axis=1)

        return df

    def _engineer_form_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engineer form and momentum features"""
        logger.info("Engineering form features...")

        if 'team' not in df.columns:
            return df

        df = df.sort_values(['team', 'match_date'])

        for window in self.config['form_windows']:
            form_features = df.groupby('team').apply(
                lambda x: self._calculate_form_features(x, window)
            ).reset_index(drop=True)

            # Merge form features
            form_df = pd.DataFrame(form_features.tolist(), index=form_features.index)
            df = pd.concat([df, form_df], axis=1)

        return df

    def _engineer_market_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engineer betting/market-based features"""
        logger.info("Engineering market features...")

        # Odds-based features
        odds_columns = [col for col in df.columns if 'odds' in col.lower()]

        for col in odds_columns:
            if df[col].dtype in ['float64', 'int64']:
                # Implied probability
                df[f'{col}_prob'] = 1 / df[col].replace(0, np.nan)

                # Value indicators
                df[f'{col}_value'] = df[col] * df.get('win_prob', 0.5) - 1

        # Market efficiency indicators
        if len(odds_columns) >= 3:  # 1X2 odds available
            total_prob = sum(1 / df[col].replace(0, np.nan) for col in odds_columns[:3])
            df['market_margin'] = total_prob - 1

        return df

    def _calculate_team_statistics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate comprehensive team statistics"""
        stats_list = []

        for team in df['team'].unique():
            team_data = df[df['team'] == team]

            if len(team_data) < self.config['min_matches_threshold']:
                continue

            stats = {'team': team}

            # Basic statistics
            if 'goals_for' in team_data.columns:
                stats.update({
                    'goals_for_avg': team_data['goals_for'].mean(),
                    'goals_for_std': team_data['goals_for'].std(),
                    'goals_for_total': team_data['goals_for'].sum()
                })

            if 'goals_against' in team_data.columns:
                stats.update({
                    'goals_against_avg': team_data['goals_against'].mean(),
                    'goals_against_std': team_data['goals_against'].std(),
                    'goals_against_total': team_data['goals_against'].sum()
                })

            # Win rate
            if 'result' in team_data.columns:
                result_counts = team_data['result'].value_counts()
                total_matches = len(team_data)
                stats.update({
                    'win_rate': result_counts.get('W', 0) / total_matches,
                    'draw_rate': result_counts.get('D', 0) / total_matches,
                    'loss_rate': result_counts.get('L', 0) / total_matches
                })

            # xG statistics
            if 'xg' in team_data.columns:
                stats.update({
                    'xg_avg': team_data['xg'].mean(),
                    'xg_total': team_data['xg'].sum()
                })

            stats_list.append(stats)

        return pd.DataFrame(stats_list)

    def _calculate_seasonal_statistics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate seasonal team statistics"""
        return df.groupby(['team', 'season']).agg({
            col: ['mean', 'sum'] for col in df.select_dtypes(include=[np.number]).columns
        }).round(3).reset_index()

    def _calculate_home_away_splits(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate home/away performance splits"""
        stats_list = []

        for team in df['team'].unique():
            for is_home in [True, False]:
                team_venue_data = df[(df['team'] == team) & (df['home'] == is_home)]

                if len(team_venue_data) == 0:
                    continue

                stats = {
                    'team': team,
                    'home': is_home,
                    'matches_played': len(team_venue_data)
                }

                # Venue-specific statistics
                for col in ['goals_for', 'goals_against', 'xg']:
                    if col in team_venue_data.columns:
                        stats[f'{col}_venue_avg'] = team_venue_data[col].mean()

                if 'result' in team_venue_data.columns:
                    result_counts = team_venue_data['result'].value_counts()
                    stats['win_rate_venue'] = result_counts.get('W', 0) / len(team_venue_data)

                stats_list.append(stats)

        return pd.DataFrame(stats_list)

    def _add_match_context_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add match context features"""
        # Competition importance weight
        competition_weights = {
            'champions_league': 1.5,
            'europa_league': 1.3,
            'premier_league': 1.2,
            'la_liga': 1.2,
            'bundesliga': 1.2,
            'serie_a': 1.2,
            'brasileirao': 1.1,
            'copa_do_brasil': 1.3
        }

        df['competition_weight'] = df['competition'].str.lower().map(competition_weights).fillna(1.0)

        # Match importance (cup finals, derbies, etc.)
        df['is_derby'] = 0  # Placeholder - would need derby definitions
        df['is_final'] = df['competition'].str.contains('final', case=False, na=False).astype(int)

        return df

    def _add_competition_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add competition-specific features"""
        if 'competition' not in df.columns:
            return df

        # Competition encoding
        competitions = df['competition'].unique()
        for comp in competitions:
            df[f'is_{comp.lower()}'] = (df['competition'] == comp).astype(int)

        # Competition stage (if available in competition name)
        df['is_knockout'] = df['competition'].str.contains('cup|final|semi', case=False, na=False).astype(int)

        return df

    def _add_referee_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add referee-based features"""
        # Referee statistics
        ref_stats = df.groupby('referee').agg({
            'goals_for': 'mean',
            'result': lambda x: (x == 'W').mean()
        }).add_suffix('_ref_avg')

        df = df.merge(ref_stats, left_on='referee', right_index=True, how='left')

        return df

    def _add_rolling_statistics(self, df: pd.DataFrame, window: int) -> pd.DataFrame:
        """Add rolling window statistics"""
        if 'team' not in df.columns:
            return df

        df = df.sort_values(['team', 'match_date'])

        # Rolling statistics for numeric columns
        numeric_cols = ['goals_for', 'goals_against', 'xg']
        for col in numeric_cols:
            if col in df.columns:
                df[f'{col}_rolling_{window}'] = df.groupby('team')[col].rolling(
                    window, min_periods=1
                ).mean().reset_index(drop=True)

        # Rolling form
        if 'result' in df.columns:
            df[f'win_rate_rolling_{window}'] = (
                df.groupby('team')['result']
                .rolling(window, min_periods=1)
                .apply(lambda x: (x == 'W').mean())
                .reset_index(drop=True)
            )

        return df

    def _add_momentum_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add momentum and trend indicators"""
        if 'team' not in df.columns:
            return df

        df = df.sort_values(['team', 'match_date'])

        # Recent form trend
        if 'result' in df.columns:
            df['recent_form_points'] = df['result'].map({'W': 3, 'D': 1, 'L': 0})
            df['form_trend'] = (
                df.groupby('team')['recent_form_points']
                .rolling(5, min_periods=1)
                .mean()
                .reset_index(drop=True)
            )

        # Goal difference trend
        if all(col in df.columns for col in ['goals_for', 'goals_against']):
            df['goal_difference'] = df['goals_for'] - df['goals_against']
            df['gd_trend'] = (
                df.groupby('team')['goal_difference']
                .rolling(5, min_periods=1)
                .mean()
                .reset_index(drop=True)
            )

        return df

    def _add_efficiency_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add efficiency and performance ratios"""
        # Goals per game ratios
        if 'goals_for' in df.columns:
            df['goals_per_game'] = df.groupby('team')['goals_for'].transform('mean')

        # xG efficiency
        if all(col in df.columns for col in ['goals_for', 'xg']):
            df['xg_efficiency'] = df['goals_for'] / df['xg'].replace(0, np.nan)

        # Defensive solidity
        if 'goals_against' in df.columns:
            df['defensive_rating'] = 1 / (1 + df.groupby('team')['goals_against'].transform('mean'))

        return df

    def _calculate_h2h_statistics(self, h2h_matches: pd.DataFrame, team: str, opponent: str) -> Dict:
        """Calculate head-to-head statistics"""
        if len(h2h_matches) == 0:
            return {}

        # Team's perspective in H2H
        team_h2h = h2h_matches[h2h_matches['team'] == team]

        stats = {
            'h2h_matches': len(h2h_matches),
            'h2h_team_matches': len(team_h2h)
        }

        if len(team_h2h) > 0:
            # Results from team's perspective
            if 'result' in team_h2h.columns:
                result_counts = team_h2h['result'].value_counts()
                stats.update({
                    'h2h_wins': result_counts.get('W', 0),
                    'h2h_draws': result_counts.get('D', 0),
                    'h2h_losses': result_counts.get('L', 0),
                    'h2h_win_rate': result_counts.get('W', 0) / len(team_h2h)
                })

            # Goals in H2H
            if 'goals_for' in team_h2h.columns:
                stats['h2h_goals_for_avg'] = team_h2h['goals_for'].mean()
            if 'goals_against' in team_h2h.columns:
                stats['h2h_goals_against_avg'] = team_h2h['goals_against'].mean()

        return stats

    def _calculate_form_features(self, team_data: pd.DataFrame, window: int) -> Dict:
        """Calculate form features for a specific window"""
        form_features = []

        for idx in range(len(team_data)):
            start_idx = max(0, idx - window)
            recent_matches = team_data.iloc[start_idx:idx]

            if len(recent_matches) == 0:
                form_features.append({})
                continue

            stats = {}

            # Form string and points
            if 'result' in recent_matches.columns:
                results = recent_matches['result'].tolist()
                stats[f'form_last_{window}'] = ''.join(results[-window:])
                stats[f'points_last_{window}'] = sum(3 if r == 'W' else 1 if r == 'D' else 0 for r in results)

            # Goals in form period
            for col in ['goals_for', 'goals_against']:
                if col in recent_matches.columns:
                    stats[f'{col}_form_{window}'] = recent_matches[col].mean()

            form_features.append(stats)

        return pd.Series(form_features)


def main():
    """Test the feature engineering pipeline"""
    # Create sample data for testing
    sample_data = pd.DataFrame({
        'team': ['Team A', 'Team B', 'Team A', 'Team B'] * 10,
        'opponent': ['Team B', 'Team A', 'Team B', 'Team A'] * 10,
        'competition': ['League'] * 40,
        'season': ['2024'] * 40,
        'match_date': pd.date_range('2024-01-01', periods=40),
        'home': [True, False, False, True] * 10,
        'goals_for': np.random.randint(0, 4, 40),
        'goals_against': np.random.randint(0, 4, 40),
        'result': np.random.choice(['W', 'D', 'L'], 40)
    })

    # Initialize feature engineer
    engineer = FootballFeatureEngineer()

    # Engineer features
    result = engineer.engineer_features(sample_data)

    print(f"Original features: {len(sample_data.columns)}")
    print(f"Engineered features: {len(result.columns)}")
    print("\nNew features:")
    new_features = set(result.columns) - set(sample_data.columns)
    for feature in sorted(new_features):
        print(f"  - {feature}")


if __name__ == '__main__':
    main()