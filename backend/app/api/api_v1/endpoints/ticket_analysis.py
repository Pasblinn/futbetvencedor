"""
🎫 TICKET ANALYSIS ENDPOINTS
Endpoints para monitorar e controlar análise automática de tickets
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict

from app.core.database import get_db
from app.services.ticket_analyzer import analyze_all_tickets
from app.services.ticket_scheduler import get_scheduler
from app.models.user import User
from app.core.security import get_current_user

router = APIRouter()


@router.get("/scheduler/status")
async def get_scheduler_status(
    current_user: User = Depends(get_current_user)
) -> Dict:
    """
    Obter status do scheduler de análise de tickets

    Retorna informações sobre:
    - Se o scheduler está rodando
    - Intervalo de execução
    - Total de execuções
    - Última execução
    - Próxima execução
    """
    scheduler = get_scheduler()
    stats = scheduler.get_stats()

    return {
        "status": "running" if stats['is_running'] else "stopped",
        "details": stats
    }


@router.post("/analyze")
async def trigger_manual_analysis(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict:
    """
    Executar análise manual de tickets

    Analisa todos os tickets pendentes imediatamente.
    Útil para testes ou quando necessário forçar uma análise.
    """
    try:
        stats = analyze_all_tickets(db)

        return {
            "success": True,
            "message": "Análise concluída com sucesso",
            "stats": stats
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao executar análise: {str(e)}"
        )


@router.get("/stats")
async def get_analysis_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict:
    """
    Obter estatísticas gerais de análise de tickets

    Retorna métricas sobre:
    - Total de tickets analisados
    - Tickets ganhos vs perdidos
    - Taxa de acerto
    - Lucro/prejuízo total
    """
    from app.models.user_ticket import UserTicket, TicketStatus

    # Total de tickets
    total_tickets = db.query(UserTicket).count()

    # Tickets por status
    pending = db.query(UserTicket).filter(
        UserTicket.status == TicketStatus.PENDING
    ).count()

    won = db.query(UserTicket).filter(
        UserTicket.status == TicketStatus.WON
    ).count()

    lost = db.query(UserTicket).filter(
        UserTicket.status == TicketStatus.LOST
    ).count()

    # Calcular totais financeiros
    from sqlalchemy import func

    total_profit = db.query(
        func.sum(UserTicket.profit_loss)
    ).filter(
        UserTicket.status == TicketStatus.WON
    ).scalar() or 0.0

    total_loss = db.query(
        func.sum(UserTicket.profit_loss)
    ).filter(
        UserTicket.status == TicketStatus.LOST
    ).scalar() or 0.0

    total_staked = db.query(
        func.sum(UserTicket.stake)
    ).filter(
        UserTicket.status.in_([TicketStatus.WON, TicketStatus.LOST])
    ).scalar() or 0.0

    # Calcular taxa de acerto
    analyzed_total = won + lost
    win_rate = (won / analyzed_total * 100) if analyzed_total > 0 else 0.0

    # Calcular ROI
    net_profit = total_profit + total_loss  # total_loss já é negativo
    roi = (net_profit / total_staked * 100) if total_staked > 0 else 0.0

    return {
        "total_tickets": total_tickets,
        "pending": pending,
        "analyzed": analyzed_total,
        "won": won,
        "lost": lost,
        "win_rate": round(win_rate, 2),
        "financial": {
            "total_staked": round(total_staked, 2),
            "total_profit": round(total_profit, 2),
            "total_loss": round(abs(total_loss), 2),
            "net_profit": round(net_profit, 2),
            "roi": round(roi, 2)
        }
    }
