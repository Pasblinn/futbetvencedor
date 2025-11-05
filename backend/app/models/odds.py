from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Odds(Base):
    __tablename__ = "odds"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    bookmaker = Column(String, nullable=False)
    market = Column(String, nullable=False)  # 1X2, Over/Under, Asian Handicap, etc.

    # Basic odds
    home_win = Column(Float)
    draw = Column(Float)
    away_win = Column(Float)

    # Over/Under odds (specific lines)
    over_1_5 = Column(Float)
    under_1_5 = Column(Float)
    over_2_5 = Column(Float)
    under_2_5 = Column(Float)
    over_3_5 = Column(Float)
    under_3_5 = Column(Float)

    # Generic over/under for any line
    over_under = Column(Float)  # The line (e.g. 2.5)
    over_odds = Column(Float)
    under_odds = Column(Float)

    # Both Teams to Score
    btts_yes = Column(Float)
    btts_no = Column(Float)

    # Asian Handicap
    asian_handicap_line = Column(Float)
    asian_handicap_home = Column(Float)
    asian_handicap_away = Column(Float)

    # Corner markets
    corners_over_8_5 = Column(Float)
    corners_under_8_5 = Column(Float)
    corners_over_9_5 = Column(Float)
    corners_under_9_5 = Column(Float)
    corners_over_10_5 = Column(Float)
    corners_under_10_5 = Column(Float)

    # Additional markets (JSON for flexibility)
    additional_markets = Column(JSON)

    # Metadata
    odds_timestamp = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    match = relationship("Match", back_populates="odds")

    @property
    def market_type(self):
        """Alias for 'market' field for backward compatibility"""
        return self.market

    @property
    def odds_data(self):
        """Return odds as dict for easy access"""
        data = {}

        # 1X2 market
        if self.home_win is not None:
            data['home'] = self.home_win
        if self.draw is not None:
            data['draw'] = self.draw
        if self.away_win is not None:
            data['away'] = self.away_win

        # Over/Under
        if self.over_1_5 is not None:
            data['over_1_5'] = self.over_1_5
        if self.under_1_5 is not None:
            data['under_1_5'] = self.under_1_5
        if self.over_2_5 is not None:
            data['over_2_5'] = self.over_2_5
        if self.under_2_5 is not None:
            data['under_2_5'] = self.under_2_5
        if self.over_3_5 is not None:
            data['over_3_5'] = self.over_3_5
        if self.under_3_5 is not None:
            data['under_3_5'] = self.under_3_5

        # BTTS
        if self.btts_yes is not None:
            data['btts_yes'] = self.btts_yes
        if self.btts_no is not None:
            data['btts_no'] = self.btts_no

        # Asian Handicap
        if self.asian_handicap_home is not None:
            data['asian_handicap_home'] = self.asian_handicap_home
        if self.asian_handicap_away is not None:
            data['asian_handicap_away'] = self.asian_handicap_away

        # Adicionar additional_markets se existir
        if self.additional_markets:
            data.update(self.additional_markets)

        return data

    def __repr__(self):
        return f"<Odds(match_id={self.match_id}, bookmaker='{self.bookmaker}', market='{self.market}')>"

class OddsHistory(Base):
    __tablename__ = "odds_history"

    id = Column(Integer, primary_key=True, index=True)
    odds_id = Column(Integer, ForeignKey("odds.id"), nullable=False)

    # Historical odds values
    home_win = Column(Float)
    draw = Column(Float)
    away_win = Column(Float)

    # Timestamp for tracking changes
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())

    # Movement indicators
    movement_direction = Column(String)  # UP, DOWN, STABLE
    movement_percentage = Column(Float)

    def __repr__(self):
        return f"<OddsHistory(odds_id={self.odds_id}, recorded_at='{self.recorded_at}')>"