#!/usr/bin/env python3
"""
Check columns in bet_combinations table
"""
import sqlite3
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent / "football_analytics.db"

def check_columns():
    """Check what columns exist in bet_combinations"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    try:
        cursor.execute("PRAGMA table_info(bet_combinations)")
        columns = cursor.fetchall()

        print("\n📋 Colunas em bet_combinations:")
        print("=" * 60)
        for col in columns:
            print(f"  {col[1]:30} {col[2]:15} {'NOT NULL' if col[3] else 'NULL'}")
        print("=" * 60)

        column_names = [col[1] for col in columns]
        missing = []

        if 'is_manual' not in column_names:
            missing.append('is_manual')
        if 'created_by' not in column_names:
            missing.append('created_by')
        if 'notes' not in column_names:
            missing.append('notes')

        if missing:
            print(f"\n⚠️  Colunas faltando: {', '.join(missing)}")
            return False
        else:
            print("\n✅ Todas as colunas necessárias estão presentes!")
            return True

    finally:
        conn.close()

if __name__ == "__main__":
    check_columns()
