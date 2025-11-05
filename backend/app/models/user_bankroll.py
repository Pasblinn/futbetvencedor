"""
💰 MODELOS DE BANCA DO USUÁRIO

Gestão financeira completa e histórico de transações
"""
from sqlalchemy import Column, Integer, Float, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class RiskLevel(str, enum.Enum):
    """Nível de risco do usuário"""
    CONSERVATIVE = "conservative"  # Conservador
    MODERATE = "moderate"          # Moderado
    AGGRESSIVE = "aggressive"      # Agressivo


class UserBankroll(Base):
    """
    💰 BANCA DO USUÁRIO

    Controle financeiro completo e estatísticas de performance
    """
    __tablename__ = "user_bankrolls"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    # Valores financeiros
    initial_bankroll = Column(Float, default=0.0)
    current_bankroll = Column(Float, default=0.0)
    total_deposited = Column(Float, default=0.0)
    total_withdrawn = Column(Float, default=0.0)

    # Estatísticas de apostas
    total_staked = Column(Float, default=0.0)      # Total apostado
    total_profit = Column(Float, default=0.0)      # Lucro líquido
    total_return = Column(Float, default=0.0)      # Retorno total

    # Performance
    roi = Column(Float, default=0.0)               # Return on Investment (%)
    win_rate = Column(Float, default=0.0)          # Taxa de acerto (%)

    # Contadores
    total_bets = Column(Integer, default=0)
    greens = Column(Integer, default=0)            # Apostas vencedoras
    reds = Column(Integer, default=0)              # Apostas perdedoras
    pending = Column(Integer, default=0)           # Apostas pendentes

    # Controle de risco
    max_bet_percentage = Column(Float, default=5.0)  # % máxima por aposta
    use_kelly_criterion = Column(Boolean, default=False)
    risk_level = Column(SQLEnum(RiskLevel), default=RiskLevel.MODERATE)

    # Metas
    profit_goal = Column(Float)                    # Meta de lucro
    stop_loss = Column(Float)                      # Stop loss

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="bankroll")

    def calculate_roi(self):
        """Calcula ROI baseado no total apostado"""
        if self.total_staked > 0:
            self.roi = (self.total_profit / self.total_staked) * 100
        else:
            self.roi = 0.0
        return self.roi

    def calculate_win_rate(self):
        """Calcula taxa de vitórias"""
        total = self.greens + self.reds
        if total > 0:
            self.win_rate = (self.greens / total) * 100
        else:
            self.win_rate = 0.0
        return self.win_rate

    def can_place_bet(self, stake: float) -> bool:
        """Verifica se o usuário pode fazer a aposta"""
        if stake > self.current_bankroll:
            return False

        # Verifica porcentagem máxima
        max_allowed = (self.max_bet_percentage / 100) * self.current_bankroll
        if stake > max_allowed:
            return False

        # Verifica stop loss
        if self.stop_loss and self.current_bankroll <= self.stop_loss:
            return False

        return True

    def suggested_stake(self, odds: float, confidence: float = 0.6) -> float:
        """
        Calcula stake sugerido usando Kelly Criterion (opcional)

        Args:
            odds: Odd da aposta
            confidence: Confiança na aposta (0-1)

        Returns:
            Valor sugerido para apostar
        """
        if self.use_kelly_criterion:
            # Kelly Criterion: f = (bp - q) / b
            # f = fração da banca
            # b = odds - 1 (net odds)
            # p = probabilidade de ganhar (confidence)
            # q = probabilidade de perder (1 - p)

            b = odds - 1
            p = confidence
            q = 1 - p

            kelly_fraction = (b * p - q) / b

            # Aplicar fração conservadora (25% do Kelly)
            conservative_fraction = max(0, kelly_fraction * 0.25)

            # Limitar pela porcentagem máxima
            max_fraction = self.max_bet_percentage / 100
            final_fraction = min(conservative_fraction, max_fraction)

            return round(self.current_bankroll * final_fraction, 2)
        else:
            # Usar porcentagem fixa baseada no nível de risco
            if self.risk_level == RiskLevel.CONSERVATIVE:
                fraction = 0.02  # 2%
            elif self.risk_level == RiskLevel.MODERATE:
                fraction = 0.05  # 5%
            else:  # AGGRESSIVE
                fraction = 0.10  # 10%

            return round(self.current_bankroll * fraction, 2)

    def __repr__(self):
        return f"<Bankroll(user_id={self.user_id}, current=R${self.current_bankroll:.2f}, roi={self.roi:.1f}%)>"


class TransactionType(str, enum.Enum):
    """Tipo de transação"""
    DEPOSIT = "deposit"        # Depósito
    WITHDRAWAL = "withdrawal"  # Saque
    BET = "bet"               # Aposta feita
    WIN = "win"               # Prêmio recebido
    LOSS = "loss"             # Perda
    REFUND = "refund"         # Reembolso
    BONUS = "bonus"           # Bônus
    ADJUSTMENT = "adjustment"  # Ajuste manual


class BankrollHistory(Base):
    """
    📊 HISTÓRICO DA BANCA

    Registra todas as movimentações financeiras do usuário
    """
    __tablename__ = "bankroll_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ticket_id = Column(Integer, ForeignKey("user_tickets.id"), nullable=True)

    # Transação
    transaction_type = Column(SQLEnum(TransactionType), nullable=False)
    amount = Column(Float, nullable=False)
    balance_before = Column(Float, nullable=False)
    balance_after = Column(Float, nullable=False)

    # Descrição
    description = Column(Text)
    notes = Column(Text)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="bankroll_history")
    ticket = relationship("UserTicket", foreign_keys=[ticket_id])

    def __repr__(self):
        return f"<BankrollHistory(type={self.transaction_type}, amount=R${self.amount:.2f}, balance=R${self.balance_after:.2f})>"
