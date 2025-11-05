#!/usr/bin/env python3
"""
🔧 MIGRAÇÃO: CRIAR TABELAS DE USUÁRIO

Adiciona todas as tabelas necessárias para o sistema de usuários:
- users
- user_bankrolls
- user_tickets
- ticket_selections
- bankroll_history
"""
from app.core.database import Base, engine
from app.models.user import User
from app.models.user_bankroll import UserBankroll, BankrollHistory
from app.models.user_ticket import UserTicket, TicketSelection

def create_user_tables():
    """Cria todas as tabelas de usuário no banco"""
    print("=" * 60)
    print("🔧 CRIANDO TABELAS DE USUÁRIO")
    print("=" * 60)

    print("\n📋 Tabelas a serem criadas:")
    print("  1. users - Dados dos usuários")
    print("  2. user_bankrolls - Banca e estatísticas")
    print("  3. user_tickets - Bilhetes de apostas")
    print("  4. ticket_selections - Seleções dos bilhetes")
    print("  5. bankroll_history - Histórico financeiro")

    print("\n🔄 Criando tabelas...")

    try:
        # Criar todas as tabelas baseadas nos modelos
        Base.metadata.create_all(bind=engine, checkfirst=True)

        print("\n✅ Tabelas criadas com sucesso!")

        # Verificar tabelas criadas
        from sqlalchemy import inspect
        inspector = inspect(engine)
        all_tables = inspector.get_table_names()

        print("\n📊 Tabelas no banco de dados:")
        for table in sorted(all_tables):
            print(f"  ✓ {table}")

        print("\n" + "=" * 60)
        print("✅ MIGRAÇÃO CONCLUÍDA!")
        print("=" * 60)

        print("\n🎯 Próximo passo:")
        print("   Testar registro de usuário:")
        print("   POST http://localhost:8000/api/v1/auth/register")

    except Exception as e:
        print(f"\n❌ Erro ao criar tabelas: {e}")
        raise

if __name__ == "__main__":
    create_user_tables()
