#!/usr/bin/env python3
from sqlalchemy import create_engine, text

engine = create_engine('sqlite:///football_analytics_dev.db')
with engine.connect() as conn:
    matches = conn.execute(text('SELECT COUNT(*) FROM matches')).scalar()
    predictions = conn.execute(text('SELECT COUNT(*) FROM predictions')).scalar()
    teams = conn.execute(text('SELECT COUNT(*) FROM teams')).scalar()

    print(f"✅ Matches: {matches}")
    print(f"✅ Predictions: {predictions}")
    print(f"✅ Teams: {teams}")
