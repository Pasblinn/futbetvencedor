"""
🔐 ENDPOINTS DE AUTENTICAÇÃO

Sistema de registro e login de usuários
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.rate_limiter import limiter
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user
)
from app.models.user import User
from app.models.user_bankroll import UserBankroll, TransactionType, BankrollHistory
from app.schemas.user_schemas import (
    UserRegister,
    UserLogin,
    Token,
    UserResponse
)

router = APIRouter()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def register_user(request: Request, user_data: UserRegister, db: Session = Depends(get_db)):
    """
    🆕 REGISTRAR NOVO USUÁRIO

    Cria conta e inicializa banca
    """
    # Verificar se email já existe
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já cadastrado"
        )

    # Verificar se username já existe
    existing_username = db.query(User).filter(User.username == user_data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username já cadastrado"
        )

    # Criar usuário
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        phone=user_data.phone,
        is_active=True,
        is_verified=False
    )

    db.add(new_user)
    db.flush()  # Obter ID sem commitar ainda

    # Criar banca inicial
    bankroll = UserBankroll(
        user_id=new_user.id,
        initial_bankroll=user_data.initial_bankroll,
        current_bankroll=user_data.initial_bankroll,
        total_deposited=user_data.initial_bankroll
    )

    db.add(bankroll)

    # Registrar transação inicial se houver depósito
    if user_data.initial_bankroll > 0:
        history = BankrollHistory(
            user_id=new_user.id,
            transaction_type=TransactionType.DEPOSIT,
            amount=user_data.initial_bankroll,
            balance_before=0.0,
            balance_after=user_data.initial_bankroll,
            description="Depósito inicial"
        )
        db.add(history)

    db.commit()
    db.refresh(new_user)

    # Criar token de acesso
    access_token = create_access_token(
        data={"sub": str(new_user.id), "username": new_user.username}
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.from_orm(new_user)
    )


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
def login(request: Request, credentials: UserLogin, db: Session = Depends(get_db)):
    """
    🔑 LOGIN

    Autentica usuário e retorna token JWT
    """
    # Buscar usuário
    user = db.query(User).filter(User.username == credentials.username).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verificar senha
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verificar se usuário está ativo
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo"
        )

    # Atualizar último login
    user.last_login = datetime.utcnow()
    db.commit()

    # Criar token de acesso
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username}
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.from_orm(user)
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    👤 OBTER DADOS DO USUÁRIO ATUAL

    Retorna informações do usuário autenticado
    """
    user_id = int(current_user["user_id"])
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )

    return UserResponse.from_orm(user)


@router.post("/refresh", response_model=Token)
def refresh_token(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    🔄 RENOVAR TOKEN

    Gera novo token para usuário autenticado
    """
    user_id = int(current_user["user_id"])
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )

    # Criar novo token
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username}
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.from_orm(user)
    )
