"""
✍️ PREDICTIONS MANUAIS - Endpoint para adicionar predictions manualmente
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from typing import Optional

from app.core.database import get_db
from app.core.rate_limiter import limiter
from app.models import Match, Prediction

router = APIRouter()

# Timezone de Brasília (BRT = UTC-3)
BRT = timezone(timedelta(hours=-3))

def to_brasilia_time(dt: datetime) -> str:
    """Converte datetime UTC para horário de Brasília (BRT)"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    brt_time = dt.astimezone(BRT)
    return brt_time.isoformat()

class ManualPredictionCreate(BaseModel):
    """Schema para criar prediction manual"""
    match_id: int
    predicted_outcome: str  # "1", "X", "2"
    confidence_score: Optional[float] = None
    probability_home: Optional[float] = None
    probability_draw: Optional[float] = None
    probability_away: Optional[float] = None
    notes: Optional[str] = None

class GreenRedStats(BaseModel):
    """Stats GREEN/RED"""
    total: int
    greens: int
    reds: int
    pending: int
    accuracy: float
    total_profit_loss: float

@router.post("/manual", status_code=201)
@limiter.limit("10/minute")
async def create_manual_prediction(
    request: Request,
    prediction_data: ManualPredictionCreate,
    db: Session = Depends(get_db)
):
    """
    Criar prediction MANUAL

    - **match_id**: ID do jogo
    - **predicted_outcome**: "1" (casa), "X" (empate), "2" (fora)
    - **confidence_score**: 0-1 (opcional)
    - **notes**: Notas/análise (opcional)

    Rate limit: 10/min
    """
    # Verificar se match existe
    match = db.query(Match).filter(Match.id == prediction_data.match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match não encontrado")

    # Verificar se já existe prediction
    existing = db.query(Prediction).filter(
        Prediction.match_id == prediction_data.match_id,
        Prediction.market_type == '1X2'
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Prediction já existe para este jogo")

    # Criar prediction
    new_prediction = Prediction(
        match_id=prediction_data.match_id,
        market_type='1X2',
        prediction_type='SINGLE',
        predicted_outcome=prediction_data.predicted_outcome,
        confidence_score=prediction_data.confidence_score,
        probability_home=prediction_data.probability_home,
        probability_draw=prediction_data.probability_draw,
        probability_away=prediction_data.probability_away,
        analysis_summary=prediction_data.notes,
        model_version='manual_v1',
        predicted_at=datetime.now()
    )

    db.add(new_prediction)
    db.commit()
    db.refresh(new_prediction)

    return {
        "success": True,
        "prediction_id": new_prediction.id,
        "match": f"{match.home_team.name} vs {match.away_team.name}",
        "predicted_outcome": new_prediction.predicted_outcome,
        "message": "Prediction manual criada com sucesso!"
    }

@router.get("/stats/green-red", response_model=GreenRedStats)
@limiter.limit("30/minute")
async def get_green_red_stats(request: Request, db: Session = Depends(get_db)):
    """
    Estatísticas GREEN/RED

    - 🟢 GREEN = Acertos
    - 🔴 RED = Erros
    - ⏳ PENDING = Aguardando resultado
    """
    # Total de predictions
    total = db.query(Prediction).filter(
        Prediction.market_type == '1X2'
    ).count()

    # GREEN (acertos)
    greens = db.query(Prediction).filter(
        Prediction.is_winner == True
    ).count()

    # RED (erros)
    reds = db.query(Prediction).filter(
        Prediction.is_winner == False
    ).count()

    # Pending (sem resultado ainda)
    pending = db.query(Prediction).filter(
        Prediction.actual_outcome.is_(None)
    ).count()

    # Calcular profit/loss total
    profit_loss = 0.0
    predictions_with_pl = db.query(Prediction).filter(
        Prediction.profit_loss.isnot(None)
    ).all()

    for pred in predictions_with_pl:
        profit_loss += pred.profit_loss

    # Acurácia
    total_with_result = greens + reds
    accuracy = (greens / total_with_result * 100) if total_with_result > 0 else 0

    return GreenRedStats(
        total=total,
        greens=greens,
        reds=reds,
        pending=pending,
        accuracy=accuracy,
        total_profit_loss=profit_loss
    )

@router.get("/green-red/history")
@limiter.limit("30/minute")
async def get_green_red_history(
    request: Request,
    db: Session = Depends(get_db),
    limit: int = 50,
    filter_result: Optional[str] = None  # "green", "red", ou None para todos
):
    """
    📜 Histórico de Bilhetes com GREEN/RED

    Retorna histórico de predictions (bilhetes) com seus resultados
    - 🟢 GREEN = Acertou
    - 🔴 RED = Errou
    - ⏳ PENDING = Aguardando resultado

    **Filtros:**
    - filter_result: "green", "red", ou vazio para todos
    """
    query = db.query(Prediction).filter(
        Prediction.market_type == '1X2'
    )

    # Aplicar filtro de resultado se fornecido
    if filter_result == "green":
        query = query.filter(Prediction.is_winner == True)
    elif filter_result == "red":
        query = query.filter(Prediction.is_winner == False)

    predictions = query.order_by(Prediction.predicted_at.desc()).limit(limit).all()

    results = []
    greens_count = 0
    reds_count = 0
    pending_count = 0

    for pred in predictions:
        match = db.query(Match).filter(Match.id == pred.match_id).first()

        if match:
            # Determinar status do bilhete
            if pred.is_winner is None:
                status = 'PENDING ⏳'
                pending_count += 1
            elif pred.is_winner:
                status = 'GREEN ✅'
                greens_count += 1
            else:
                status = 'RED ❌'
                reds_count += 1

            results.append({
                'id': pred.id,
                'created_at': to_brasilia_time(pred.predicted_at),
                'match': {
                    'id': match.id,
                    'home_team': match.home_team,
                    'away_team': match.away_team,
                    'league': match.league,
                    'match_date': to_brasilia_time(match.match_date),
                    'score': {
                        'home': match.home_score,
                        'away': match.away_score
                    } if match.home_score is not None else None
                },
                'bilhete': {
                    'market_type': pred.market_type,
                    'predicted_outcome': pred.predicted_outcome,
                    'actual_outcome': pred.actual_outcome,
                    'confidence': round(pred.confidence_score * 100, 1) if pred.confidence_score else None,
                    'recommendation': pred.final_recommendation
                },
                'resultado': {
                    'status': status,
                    'is_green': pred.is_winner if pred.is_winner is not None else None,
                    'profit_loss': round(pred.profit_loss, 2) if pred.profit_loss else 0.0
                }
            })

    return {
        'bilhetes': results,
        'total': len(results),
        'resumo': {
            'greens': greens_count,
            'reds': reds_count,
            'pending': pending_count,
            'accuracy': round(greens_count / (greens_count + reds_count) * 100, 1) if (greens_count + reds_count) > 0 else 0
        }
    }
