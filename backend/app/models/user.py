"""
👤 MODELO DE USUÁRIO

Sistema completo de autenticação e perfil
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    """
    Modelo de Usuário

    Armazena dados básicos, autenticação e relacionamentos
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    # Perfil
    full_name = Column(String)
    phone = Column(String)

    # Status
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))

    # Relationships
    bankroll = relationship("UserBankroll", back_populates="user", uselist=False, cascade="all, delete-orphan")
    tickets = relationship("UserTicket", back_populates="user", cascade="all, delete-orphan")
    bankroll_history = relationship("BankrollHistory", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"
