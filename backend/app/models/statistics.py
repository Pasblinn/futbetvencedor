from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class MatchStatistics(Base):
    __tablename__ = "match_statistics"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False, unique=True)

    # Basic statistics
    possession_home = Column(Float)
    possession_away = Column(Float)
    shots_home = Column(Integer)
    shots_away = Column(Integer)
    shots_on_target_home = Column(Integer)
    shots_on_target_away = Column(Integer)
    corners_home = Column(Integer)
    corners_away = Column(Integer)
    fouls_home = Column(Integer)
    fouls_away = Column(Integer)
    yellow_cards_home = Column(Integer)
    yellow_cards_away = Column(Integer)
    red_cards_home = Column(Integer)
    red_cards_away = Column(Integer)

    # Advanced metrics
    xg_home = Column(Float)  # Expected Goals
    xg_away = Column(Float)
    xga_home = Column(Float)  # Expected Goals Against
    xga_away = Column(Float)
    passes_home = Column(Integer)
    passes_away = Column(Integer)
    pass_accuracy_home = Column(Float)
    pass_accuracy_away = Column(Float)
    progressive_passes_home = Column(Integer)
    progressive_passes_away = Column(Integer)

    # Defensive metrics
    tackles_home = Column(Integer)
    tackles_away = Column(Integer)
    interceptions_home = Column(Integer)
    interceptions_away = Column(Integer)
    clearances_home = Column(Integer)
    clearances_away = Column(Integer)

    # Additional data (JSON for flexibility)
    additional_stats = Column(JSON)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    match = relationship("Match", back_populates="statistics")

class TeamStatistics(Base):
    __tablename__ = "team_statistics"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    season = Column(String, nullable=False)

    # Form metrics (last 15 games)
    games_played = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    draws = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    goals_for = Column(Integer, default=0)
    goals_against = Column(Integer, default=0)
    clean_sheets = Column(Integer, default=0)

    # Advanced season metrics
    avg_xg_for = Column(Float, default=0.0)
    avg_xg_against = Column(Float, default=0.0)
    avg_possession = Column(Float, default=0.0)
    avg_shots_for = Column(Float, default=0.0)
    avg_shots_against = Column(Float, default=0.0)
    avg_corners_for = Column(Float, default=0.0)
    avg_corners_against = Column(Float, default=0.0)

    # Home/Away splits
    home_wins = Column(Integer, default=0)
    home_draws = Column(Integer, default=0)
    home_losses = Column(Integer, default=0)
    away_wins = Column(Integer, default=0)
    away_draws = Column(Integer, default=0)
    away_losses = Column(Integer, default=0)

    # Form trends (JSON for time series data)
    form_trend = Column(JSON)  # Last 15 games trend
    goal_trend = Column(JSON)
    xg_trend = Column(JSON)

    # Metadata
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    team = relationship("Team", back_populates="statistics")

    # Propriedades calculadas para compatibilidade
    @property
    def goals_scored_avg(self):
        """Média de gols marcados por jogo"""
        return self.goals_for / self.games_played if self.games_played > 0 else 0.0

    @property
    def goals_conceded_avg(self):
        """Média de gols sofridos por jogo"""
        return self.goals_against / self.games_played if self.games_played > 0 else 0.0

    def __repr__(self):
        return f"<TeamStatistics(team_id={self.team_id}, season='{self.season}')>"