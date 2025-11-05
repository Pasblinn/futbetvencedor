from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.rate_limiter import limiter
from app.models import BetCombination, Prediction, Match
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

router = APIRouter()

# Timezone de Brasília (BRT = UTC-3)
BRT = timezone(timedelta(hours=-3))

def to_brasilia_time(dt: datetime) -> str:
    """Converte datetime UTC para horário de Brasília (BRT) e retorna string ISO"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    brt_time = dt.astimezone(BRT)
    return brt_time.isoformat()


@router.get("/all")
async def get_all_tickets(
    ticket_type: Optional[str] = Query(None, description="SINGLE, DOUBLE, TREBLE, QUAD"),
    min_confidence: Optional[float] = Query(None, description="Confidence mínima (0-1)"),
    risk_level: Optional[str] = Query(None, description="LOW, MEDIUM, HIGH"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Retorna todos os tickets/bilhetes gerados
    """
    query = db.query(BetCombination)

    # Filtros
    if ticket_type:
        query = query.filter(BetCombination.combination_type == ticket_type.upper())

    if min_confidence is not None:
        query = query.filter(BetCombination.combined_confidence >= min_confidence)

    if risk_level:
        query = query.filter(BetCombination.risk_level == risk_level.upper())

    # Ordenar por confidence (maior primeiro)
    query = query.order_by(BetCombination.combined_confidence.desc())

    # Limit
    tickets = query.limit(limit).all()

    # Formatar response
    response = []
    for ticket in tickets:
        # Buscar detalhes dos jogos
        predictions = db.query(Prediction).filter(
            Prediction.id.in_(ticket.prediction_ids)
        ).all()

        matches = []
        for pred in predictions:
            match = db.query(Match).filter(Match.id == pred.match_id).first()
            if match:
                matches.append({
                    'match_id': match.id,
                    'home_team': match.home_team,
                    'away_team': match.away_team,
                    'league': match.league,
                    'match_date': to_brasilia_time(match.match_date),
                    'market': pred.market_type,
                    'selection': pred.predicted_outcome,
                    'odd': pred.actual_odds,
                    'confidence': pred.confidence_score
                })

        response.append({
            'id': ticket.id,
            'type': ticket.combination_type,
            'selections_count': ticket.selections_count,
            'total_odds': round(ticket.total_odds, 2),
            'combined_confidence': round(ticket.combined_confidence * 100, 1),
            'expected_value': round(ticket.expected_value, 2),
            'risk_level': ticket.risk_level,
            'is_recommended': ticket.is_recommended,
            'matches': matches,
            'created_at': to_brasilia_time(ticket.created_at)
        })

    return {
        'tickets': response,
        'total': len(response),
        'filters': {
            'type': ticket_type,
            'min_confidence': min_confidence,
            'risk_level': risk_level
        }
    }


@router.get("/stats")
async def get_tickets_stats(db: Session = Depends(get_db)):
    """
    Estatísticas dos tickets gerados
    """
    total_singles = db.query(BetCombination).filter(BetCombination.combination_type == 'SINGLE').count()
    total_doubles = db.query(BetCombination).filter(BetCombination.combination_type == 'DOUBLE').count()
    total_trebles = db.query(BetCombination).filter(BetCombination.combination_type == 'TREBLE').count()
    total_quads = db.query(BetCombination).filter(BetCombination.combination_type == 'QUAD').count()

    # Confidence média por tipo
    avg_conf_single = db.query(BetCombination).filter(BetCombination.combination_type == 'SINGLE').with_entities(
        BetCombination.combined_confidence
    ).all()
    avg_single = sum([x[0] for x in avg_conf_single if x[0]]) / len(avg_conf_single) if avg_conf_single else 0

    avg_conf_double = db.query(BetCombination).filter(BetCombination.combination_type == 'DOUBLE').with_entities(
        BetCombination.combined_confidence
    ).all()
    avg_double = sum([x[0] for x in avg_conf_double if x[0]]) / len(avg_conf_double) if avg_conf_double else 0

    avg_conf_treble = db.query(BetCombination).filter(BetCombination.combination_type == 'TREBLE').with_entities(
        BetCombination.combined_confidence
    ).all()
    avg_treble = sum([x[0] for x in avg_conf_treble if x[0]]) / len(avg_conf_treble) if avg_conf_treble else 0

    avg_conf_quad = db.query(BetCombination).filter(BetCombination.combination_type == 'QUAD').with_entities(
        BetCombination.combined_confidence
    ).all()
    avg_quad = sum([x[0] for x in avg_conf_quad if x[0]]) / len(avg_conf_quad) if avg_conf_quad else 0

    return {
        'total_tickets': total_singles + total_doubles + total_trebles + total_quads,
        'breakdown': {
            'singles': {
                'count': total_singles,
                'avg_confidence': round(avg_single * 100, 1)
            },
            'doubles': {
                'count': total_doubles,
                'avg_confidence': round(avg_double * 100, 1)
            },
            'trebles': {
                'count': total_trebles,
                'avg_confidence': round(avg_treble * 100, 1)
            },
            'quadruples': {
                'count': total_quads,
                'avg_confidence': round(avg_quad * 100, 1)
            }
        },
        'recommended_count': db.query(BetCombination).filter(BetCombination.is_recommended == True).count()
    }


@router.get("/best")
async def get_best_tickets(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Retorna os melhores tickets por tipo (maior confidence)
    """
    best_singles = db.query(BetCombination).filter(
        BetCombination.combination_type == 'SINGLE'
    ).order_by(BetCombination.combined_confidence.desc()).limit(limit).all()

    best_doubles = db.query(BetCombination).filter(
        BetCombination.combination_type == 'DOUBLE'
    ).order_by(BetCombination.combined_confidence.desc()).limit(limit).all()

    best_trebles = db.query(BetCombination).filter(
        BetCombination.combination_type == 'TREBLE'
    ).order_by(BetCombination.combined_confidence.desc()).limit(limit).all()

    best_quads = db.query(BetCombination).filter(
        BetCombination.combination_type == 'QUAD'
    ).order_by(BetCombination.combined_confidence.desc()).limit(limit).all()

    def format_ticket(ticket):
        predictions = db.query(Prediction).filter(
            Prediction.id.in_(ticket.prediction_ids)
        ).all()

        matches = []
        for pred in predictions:
            match = db.query(Match).filter(Match.id == pred.match_id).first()
            if match:
                matches.append({
                    'match_id': match.id,
                    'home_team': match.home_team,
                    'away_team': match.away_team,
                    'league': match.league,
                    'match_date': to_brasilia_time(match.match_date),
                    'market': pred.market_type,
                    'selection': pred.predicted_outcome,
                    'odd': pred.actual_odds,
                    'confidence': round(pred.confidence_score * 100, 1)
                })

        return {
            'id': ticket.id,
            'type': ticket.combination_type,
            'total_odds': round(ticket.total_odds, 2),
            'combined_confidence': round(ticket.combined_confidence * 100, 1),
            'expected_value': round(ticket.expected_value, 2),
            'risk_level': ticket.risk_level,
            'matches': matches
        }

    return {
        'best_singles': [format_ticket(t) for t in best_singles],
        'best_doubles': [format_ticket(t) for t in best_doubles],
        'best_trebles': [format_ticket(t) for t in best_trebles],
        'best_quadruples': [format_ticket(t) for t in best_quads]
    }


# Pydantic models for manual ticket creation
class ManualSelection(BaseModel):
    """Seleção individual para ticket manual"""
    match_id: int
    market_type: str  # 1X2, BTTS, Over/Under, etc.
    predicted_outcome: str  # 1, X, 2, Over 2.5, etc.
    odd: float  # Odd real da aposta
    confidence_score: Optional[float] = 0.5  # User confidence (0-1)


class ManualTicketCreate(BaseModel):
    """Schema para criar ticket manual (GOLD data)"""
    selections: List[ManualSelection]
    notes: Optional[str] = None  # User reasoning/analysis
    created_by: Optional[str] = "user"  # Username or ID
    risk_level: Optional[str] = "MEDIUM"  # LOW, MEDIUM, HIGH


@router.post("/manual", status_code=201)
@limiter.limit("20/minute")
async def create_manual_ticket(
    request: Request,
    ticket_data: ManualTicketCreate,
    db: Session = Depends(get_db)
):
    """
    🏆 Criar Ticket Manual (GOLD DATA para ML)

    Permite ao usuário criar bilhetes manualmente com suas próprias análises.
    Esses tickets são marcados como "GOLD data" para treinamento da ML.

    - **selections**: Lista de seleções (match_id, market, outcome, odd)
    - **notes**: Análise/raciocínio do usuário
    - **risk_level**: LOW, MEDIUM, HIGH

    Rate limit: 20/min
    """
    if not ticket_data.selections or len(ticket_data.selections) == 0:
        raise HTTPException(status_code=400, detail="Ticket deve ter pelo menos 1 seleção")

    if len(ticket_data.selections) > 10:
        raise HTTPException(status_code=400, detail="Ticket não pode ter mais de 10 seleções")

    # Verificar se todos os jogos existem
    for selection in ticket_data.selections:
        match = db.query(Match).filter(Match.id == selection.match_id).first()
        if not match:
            raise HTTPException(
                status_code=404,
                detail=f"Jogo {selection.match_id} não encontrado"
            )

    # Criar predictions para cada seleção
    prediction_ids = []
    total_odds = 1.0
    combined_confidence = 1.0

    for selection in ticket_data.selections:
        # Criar prediction individual
        new_pred = Prediction(
            match_id=selection.match_id,
            prediction_type='MANUAL',
            market_type=selection.market_type,
            predicted_outcome=selection.predicted_outcome,
            actual_odds=selection.odd,
            confidence_score=selection.confidence_score,
            model_version='manual_user_v1',
            predicted_at=datetime.now(timezone.utc),
            analysis_summary=ticket_data.notes
        )

        db.add(new_pred)
        db.flush()  # Get the ID

        prediction_ids.append(new_pred.id)
        total_odds *= selection.odd
        combined_confidence *= selection.confidence_score

    # Determinar tipo de combinação
    selections_count = len(ticket_data.selections)
    if selections_count == 1:
        combination_type = 'SINGLE'
    elif selections_count == 2:
        combination_type = 'DOUBLE'
    elif selections_count == 3:
        combination_type = 'TREBLE'
    else:
        combination_type = 'QUAD' if selections_count == 4 else 'MULTIPLE'

    # Criar BetCombination MANUAL
    new_ticket = BetCombination(
        combination_type=combination_type,
        selections_count=selections_count,
        total_odds=total_odds,
        combined_confidence=combined_confidence,
        expected_value=total_odds * combined_confidence,
        risk_level=ticket_data.risk_level.upper(),
        prediction_ids=prediction_ids,
        is_recommended=True,  # User created it, so they recommend it
        is_manual=True,  # GOLD DATA flag
        created_by=ticket_data.created_by,
        notes=ticket_data.notes
    )

    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)

    # Formatar response com detalhes dos jogos
    matches = []
    for selection in ticket_data.selections:
        match = db.query(Match).filter(Match.id == selection.match_id).first()
        if match:
            matches.append({
                'match_id': match.id,
                'home_team': match.home_team,
                'away_team': match.away_team,
                'league': match.league,
                'match_date': to_brasilia_time(match.match_date),
                'market': selection.market_type,
                'selection': selection.predicted_outcome,
                'odd': selection.odd
            })

    return {
        'success': True,
        'ticket_id': new_ticket.id,
        'type': combination_type,
        'total_odds': round(total_odds, 2),
        'combined_confidence': round(combined_confidence * 100, 1),
        'expected_value': round(new_ticket.expected_value, 2),
        'risk_level': new_ticket.risk_level,
        'is_gold_data': True,
        'matches': matches,
        'message': f'Ticket manual criado com sucesso! 🏆 (GOLD DATA para ML)'
    }
