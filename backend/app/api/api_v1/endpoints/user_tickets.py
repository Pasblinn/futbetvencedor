"""
🎫 ENDPOINTS DE BILHETES DO USUÁRIO

Sistema completo de gestão de apostas
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user_ticket import UserTicket, TicketSelection, TicketStatus, TicketSource
from app.models.user_bankroll import UserBankroll, BankrollHistory, TransactionType
from app.models.match import Match
from app.schemas.ticket_schemas import (
    TicketCreate,
    TicketResponse,
    TicketDetailResponse,
    TicketUpdate,
    TicketStatistics
)

router = APIRouter()


@router.post("/tickets", response_model=TicketDetailResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(
    ticket_data: TicketCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    🎫 CRIAR BILHETE

    Cria novo bilhete de apostas e atualiza banca
    """
    user_id = int(current_user["user_id"])

    # Buscar banca
    bankroll = db.query(UserBankroll).filter(UserBankroll.user_id == user_id).first()

    if not bankroll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Banca não encontrada"
        )

    # Verificar se pode apostar
    if not bankroll.can_place_bet(ticket_data.stake):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Saldo insuficiente. Disponível: R$ {bankroll.current_bankroll:.2f}"
        )

    # Calcular odds total
    total_odds = 1.0
    for selection in ticket_data.selections:
        total_odds *= selection.odd

    # Calcular retorno potencial
    potential_return = ticket_data.stake * total_odds

    # Criar bilhete
    new_ticket = UserTicket(
        user_id=user_id,
        ticket_type=ticket_data.ticket_type,
        source=TicketSource.MANUAL,
        stake=ticket_data.stake,
        total_odds=round(total_odds, 2),
        potential_return=round(potential_return, 2),
        status=TicketStatus.PENDING,
        notes=ticket_data.notes,
        confidence_level=ticket_data.confidence_level,
        selections_count=len(ticket_data.selections)
    )

    db.add(new_ticket)
    db.flush()  # Obter ID

    # Criar seleções
    for sel_data in ticket_data.selections:
        selection = TicketSelection(
            ticket_id=new_ticket.id,
            match_id=sel_data.match_id,
            market=sel_data.market,
            outcome=sel_data.outcome,
            odd=sel_data.odd
        )
        db.add(selection)

    # Atualizar banca
    balance_before = bankroll.current_bankroll
    bankroll.current_bankroll -= ticket_data.stake
    bankroll.total_staked += ticket_data.stake
    bankroll.total_bets += 1
    bankroll.pending += 1

    # Registrar transação
    history = BankrollHistory(
        user_id=user_id,
        transaction_type=TransactionType.BET,
        amount=ticket_data.stake,
        balance_before=balance_before,
        balance_after=bankroll.current_bankroll,
        description=f"Aposta - Bilhete #{new_ticket.id}",
        ticket_id=new_ticket.id
    )
    db.add(history)

    db.commit()
    db.refresh(new_ticket)

    # Carregar seleções
    new_ticket.selections = db.query(TicketSelection)\
        .filter(TicketSelection.ticket_id == new_ticket.id)\
        .all()

    return new_ticket


@router.get("/tickets", response_model=List[TicketResponse])
def list_tickets(
    status: Optional[TicketStatus] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    📋 LISTAR BILHETES

    Lista todos os bilhetes do usuário com filtros
    """
    user_id = int(current_user["user_id"])

    query = db.query(UserTicket).filter(UserTicket.user_id == user_id)

    if status:
        query = query.filter(UserTicket.status == status)

    tickets = query.order_by(UserTicket.created_at.desc())\
        .limit(limit)\
        .offset(offset)\
        .all()

    return tickets


@router.get("/tickets/{ticket_id}", response_model=TicketDetailResponse)
def get_ticket_detail(
    ticket_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    🔍 DETALHES DO BILHETE

    Retorna bilhete com todas as seleções e informações dos jogos
    """
    user_id = int(current_user["user_id"])

    ticket = db.query(UserTicket)\
        .filter(UserTicket.id == ticket_id, UserTicket.user_id == user_id)\
        .first()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bilhete não encontrado"
        )

    # Carregar seleções com info dos jogos
    selections = db.query(TicketSelection)\
        .filter(TicketSelection.ticket_id == ticket_id)\
        .all()

    # Adicionar info dos jogos
    for selection in selections:
        match = db.query(Match).filter(Match.id == selection.match_id).first()
        if match:
            selection.match_info = {
                "home_team": match.home_team,
                "away_team": match.away_team,
                "league": match.league,
                "match_date": match.match_date.isoformat() if match.match_date else None,
                "status": match.status
            }

    ticket.selections = selections

    return ticket


@router.put("/tickets/{ticket_id}", response_model=TicketResponse)
def update_ticket(
    ticket_id: int,
    update_data: TicketUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ✏️ ATUALIZAR BILHETE

    Permite editar notas e nível de confiança
    """
    user_id = int(current_user["user_id"])

    ticket = db.query(UserTicket)\
        .filter(UserTicket.id == ticket_id, UserTicket.user_id == user_id)\
        .first()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bilhete não encontrado"
        )

    # Atualizar campos
    update_dict = update_data.dict(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(ticket, field, value)

    db.commit()
    db.refresh(ticket)

    return ticket


@router.delete("/tickets/{ticket_id}")
def cancel_ticket(
    ticket_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ❌ CANCELAR BILHETE

    Cancela bilhete pendente e devolve stake à banca
    """
    user_id = int(current_user["user_id"])

    ticket = db.query(UserTicket)\
        .filter(UserTicket.id == ticket_id, UserTicket.user_id == user_id)\
        .first()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bilhete não encontrado"
        )

    if ticket.status != TicketStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Apenas bilhetes pendentes podem ser cancelados"
        )

    # Buscar banca
    bankroll = db.query(UserBankroll).filter(UserBankroll.user_id == user_id).first()

    # Devolver stake
    balance_before = bankroll.current_bankroll
    bankroll.current_bankroll += ticket.stake
    bankroll.total_staked -= ticket.stake
    bankroll.total_bets -= 1
    bankroll.pending -= 1

    # Atualizar status
    ticket.status = TicketStatus.CANCELLED

    # Registrar transação
    history = BankrollHistory(
        user_id=user_id,
        transaction_type=TransactionType.REFUND,
        amount=ticket.stake,
        balance_before=balance_before,
        balance_after=bankroll.current_bankroll,
        description=f"Cancelamento - Bilhete #{ticket.id}",
        ticket_id=ticket.id
    )
    db.add(history)

    db.commit()

    return {"message": "Bilhete cancelado e stake devolvido"}


@router.get("/statistics", response_model=TicketStatistics)
def get_user_statistics(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    📊 ESTATÍSTICAS DO USUÁRIO

    Retorna estatísticas completas de apostas
    """
    user_id = int(current_user["user_id"])

    # Buscar todos bilhetes
    all_tickets = db.query(UserTicket).filter(UserTicket.user_id == user_id).all()

    # Contar por status
    total_tickets = len(all_tickets)
    pending = len([t for t in all_tickets if t.status == TicketStatus.PENDING])
    won = len([t for t in all_tickets if t.status == TicketStatus.WON])
    lost = len([t for t in all_tickets if t.status == TicketStatus.LOST])
    cancelled = len([t for t in all_tickets if t.status == TicketStatus.CANCELLED])

    # Calcular win rate (apenas finalizados)
    finished = won + lost
    win_rate = (won / finished * 100) if finished > 0 else 0.0

    # Calcular médias
    avg_odds = sum(t.total_odds for t in all_tickets) / total_tickets if total_tickets > 0 else 0.0
    avg_stake = sum(t.stake for t in all_tickets) / total_tickets if total_tickets > 0 else 0.0

    # Totais financeiros
    total_staked = sum(t.stake for t in all_tickets)
    total_return = sum(t.actual_return for t in all_tickets)
    total_profit = total_return - total_staked

    # ROI
    roi = (total_profit / total_staked * 100) if total_staked > 0 else 0.0

    # Por tipo
    by_type = {}
    for ticket_type in ["single", "multiple", "system"]:
        type_tickets = [t for t in all_tickets if t.ticket_type.value == ticket_type]
        type_won = len([t for t in type_tickets if t.status == TicketStatus.WON])
        type_finished = len([t for t in type_tickets if t.status in [TicketStatus.WON, TicketStatus.LOST]])
        by_type[ticket_type] = {
            "count": len(type_tickets),
            "win_rate": (type_won / type_finished * 100) if type_finished > 0 else 0.0
        }

    # Melhor e pior
    won_tickets = [t for t in all_tickets if t.status == TicketStatus.WON]
    lost_tickets = [t for t in all_tickets if t.status == TicketStatus.LOST]

    best_ticket = max(won_tickets, key=lambda t: t.profit_loss) if won_tickets else None
    worst_ticket = min(lost_tickets, key=lambda t: t.profit_loss) if lost_tickets else None
    biggest_win = best_ticket.profit_loss if best_ticket else None
    biggest_loss = abs(worst_ticket.profit_loss) if worst_ticket else None

    return {
        "total_tickets": total_tickets,
        "pending": pending,
        "won": won,
        "lost": lost,
        "cancelled": cancelled,
        "win_rate": round(win_rate, 2),
        "avg_odds": round(avg_odds, 2),
        "avg_stake": round(avg_stake, 2),
        "total_staked": round(total_staked, 2),
        "total_return": round(total_return, 2),
        "total_profit": round(total_profit, 2),
        "roi": round(roi, 2),
        "by_type": by_type,
        "best_ticket": best_ticket,
        "worst_ticket": worst_ticket,
        "biggest_win": biggest_win,
        "biggest_loss": biggest_loss
    }
