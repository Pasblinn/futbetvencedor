"""
💰 ENDPOINTS DE GESTÃO DE BANCA

Sistema completo de gerenciamento financeiro do usuário
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user_bankroll import UserBankroll, BankrollHistory, TransactionType
from app.schemas.user_schemas import (
    BankrollResponse,
    BankrollUpdate,
    DepositRequest,
    WithdrawalRequest,
    BankrollResetRequest,
    TransactionResponse
)

router = APIRouter()


@router.get("/bankroll", response_model=BankrollResponse)
def get_user_bankroll(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    💰 OBTER BANCA DO USUÁRIO

    Retorna todas as informações da banca e estatísticas
    🔧 Se não existir, cria automaticamente com valores padrão
    """
    user_id = int(current_user["user_id"])

    bankroll = db.query(UserBankroll).filter(UserBankroll.user_id == user_id).first()

    if not bankroll:
        # 🔧 CORRIGIDO: Criar banca automaticamente com valores padrão
        bankroll = UserBankroll(
            user_id=user_id,
            initial_bankroll=1000.0,  # Valor padrão inicial
            current_bankroll=1000.0,
            max_bet_percentage=5.0,
            use_kelly_criterion=False,
            risk_level="medium",
            profit_goal=None,
            stop_loss=None
        )
        db.add(bankroll)
        db.commit()
        db.refresh(bankroll)

    return bankroll


@router.put("/bankroll/settings", response_model=BankrollResponse)
def update_bankroll_settings(
    settings: BankrollUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ⚙️ ATUALIZAR CONFIGURAÇÕES DA BANCA

    Permite alterar:
    - Percentual máximo de aposta
    - Uso do Kelly Criterion
    - Nível de risco
    - Metas de lucro e stop loss
    """
    user_id = int(current_user["user_id"])

    bankroll = db.query(UserBankroll).filter(UserBankroll.user_id == user_id).first()

    if not bankroll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Banca não encontrada"
        )

    # Atualizar campos fornecidos
    update_data = settings.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(bankroll, field, value)

    db.commit()
    db.refresh(bankroll)

    return bankroll


@router.post("/bankroll/deposit", response_model=TransactionResponse)
def deposit_funds(
    deposit: DepositRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    💵 DEPOSITAR FUNDOS

    Adiciona valor à banca e registra no histórico
    """
    user_id = int(current_user["user_id"])

    bankroll = db.query(UserBankroll).filter(UserBankroll.user_id == user_id).first()

    if not bankroll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Banca não encontrada"
        )

    # Salvar valores antes da transação
    balance_before = bankroll.current_bankroll

    # Atualizar banca
    bankroll.current_bankroll += deposit.amount
    bankroll.total_deposited += deposit.amount

    # Criar registro no histórico
    history = BankrollHistory(
        user_id=user_id,
        transaction_type=TransactionType.DEPOSIT,
        amount=deposit.amount,
        balance_before=balance_before,
        balance_after=bankroll.current_bankroll,
        description=deposit.notes or f"Depósito de R$ {deposit.amount:.2f}"
    )

    db.add(history)
    db.commit()
    db.refresh(history)

    return history


@router.post("/bankroll/withdraw", response_model=TransactionResponse)
def withdraw_funds(
    withdrawal: WithdrawalRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    💸 SACAR FUNDOS

    Remove valor da banca e registra no histórico
    """
    user_id = int(current_user["user_id"])

    bankroll = db.query(UserBankroll).filter(UserBankroll.user_id == user_id).first()

    if not bankroll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Banca não encontrada"
        )

    # Verificar se há saldo suficiente
    if bankroll.current_bankroll < withdrawal.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Saldo insuficiente. Disponível: R$ {bankroll.current_bankroll:.2f}"
        )

    # Salvar valores antes da transação
    balance_before = bankroll.current_bankroll

    # Atualizar banca
    bankroll.current_bankroll -= withdrawal.amount
    bankroll.total_withdrawn += withdrawal.amount

    # Criar registro no histórico
    history = BankrollHistory(
        user_id=user_id,
        transaction_type=TransactionType.WITHDRAWAL,
        amount=withdrawal.amount,
        balance_before=balance_before,
        balance_after=bankroll.current_bankroll,
        description=withdrawal.notes or f"Saque de R$ {withdrawal.amount:.2f}"
    )

    db.add(history)
    db.commit()
    db.refresh(history)

    return history


@router.post("/bankroll/reset", response_model=BankrollResponse)
def reset_bankroll(
    reset_data: BankrollResetRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    🔄 RESETAR BANCA INICIAL

    Redefine o valor inicial da banca e reseta a banca atual.
    ATENÇÃO: Esta ação não pode ser desfeita!
    """
    user_id = int(current_user["user_id"])

    bankroll = db.query(UserBankroll).filter(UserBankroll.user_id == user_id).first()

    if not bankroll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Banca não encontrada"
        )

    # Salvar valores antigos
    old_initial = bankroll.initial_bankroll
    old_current = bankroll.current_bankroll

    # Resetar valores
    bankroll.initial_bankroll = reset_data.initial_bankroll
    bankroll.current_bankroll = reset_data.initial_bankroll

    # Criar registro no histórico
    history = BankrollHistory(
        user_id=user_id,
        transaction_type=TransactionType.ADJUSTMENT,
        amount=reset_data.initial_bankroll - old_current,
        balance_before=old_current,
        balance_after=reset_data.initial_bankroll,
        description=reset_data.notes or f"Reset de banca: R$ {old_initial:.2f} → R$ {reset_data.initial_bankroll:.2f}"
    )

    db.add(history)
    db.commit()
    db.refresh(bankroll)

    return bankroll


@router.get("/bankroll/history", response_model=List[TransactionResponse])
def get_transaction_history(
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    📜 HISTÓRICO DE TRANSAÇÕES

    Lista todas as movimentações financeiras da banca
    """
    user_id = int(current_user["user_id"])

    history = db.query(BankrollHistory)\
        .filter(BankrollHistory.user_id == user_id)\
        .order_by(BankrollHistory.created_at.desc())\
        .limit(limit)\
        .offset(offset)\
        .all()

    return history


@router.get("/bankroll/stake-suggestion")
def get_stake_suggestion(
    odds: float,
    confidence: float = 0.6,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    💡 SUGESTÃO DE STAKE

    Calcula stake sugerido baseado em:
    - Kelly Criterion (se habilitado)
    - Percentual máximo permitido
    - Nível de risco configurado
    - Banca atual

    Parâmetros:
    - odds: Odd da aposta
    - confidence: Confiança na aposta (0.0 - 1.0)
    """
    user_id = int(current_user["user_id"])

    bankroll = db.query(UserBankroll).filter(UserBankroll.user_id == user_id).first()

    if not bankroll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Banca não encontrada"
        )

    # Calcular stake sugerido
    suggested = bankroll.suggested_stake(odds, confidence)

    # Calcular stake máximo permitido
    max_allowed = bankroll.current_bankroll * (bankroll.max_bet_percentage / 100)

    # Garantir que sugestão não excede máximo
    final_suggestion = min(suggested, max_allowed)

    # Verificar se pode apostar
    can_bet = bankroll.can_place_bet(final_suggestion)

    return {
        "suggested_amount": round(final_suggestion, 2),
        "max_allowed": round(max_allowed, 2),
        "percentage_of_bankroll": round((final_suggestion / bankroll.current_bankroll) * 100, 2),
        "risk_level": bankroll.risk_level.value,
        "kelly_applied": bankroll.use_kelly_criterion,
        "can_bet": can_bet,
        "current_bankroll": round(bankroll.current_bankroll, 2),
        "potential_return": round(final_suggestion * odds, 2),
        "potential_profit": round(final_suggestion * (odds - 1), 2),
        "reason": None if can_bet else "Saldo insuficiente ou stake muito baixo"
    }
