from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Boolean, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)

    # Prediction type
    prediction_type = Column(String, nullable=False)  # SINGLE, DOUBLE, TREBLE, MULTIPLE
    market_type = Column(String, nullable=False)  # 1X2, O/U, BTTS, Corners, etc.

    # Predicted outcomes
    predicted_outcome = Column(String)  # 1, X, 2, Over 2.5, etc.
    predicted_probability = Column(Float)  # Our calculated probability
    probability_home = Column(Float)  # Probability home win
    probability_draw = Column(Float)  # Probability draw
    probability_away = Column(Float)  # Probability away win
    recommended_odds = Column(Float)  # Minimum odds to be profitable
    actual_odds = Column(Float)  # Current market odds

    # Confidence and value
    confidence_score = Column(Float)  # 0-1 scale
    value_score = Column(Float)  # Expected value calculation
    kelly_percentage = Column(Float)  # Kelly criterion suggested stake

    # Factors considered
    form_weight = Column(Float)
    h2h_weight = Column(Float)
    xg_weight = Column(Float)
    injury_impact = Column(Float)
    weather_impact = Column(Float)
    motivation_impact = Column(Float)

    # Analysis details
    analysis_summary = Column(Text)
    key_factors = Column(JSON)  # List of key factors influencing prediction

    # Validation
    is_validated = Column(Boolean, default=False)
    validation_score = Column(Float)
    final_recommendation = Column(String)  # BET, SKIP, MONITOR

    # Outcome tracking
    actual_outcome = Column(String)
    is_winner = Column(Boolean)
    profit_loss = Column(Float)

    # AI Agent Analysis (🧠 NEW)
    ai_analyzed = Column(Boolean, default=False)  # Flag se foi analisada por AI
    ai_analyzed_at = Column(DateTime(timezone=True))  # Quando foi analisada
    ai_analysis = Column(Text)  # Explicação do AI Agent
    ai_recommendation = Column(String)  # BET, SKIP, MONITOR
    ai_risk_level = Column(String)  # LOW, MEDIUM, HIGH
    ai_confidence_delta = Column(Float)  # Diferença da confidence (AI - ML)

    # Metadata
    model_version = Column(String)  # Version of model used
    predicted_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    match = relationship("Match", back_populates="predictions")

    def __repr__(self):
        return f"<Prediction(match_id={self.match_id}, type='{self.prediction_type}', outcome='{self.predicted_outcome}')>"

class BetCombination(Base):
    __tablename__ = "bet_combinations"

    id = Column(Integer, primary_key=True, index=True)

    # Combination details
    combination_type = Column(String, nullable=False)  # DOUBLE, TREBLE, MULTIPLE
    selections_count = Column(Integer, nullable=False)
    total_odds = Column(Float, nullable=False)

    # Target criteria
    min_odds = Column(Float, default=1.5)
    max_odds = Column(Float, default=2.0)
    target_confidence = Column(Float, default=0.95)

    # Combined metrics
    combined_probability = Column(Float)
    combined_confidence = Column(Float)
    expected_value = Column(Float)
    risk_score = Column(Float)

    # Selections (JSON array of prediction IDs)
    prediction_ids = Column(JSON, nullable=False)
    selection_details = Column(JSON)  # Detailed breakdown

    # Recommendation
    is_recommended = Column(Boolean, default=False)
    recommendation_reason = Column(Text)
    risk_level = Column(String)  # LOW, MEDIUM, HIGH

    # Outcome tracking
    is_settled = Column(Boolean, default=False)
    is_winner = Column(Boolean)
    actual_return = Column(Float)

    # Source tracking (GOLD data for ML training)
    is_manual = Column(Boolean, default=False)  # True if manually created by user
    created_by = Column(String)  # User who created it (for manual tickets)
    notes = Column(Text)  # User notes/reasoning (for manual tickets)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))

    def __repr__(self):
        return f"<BetCombination(type='{self.combination_type}', odds={self.total_odds}, confidence={self.combined_confidence})>"