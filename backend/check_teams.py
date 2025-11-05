import sqlite3

conn = sqlite3.connect('football_analytics_dev.db')
cur = conn.cursor()

# Check if teams table exists
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='teams'")
if cur.fetchone():
    print('Teams table exists')
    cur.execute('SELECT COUNT(*) FROM teams')
    print(f'Total teams: {cur.fetchone()[0]}')
    cur.execute('SELECT id, name FROM teams LIMIT 10')
    print('Sample teams:')
    for row in cur.fetchall():
        print(f'  {row[0]}: {row[1]}')
else:
    print('Teams table does not exist')

conn.close()