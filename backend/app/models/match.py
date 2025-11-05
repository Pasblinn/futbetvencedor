from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, unique=True, index=True)

    # Teams
    home_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    away_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)

    # Match details
    league = Column(String, index=True)
    season = Column(String)
    matchday = Column(Integer)
    match_date = Column(DateTime(timezone=True), index=True)
    venue = Column(String)
    referee = Column(String)

    # Scores
    home_score = Column(Integer)
    away_score = Column(Integer)
    home_score_ht = Column(Integer)  # Half-time
    away_score_ht = Column(Integer)

    # Match status
    status = Column(String, default="SCHEDULED")  # SCHEDULED, LIVE, FINISHED, POSTPONED
    minute = Column(Integer)

    # Weather conditions
    temperature = Column(Float)
    humidity = Column(Float)
    wind_speed = Column(Float)
    weather_condition = Column(String)

    # External factors
    importance_factor = Column(Float, default=1.0)  # Tournament importance
    motivation_home = Column(Float, default=0.5)
    motivation_away = Column(Float, default=0.5)

    # Prediction metadata
    is_predicted = Column(Boolean, default=False)
    confidence_score = Column(Float)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_matches")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_matches")
    statistics = relationship("MatchStatistics", back_populates="match", uselist=False)
    odds = relationship("Odds", back_populates="match")
    predictions = relationship("Prediction", back_populates="match")
    prediction_logs = relationship("PredictionLog", back_populates="match")

    def __repr__(self):
        return f"<Match({self.home_team.name if self.home_team else 'TBD'} vs {self.away_team.name if self.away_team else 'TBD'})>"