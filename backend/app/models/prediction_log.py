from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, JSON, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class PredictionLog(Base):
    """Log completo de todas as predições para análise e aprendizado do ML"""
    __tablename__ = "prediction_logs"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    prediction_id = Column(Integer, ForeignKey("predictions.id"), nullable=True)
    
    # Dados da predição original
    predicted_outcome = Column(String, nullable=False)  # home, away, draw
    confidence_score = Column(Float, nullable=False)  # 0-1
    predicted_probability = Column(Float, nullable=False)
    
    # Dados do jogo no momento da predição
    match_date = Column(DateTime, nullable=False)
    home_team_id = Column(Integer, ForeignKey("teams.id"))
    away_team_id = Column(Integer, ForeignKey("teams.id"))
    league = Column(String, nullable=False)
    
    # Features utilizadas na predição
    features_used = Column(JSON)  # Lista de features utilizadas
    feature_values = Column(JSON)  # Valores das features no momento da predição
    
    # Modelo utilizado
    model_name = Column(String, nullable=False)
    model_version = Column(String, nullable=False)
    
    # Análise e contexto
    analysis_summary = Column(Text)
    key_factors = Column(JSON)
    market_conditions = Column(JSON)  # Odds, volume de apostas, etc.
    
    # Resultado real (preenchido após o jogo)
    actual_outcome = Column(String)  # home, away, draw
    actual_home_score = Column(Integer)
    actual_away_score = Column(Integer)
    match_status = Column(String)  # finished, cancelled, etc.
    
    # Análise de performance
    was_correct = Column(Boolean)  # True se a predição estava certa
    confidence_vs_accuracy = Column(Float)  # Diferença entre confiança e acurácia
    prediction_error = Column(Float)  # Erro da predição (0-1)
    
    # Feedback para ML
    feedback_score = Column(Float)  # Score de feedback para o modelo
    learning_insights = Column(JSON)  # Insights para melhorar o modelo
    feature_importance_feedback = Column(JSON)  # Feedback sobre importância das features
    
    # Metadados
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    analyzed_at = Column(DateTime(timezone=True))  # Quando foi reanalisada
    
    # Relationships
    match = relationship("Match", back_populates="prediction_logs")
    prediction = relationship("Prediction")
    home_team = relationship("Team", foreign_keys=[home_team_id])
    away_team = relationship("Team", foreign_keys=[away_team_id])

    def __repr__(self):
        return f"<PredictionLog(match_id={self.match_id}, predicted={self.predicted_outcome}, actual={self.actual_outcome}, correct={self.was_correct})>"

class ModelPerformance(Base):
    """Performance histórica dos modelos ML"""
    __tablename__ = "model_performance"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, nullable=False)
    model_version = Column(String, nullable=False)
    
    # Período de análise
    analysis_period_start = Column(DateTime, nullable=False)
    analysis_period_end = Column(DateTime, nullable=False)
    
    # Métricas de performance
    total_predictions = Column(Integer, nullable=False)
    correct_predictions = Column(Integer, nullable=False)
    accuracy = Column(Float, nullable=False)  # 0-1
    
    # Métricas de confiança
    avg_confidence = Column(Float, nullable=False)
    confidence_accuracy_correlation = Column(Float)  # Correlação entre confiança e acurácia
    
    # Métricas por tipo de predição
    home_win_accuracy = Column(Float)
    away_win_accuracy = Column(Float)
    draw_accuracy = Column(Float)
    
    # Métricas por liga
    league_performance = Column(JSON)  # Performance por liga
    
    # Insights e melhorias
    key_insights = Column(JSON)
    recommended_improvements = Column(JSON)
    feature_importance_analysis = Column(JSON)
    
    # Metadados
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<ModelPerformance(model={self.model_name}, accuracy={self.accuracy}, period={self.analysis_period_start} to {self.analysis_period_end})>"
