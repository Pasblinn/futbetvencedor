from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Boolean, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, unique=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)

    # Personal details
    name = Column(String, nullable=False)
    full_name = Column(String)
    birth_date = Column(Date)
    nationality = Column(String)
    position = Column(String)  # GK, DEF, MID, FWD
    jersey_number = Column(Integer)

    # Physical attributes
    height = Column(Float)  # in cm
    weight = Column(Float)  # in kg
    preferred_foot = Column(String)  # Left, Right, Both

    # Market value and status
    market_value = Column(Float)
    contract_until = Column(Date)
    is_active = Column(Boolean, default=True)
    is_injured = Column(Boolean, default=False)
    is_suspended = Column(Boolean, default=False)

    # Performance metrics
    appearances_season = Column(Integer, default=0)
    goals_season = Column(Integer, default=0)
    assists_season = Column(Integer, default=0)
    yellow_cards_season = Column(Integer, default=0)
    red_cards_season = Column(Integer, default=0)
    minutes_played_season = Column(Integer, default=0)

    # Advanced metrics
    xg_season = Column(Float, default=0.0)
    xa_season = Column(Float, default=0.0)  # Expected assists
    pass_completion_rate = Column(Float, default=0.0)
    tackle_success_rate = Column(Float, default=0.0)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    team = relationship("Team")
    injuries = relationship("PlayerInjury", back_populates="player")

    def __repr__(self):
        return f"<Player(name='{self.name}', position='{self.position}', team_id={self.team_id})>"

class PlayerInjury(Base):
    __tablename__ = "player_injuries"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)

    # Injury details
    injury_type = Column(String, nullable=False)
    severity = Column(String)  # Minor, Moderate, Severe
    body_part = Column(String)  # Knee, Ankle, Hamstring, etc.

    # Timeline
    injury_date = Column(Date, nullable=False)
    expected_return_date = Column(Date)
    actual_return_date = Column(Date)

    # Status
    is_active = Column(Boolean, default=True)
    recovery_percentage = Column(Float, default=0.0)

    # Impact assessment
    impact_on_team = Column(Float, default=0.0)  # 0-1 scale
    replacement_quality = Column(Float, default=0.5)  # Quality of replacement player

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    player = relationship("Player", back_populates="injuries")

    def __repr__(self):
        return f"<PlayerInjury(player_id={self.player_id}, type='{self.injury_type}', severity='{self.severity}')>"