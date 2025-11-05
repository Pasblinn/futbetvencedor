"""
🎫 SCHEMAS DE BILHETES

Modelos Pydantic para bilhetes e seleções do usuário
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from app.models.user_ticket import TicketType, TicketStatus, TicketSource, SelectionStatus


# =============== SELECTION SCHEMAS ===============

class SelectionCreate(BaseModel):
    """Schema para criar uma seleção"""
    match_id: int
    market: str = Field(..., min_length=1, max_length=100)
    outcome: str = Field(..., min_length=1, max_length=100)
    odd: float = Field(..., gt=1.0)  # Odd deve ser > 1.0

    @validator('market')
    def valid_market(cls, v):
        valid_markets = [
            '1X2', 'Match Winner',
            'Over/Under 0.5', 'Over/Under 1.5', 'Over/Under 2.5', 'Over/Under 3.5',
            'BTTS', 'Both Teams To Score',
            'Asian Handicap',
            'Corners', 'Cards'
        ]
        # Validação mais flexível - apenas verificar se contém palavras-chave
        return v


class SelectionResponse(BaseModel):
    """Schema de resposta de seleção"""
    id: int
    match_id: int
    market: str
    outcome: str
    odd: float
    status: SelectionStatus
    actual_outcome: Optional[str] = None
    created_at: datetime
    settled_at: Optional[datetime] = None

    # Info do jogo (opcional, preenchido via join)
    match_info: Optional[dict] = None

    class Config:
        from_attributes = True


# =============== TICKET SCHEMAS ===============

class TicketCreate(BaseModel):
    """Schema para criar um bilhete"""
    selections: List[SelectionCreate] = Field(..., min_items=1, max_items=20)
    stake: float = Field(..., gt=0)
    ticket_type: Optional[TicketType] = None  # Auto-detect se não fornecido
    notes: Optional[str] = Field(None, max_length=1000)
    confidence_level: Optional[str] = Field(None, pattern='^(high|medium|low)$')

    @validator('ticket_type', always=True)
    def determine_ticket_type(cls, v, values):
        """Auto-detecta o tipo de bilhete baseado no número de seleções"""
        if v is None and 'selections' in values:
            selections_count = len(values['selections'])
            if selections_count == 1:
                return TicketType.SINGLE
            else:
                return TicketType.MULTIPLE
        return v or TicketType.SINGLE

    @validator('selections')
    def validate_selections(cls, v):
        """Validações adicionais nas seleções"""
        # Verificar duplicatas (mesmo jogo + mesmo mercado)
        seen = set()
        for sel in v:
            key = (sel.match_id, sel.market)
            if key in seen:
                raise ValueError(f"Seleção duplicada: jogo {sel.match_id}, mercado {sel.market}")
            seen.add(key)
        return v


class TicketResponse(BaseModel):
    """Schema de resposta de bilhete"""
    id: int
    user_id: int
    ticket_type: TicketType
    source: TicketSource
    stake: float
    total_odds: float
    potential_return: float
    actual_return: float
    profit_loss: float
    status: TicketStatus
    notes: Optional[str] = None
    confidence_level: Optional[str] = None

    # Estatísticas
    selections_count: int
    selections_won: int
    selections_lost: int
    selections_pending: int

    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    settled_at: Optional[datetime] = None

    # Seleções (opcional)
    selections: Optional[List[SelectionResponse]] = None

    class Config:
        from_attributes = True


class TicketDetailResponse(TicketResponse):
    """Schema de resposta com detalhes completos (inclui seleções)"""
    selections: List[SelectionResponse]


class TicketUpdate(BaseModel):
    """Schema para atualizar um bilhete (apenas notas/confidence)"""
    notes: Optional[str] = Field(None, max_length=1000)
    confidence_level: Optional[str] = Field(None, pattern='^(high|medium|low)$')


class TicketListFilter(BaseModel):
    """Filtros para listagem de bilhetes"""
    status: Optional[TicketStatus] = None
    ticket_type: Optional[TicketType] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_odds: Optional[float] = None
    max_odds: Optional[float] = None
    limit: int = Field(50, ge=1, le=200)
    offset: int = Field(0, ge=0)


class TicketListResponse(BaseModel):
    """Schema de resposta de lista de bilhetes"""
    tickets: List[TicketResponse]
    total: int
    page: int
    page_size: int
    has_next: bool


# =============== VALIDATION SCHEMAS ===============

class StakeValidation(BaseModel):
    """Validação de stake antes de criar bilhete"""
    stake: float
    total_odds: float


class StakeValidationResponse(BaseModel):
    """Resposta da validação de stake"""
    can_bet: bool
    suggested_stake: float
    max_allowed_stake: float
    percentage_of_bankroll: float
    current_bankroll: float
    potential_return: float
    potential_profit: float
    warnings: List[str] = []
    errors: List[str] = []


# =============== SETTLEMENT SCHEMAS ===============

class SettleTicketRequest(BaseModel):
    """Request para finalizar um bilhete (admin/system)"""
    ticket_id: int
    force_status: Optional[TicketStatus] = None  # Forçar status específico


class BulkSettleRequest(BaseModel):
    """Request para finalizar múltiplos bilhetes"""
    match_id: int  # Finalizar todos bilhetes deste jogo


# =============== STATISTICS SCHEMAS ===============

class TicketStatistics(BaseModel):
    """Estatísticas de bilhetes do usuário"""
    total_tickets: int
    pending: int
    won: int
    lost: int
    cancelled: int

    win_rate: float
    avg_odds: float
    avg_stake: float
    total_staked: float
    total_return: float
    total_profit: float
    roi: float

    # Por tipo
    by_type: dict = {
        "single": {"count": 0, "win_rate": 0.0},
        "multiple": {"count": 0, "win_rate": 0.0},
        "system": {"count": 0, "win_rate": 0.0}
    }

    # Melhores e piores
    best_ticket: Optional[TicketResponse] = None
    worst_ticket: Optional[TicketResponse] = None
    biggest_win: Optional[float] = None
    biggest_loss: Optional[float] = None
