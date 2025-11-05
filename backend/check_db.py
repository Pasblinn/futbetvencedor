import sqlite3

conn = sqlite3.connect('football_analytics_dev.db')
cur = conn.cursor()

# Check total matches
cur.execute('SELECT COUNT(*) FROM matches')
total_matches = cur.fetchone()[0]
print(f'Total matches: {total_matches}')

# Check sample matches
cur.execute('SELECT home_team, away_team, date FROM matches LIMIT 10')
print('Sample matches:')
for row in cur.fetchall():
    print(f'  {row[0]} vs {row[1]} on {row[2]}')

conn.close()