#!/usr/bin/env python3
"""
🚀 API DATA COLLECTOR - Collect fresh data from integrated APIs
Uses the existing FastAPI endpoints to gather live data before rate limits reset
Focus: Real-time data, current odds, live matches, fresh predictions
"""

import requests
import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class APIDataCollector:
    """Collect data from our integrated FastAPI endpoints"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.collected_data = {}
        self.output_dir = Path("api_fresh_data")
        self.output_dir.mkdir(exist_ok=True)

    def collect_all_fresh_data(self):
        """Collect all available fresh data from APIs"""
        logger.info("🚀 Starting fresh API data collection")
        start_time = datetime.now()

        # First, trigger syncs to get fresh data
        self._trigger_data_syncs()

        # Wait for syncs to complete
        time.sleep(10)

        # Collect data from all endpoints
        self._collect_matches_data()
        self._collect_teams_data()
        self._collect_odds_data()
        self._collect_predictions_data()
        self._collect_ml_data()

        # Process and save
        self._process_and_save()

        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Collection completed in {duration:.1f}s")

        return self.collected_data

    def _trigger_data_syncs(self):
        """Trigger data synchronization from external APIs"""
        logger.info("🔄 Triggering data syncs...")

        sync_endpoints = [
            '/api/v1/sync/matches',
            '/api/v1/sync/odds',
            '/api/v1/sync/predictions'
        ]

        for endpoint in sync_endpoints:
            try:
                response = self.session.post(f"{self.base_url}{endpoint}")
                if response.status_code == 200:
                    logger.info(f"✅ Triggered: {endpoint}")
                else:
                    logger.warning(f"⚠️ Failed to trigger {endpoint}: {response.status_code}")
            except Exception as e:
                logger.error(f"❌ Error triggering {endpoint}: {e}")

    def _collect_matches_data(self):
        """Collect matches data"""
        logger.info("⚽ Collecting matches data...")

        endpoints = [
            '/api/v1/matches/today',
            '/api/v1/matches/',
            '/api/v1/matches/competition/BSA',  # Brasileirão if available
            '/api/v1/matches/competition/PD',   # La Liga
            '/api/v1/matches/competition/PL',   # Premier League
        ]

        matches_data = []

        for endpoint in endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                if response.status_code == 200:
                    data = response.json()

                    # Handle different response formats
                    if 'matches' in data:
                        matches_data.extend(data['matches'])
                        logger.info(f"✅ {endpoint}: {len(data['matches'])} matches")
                    elif isinstance(data, list):
                        matches_data.extend(data)
                        logger.info(f"✅ {endpoint}: {len(data)} matches")
                else:
                    logger.warning(f"⚠️ {endpoint}: HTTP {response.status_code}")
            except Exception as e:
                logger.error(f"❌ Error collecting {endpoint}: {e}")

        self.collected_data['matches'] = matches_data
        logger.info(f"📊 Total matches collected: {len(matches_data)}")

    def _collect_teams_data(self):
        """Collect teams data and statistics"""
        logger.info("🏆 Collecting teams data...")

        teams_data = []
        team_stats_data = []

        try:
            # Get all teams
            response = self.session.get(f"{self.base_url}/api/v1/teams/")
            if response.status_code == 200:
                teams = response.json()
                if isinstance(teams, list):
                    teams_data = teams
                    logger.info(f"✅ Collected {len(teams)} teams")

                    # Get statistics for each team (sample first 20 to respect rate limits)
                    for team in teams[:20]:
                        team_id = team.get('id')
                        if team_id:
                            try:
                                stats_response = self.session.get(f"{self.base_url}/api/v1/teams/{team_id}/statistics")
                                if stats_response.status_code == 200:
                                    stats = stats_response.json()
                                    stats['team_id'] = team_id
                                    stats['team_name'] = team.get('name')
                                    team_stats_data.append(stats)

                                time.sleep(0.1)  # Small delay to be respectful
                            except Exception as e:
                                logger.debug(f"Could not get stats for team {team_id}: {e}")

        except Exception as e:
            logger.error(f"❌ Error collecting teams: {e}")

        self.collected_data['teams'] = teams_data
        self.collected_data['team_statistics'] = team_stats_data
        logger.info(f"📊 Teams: {len(teams_data)}, Stats: {len(team_stats_data)}")

    def _collect_odds_data(self):
        """Collect odds and betting data"""
        logger.info("💰 Collecting odds data...")

        odds_data = []

        try:
            # Get current sports with odds
            response = self.session.get(f"{self.base_url}/api/v1/odds/sports")
            if response.status_code == 200:
                sports = response.json()
                logger.info(f"✅ Available sports: {len(sports) if isinstance(sports, list) else 'N/A'}")

                # Get odds for football/soccer
                if isinstance(sports, list):
                    for sport in sports[:3]:  # Limit to first 3 sports
                        sport_key = sport.get('key', sport) if isinstance(sport, dict) else sport
                        try:
                            odds_response = self.session.get(f"{self.base_url}/api/v1/odds/current/{sport_key}")
                            if odds_response.status_code == 200:
                                sport_odds = odds_response.json()
                                if isinstance(sport_odds, list):
                                    odds_data.extend(sport_odds)
                                    logger.info(f"✅ {sport_key}: {len(sport_odds)} odds")

                            time.sleep(0.2)  # Rate limiting
                        except Exception as e:
                            logger.debug(f"Could not get odds for {sport_key}: {e}")

        except Exception as e:
            logger.error(f"❌ Error collecting odds: {e}")

        self.collected_data['odds'] = odds_data
        logger.info(f"📊 Total odds collected: {len(odds_data)}")

    def _collect_predictions_data(self):
        """Collect predictions data"""
        logger.info("🔮 Collecting predictions data...")

        predictions_data = []

        endpoints = [
            '/api/v1/predictions/',
            '/api/v1/predictions/combinations/today',
            '/api/v1/predictions/performance/stats'
        ]

        for endpoint in endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        predictions_data.extend(data)
                        logger.info(f"✅ {endpoint}: {len(data)} predictions")
                    elif isinstance(data, dict):
                        predictions_data.append(data)
                        logger.info(f"✅ {endpoint}: prediction data")
                else:
                    logger.warning(f"⚠️ {endpoint}: HTTP {response.status_code}")
            except Exception as e:
                logger.error(f"❌ Error collecting {endpoint}: {e}")

        self.collected_data['predictions'] = predictions_data
        logger.info(f"📊 Total predictions collected: {len(predictions_data)}")

    def _collect_ml_data(self):
        """Collect ML system data and status"""
        logger.info("🤖 Collecting ML data...")

        ml_data = {}

        endpoints = [
            '/api/v1/ml/system/status',
            '/api/v1/ml/models/info',
            '/api/v1/ml/training/reports',
            '/api/v1/ml-real/system/status',
            '/api/v1/ml-real/teams/supported'
        ]

        for endpoint in endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                if response.status_code == 200:
                    data = response.json()
                    endpoint_key = endpoint.split('/')[-1]
                    ml_data[endpoint_key] = data
                    logger.info(f"✅ {endpoint}: ML data collected")
                else:
                    logger.warning(f"⚠️ {endpoint}: HTTP {response.status_code}")
            except Exception as e:
                logger.error(f"❌ Error collecting {endpoint}: {e}")

        self.collected_data['ml_data'] = ml_data
        logger.info(f"📊 ML data components: {len(ml_data)}")

    def _process_and_save(self):
        """Process and save collected data"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Save raw data
        raw_file = self.output_dir / f"api_data_raw_{timestamp}.json"
        with open(raw_file, 'w', encoding='utf-8') as f:
            json.dump(self.collected_data, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"💾 Raw data saved: {raw_file}")

        # Process matches for ML pipeline
        if 'matches' in self.collected_data:
            matches_df = pd.DataFrame(self.collected_data['matches'])

            if not matches_df.empty:
                # Convert to ML-ready format
                ml_matches = []
                for _, match in matches_df.iterrows():
                    if pd.notna(match.get('home_score')) and pd.notna(match.get('away_score')):
                        # Only include matches with results
                        # Handle both dict and string formats for team data
                        home_team_data = match.get('home_team', {})
                        away_team_data = match.get('away_team', {})

                        home_team_name = (home_team_data.get('name', 'Unknown') if isinstance(home_team_data, dict)
                                         else str(home_team_data))
                        away_team_name = (away_team_data.get('name', 'Unknown') if isinstance(away_team_data, dict)
                                         else str(away_team_data))

                        ml_match = {
                            'home_team': home_team_name,
                            'away_team': away_team_name,
                            'home_score': match.get('home_score'),
                            'away_score': match.get('away_score'),
                            'total_goals': match.get('home_score', 0) + match.get('away_score', 0),
                            'result': self._determine_result(match.get('home_score'), match.get('away_score')),
                            'league': match.get('league', 'Unknown'),
                            'source': 'api_fresh',
                            'match_date': match.get('match_date'),
                            'status': match.get('status')
                        }
                        ml_matches.append(ml_match)

                if ml_matches:
                    ml_file = self.output_dir / f"matches_ml_ready_{timestamp}.csv"
                    pd.DataFrame(ml_matches).to_csv(ml_file, index=False)
                    logger.info(f"🔧 ML-ready matches saved: {ml_file} ({len(ml_matches)} matches)")

        # Process teams data
        if 'team_statistics' in self.collected_data and self.collected_data['team_statistics']:
            stats_df = pd.DataFrame(self.collected_data['team_statistics'])
            stats_file = self.output_dir / f"team_stats_{timestamp}.csv"
            stats_df.to_csv(stats_file, index=False)
            logger.info(f"📊 Team statistics saved: {stats_file}")

        # Summary report
        self._generate_summary_report(timestamp)

    def _determine_result(self, home_score, away_score):
        """Determine match result"""
        if pd.isna(home_score) or pd.isna(away_score):
            return None

        if home_score > away_score:
            return 'home_win'
        elif away_score > home_score:
            return 'away_win'
        else:
            return 'draw'

    def _generate_summary_report(self, timestamp):
        """Generate collection summary report"""
        summary = {
            'collection_timestamp': timestamp,
            'total_data_points': sum(len(data) if isinstance(data, list) else 1 for data in self.collected_data.values()),
            'data_categories': list(self.collected_data.keys()),
            'matches_total': len(self.collected_data.get('matches', [])),
            'matches_with_results': len([m for m in self.collected_data.get('matches', [])
                                       if m.get('home_score') is not None]),
            'teams_total': len(self.collected_data.get('teams', [])),
            'team_stats': len(self.collected_data.get('team_statistics', [])),
            'odds_entries': len(self.collected_data.get('odds', [])),
            'predictions': len(self.collected_data.get('predictions', [])),
            'ml_status': bool(self.collected_data.get('ml_data', {}))
        }

        summary_file = self.output_dir / f"summary_{timestamp}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, default=str)

        logger.info(f"📋 Summary report saved: {summary_file}")

        # Print summary to console
        print("\n" + "="*60)
        print("🚀 API DATA COLLECTION SUMMARY")
        print("="*60)
        print(f"📅 Timestamp: {timestamp}")
        print(f"📊 Data points: {summary['total_data_points']}")
        print(f"⚽ Matches: {summary['matches_total']} (with results: {summary['matches_with_results']})")
        print(f"🏆 Teams: {summary['teams_total']} (with stats: {summary['team_stats']})")
        print(f"💰 Odds: {summary['odds_entries']}")
        print(f"🔮 Predictions: {summary['predictions']}")
        print(f"🤖 ML system: {'Active' if summary['ml_status'] else 'Inactive'}")
        print("="*60)

def main():
    """Main entry point"""
    collector = APIDataCollector()

    try:
        data = collector.collect_all_fresh_data()

        print("✅ Fresh API data collection completed successfully!")
        print("🎯 Ready to integrate with ML pipeline")

    except Exception as e:
        logger.error(f"❌ Collection failed: {e}")
        raise

if __name__ == "__main__":
    main()