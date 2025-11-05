"""
📝 SCHEMAS DO USUÁRIO

Modelos Pydantic para validação de requests/responses
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
from app.models.user_bankroll import RiskLevel


# =============== AUTH SCHEMAS ===============

class UserRegister(BaseModel):
    """Schema para registro de novo usuário"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)
    full_name: Optional[str] = None
    phone: Optional[str] = None
    initial_bankroll: float = Field(0.0, ge=0)  # Banca inicial

    @validator('username')
    def username_alphanumeric(cls, v):
        assert v.replace('_', '').replace('-', '').isalnum(), 'Username deve ser alfanumérico'
        return v


class UserLogin(BaseModel):
    """Schema para login"""
    username: str
    password: str


class Token(BaseModel):
    """Schema de resposta de autenticação"""
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    """Schema de resposta com dados do usuário"""
    id: int
    email: str
    username: str
    full_name: Optional[str] = None
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


# =============== BANKROLL SCHEMAS ===============

class BankrollResponse(BaseModel):
    """Schema de resposta da banca"""
    id: int
    user_id: int

    # Valores financeiros
    initial_bankroll: float
    current_bankroll: float
    total_deposited: float
    total_withdrawn: float

    # Estatísticas
    total_staked: float
    total_profit: float
    total_return: float
    roi: float
    win_rate: float

    # Contadores
    total_bets: int
    greens: int
    reds: int
    pending: int

    # Controle de risco
    max_bet_percentage: float
    use_kelly_criterion: bool
    risk_level: RiskLevel

    # Metas
    profit_goal: Optional[float] = None
    stop_loss: Optional[float] = None

    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BankrollUpdate(BaseModel):
    """Schema para atualizar configurações da banca"""
    max_bet_percentage: Optional[float] = Field(None, ge=0.1, le=100)
    use_kelly_criterion: Optional[bool] = None
    risk_level: Optional[RiskLevel] = None
    profit_goal: Optional[float] = Field(None, ge=0)
    stop_loss: Optional[float] = Field(None, ge=0)


class DepositRequest(BaseModel):
    """Schema para depósito"""
    amount: float = Field(..., gt=0)
    notes: Optional[str] = None


class WithdrawalRequest(BaseModel):
    """Schema para saque"""
    amount: float = Field(..., gt=0)
    notes: Optional[str] = None


class BankrollResetRequest(BaseModel):
    """Schema para resetar banca inicial"""
    initial_bankroll: float = Field(..., gt=0, description="Novo valor inicial da banca")
    notes: Optional[str] = None


class TransactionResponse(BaseModel):
    """Schema de resposta de transação"""
    id: int
    transaction_type: str
    amount: float
    balance_before: float
    balance_after: float
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# =============== STATISTICS SCHEMAS ===============

class UserStatistics(BaseModel):
    """Estatísticas gerais do usuário"""
    # Performance geral
    total_bets: int
    greens: int
    reds: int
    pending: int
    win_rate: float
    roi: float

    # Financeiro
    total_staked: float
    total_profit: float
    current_bankroll: float

    # Por período (últimos 30 dias)
    last_30_days: dict = {
        "bets": 0,
        "profit": 0.0,
        "roi": 0.0,
        "win_rate": 0.0
    }

    # Top mercados
    best_markets: list = []  # Mercados com melhor performance

    # Top ligas
    best_leagues: list = []  # Ligas com melhor performance


class SuggestedStake(BaseModel):
    """Sugestão de stake para uma aposta"""
    suggested_amount: float
    max_allowed: float
    percentage_of_bankroll: float
    risk_level: str
    kelly_applied: bool
    can_bet: bool
    reason: Optional[str] = None  # Se can_bet = False
