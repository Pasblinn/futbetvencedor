from fastapi import APIRouter
from app.api.api_v1.endpoints import matches, teams, analytics, predictions, odds, sync, ml_predictions, real_predictions, global_system, odds_comparison, ml_retraining, tickets, user_auth, ticket_analysis, ai_predictions, dashboard, user_bankroll, user_tickets, markets, predictions_modes, live_matches, news

api_router = APIRouter()

# Authentication
api_router.include_router(user_auth.router, prefix="/auth", tags=["authentication"])

# Dashboard
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])

# User Management
api_router.include_router(user_bankroll.router, prefix="/user", tags=["user"])
api_router.include_router(user_tickets.router, prefix="/user", tags=["user"])

api_router.include_router(matches.router, prefix="/matches", tags=["matches"])
api_router.include_router(live_matches.router, prefix="/live-matches", tags=["live-matches"])
api_router.include_router(teams.router, prefix="/teams", tags=["teams"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(predictions.router, prefix="/predictions", tags=["predictions"])
api_router.include_router(tickets.router, prefix="/tickets", tags=["tickets"])
api_router.include_router(ticket_analysis.router, prefix="/ticket-analysis", tags=["ticket-analysis"])
api_router.include_router(ml_predictions.router, prefix="/ml", tags=["machine-learning"])
api_router.include_router(real_predictions.router, prefix="/ml-real", tags=["ml-real-data"])
api_router.include_router(ai_predictions.router, prefix="/ai", tags=["ai-agent"])  # 🧠 NOVO: AI Agent
api_router.include_router(odds.router, prefix="/odds", tags=["odds"])
api_router.include_router(odds_comparison.router, prefix="/odds-comparison", tags=["odds-comparison"])
api_router.include_router(ml_retraining.router, prefix="/ml-retraining", tags=["ml-retraining"])
api_router.include_router(sync.router, prefix="/sync", tags=["synchronization"])
api_router.include_router(global_system.router, prefix="/global", tags=["global-system"])
api_router.include_router(markets.router, prefix="/markets", tags=["markets-poisson-valuebets"])
api_router.include_router(predictions_modes.router, prefix="/predictions-modes", tags=["predictions-modes"])  # 🎯 NOVO: 3 Modos
api_router.include_router(news.router, prefix="/news", tags=["news-injuries"])  # 📰 News & Injuries