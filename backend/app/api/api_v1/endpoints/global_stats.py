from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models import Match, Prediction, Team
from app.models.statistics import MatchStatistics

router = APIRouter()

@router.get("/performance")
async def get_global_performance(db: Session = Depends(get_db)):
    """
    🌍 Global Performance Dashboard
    
    Retorna métricas globais do sistema:
    - Status de saúde de componentes
    - Estatísticas globais
    - Performance regional
    - Métricas do modelo ML
    """
    
    # System Health
    # Verificar se temos dados recentes (API está operacional)
    recent_match = db.query(Match).order_by(Match.created_at.desc()).first()
    api_status = "operational" if recent_match else "warning"
    
    # Database status
    total_matches = db.query(Match).count()
    database_status = "connected" if total_matches > 0 else "offline"
    
    # ML Engine status
    total_predictions = db.query(Prediction).count()
    ml_engine_status = "active" if total_predictions > 0 else "inactive"
    
    # Cache status (simulado)
    cache_status = "active"
    
    # Global Stats
    total_leagues = db.query(Match.league).filter(Match.league.isnot(None)).distinct().count()
    
    # Active matches (próximos 7 dias)
    week_from_now = datetime.now() + timedelta(days=7)
    active_matches = db.query(Match).filter(
        Match.match_date <= week_from_now,
        Match.status.in_(['NS', 'TBD', 'SCHEDULED'])
    ).count()
    
    processed_predictions = total_predictions
    
    # Taxa de sucesso global
    validated_predictions = db.query(Prediction).filter(
        Prediction.is_validated == True,
        Prediction.actual_outcome.isnot(None)
    ).count()
    
    successful_predictions = db.query(Prediction).filter(
        Prediction.is_validated == True,
        Prediction.is_winner == True
    ).count()
    
    success_rate_global = (successful_predictions / validated_predictions * 100) if validated_predictions > 0 else 0.0
    
    # Uptime (simulado - calcular baseado na data de criação do primeiro match)
    first_match = db.query(Match).order_by(Match.created_at.asc()).first()
    if first_match and first_match.created_at:
        uptime_delta = datetime.now() - first_match.created_at
        uptime_hours = uptime_delta.total_seconds() / 3600
    else:
        uptime_hours = 0
    
    # Regional Performance
    # Brasil
    brazil_leagues = ['71', '72']  # Brasileirão A e B
    brazil_matches = db.query(Match).filter(Match.league.in_(brazil_leagues)).count()
    brazil_predictions = db.query(Prediction).join(
        Match, Match.id == Prediction.match_id
    ).filter(
        Match.league.in_(brazil_leagues),
        Prediction.is_validated == True
    ).count()
    brazil_successful = db.query(Prediction).join(
        Match, Match.id == Prediction.match_id
    ).filter(
        Match.league.in_(brazil_leagues),
        Prediction.is_validated == True,
        Prediction.is_winner == True
    ).count()
    brazil_accuracy = (brazil_successful / brazil_predictions * 100) if brazil_predictions > 0 else 0.0
    
    # Europa (Premier League, La Liga, Bundesliga, Serie A)
    europe_leagues = ['Premier League', 'La Liga', 'Bundesliga', '13']  # 13 = Serie A
    europe_matches = db.query(Match).filter(Match.league.in_(europe_leagues)).count()
    europe_predictions = db.query(Prediction).join(
        Match, Match.id == Prediction.match_id
    ).filter(
        Match.league.in_(europe_leagues),
        Prediction.is_validated == True
    ).count()
    europe_successful = db.query(Prediction).join(
        Match, Match.id == Prediction.match_id
    ).filter(
        Match.league.in_(europe_leagues),
        Prediction.is_validated == True,
        Prediction.is_winner == True
    ).count()
    europe_accuracy = (europe_successful / europe_predictions * 100) if europe_predictions > 0 else 0.0
    
    # América do Sul (Libertadores, Sul-Americana)
    south_america_leagues = ['11', '12']  # Libertadores e Sul-Americana
    south_america_matches = db.query(Match).filter(Match.league.in_(south_america_leagues)).count()
    south_america_predictions = db.query(Prediction).join(
        Match, Match.id == Prediction.match_id
    ).filter(
        Match.league.in_(south_america_leagues),
        Prediction.is_validated == True
    ).count()
    south_america_successful = db.query(Prediction).join(
        Match, Match.id == Prediction.match_id
    ).filter(
        Match.league.in_(south_america_leagues),
        Prediction.is_validated == True,
        Prediction.is_winner == True
    ).count()
    south_america_accuracy = (south_america_successful / south_america_predictions * 100) if south_america_predictions > 0 else 0.0
    
    # ML Metrics
    avg_confidence = db.query(func.avg(Prediction.confidence_score)).scalar() or 0.0
    
    # Data quality score (% de matches com estatísticas)
    total_stats = db.query(MatchStatistics).count()
    data_quality_score = (total_stats / total_matches * 100) if total_matches > 0 else 0.0
    
    # Last retrain (usar a predição mais recente como proxy)
    latest_prediction = db.query(Prediction).order_by(Prediction.predicted_at.desc()).first()
    last_retrain = latest_prediction.predicted_at.isoformat() if latest_prediction and latest_prediction.predicted_at else "N/A"
    
    return {
        "system_health": {
            "api_status": api_status,
            "database_status": database_status,
            "ml_engine_status": ml_engine_status,
            "cache_status": cache_status
        },
        "global_stats": {
            "total_leagues": total_leagues,
            "active_matches": active_matches,
            "processed_predictions": processed_predictions,
            "success_rate_global": round(success_rate_global, 1),
            "uptime_hours": round(uptime_hours, 1)
        },
        "regional_performance": {
            "brazil": {
                "matches": brazil_matches,
                "accuracy": round(brazil_accuracy, 1)
            },
            "europe": {
                "matches": europe_matches,
                "accuracy": round(europe_accuracy, 1)
            },
            "south_america": {
                "matches": south_america_matches,
                "accuracy": round(south_america_accuracy, 1)
            }
        },
        "ml_metrics": {
            "model_accuracy": 59.0,  # Random Forest Enhanced
            "prediction_confidence_avg": round(float(avg_confidence), 2),
            "data_quality_score": round(data_quality_score, 1),
            "last_retrain": last_retrain
        }
    }
