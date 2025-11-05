from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from app.core.config import settings
from app.api.api_v1.api import api_router
from app.startup import lifespan, startup_manager

def create_application() -> FastAPI:
    application = FastAPI(
        title=settings.PROJECT_NAME,
        description="Advanced Football Analytics API with Real-time Data Synchronization",
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan  # Automatic startup/shutdown management
    )

    # For development, allow all origins. In production, use specific origins.
    cors_origins = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"] if settings.BACKEND_CORS_ORIGINS else ["*"]

    application.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.add_middleware(GZipMiddleware, minimum_size=1000)

    application.include_router(api_router, prefix=settings.API_V1_STR)

    return application

app = create_application()

@app.get("/")
async def root():
    return {
        "message": "Football Analytics API with Real-time Data Synchronization",
        "version": settings.VERSION,
        "features": [
            "Real-time match data synchronization",
            "AI-powered predictions",
            "Live odds tracking",
            "Automated data updates",
            "Multi-league support"
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "football-analytics-api"}

@app.get("/system/status")
async def system_status():
    """Get comprehensive system status including sync and scheduler info"""
    try:
        status = await startup_manager.get_system_status()
        return status
    except Exception as e:
        return {"error": str(e), "is_ready": False}