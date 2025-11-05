import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.services.data_synchronizer import data_synchronizer
from app.core.redis import redis_client

logger = logging.getLogger(__name__)

class FootballDataScheduler:
    """
    Automated scheduler for football data synchronization.
    Handles different sync frequencies based on data importance and volatility.
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False

    async def start(self):
        """Start the scheduler with all data sync jobs"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return

        logger.info("🚀 Starting Football Data Scheduler...")

        # Job 1: Full data sync - Daily at 6 AM
        self.scheduler.add_job(
            self._full_sync_job,
            CronTrigger(hour=6, minute=0),
            id="full_sync_daily",
            name="Daily Full Sync",
            replace_existing=True
        )

        # Job 2: Match data sync - Every 2 hours during the day
        self.scheduler.add_job(
            self._match_sync_job,
            CronTrigger(hour="8-23/2"),  # Every 2 hours from 8 AM to 11 PM
            id="match_sync_regular",
            name="Regular Match Sync",
            replace_existing=True
        )

        # Job 3: Quick live sync - Every 5 minutes during match hours
        self.scheduler.add_job(
            self._live_sync_job,
            IntervalTrigger(minutes=5),
            id="live_sync_frequent",
            name="Live Data Sync",
            replace_existing=True
        )

        # Job 4: Odds sync - Every 5 minutes (ODDS SEMPRE FRESCAS!)
        self.scheduler.add_job(
            self._odds_sync_job,
            IntervalTrigger(minutes=5),
            id="odds_sync_regular",
            name="Odds Sync",
            replace_existing=True
        )

        # Job 5: Predictions generation - Every 4 hours
        self.scheduler.add_job(
            self._predictions_job,
            IntervalTrigger(hours=4),
            id="predictions_generation",
            name="Predictions Generation",
            replace_existing=True
        )

        # Job 6: Health check - Every 15 minutes
        self.scheduler.add_job(
            self._health_check_job,
            IntervalTrigger(minutes=15),
            id="health_check",
            name="Health Check",
            replace_existing=True
        )

        # Job 7: Cache cleanup - Daily at 3 AM
        self.scheduler.add_job(
            self._cleanup_job,
            CronTrigger(hour=3, minute=0),
            id="cache_cleanup",
            name="Cache Cleanup",
            replace_existing=True
        )

        # Job 8: Stuck matches cleanup - Every hour
        self.scheduler.add_job(
            self._stuck_matches_cleanup_job,
            IntervalTrigger(hours=1),
            id="stuck_matches_cleanup",
            name="Stuck Matches Cleanup",
            replace_existing=True
        )

        # Start the scheduler
        self.scheduler.start()
        self.is_running = True

        # Log scheduled jobs
        jobs = self.scheduler.get_jobs()
        logger.info(f"📅 Scheduler started with {len(jobs)} jobs:")
        for job in jobs:
            logger.info(f"  - {job.name} (ID: {job.id})")

    async def stop(self):
        """Stop the scheduler"""
        if not self.is_running:
            return

        logger.info("⏹️ Stopping Football Data Scheduler...")
        self.scheduler.shutdown()
        self.is_running = False

    async def _full_sync_job(self):
        """Job for complete data synchronization"""
        logger.info("🔄 Running daily full sync job...")

        try:
            # Mark sync start time
            start_time = datetime.now()
            await redis_client.setex("sync_job_status:full", 3600, "running")

            # Run full sync
            results = await data_synchronizer.full_sync()

            # Log results
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Full sync completed in {duration:.1f}s: {results}")

            # Store sync stats
            await self._store_sync_stats("full_sync", results, duration)

        except Exception as e:
            logger.error(f"❌ Full sync job failed: {str(e)}")
            await redis_client.setex("sync_job_status:full", 300, f"error: {str(e)}")

    async def _match_sync_job(self):
        """Job for regular match data updates"""
        logger.info("⚽ Running match sync job...")

        try:
            start_time = datetime.now()
            await redis_client.setex("sync_job_status:matches", 1800, "running")

            # Sync only matches and related data
            results = {
                "matches": await data_synchronizer._sync_matches(),
                "live_updates": await data_synchronizer._update_live_matches()
            }

            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Match sync completed in {duration:.1f}s: {results}")

            await self._store_sync_stats("match_sync", results, duration)

        except Exception as e:
            logger.error(f"❌ Match sync job failed: {str(e)}")
            await redis_client.setex("sync_job_status:matches", 300, f"error: {str(e)}")

    async def _live_sync_job(self):
        """Job for live data updates during match hours"""
        # Only run during potential match hours (12 PM to 11 PM UTC)
        current_hour = datetime.now().hour
        if not (12 <= current_hour <= 23):
            return

        try:
            start_time = datetime.now()

            # Quick sync for live data
            results = await data_synchronizer.quick_sync()

            duration = (datetime.now() - start_time).total_seconds()

            # Only log if there were updates
            if results.get("live_matches", 0) > 0 or results.get("updated_odds", 0) > 0:
                logger.info(f"⚡ Live sync completed in {duration:.1f}s: {results}")

            await self._store_sync_stats("live_sync", results, duration)

        except Exception as e:
            logger.error(f"❌ Live sync job failed: {str(e)}")

    async def _odds_sync_job(self):
        """Job for odds updates"""
        logger.info("💰 Running odds sync job...")

        try:
            start_time = datetime.now()

            # Sync odds
            odds_count = await data_synchronizer._sync_odds()
            live_odds = await data_synchronizer._update_live_odds()

            results = {
                "new_odds": odds_count,
                "updated_odds": live_odds
            }

            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Odds sync completed in {duration:.1f}s: {results}")

            await self._store_sync_stats("odds_sync", results, duration)

        except Exception as e:
            logger.error(f"❌ Odds sync job failed: {str(e)}")

    async def _predictions_job(self):
        """Job for generating predictions"""
        logger.info("🔮 Running predictions job...")

        try:
            start_time = datetime.now()

            # Generate predictions
            predictions_count = await data_synchronizer._sync_predictions()

            results = {"predictions": predictions_count}

            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Predictions job completed in {duration:.1f}s: {results}")

            await self._store_sync_stats("predictions", results, duration)

        except Exception as e:
            logger.error(f"❌ Predictions job failed: {str(e)}")

    async def _health_check_job(self):
        """Job for health monitoring"""
        try:
            health_status = await data_synchronizer.health_check()

            # Store health status
            await redis_client.setex(
                "system_health",
                900,  # 15 minutes
                str(health_status)
            )

            # Log only if there are issues
            if health_status["overall_status"] != "healthy":
                logger.warning(f"⚠️ System health check: {health_status['overall_status']}")

        except Exception as e:
            logger.error(f"❌ Health check failed: {str(e)}")

    async def _cleanup_job(self):
        """Job for cleaning up old cache and temporary data"""
        logger.info("🧹 Running cleanup job...")

        try:
            # Clear expired cache entries
            # This is handled automatically by Redis TTL, but we can do additional cleanup here

            # Clean old sync stats (keep only last 30 days)
            thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

            # Get all sync stat keys
            sync_keys = await redis_client.keys("sync_stats:*")
            for key in sync_keys:
                key_date = key.decode().split(":")[-1]
                if key_date < thirty_days_ago:
                    await redis_client.delete(key)

            logger.info("✅ Cleanup job completed")

        except Exception as e:
            logger.error(f"❌ Cleanup job failed: {str(e)}")

    async def _stuck_matches_cleanup_job(self):
        """Job for cleaning up matches stuck in LIVE status"""
        logger.info("🔧 Running stuck matches cleanup job...")

        try:
            from app.core.database import SessionLocal
            from app.models import Match
            from sqlalchemy import and_
            from datetime import timezone

            db = SessionLocal()

            try:
                # Find matches stuck in LIVE status for more than 2 hours
                cutoff_time = datetime.now(timezone.utc) - timedelta(hours=2)
                live_statuses = ['LIVE', '1H', '2H', 'HT', 'BT', 'ET', 'P', 'SUSP', 'INT']

                stuck_matches = db.query(Match).filter(
                    and_(
                        Match.status.in_(live_statuses),
                        Match.match_date < cutoff_time
                    )
                ).all()

                if not stuck_matches:
                    logger.info("✅ No stuck matches found")
                    return

                # Fix each stuck match
                fixed_count = 0
                for match in stuck_matches:
                    old_status = match.status
                    match.status = 'FT'
                    db.commit()
                    fixed_count += 1

                    logger.info(
                        f"  Fixed match {match.id}: {match.home_team.name if match.home_team else 'Unknown'} vs "
                        f"{match.away_team.name if match.away_team else 'Unknown'} "
                        f"({old_status} → FT)"
                    )

                logger.info(f"✅ Stuck matches cleanup completed: {fixed_count} matches fixed")

                # Store cleanup stats
                await redis_client.setex(
                    f"stuck_matches_cleanup:{datetime.now().strftime('%Y-%m-%d_%H')}",
                    86400,  # 24 hours
                    str({"fixed_count": fixed_count, "timestamp": datetime.now().isoformat()})
                )

            finally:
                db.close()

        except Exception as e:
            logger.error(f"❌ Stuck matches cleanup job failed: {str(e)}")

    async def _store_sync_stats(self, sync_type: str, results: Dict, duration: float):
        """Store synchronization statistics for monitoring"""
        try:
            date_key = datetime.now().strftime("%Y-%m-%d")
            stats_key = f"sync_stats:{sync_type}:{date_key}"

            stats = {
                "timestamp": datetime.now().isoformat(),
                "duration": duration,
                "results": results,
                "success": results.get("errors", 0) == 0
            }

            # Store stats for 7 days
            await redis_client.setex(stats_key, 604800, str(stats))

        except Exception as e:
            logger.error(f"❌ Failed to store sync stats: {str(e)}")

    def get_job_status(self) -> Dict:
        """Get current status of all scheduled jobs"""
        if not self.is_running:
            return {"status": "stopped", "jobs": []}

        jobs = self.scheduler.get_jobs()
        job_info = []

        for job in jobs:
            job_info.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })

        return {
            "status": "running",
            "jobs": job_info,
            "total_jobs": len(jobs)
        }

    async def trigger_manual_sync(self, sync_type: str = "full") -> Dict:
        """Manually trigger a specific sync type"""
        logger.info(f"🔄 Manual {sync_type} sync triggered...")

        try:
            if sync_type == "full":
                results = await data_synchronizer.full_sync()
            elif sync_type == "quick":
                results = await data_synchronizer.quick_sync()
            elif sync_type == "matches":
                results = {"matches": await data_synchronizer._sync_matches()}
            elif sync_type == "odds":
                results = {"odds": await data_synchronizer._sync_odds()}
            elif sync_type == "predictions":
                results = {"predictions": await data_synchronizer._sync_predictions()}
            else:
                raise ValueError(f"Unknown sync type: {sync_type}")

            logger.info(f"✅ Manual {sync_type} sync completed: {results}")
            return {"success": True, "results": results}

        except Exception as e:
            logger.error(f"❌ Manual {sync_type} sync failed: {str(e)}")
            return {"success": False, "error": str(e)}

# Global scheduler instance
football_scheduler = FootballDataScheduler()