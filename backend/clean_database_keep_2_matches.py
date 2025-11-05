#!/usr/bin/env python3
"""
Script para LIMPAR COMPLETAMENTE o database e manter apenas 2 jogos reais:
- Chelsea vs Brighton 27/09 14:00 UTC
- Manchester City vs Burnley 27/09 14:00 UTC
"""
import sqlite3
import json
from datetime import datetime

def clean_and_populate_database():
    """Clean database and add only the 2 real matches"""
    print("🧹 LIMPANDO DATABASE COMPLETAMENTE...")

    conn = sqlite3.connect('football_analytics_dev.db')
    cursor = conn.cursor()

    # 1. DELETE ALL DATA
    print("❌ Deletando todos os dados...")
    cursor.execute('DELETE FROM matches')
    cursor.execute('DELETE FROM teams')

    # Reset auto-increment counters (if table exists)
    try:
        cursor.execute('DELETE FROM sqlite_sequence WHERE name="matches"')
        cursor.execute('DELETE FROM sqlite_sequence WHERE name="teams"')
    except sqlite3.OperationalError:
        pass  # Table might not exist

    # 2. INSERT ONLY THE 4 TEAMS WE NEED
    print("✅ Adicionando apenas 4 times reais...")
    teams = [
        (1, 'Chelsea FC', 'England', 'Premier League'),
        (2, 'Brighton & Hove Albion FC', 'England', 'Premier League'),
        (3, 'Manchester City FC', 'England', 'Premier League'),
        (4, 'Burnley FC', 'England', 'Premier League')
    ]

    cursor.executemany('''
        INSERT INTO teams (id, name, country, league)
        VALUES (?, ?, ?, ?)
    ''', teams)

    # 3. INSERT ONLY THE 2 REAL MATCHES
    print("✅ Adicionando apenas 2 jogos reais...")
    matches = [
        (1, 'CHELSEA_BRIGHTON_27_09', 1, 2, 'Premier League', '2024-25', 6, '2025-09-27 14:00:00', 'Stamford Bridge', 'TBD', None, None, None, None, 'SCHEDULED', None, None, None, None, None, 1.0, 0.8, 0.8, False, None),
        (2, 'MANCITY_BURNLEY_27_09', 3, 4, 'Premier League', '2024-25', 6, '2025-09-27 14:00:00', 'Etihad Stadium', 'TBD', None, None, None, None, 'SCHEDULED', None, None, None, None, None, 1.0, 0.9, 0.6, False, None)
    ]

    cursor.executemany('''
        INSERT INTO matches (id, external_id, home_team_id, away_team_id, league, season, matchday, match_date, venue, referee, home_score, away_score, home_score_ht, away_score_ht, status, minute, temperature, humidity, wind_speed, weather_condition, importance_factor, motivation_home, motivation_away, is_predicted, confidence_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', matches)

    # 4. VERIFY CLEAN DATA
    print("\n📊 VERIFICANDO DADOS LIMPOS:")

    cursor.execute('SELECT COUNT(*) FROM teams')
    team_count = cursor.fetchone()[0]
    print(f"Teams: {team_count}")

    cursor.execute('SELECT COUNT(*) FROM matches')
    match_count = cursor.fetchone()[0]
    print(f"Matches: {match_count}")

    print("\n🎯 JOGOS FINAIS:")
    cursor.execute('''
        SELECT m.id, t1.name as home, t2.name as away, m.match_date, m.status
        FROM matches m
        JOIN teams t1 ON m.home_team_id = t1.id
        JOIN teams t2 ON m.away_team_id = t2.id
        ORDER BY m.id
    ''')

    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} vs {row[2]} - {row[3]} ({row[4]})")

    conn.commit()
    conn.close()

    print("\n✅ DATABASE LIMPO! Apenas 2 jogos reais restantes")

if __name__ == "__main__":
    clean_and_populate_database()