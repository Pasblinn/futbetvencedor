from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, unique=True, index=True)  # ID from external API
    name = Column(String, index=True, nullable=False)
    short_name = Column(String)
    country = Column(String)
    league = Column(String, index=True)
    founded = Column(Integer)
    venue = Column(String)
    logo_url = Column(String)

    # Performance metrics
    elo_rating = Column(Float, default=1200.0)
    form_rating = Column(Float, default=0.0)
    attack_rating = Column(Float, default=0.0)
    defense_rating = Column(Float, default=0.0)

    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    home_matches = relationship("Match", foreign_keys="Match.home_team_id", back_populates="home_team")
    away_matches = relationship("Match", foreign_keys="Match.away_team_id", back_populates="away_team")
    statistics = relationship("TeamStatistics", back_populates="team")

    def __repr__(self):
        return f"<Team(name='{self.name}', league='{self.league}')>"