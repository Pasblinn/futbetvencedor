import sqlite3

conn = sqlite3.connect('football_analytics_dev.db')
cur = conn.cursor()

# Check table schema
cur.execute("PRAGMA table_info(matches)")
columns = cur.fetchall()
print('Matches table columns:')
for col in columns:
    print(f'  {col[1]} ({col[2]})')

# Get sample data
cur.execute('SELECT * FROM matches LIMIT 2')
sample = cur.fetchall()
print('\nSample data:')
for row in sample:
    print(row)

conn.close()