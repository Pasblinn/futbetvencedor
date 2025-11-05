#!/usr/bin/env python3
"""
🔄 CONTINUOUS ML PIPELINE - Automated data collection + ML retraining
Combines all data sources and maintains updated ML models daily

Pipeline Flow:
1. Collect fresh data from APIs (live matches, odds, predictions)
2. Merge with existing enriched dataset
3. Retrain ML models if sufficient new data
4. Update production models
5. Generate performance reports

Designed for: Daily cron job at 6:00 AM
"""

import pandas as pd
import numpy as np
import joblib
from datetime import datetime, timedelta
from pathlib import Path
import logging
import json
import subprocess
import shutil
from typing import Dict, List, Optional, Tuple

# Import our existing modules
from api_data_collector import APIDataCollector
from integrate_scraped_data import ScrapedDataIntegrator
from train_ml_enriched import EnhancedMLTrainer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/continuous_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ContinuousMLPipeline:
    """Continuous ML pipeline for daily data collection and model updates"""

    def __init__(self):
        self.base_dir = Path(".")
        self.data_dir = Path("continuous_data")
        self.models_dir = Path("models/continuous")
        self.reports_dir = Path("reports/continuous")

        # Create directories
        for directory in [self.data_dir, self.models_dir, self.reports_dir, Path("logs")]:
            directory.mkdir(parents=True, exist_ok=True)

        self.current_dataset_path = "brasileirao_2024_matches_enriched.csv"
        self.min_new_matches_for_retrain = 10
        self.performance_threshold = 0.40  # Retrain if performance drops below this

    def run_daily_pipeline(self) -> Dict:
        """Execute the complete daily pipeline"""
        logger.info("🚀 Starting continuous ML pipeline")
        start_time = datetime.now()

        pipeline_results = {
            'start_time': start_time,
            'steps_completed': [],
            'errors': [],
            'data_stats': {},
            'model_performance': {},
            'recommendations': []
        }

        try:
            # Step 1: Collect fresh data from APIs
            logger.info("📡 Step 1: Collecting fresh data from APIs")
            fresh_data = self._collect_fresh_api_data()
            pipeline_results['steps_completed'].append('api_collection')
            pipeline_results['data_stats']['fresh_matches'] = len(fresh_data.get('matches', []))

            # Step 2: Load and merge with existing dataset
            logger.info("🔄 Step 2: Merging with existing dataset")
            merged_dataset = self._merge_with_existing_data(fresh_data)
            pipeline_results['steps_completed'].append('data_merge')
            pipeline_results['data_stats']['total_matches'] = len(merged_dataset)

            # Step 3: Evaluate if retraining is needed
            logger.info("🤔 Step 3: Evaluating retraining necessity")
            should_retrain, retrain_reason = self._should_retrain_models(fresh_data, merged_dataset)
            pipeline_results['retrain_decision'] = {'should_retrain': should_retrain, 'reason': retrain_reason}

            if should_retrain:
                # Step 4: Retrain models
                logger.info("🎯 Step 4: Retraining ML models")
                training_results = self._retrain_models(merged_dataset)
                pipeline_results['steps_completed'].append('model_training')
                pipeline_results['model_performance'] = training_results

                # Step 5: Validate and deploy models
                logger.info("✅ Step 5: Validating and deploying models")
                deployment_success = self._validate_and_deploy_models(training_results)
                pipeline_results['steps_completed'].append('model_deployment')
                pipeline_results['deployment_success'] = deployment_success

            else:
                logger.info("ℹ️ Skipping model retraining - not needed")

            # Step 6: Generate reports
            logger.info("📊 Step 6: Generating reports")
            self._generate_pipeline_reports(pipeline_results, merged_dataset)
            pipeline_results['steps_completed'].append('report_generation')

            # Step 7: Cleanup old data
            self._cleanup_old_data()
            pipeline_results['steps_completed'].append('cleanup')

        except Exception as e:
            logger.error(f"❌ Pipeline failed: {e}")
            pipeline_results['errors'].append(str(e))

        pipeline_results['end_time'] = datetime.now()
        pipeline_results['duration'] = (pipeline_results['end_time'] - start_time).total_seconds()

        logger.info(f"🏁 Pipeline completed in {pipeline_results['duration']:.1f}s")
        return pipeline_results

    def _collect_fresh_api_data(self) -> Dict:
        """Collect fresh data from all API sources"""
        collector = APIDataCollector()

        try:
            fresh_data = collector.collect_all_fresh_data()

            # Save timestamp for tracking
            timestamp_file = self.data_dir / "last_collection.json"
            with open(timestamp_file, 'w') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'matches_collected': len(fresh_data.get('matches', [])),
                    'data_categories': list(fresh_data.keys())
                }, f, indent=2)

            return fresh_data

        except Exception as e:
            logger.error(f"Failed to collect fresh data: {e}")
            return {}

    def _merge_with_existing_data(self, fresh_data: Dict) -> pd.DataFrame:
        """Merge fresh data with existing enriched dataset"""

        # Load existing enriched dataset
        if Path(self.current_dataset_path).exists():
            existing_df = pd.read_csv(self.current_dataset_path)
            logger.info(f"📊 Loaded existing dataset: {len(existing_df)} matches")
        else:
            logger.warning("⚠️ No existing dataset found, using fresh data only")
            existing_df = pd.DataFrame()

        # Process fresh matches if available
        fresh_matches_df = pd.DataFrame()
        if 'matches' in fresh_data and fresh_data['matches']:
            fresh_matches = []

            for match in fresh_data['matches']:
                if (isinstance(match, dict) and
                    match.get('home_score') is not None and
                    match.get('away_score') is not None):

                    # Convert to format compatible with existing dataset
                    home_team_data = match.get('home_team', {})
                    away_team_data = match.get('away_team', {})

                    home_team_name = (home_team_data.get('name', 'Unknown') if isinstance(home_team_data, dict)
                                     else str(home_team_data))
                    away_team_name = (away_team_data.get('name', 'Unknown') if isinstance(away_team_data, dict)
                                     else str(away_team_data))

                    fresh_match = {
                        'home_team': home_team_name,
                        'away_team': away_team_name,
                        'home_score': match.get('home_score'),
                        'away_score': match.get('away_score'),
                        'total_goals': match.get('home_score', 0) + match.get('away_score', 0),
                        'result': self._determine_result(match.get('home_score'), match.get('away_score')),
                        'league': match.get('league', 'Unknown'),
                        'source': 'api_fresh'
                    }
                    fresh_matches.append(fresh_match)

            if fresh_matches:
                fresh_matches_df = pd.DataFrame(fresh_matches)
                logger.info(f"📊 Processed {len(fresh_matches_df)} fresh matches with results")

        # Merge datasets
        if not existing_df.empty and not fresh_matches_df.empty:
            # Remove duplicates based on teams and scores
            merged_df = pd.concat([existing_df, fresh_matches_df], ignore_index=True)
            merged_df = merged_df.drop_duplicates(
                subset=['home_team', 'away_team', 'home_score', 'away_score'],
                keep='first'
            )
            logger.info(f"📊 Merged dataset: {len(merged_df)} total matches")
        elif not existing_df.empty:
            merged_df = existing_df
            logger.info("📊 Using existing dataset only")
        elif not fresh_matches_df.empty:
            merged_df = fresh_matches_df
            logger.info("📊 Using fresh data only")
        else:
            logger.warning("⚠️ No data available for training")
            merged_df = pd.DataFrame()

        # Save merged dataset
        if not merged_df.empty:
            merged_file = self.data_dir / f"merged_dataset_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            merged_df.to_csv(merged_file, index=False)
            logger.info(f"💾 Saved merged dataset: {merged_file}")

        return merged_df

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

    def _should_retrain_models(self, fresh_data: Dict, merged_dataset: pd.DataFrame) -> Tuple[bool, str]:
        """Determine if models should be retrained"""

        # Check 1: Sufficient new data
        new_matches_count = len([m for m in fresh_data.get('matches', [])
                               if m.get('home_score') is not None])

        if new_matches_count >= self.min_new_matches_for_retrain:
            return True, f"Sufficient new matches: {new_matches_count}"

        # Check 2: Time since last training
        try:
            metadata_file = self.models_dir / "metadata_continuous.joblib"
            if metadata_file.exists():
                metadata = joblib.load(metadata_file)
                last_training = datetime.fromisoformat(metadata['training_date'])
                days_since = (datetime.now() - last_training).days

                if days_since >= 7:  # Weekly retraining
                    return True, f"Weekly retraining due: {days_since} days since last training"
            else:
                return True, "No previous training found"
        except Exception as e:
            logger.warning(f"Could not check last training date: {e}")

        # Check 3: Model performance degradation (would need live evaluation)
        # This could be implemented with recent prediction accuracy tracking

        return False, "No retraining needed"

    def _retrain_models(self, dataset: pd.DataFrame) -> Dict:
        """Retrain ML models with merged dataset"""

        if len(dataset) < 50:  # Minimum dataset size
            raise ValueError(f"Dataset too small for training: {len(dataset)} matches")

        # Use enhanced trainer with the merged dataset
        trainer = EnhancedMLTrainer()

        # Prepare features - we need to simulate the enriched format
        # For now, create basic features from available data
        enhanced_data = self._prepare_basic_enhanced_features(dataset)

        # Train models
        X, y, feature_names, processed_df = trainer.prepare_enhanced_features(enhanced_data)
        results, ensemble_score = trainer.train_enhanced_models(X, y, feature_names)

        # Save models to continuous directory
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Copy models to continuous directory
        source_dir = Path("models/enriched_brasileirao")
        if source_dir.exists():
            for model_file in source_dir.glob("*.joblib"):
                dest_file = self.models_dir / f"{model_file.stem}_continuous_{timestamp}.joblib"
                shutil.copy2(model_file, dest_file)

                # Also create symlink to latest
                latest_file = self.models_dir / f"{model_file.stem}_latest.joblib"
                if latest_file.exists():
                    latest_file.unlink()
                latest_file.symlink_to(dest_file.name)

        # Save enhanced metadata
        trainer.save_enhanced_metadata(feature_names, results, processed_df)

        logger.info(f"🎯 Training completed - Best model: {max(results.keys(), key=lambda k: results[k]['test_accuracy'])}")

        return {
            'training_timestamp': timestamp,
            'dataset_size': len(dataset),
            'feature_count': len(feature_names),
            'model_results': results,
            'ensemble_score': ensemble_score,
            'best_model': max(results.keys(), key=lambda k: results[k]['test_accuracy'])
        }

    def _prepare_basic_enhanced_features(self, dataset: pd.DataFrame) -> pd.DataFrame:
        """Prepare basic enhanced features when full team stats aren't available"""

        # Calculate basic team statistics from match history
        enhanced_data = dataset.copy()

        # Add dummy values for missing enriched features
        numeric_features = ['points_home', 'points_away', 'win_rate_home', 'win_rate_away',
                          'goals_for_home', 'goals_for_away', 'goals_against_home', 'goals_against_away']

        for feature in numeric_features:
            if feature not in enhanced_data.columns:
                # Calculate or use default values
                if 'win_rate' in feature:
                    enhanced_data[feature] = 0.5  # Neutral win rate
                elif 'points' in feature:
                    enhanced_data[feature] = 45.0  # Average points
                elif 'goals' in feature:
                    enhanced_data[feature] = 1.5   # Average goals
                else:
                    enhanced_data[feature] = 0.0

        # Calculate derived features
        enhanced_data['points_diff'] = enhanced_data['points_home'] - enhanced_data['points_away']
        enhanced_data['win_rate_diff'] = enhanced_data['win_rate_home'] - enhanced_data['win_rate_away']

        return enhanced_data

    def _validate_and_deploy_models(self, training_results: Dict) -> bool:
        """Validate new models and deploy if they meet criteria"""

        best_accuracy = max(training_results['model_results'].values(),
                          key=lambda x: x['test_accuracy'])['test_accuracy']

        if best_accuracy >= self.performance_threshold:
            logger.info(f"✅ Model validation passed - Accuracy: {best_accuracy:.3f}")

            # Deploy to production (copy to main models directory)
            try:
                prod_dir = Path("models/production")
                prod_dir.mkdir(exist_ok=True)

                for model_file in self.models_dir.glob("*_latest.joblib"):
                    prod_file = prod_dir / model_file.name
                    shutil.copy2(model_file, prod_file)

                logger.info("🚀 Models deployed to production")
                return True

            except Exception as e:
                logger.error(f"❌ Deployment failed: {e}")
                return False
        else:
            logger.warning(f"⚠️ Model validation failed - Accuracy too low: {best_accuracy:.3f}")
            return False

    def _generate_pipeline_reports(self, results: Dict, dataset: pd.DataFrame):
        """Generate comprehensive pipeline reports"""

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Performance report
        performance_report = {
            'pipeline_execution': results,
            'dataset_stats': {
                'total_matches': len(dataset),
                'unique_teams': len(set(dataset['home_team'].tolist() + dataset['away_team'].tolist())) if not dataset.empty else 0,
                'leagues': dataset['league'].unique().tolist() if 'league' in dataset.columns else [],
                'date_range': {
                    'oldest': dataset['match_date'].min() if 'match_date' in dataset.columns else None,
                    'newest': dataset['match_date'].max() if 'match_date' in dataset.columns else None
                }
            },
            'recommendations': self._generate_recommendations(results, dataset)
        }

        # Save reports
        report_file = self.reports_dir / f"pipeline_report_{timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(performance_report, f, indent=2, default=str)

        # Save summary for monitoring
        summary_file = self.reports_dir / "latest_summary.json"
        summary = {
            'last_run': timestamp,
            'status': 'success' if not results['errors'] else 'error',
            'steps_completed': len(results['steps_completed']),
            'total_matches': len(dataset),
            'retrained': results.get('retrain_decision', {}).get('should_retrain', False),
            'best_accuracy': max([r.get('test_accuracy', 0) for r in results.get('model_performance', {}).get('model_results', {}).values()], default=0)
        }

        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        logger.info(f"📊 Reports saved: {report_file}")

    def _generate_recommendations(self, results: Dict, dataset: pd.DataFrame) -> List[str]:
        """Generate actionable recommendations based on pipeline results"""
        recommendations = []

        if results['errors']:
            recommendations.append("🔧 Fix pipeline errors for stable operation")

        if len(dataset) < 500:
            recommendations.append("📈 Collect more historical data for better model performance")

        retrain_info = results.get('retrain_decision', {})
        if not retrain_info.get('should_retrain', False):
            recommendations.append("⏰ Consider manual retraining if new data patterns emerge")

        model_perf = results.get('model_performance', {})
        if model_perf and max([r.get('test_accuracy', 0) for r in model_perf.get('model_results', {}).values()], default=0) < 0.5:
            recommendations.append("🎯 Model performance is low - consider feature engineering improvements")

        return recommendations

    def _cleanup_old_data(self):
        """Clean up old data files to save space"""
        cutoff_date = datetime.now() - timedelta(days=30)

        for data_dir in [self.data_dir, self.reports_dir]:
            for file_path in data_dir.glob("*_*"):
                try:
                    # Extract timestamp from filename
                    parts = file_path.stem.split('_')
                    if len(parts) >= 2 and parts[-2].isdigit() and len(parts[-2]) == 8:
                        file_date = datetime.strptime(parts[-2], '%Y%m%d')
                        if file_date < cutoff_date:
                            file_path.unlink()
                            logger.debug(f"Deleted old file: {file_path}")
                except Exception as e:
                    logger.debug(f"Could not process file {file_path}: {e}")

def main():
    """Main entry point for continuous pipeline"""
    pipeline = ContinuousMLPipeline()

    try:
        results = pipeline.run_daily_pipeline()

        print("\n" + "="*80)
        print("🔄 CONTINUOUS ML PIPELINE SUMMARY")
        print("="*80)
        print(f"⏱️  Duration: {results['duration']:.1f} seconds")
        print(f"✅ Steps completed: {len(results['steps_completed'])}")
        print(f"❌ Errors: {len(results['errors'])}")
        print(f"📊 Total matches: {results['data_stats'].get('total_matches', 0)}")
        print(f"🆕 Fresh matches: {results['data_stats'].get('fresh_matches', 0)}")

        if results.get('retrain_decision', {}).get('should_retrain'):
            print(f"🎯 Models retrained: Yes")
            model_perf = results.get('model_performance', {})
            if model_perf:
                best_acc = max([r.get('test_accuracy', 0) for r in model_perf.get('model_results', {}).values()], default=0)
                print(f"📈 Best accuracy: {best_acc:.3f}")
        else:
            print(f"🎯 Models retrained: No")

        print("="*80)

        if results['errors']:
            print("❌ Errors encountered:")
            for error in results['errors']:
                print(f"   {error}")
        else:
            print("✅ Pipeline completed successfully!")

    except Exception as e:
        logger.error(f"❌ Pipeline execution failed: {e}")
        raise

if __name__ == "__main__":
    main()