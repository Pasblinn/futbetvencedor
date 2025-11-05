#!/usr/bin/env python3
"""
Criar tabela bet_combinations com todos os campos necessários no DB DEV
"""
import sqlite3
from pathlib import Path

# Database path - DEV
DB_PATH = Path(__file__).parent / "football_analytics_dev.db"

def create_table():
    """Cria tabela bet_combinations se não existir"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    try:
        # Listar tabelas existentes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📋 Tabelas existentes: {', '.join(tables) if tables else 'nenhuma'}")

        # Verificar se bet_combinations existe
        if 'bet_combinations' not in tables:
            print("\n🔨 Criando tabela bet_combinations...")

            cursor.execute('''
                CREATE TABLE bet_combinations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    combination_type VARCHAR NOT NULL,
                    selections_count INTEGER NOT NULL,
                    total_odds FLOAT NOT NULL,
                    min_odds FLOAT DEFAULT 1.5,
                    max_odds FLOAT DEFAULT 2.0,
                    target_confidence FLOAT DEFAULT 0.95,
                    combined_probability FLOAT,
                    combined_confidence FLOAT,
                    expected_value FLOAT,
                    risk_score FLOAT,
                    prediction_ids TEXT NOT NULL,
                    selection_details TEXT,
                    is_recommended BOOLEAN DEFAULT 0,
                    recommendation_reason TEXT,
                    risk_level VARCHAR,
                    is_settled BOOLEAN DEFAULT 0,
                    is_winner BOOLEAN,
                    actual_return FLOAT,
                    is_manual BOOLEAN DEFAULT 0,
                    created_by VARCHAR,
                    notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME
                )
            ''')

            print("✅ Tabela bet_combinations criada com sucesso!")
        else:
            print("\n⏭️  Tabela bet_combinations já existe")

            # Verificar e adicionar colunas se necessário
            cursor.execute("PRAGMA table_info(bet_combinations)")
            columns = [col[1] for col in cursor.fetchall()]

            if 'is_manual' not in columns:
                cursor.execute('ALTER TABLE bet_combinations ADD COLUMN is_manual BOOLEAN DEFAULT 0')
                print("✅ Coluna 'is_manual' adicionada")

            if 'created_by' not in columns:
                cursor.execute('ALTER TABLE bet_combinations ADD COLUMN created_by VARCHAR')
                print("✅ Coluna 'created_by' adicionada")

            if 'notes' not in columns:
                cursor.execute('ALTER TABLE bet_combinations ADD COLUMN notes TEXT')
                print("✅ Coluna 'notes' adicionada")

        conn.commit()
        print("\n🎉 Operação concluída com sucesso!")

    except Exception as e:
        conn.rollback()
        print(f"❌ Erro: {e}")
        raise

    finally:
        conn.close()

if __name__ == "__main__":
    create_table()
