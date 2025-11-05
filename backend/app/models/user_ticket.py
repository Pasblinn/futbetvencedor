"""
🎫 MODELOS DE BILHETES DO USUÁRIO

Sistema completo de gerenciamento de apostas pessoais
"""
from sqlalchemy import Column, Integer, Float, DateTime, Text, String, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class TicketType(str, enum.Enum):
    """Tipo de bilhete"""
    SINGLE = "single"          # Aposta simples (1 seleção)
    MULTIPLE = "multiple"      # Aposta múltipla (2+ seleções)
    SYSTEM = "system"          # Sistema (múltiplas com combinações)


class TicketStatus(str, enum.Enum):
    """Status do bilhete"""
    PENDING = "pending"        # Aguardando resultado
    WON = "won"                # Ganhou (GREEN)
    LOST = "lost"              # Perdeu (RED)
    PARTIALLY_WON = "partially_won"  # Ganho parcial (sistema)
    CANCELLED = "cancelled"    # Cancelado
    CASHED_OUT = "cashed_out"  # Cash out antecipado


class TicketSource(str, enum.Enum):
    """Origem do bilhete"""
    MANUAL = "manual"                  # Criado manualmente pelo usuário
    ML_SUGGESTION = "ml_suggestion"    # Baseado em sugestão da ML
    COPY = "copy"                      # Copiado de outro usuário


class UserTicket(Base):
    """
    🎫 BILHETE DO USUÁRIO

    Representa uma aposta completa com uma ou mais seleções
    """
    __tablename__ = "user_tickets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Tipo e origem
    ticket_type = Column(SQLEnum(TicketType), default=TicketType.SINGLE)
    source = Column(SQLEnum(TicketSource), default=TicketSource.MANUAL)

    # Valores financeiros
    stake = Column(Float, nullable=False)           # Valor apostado
    total_odds = Column(Float, nullable=False)      # Odd total
    potential_return = Column(Float, nullable=False) # Retorno potencial (stake * odds)
    actual_return = Column(Float, default=0.0)      # Retorno real recebido
    profit_loss = Column(Float, default=0.0)        # Lucro/prejuízo (return - stake)

    # Status
    status = Column(SQLEnum(TicketStatus), default=TicketStatus.PENDING)

    # Metadata
    notes = Column(Text)                            # Notas/análise do usuário
    confidence_level = Column(String)               # 'high', 'medium', 'low'

    # Estatísticas das seleções
    selections_count = Column(Integer, default=0)
    selections_won = Column(Integer, default=0)
    selections_lost = Column(Integer, default=0)
    selections_pending = Column(Integer, default=0)
    selections_void = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    settled_at = Column(DateTime(timezone=True))    # Quando foi finalizado

    # Relationships
    user = relationship("User", back_populates="tickets")
    selections = relationship("TicketSelection", back_populates="ticket", cascade="all, delete-orphan")

    def update_status(self):
        """
        Atualiza o status do bilhete baseado nas seleções

        Lógica:
        - Se alguma perdeu em múltipla → LOST
        - Se todas ganharam → WON
        - Se algumas ganharam (sistema) → PARTIALLY_WON
        - Se todas pendentes → PENDING
        """
        if self.selections_count == 0:
            return

        if self.ticket_type == TicketType.MULTIPLE:
            # Múltipla: todas devem ganhar
            if self.selections_lost > 0:
                self.status = TicketStatus.LOST
                self.profit_loss = -self.stake
            elif self.selections_won == self.selections_count:
                self.status = TicketStatus.WON
                self.actual_return = self.potential_return
                self.profit_loss = self.actual_return - self.stake
            # Permanece PENDING se houver alguma pendente

        elif self.ticket_type == TicketType.SINGLE:
            # Simples: baseado na única seleção
            if self.selections_lost > 0:
                self.status = TicketStatus.LOST
                self.profit_loss = -self.stake
            elif self.selections_won > 0:
                self.status = TicketStatus.WON
                self.actual_return = self.potential_return
                self.profit_loss = self.actual_return - self.stake

        elif self.ticket_type == TicketType.SYSTEM:
            # Sistema: pode ter ganho parcial
            if self.selections_lost > 0 and self.selections_won > 0:
                self.status = TicketStatus.PARTIALLY_WON
                # Calcular retorno parcial (implementar lógica de sistema)
            elif self.selections_lost > 0:
                self.status = TicketStatus.LOST
                self.profit_loss = -self.stake
            elif self.selections_won == self.selections_count:
                self.status = TicketStatus.WON
                self.actual_return = self.potential_return
                self.profit_loss = self.actual_return - self.stake

    def __repr__(self):
        return f"<UserTicket(id={self.id}, stake=R${self.stake:.2f}, odds={self.total_odds:.2f}, status={self.status})>"


class SelectionStatus(str, enum.Enum):
    """Status da seleção individual"""
    PENDING = "pending"        # Aguardando resultado
    WON = "won"                # Ganhou
    LOST = "lost"              # Perdeu
    VOID = "void"              # Anulada (jogo cancelado, etc)


class TicketSelection(Base):
    """
    ⚽ SELEÇÃO DO BILHETE

    Uma escolha individual dentro de um bilhete
    Cada seleção representa um mercado específico de uma partida
    """
    __tablename__ = "ticket_selections"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("user_tickets.id"), nullable=False)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)

    # Mercado e escolha
    market = Column(String, nullable=False)         # '1X2', 'Over/Under 2.5', 'BTTS', etc
    outcome = Column(String, nullable=False)        # 'Home', 'Over', 'Yes', etc
    odd = Column(Float, nullable=False)             # Odd no momento da aposta

    # Resultado
    status = Column(SQLEnum(SelectionStatus), default=SelectionStatus.PENDING)
    actual_outcome = Column(String)                 # Resultado real que ocorreu

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    settled_at = Column(DateTime(timezone=True))    # Quando foi resolvida

    # Relationships
    ticket = relationship("UserTicket", back_populates="selections")
    match = relationship("Match")

    def check_result(self, match_result: dict):
        """
        Verifica o resultado da seleção baseado no resultado da partida

        Args:
            match_result: Dict com dados do resultado
                - home_score
                - away_score
                - corners, cards, etc (se aplicável)
        """
        home_score = match_result.get('home_score')
        away_score = match_result.get('away_score')

        if home_score is None or away_score is None:
            return  # Jogo ainda não finalizado

        # Lógica por mercado
        if self.market == '1X2' or self.market == 'Match Winner':
            if home_score > away_score:
                actual = 'Home'
            elif home_score < away_score:
                actual = 'Away'
            else:
                actual = 'Draw'

            self.actual_outcome = actual
            self.status = SelectionStatus.WON if actual == self.outcome else SelectionStatus.LOST

        elif 'Over/Under' in self.market:
            # Extrair linha (ex: "Over/Under 2.5" → 2.5)
            try:
                line = float(self.market.split()[-1])
                total_goals = home_score + away_score

                if 'Over' in self.outcome:
                    self.status = SelectionStatus.WON if total_goals > line else SelectionStatus.LOST
                else:  # Under
                    self.status = SelectionStatus.WON if total_goals < line else SelectionStatus.LOST

                self.actual_outcome = f"Total: {total_goals}"
            except:
                pass

        elif self.market == 'BTTS' or 'Both Teams' in self.market:
            both_scored = home_score > 0 and away_score > 0

            if 'Yes' in self.outcome:
                self.status = SelectionStatus.WON if both_scored else SelectionStatus.LOST
            else:  # No
                self.status = SelectionStatus.WON if not both_scored else SelectionStatus.LOST

            self.actual_outcome = f"BTTS: {'Yes' if both_scored else 'No'}"

        # Atualizar timestamp
        if self.status in [SelectionStatus.WON, SelectionStatus.LOST]:
            self.settled_at = func.now()

    def __repr__(self):
        return f"<Selection(match_id={self.match_id}, market={self.market}, outcome={self.outcome}, odd={self.odd:.2f}, status={self.status})>"
