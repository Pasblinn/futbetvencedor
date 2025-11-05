#!/usr/bin/env python3
"""
Adicionar colunas de probabilidade ao modelo Prediction
"""
import sqlite3

db_path = 'football_analytics_dev.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Adicionar colunas se não existirem
columns_to_add = [
    ('probability_home', 'REAL'),
    ('probability_draw', 'REAL'),
    ('probability_away', 'REAL')
]

for col_name, col_type in columns_to_add:
    try:
        cursor.execute(f"ALTER TABLE predictions ADD COLUMN {col_name} {col_type}")
        print(f"✅ Coluna '{col_name}' adicionada")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e):
            print(f"ℹ️  Coluna '{col_name}' já existe")
        else:
            print(f"❌ Erro: {e}")

conn.commit()
conn.close()

print("\n✅ Concluído!")
