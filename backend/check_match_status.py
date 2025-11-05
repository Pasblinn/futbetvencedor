#!/usr/bin/env python3
"""Check status of Racing Club match"""
from app.core.database import SessionLocal
from app.models.match import Match

db = SessionLocal()
try:
    match = db.query(Match).filter(Match.id == 2784).first()

    if match:
        print(f"Match ID: {match.id}")
        print(f"Teams: {match.home_team.name} vs {match.away_team.name}")
        print(f"Status: {match.status}")
        print(f"Score: {match.home_score} - {match.away_score}")
        print(f"Date: {match.match_date}")
    else:
        print("Match not found")

finally:
    db.close()
