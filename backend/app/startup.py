import asyncio
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.services.scheduler import football_scheduler
from app.services.data_synchronizer import data_synchronizer
from app.services.ticket_scheduler import get_scheduler as get_ticket_scheduler
from app.core.redis import redis_client
from app.core.scheduler import start_scheduler as start_automated_scheduler, stop_scheduler as stop_automated_scheduler

logger = logging.getLogger(__name__)

class FootballAnalyticsStartup:
    """
    Startup manager for the Football Analytics system.
    Handles initialization of all background services and data synchronization.
    """

    def __init__(self):
        self.scheduler_started = False
        self.ticket_scheduler_started = False
        self.automated_scheduler_started = False
        self.initial_sync_completed = False

    async def initialize_system(self):
        """
        Initialize the entire football analytics system.
        This should be called when the application starts.
        """
        logger.info("🚀 Initializing Football Analytics System...")

        try:
            # Step 1: Check Redis connectivity
            await self._check_redis_connection()

            # Step 2: Perform initial data sync (if needed)
            await self._perform_initial_sync()

            # Step 3: Start the automated scheduler
            await self._start_scheduler()

            # Step 4: Store startup status
            await self._store_startup_status()

            logger.info("✅ Football Analytics System initialized successfully!")

        except Exception as e:
            logger.error(f"❌ Failed to initialize system: {str(e)}")
            raise

    async def shutdown_system(self):
        """
        Gracefully shutdown the system.
        This should be called when the application shuts down.
        """
        logger.info("⏹️ Shutting down Football Analytics System...")

        try:
            # Stop the data synchronization scheduler
            if self.scheduler_started:
                await football_scheduler.stop()
                self.scheduler_started = False

            # Stop the ticket analysis scheduler
            if self.ticket_scheduler_started:
                ticket_scheduler = get_ticket_scheduler()
                ticket_scheduler.stop()
                self.ticket_scheduler_started = False
                logger.info("✅ Ticket analysis scheduler stopped")

            # Stop the automated pipeline scheduler
            if self.automated_scheduler_started:
                stop_automated_scheduler()
                self.automated_scheduler_started = False
                logger.info("✅ Automated pipeline scheduler stopped")

            # Clear startup status
            await redis_client.delete("system_startup_status")

            logger.info("✅ Football Analytics System shutdown complete")

        except Exception as e:
            logger.error(f"❌ Error during shutdown: {str(e)}")

    async def _check_redis_connection(self):
        """Check if Redis is accessible"""
        import os

        # Modo de desenvolvimento sem Redis
        if os.getenv("DEV_MODE_NO_REDIS", "false").lower() == "true":
            logger.info("🔧 DEV MODE: Pulando verificação do Redis")
            return

        try:
            await redis_client.ping()
            logger.info("✅ Redis connection verified")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {str(e)}")
            raise Exception("Redis is not accessible. Please check your Redis server.")

    async def _perform_initial_sync(self):
        """Perform initial data synchronization if needed"""
        import os

        # Modo de desenvolvimento sem Redis
        if os.getenv("DEV_MODE_NO_REDIS", "false").lower() == "true":
            logger.info("🔧 DEV MODE: Pulando sincronização inicial")
            return

        try:
            # Check if we've done an initial sync recently
            last_sync = await redis_client.get("last_full_sync")

            if not last_sync:
                logger.info("🔄 Performing initial data synchronization...")

                # Start with a quick sync to get immediate data
                quick_result = await data_synchronizer.quick_sync()
                logger.info(f"✅ Quick sync completed: {quick_result}")

                # Schedule a full sync to run in the background
                asyncio.create_task(self._background_full_sync())

                self.initial_sync_completed = True
                logger.info("✅ Initial synchronization initiated")
            else:
                logger.info("ℹ️ Recent sync found, skipping initial sync")
                self.initial_sync_completed = True

        except Exception as e:
            logger.error(f"❌ Initial sync failed: {str(e)}")
            # Don't raise here - we can continue without initial sync
            # The scheduler will handle regular syncing

    async def _background_full_sync(self):
        """Run a full sync in the background"""
        try:
            logger.info("🔄 Running background full sync...")
            result = await data_synchronizer.full_sync()
            logger.info(f"✅ Background full sync completed: {result}")
        except Exception as e:
            logger.error(f"❌ Background full sync failed: {str(e)}")

    async def _start_scheduler(self):
        """Start the automated data synchronization scheduler"""
        try:
            await football_scheduler.start()
            self.scheduler_started = True
            logger.info("✅ Automated scheduler started")
        except Exception as e:
            logger.error(f"❌ Failed to start scheduler: {str(e)}")
            # Don't raise here - manual sync is still possible

        # Start ticket analysis scheduler
        try:
            ticket_scheduler = get_ticket_scheduler()
            ticket_scheduler.start()
            self.ticket_scheduler_started = True
            logger.info("✅ Ticket analysis scheduler started")
        except Exception as e:
            logger.error(f"❌ Failed to start ticket scheduler: {str(e)}")
            # Don't raise here - manual ticket analysis is still possible

        # Start automated pipeline scheduler (NOVO - importação, live updates, predictions)
        try:
            start_automated_scheduler()
            self.automated_scheduler_started = True
            logger.info("✅ Automated pipeline scheduler started")
        except Exception as e:
            logger.error(f"❌ Failed to start automated pipeline scheduler: {str(e)}")
            # Don't raise here - manual execution is still possible

    async def _store_startup_status(self):
        """Store system startup status in Redis"""
        try:
            startup_status = {
                "initialized_at": datetime.now().isoformat(),
                "scheduler_started": self.scheduler_started,
                "ticket_scheduler_started": self.ticket_scheduler_started,
                "initial_sync_completed": self.initial_sync_completed,
                "version": "1.0.0"
            }

            await redis_client.setex(
                "system_startup_status",
                3600,  # 1 hour
                str(startup_status)
            )

        except Exception as e:
            logger.error(f"❌ Failed to store startup status: {str(e)}")

    async def get_system_status(self):
        """Get current system status"""
        try:
            startup_status = await redis_client.get("system_startup_status")
            scheduler_status = football_scheduler.get_job_status()
            health_status = await data_synchronizer.health_check()

            # Get ticket scheduler status
            ticket_scheduler_status = None
            try:
                ticket_scheduler = get_ticket_scheduler()
                ticket_scheduler_status = ticket_scheduler.get_stats()
            except Exception as e:
                logger.error(f"Failed to get ticket scheduler status: {e}")

            return {
                "startup_status": startup_status.decode() if startup_status else None,
                "scheduler": scheduler_status,
                "ticket_scheduler": ticket_scheduler_status,
                "health": health_status,
                "is_ready": self.scheduler_started and self.initial_sync_completed
            }

        except Exception as e:
            logger.error(f"❌ Failed to get system status: {str(e)}")
            return {
                "error": str(e),
                "is_ready": False
            }

# Global instance
startup_manager = FootballAnalyticsStartup()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.
    Handles startup and shutdown of the football analytics system.
    """
    # Startup
    try:
        await startup_manager.initialize_system()
        yield
    finally:
        # Shutdown
        await startup_manager.shutdown_system()

# Startup functions for manual initialization
async def manual_startup():
    """Manually start the system (for testing or manual deployment)"""
    await startup_manager.initialize_system()

async def manual_shutdown():
    """Manually shutdown the system (for testing or manual deployment)"""
    await startup_manager.shutdown_system()

# Health check function
async def system_health_check():
    """Comprehensive system health check"""
    return await startup_manager.get_system_status()