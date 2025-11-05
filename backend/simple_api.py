#!/usr/bin/env python3
"""
🚀 API SIMPLIFICADA - Endpoints de predições ML
✅ COM SCHEDULER AUTOMÁTICO de atualização de resultados
"""
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from slowapi.errors import RateLimitExceeded

from app.core.database import get_db
from app.core.rate_limiter import limiter, rate_limit_exceeded_handler
from app.core.scheduler import start_scheduler, stop_scheduler
from app.api.api_v1.endpoints import predictions, analytics, global_stats, news, monitoring, dashboard, matches, ml_performance, auth, manual_predictions, live_matches, tickets, user_bankroll, user_tickets

app = FastAPI(
    title="Football Analytics - Predictions API",
    version="1.0.0"
)

# Lifecycle events
@app.on_event("startup")
async def startup_event():
    """Iniciar scheduler ao iniciar a API"""
    start_scheduler()

@app.on_event("shutdown")
async def shutdown_event():
    """Parar scheduler ao desligar a API"""
    stop_scheduler()

# Configurar rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rotas
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(user_bankroll.router, prefix="/api/v1/user", tags=["user-bankroll"])
app.include_router(user_tickets.router, prefix="/api/v1/user", tags=["user-tickets"])
app.include_router(manual_predictions.router, prefix="/api/v1/predictions", tags=["manual-predictions"])
app.include_router(predictions.router, prefix="/api/v1/predictions", tags=["predictions"])
app.include_router(tickets.router, prefix="/api/v1/tickets", tags=["tickets"])
app.include_router(live_matches.router, prefix="/api/v1/live", tags=["live-matches"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(global_stats.router, prefix="/api/v1/global", tags=["global"])
app.include_router(news.router, prefix="/api/v1/news", tags=["news"])
app.include_router(monitoring.router, prefix="/api/v1/monitoring", tags=["monitoring"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(matches.router, prefix="/api/v1/matches", tags=["matches"])
app.include_router(ml_performance.router, prefix="/api/v1/ml", tags=["ml-performance"])

@app.get("/")
@limiter.limit("20/minute")
async def root(request: Request):
    return {
        "message": "Football Analytics - Predictions API",
        "version": "1.0.0",
        "authentication": "JWT Bearer Token",
        "rate_limit": "100 requests/minute per IP",
        "endpoints": {
            "auth": [
                "/api/v1/auth/register",
                "/api/v1/auth/login",
                "/api/v1/auth/me",
                "/api/v1/auth/refresh"
            ],
            "predictions": [
                "/api/v1/predictions/upcoming",
                "/api/v1/predictions/ml-enhanced/{match_id}",
                "/api/v1/predictions/statistics/overview",
                "/api/v1/predictions/manual",
                "/api/v1/predictions/stats/green-red",
                "/api/v1/predictions/green-red/history"
            ],
            "news": [
                "/api/v1/news/rss",
                "/api/v1/news/search"
            ]
        },
        "docs": "/docs"
    }

@app.get("/health")
@limiter.limit("200/minute")
async def health(request: Request):
    return {"status": "healthy", "rate_limit": "200/minute"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
