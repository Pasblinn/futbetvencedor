#!/usr/bin/env python3
"""
Create users table in database
"""
from sqlalchemy import create_engine
from app.models.user import User
from app.core.database import Base
from app.core.config import settings

def create_users_table():
    """Create users table"""
    engine = create_engine(settings.get_database_url())

    # Create users table
    User.__table__.create(engine, checkfirst=True)
    print("✅ Users table created successfully!")

if __name__ == "__main__":
    create_users_table()
