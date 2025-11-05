from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Optional
from datetime import datetime

from app.services.data_synchronizer import data_synchronizer
from app.services.scheduler import football_scheduler

router = APIRouter()

@router.post("/full")
async def trigger_full_sync(background_tasks: BackgroundTasks):
    """
    Trigger a complete data synchronization.
    This will sync teams, matches, odds, and generate predictions.
    """
    try:
        # Run sync in background to avoid timeout
        background_tasks.add_task(data_synchronizer.full_sync)

        return {
            "message": "Full synchronization started",
            "status": "running",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start sync: {str(e)}")

@router.post("/quick")
async def trigger_quick_sync():
    """
    Trigger a quick synchronization for live data updates.
    Updates match scores, status, and live odds.
    """
    try:
        results = await data_synchronizer.quick_sync()

        return {
            "message": "Quick sync completed",
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quick sync failed: {str(e)}")

@router.post("/matches")
async def sync_matches(background_tasks: BackgroundTasks):
    """Sync only match data"""
    try:
        background_tasks.add_task(data_synchronizer._sync_matches)

        return {
            "message": "Match synchronization started",
            "status": "running",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync matches: {str(e)}")

@router.post("/odds")
async def sync_odds(background_tasks: BackgroundTasks):
    """Sync betting odds"""
    try:
        background_tasks.add_task(data_synchronizer._sync_odds)

        return {
            "message": "Odds synchronization started",
            "status": "running",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync odds: {str(e)}")

@router.post("/predictions")
async def sync_predictions(background_tasks: BackgroundTasks):
    """Generate predictions for matches"""
    try:
        background_tasks.add_task(data_synchronizer._sync_predictions)

        return {
            "message": "Predictions generation started",
            "status": "running",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate predictions: {str(e)}")

@router.get("/status")
async def get_sync_status():
    """Get current synchronization status"""
    try:
        # Get last sync times from Redis
        from app.core.redis import redis_client

        last_full_sync = await redis_client.get("last_full_sync")
        last_quick_sync = await redis_client.get("last_quick_sync")

        # Get scheduler status
        scheduler_status = football_scheduler.get_job_status()

        return {
            "sync_status": {
                "last_full_sync": last_full_sync.decode() if last_full_sync else None,
                "last_quick_sync": last_quick_sync.decode() if last_quick_sync else None
            },
            "scheduler": scheduler_status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

@router.get("/health")
async def health_check():
    """Check health of all external services"""
    try:
        health_status = await data_synchronizer.health_check()
        return health_status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.post("/scheduler/start")
async def start_scheduler():
    """Start the automated data synchronization scheduler"""
    try:
        await football_scheduler.start()
        return {
            "message": "Scheduler started successfully",
            "status": "running",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start scheduler: {str(e)}")

@router.post("/scheduler/stop")
async def stop_scheduler():
    """Stop the automated data synchronization scheduler"""
    try:
        await football_scheduler.stop()
        return {
            "message": "Scheduler stopped successfully",
            "status": "stopped",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop scheduler: {str(e)}")

@router.get("/scheduler/status")
async def get_scheduler_status():
    """Get current scheduler status and job information"""
    try:
        status = football_scheduler.get_job_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get scheduler status: {str(e)}")

@router.post("/manual/{sync_type}")
async def manual_sync(sync_type: str):
    """
    Manually trigger a specific type of synchronization.

    Available sync types:
    - full: Complete synchronization
    - quick: Live data updates only
    - matches: Match data only
    - odds: Betting odds only
    - predictions: Generate predictions only
    """
    valid_types = ["full", "quick", "matches", "odds", "predictions"]

    if sync_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sync type. Valid types: {', '.join(valid_types)}"
        )

    try:
        result = await football_scheduler.trigger_manual_sync(sync_type)

        if result.get("success"):
            return {
                "message": f"Manual {sync_type} sync completed",
                "results": result.get("results"),
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Manual sync failed: {result.get('error')}"
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Manual sync failed: {str(e)}")