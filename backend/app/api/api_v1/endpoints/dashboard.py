#!/usr/bin/env python3
"""
📊 Dashboard Endpoints
Endpoints específicos para o Dashboard e Sidebar
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.match import Match
from app.models.prediction import Prediction

router = APIRouter()

@router.get("/overview")
async def get_dashboard_overview(db: Session = Depends(get_db)):
    """
    Overview do dashboard para sidebar - Today's Overview
    Retorna estatísticas do dia atual
    """
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    # Jogos de hoje
    today_matches = db.query(func.count(Match.id)).filter(
        and_(
            Match.match_date >= today_start,
            Match.match_date <= today_end
        )
    ).scalar() or 0

    # Predições feitas (total)
    predictions_made = db.query(func.count(Prediction.id)).scalar() or 0

    # Taxa de acurácia do modelo
    accuracy_rate = 59.0  # Baseado no modelo Random Forest Enhanced

    # Alertas ativos (jogos próximos sem predições)
    future_24h = now + timedelta(hours=24)

    # Buscar jogos nas próximas 24h
    upcoming_matches = db.query(Match.id).filter(
        and_(
            Match.match_date >= now,
            Match.match_date <= future_24h,
            Match.status.in_(['NS', 'TBD', 'SCHEDULED'])
        )
    ).all()

    # Extrair IDs dos jogos
    upcoming_match_ids = [m.id for m in upcoming_matches]

    # Buscar predições para esses jogos
    predictions_for_upcoming = db.query(Prediction.match_id).filter(
        Prediction.match_id.in_(upcoming_match_ids)
    ).all() if upcoming_match_ids else []

    # Contar jogos sem predições
    pred_match_ids = {p.match_id for p in predictions_for_upcoming}
    active_alerts = sum(1 for m in upcoming_matches if m.id not in pred_match_ids)

    return {
        "today_matches": today_matches,
        "predictions_made": predictions_made,
        "accuracy_rate": accuracy_rate,
        "active_alerts": active_alerts,
        "last_update": datetime.now().isoformat()
    }
