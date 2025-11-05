"""
🔧 SCRIPT DE INICIALIZAÇÃO DO BANCO DE DADOS

Cria TODAS as tabelas necessárias para o sistema funcionar.

IMPORTANTE: Execute este script ANTES de rodar o sistema pela primeira vez!

Uso:
    python init_database.py
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from sqlalchemy import create_engine
from app.core.database import Base
from app.models import (
    Match, Team, Odds, Prediction,
    BetCombination, User, UserBankroll,
    BankrollHistory, UserTicket, TicketSelection
)

print("🔧 INICIALIZANDO BANCO DE DADOS")
print("="*80)

# Create database
DATABASE_URL = f"sqlite:///{backend_path}/football_analytics.db"
engine = create_engine(DATABASE_URL, echo=True)

print("\n📊 Criando todas as tabelas...")
Base.metadata.create_all(bind=engine)

print("\n✅ BANCO DE DADOS INICIALIZADO COM SUCESSO!")
print("="*80)

# List created tables
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()

print(f"\n📋 Tabelas criadas ({len(tables)}):")
for table in sorted(tables):
    print(f"  ✓ {table}")

print("\n🚀 Sistema pronto para uso!")
