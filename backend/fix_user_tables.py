#!/usr/bin/env python3
"""
🔧 FIX: Recriar tabelas de usuário com schema correto
"""
from app.core.database import Base, engine
from app.models.user import User
from app.models.user_bankroll import UserBankroll, BankrollHistory
from app.models.user_ticket import UserTicket, TicketSelection
from sqlalchemy import inspect

def fix_user_tables():
    """Remove tabelas antigas e recria com schema correto"""
    print("=" * 60)
    print("🔧 RECRIANDO TABELAS DE USUÁRIO")
    print("=" * 60)

    # Verificar tabelas existentes
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    user_tables = ['users', 'user_bankrolls', 'user_tickets', 'ticket_selections', 'bankroll_history']

    print("\n📋 Verificando tabelas existentes...")
    for table in user_tables:
        if table in existing_tables:
            print(f"  ⚠️  {table} existe - será recriada")
        else:
            print(f"  ✓ {table} não existe - será criada")

    # Dropar tabelas de usuário (ordem inversa por causa das FKs)
    print("\n🗑️  Removendo tabelas antigas...")
    Base.metadata.drop_all(
        bind=engine,
        tables=[
            BankrollHistory.__table__,
            TicketSelection.__table__,
            UserTicket.__table__,
            UserBankroll.__table__,
            User.__table__
        ]
    )
    print("  ✓ Tabelas antigas removidas")

    # Criar tabelas com schema correto
    print("\n🔄 Criando tabelas com schema correto...")
    Base.metadata.create_all(
        bind=engine,
        tables=[
            User.__table__,
            UserBankroll.__table__,
            UserTicket.__table__,
            TicketSelection.__table__,
            BankrollHistory.__table__
        ]
    )
    print("  ✓ Tabelas criadas com sucesso")

    # Verificar resultado
    inspector = inspect(engine)
    all_tables = inspector.get_table_names()

    print("\n📊 Tabelas no banco de dados:")
    for table in sorted(all_tables):
        print(f"  ✓ {table}")

    print("\n" + "=" * 60)
    print("✅ MIGRAÇÃO CONCLUÍDA!")
    print("=" * 60)

if __name__ == "__main__":
    fix_user_tables()
