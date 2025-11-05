#!/usr/bin/env python3
"""
Migration: Adicionar campos para tickets manuais (GOLD DATA)
"""
import sqlite3
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent / "football_analytics.db"

def migrate():
    """Adiciona colunas para tracking de tickets manuais"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    try:
        # Verificar se colunas já existem
        cursor.execute("PRAGMA table_info(bet_combinations)")
        columns = [col[1] for col in cursor.fetchall()]

        # Adicionar is_manual
        if 'is_manual' not in columns:
            cursor.execute('''
                ALTER TABLE bet_combinations
                ADD COLUMN is_manual BOOLEAN DEFAULT 0
            ''')
            print("✅ Coluna 'is_manual' adicionada")
        else:
            print("⏭️  Coluna 'is_manual' já existe")

        # Adicionar created_by
        if 'created_by' not in columns:
            cursor.execute('''
                ALTER TABLE bet_combinations
                ADD COLUMN created_by VARCHAR
            ''')
            print("✅ Coluna 'created_by' adicionada")
        else:
            print("⏭️  Coluna 'created_by' já existe")

        # Adicionar notes
        if 'notes' not in columns:
            cursor.execute('''
                ALTER TABLE bet_combinations
                ADD COLUMN notes TEXT
            ''')
            print("✅ Coluna 'notes' adicionada")
        else:
            print("⏭️  Coluna 'notes' já existe")

        conn.commit()
        print("\n🎉 Migração concluída com sucesso!")
        print("Tickets manuais agora podem ser salvos como GOLD DATA para ML")

    except Exception as e:
        conn.rollback()
        print(f"❌ Erro na migração: {e}")
        raise

    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
