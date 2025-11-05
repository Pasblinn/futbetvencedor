#!/usr/bin/env python3
"""
📊 Monitoring & Performance Endpoints
Fornece métricas de sistema, monitoramento ao vivo e performance ML
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from typing import List
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.core.database import get_db
from app.models.match import Match
from app.models.prediction import Prediction

router = APIRouter()

# Pydantic models
class Alert(BaseModel):
    id: int
    type: str
    match: str
    message: str
    severity: str  # high, medium, low
    timestamp: str

class SystemMetrics(BaseModel):
    api_response_time: float
    database_queries_per_second: int
    cache_hit_rate: float
    active_websocket_connections: int

class DataSource(BaseModel):
    name: str
    status: str  # online, offline, warning
    last_update: str

class LiveMonitoringResponse(BaseModel):
    active_monitors: int
    alerts: List[Alert]
    system_metrics: SystemMetrics
    live_data_sources: List[DataSource]

class PerformanceMetrics(BaseModel):
    total_predictions: int
    successful_predictions: int
    accuracy: float
    avg_confidence: float
    model_performance: dict
    recent_performance: List[dict]

@router.get("/live", response_model=LiveMonitoringResponse)
async def get_live_monitoring(db: Session = Depends(get_db)):
    """
    Retorna dados de monitoramento ao vivo

    - System metrics (response time, queries, cache, connections)
    - Active alerts
    - Data sources status
    """

    # Simular system metrics (em produção, pegar do Prometheus/Grafana)
    system_metrics = SystemMetrics(
        api_response_time=45.2,
        database_queries_per_second=120,
        cache_hit_rate=94.5,
        active_websocket_connections=0  # Não implementado ainda
    )

    # Data sources status
    data_sources = [
        DataSource(
            name="API-Sports",
            status="online",
            last_update=datetime.now().isoformat()
        ),
        DataSource(
            name="SQLite Database",
            status="online",
            last_update=datetime.now().isoformat()
        ),
        DataSource(
            name="ML Model Engine",
            status="online",
            last_update=datetime.now().isoformat()
        ),
        DataSource(
            name="RSS News Feeds",
            status="online",
            last_update=datetime.now().isoformat()
        )
    ]

    # Buscar alertas de jogos próximos sem predições
    alerts = []
    now = datetime.now()
    future = now + timedelta(hours=24)

    # Jogos nas próximas 24h sem predições
    upcoming_matches = db.query(Match).filter(
        and_(
            Match.match_date >= now,
            Match.match_date <= future,
            Match.status.in_(['NS', 'TBD', 'SCHEDULED'])
        )
    ).limit(5).all()

    for idx, match in enumerate(upcoming_matches):
        # Verificar se tem predição
        prediction = db.query(Prediction).filter(
            Prediction.match_id == match.id
        ).first()

        if not prediction:
            from app.models.team import Team
            home_team = db.query(Team).filter(Team.id == match.home_team_id).first()
            away_team = db.query(Team).filter(Team.id == match.away_team_id).first()

            alerts.append(Alert(
                id=idx + 1,
                type="missing_prediction",
                match=f"{home_team.name if home_team else 'Unknown'} vs {away_team.name if away_team else 'Unknown'}",
                message=f"Jogo em {match.match_date.strftime('%H:%M')} sem predição gerada",
                severity="medium",
                timestamp=datetime.now().isoformat()
            ))

    # Active monitors (número de jogos sendo monitorados)
    active_monitors = db.query(func.count(Match.id)).filter(
        and_(
            Match.match_date >= now,
            Match.match_date <= future,
            Match.status.in_(['NS', 'TBD', 'SCHEDULED', 'LIVE'])
        )
    ).scalar() or 0

    return LiveMonitoringResponse(
        active_monitors=active_monitors,
        alerts=alerts,
        system_metrics=system_metrics,
        live_data_sources=data_sources
    )

@router.get("/performance", response_model=PerformanceMetrics)
async def get_performance_metrics(db: Session = Depends(get_db)):
    """
    Retorna métricas de performance do sistema ML

    - Total de predições
    - Acurácia
    - Performance por modelo
    - Performance recente
    """

    # Total de predições
    total_predictions = db.query(func.count(Prediction.id)).scalar() or 0

    # Predições com resultado conhecido (matches finalizados)
    successful_predictions = 0  # TODO: Implementar quando houver validação de resultados

    # Acurácia (baseado no modelo treinado)
    accuracy = 0.59  # 59% do modelo Random Forest Enhanced

    # Confiança média das predições
    avg_confidence = db.query(func.avg(Prediction.confidence_score)).scalar() or 0.0

    # Performance por modelo
    model_performance = {
        "random_forest_enhanced": {
            "accuracy": 0.59,
            "total_predictions": total_predictions,
            "confidence_avg": avg_confidence,
            "status": "active"
        }
    }

    # Performance recente (últimas 10 predições)
    recent_predictions = db.query(Prediction).order_by(
        desc(Prediction.predicted_at)
    ).limit(10).all()

    recent_performance = []
    for pred in recent_predictions:
        match = db.query(Match).filter(Match.id == pred.match_id).first()
        if match:
            from app.models.team import Team
            home_team = db.query(Team).filter(Team.id == match.home_team_id).first()
            away_team = db.query(Team).filter(Team.id == match.away_team_id).first()

            recent_performance.append({
                "match": f"{home_team.name if home_team else 'Unknown'} vs {away_team.name if away_team else 'Unknown'}",
                "prediction": pred.predicted_outcome,
                "confidence": pred.confidence_score,
                "date": match.match_date.isoformat(),
                "actual_result": None  # TODO: Implementar
            })

    return PerformanceMetrics(
        total_predictions=total_predictions,
        successful_predictions=successful_predictions,
        accuracy=accuracy,
        avg_confidence=float(avg_confidence),
        model_performance=model_performance,
        recent_performance=recent_performance
    )

@router.get("/system/health")
async def get_system_health(db: Session = Depends(get_db)):
    """
    Health check do sistema
    """
    try:
        # Test database connection
        db.execute("SELECT 1")
        db_status = "healthy"
    except:
        db_status = "unhealthy"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


@router.post("/update-results")
async def update_match_results(db: Session = Depends(get_db)):
    """
    🔄 ATUALIZAÇÃO AUTOMÁTICA DE RESULTADOS

    Executa o fluxo completo:
    1. Busca jogos finalizados
    2. Atualiza resultados reais da API
    3. Calcula GREEN/RED das predictions
    4. Retorna estatísticas

    Este endpoint deve ser chamado periodicamente (scheduler)
    """
    from app.services.results_updater import run_results_update

    try:
        stats = run_results_update(db)

        return {
            "success": True,
            "message": "Atualização de resultados concluída",
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Erro na atualização: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
