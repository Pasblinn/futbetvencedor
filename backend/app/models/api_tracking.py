"""
📊 MODELOS DE TRACKING - API-FOOTBALL
Rastreamento de requisições e otimização de uso da API
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, Float
from sqlalchemy.sql import func
from app.core.database import Base

class APIRequestLog(Base):
    """Log de todas as requisições à API-Football"""
    __tablename__ = "api_request_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Request info
    endpoint = Column(String, nullable=False, index=True)
    params = Column(JSON)
    http_status = Column(Integer)
    success = Column(Boolean, default=True)

    # Response info
    results_count = Column(Integer, default=0)
    error_message = Column(String)

    # Rate limiting
    requests_remaining = Column(Integer)
    requests_limit = Column(Integer)

    # Timing
    request_date = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    response_time_ms = Column(Float)

    # Metadata
    api_version = Column(String, default="v3")

    def __repr__(self):
        return f"<APIRequestLog(endpoint='{self.endpoint}', status={self.http_status})>"


class DataCollectionJob(Base):
    """Jobs de coleta de dados (histórico e incrementais)"""
    __tablename__ = "data_collection_jobs"

    id = Column(Integer, primary_key=True, index=True)

    # Job info
    job_type = Column(String, nullable=False, index=True)  # INITIAL_HISTORICAL, DAILY_INCREMENTAL, MANUAL
    job_name = Column(String, nullable=False)
    description = Column(String)

    # Parameters
    league_ids = Column(JSON)  # Lista de IDs de ligas
    season = Column(Integer)
    date_from = Column(String)  # YYYY-MM-DD
    date_to = Column(String)

    # Status
    status = Column(String, default="PENDING", index=True)  # PENDING, RUNNING, COMPLETED, FAILED, CANCELLED
    progress = Column(Float, default=0.0)  # 0-100

    # Results
    fixtures_collected = Column(Integer, default=0)
    fixtures_with_stats = Column(Integer, default=0)
    requests_used = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    error_details = Column(JSON)

    # Timing
    scheduled_at = Column(DateTime(timezone=True))
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    created_by = Column(String, default="system")

    def __repr__(self):
        return f"<DataCollectionJob(name='{self.job_name}', status='{self.status}')>"


class FixtureCache(Base):
    """Cache de fixtures da API-Football para evitar requisições duplicadas"""
    __tablename__ = "fixture_cache"

    id = Column(Integer, primary_key=True, index=True)

    # API IDs
    fixture_id = Column(Integer, unique=True, nullable=False, index=True)  # ID da API-Football
    match_id = Column(Integer, index=True)  # ID local do Match

    # Basic info
    league_id = Column(Integer, index=True)
    season = Column(Integer, index=True)
    fixture_date = Column(DateTime(timezone=True), index=True)
    status = Column(String, index=True)  # NS, FT, LIVE, etc.

    # Data flags
    has_basic_data = Column(Boolean, default=False)
    has_statistics = Column(Boolean, default=False)
    has_lineups = Column(Boolean, default=False)
    has_events = Column(Boolean, default=False)

    # Raw data (JSON)
    raw_fixture_data = Column(JSON)
    raw_statistics_data = Column(JSON)

    # Sync info
    last_synced = Column(DateTime(timezone=True), server_default=func.now())
    needs_update = Column(Boolean, default=False, index=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<FixtureCache(fixture_id={self.fixture_id}, status='{self.status}')>"


class LeagueConfig(Base):
    """Configuração de ligas para coleta automática"""
    __tablename__ = "league_configs"

    id = Column(Integer, primary_key=True, index=True)

    # League info
    league_id = Column(Integer, unique=True, nullable=False, index=True)
    league_name = Column(String, nullable=False)
    country = Column(String)

    # Priority
    priority = Column(Integer, default=5)  # 1=highest, 10=lowest
    is_active = Column(Boolean, default=True, index=True)

    # Collection settings
    collect_historical = Column(Boolean, default=True)
    collect_daily = Column(Boolean, default=True)
    collect_statistics = Column(Boolean, default=True)
    collect_lineups = Column(Boolean, default=False)
    collect_events = Column(Boolean, default=False)

    # Seasons to track
    seasons = Column(JSON)  # [2023, 2024, 2025]
    current_season = Column(Integer)

    # Stats
    total_fixtures = Column(Integer, default=0)
    last_collection_date = Column(DateTime(timezone=True))

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<LeagueConfig(name='{self.league_name}', priority={self.priority})>"


class DailyAPIQuota(Base):
    """Tracking diário de quota da API"""
    __tablename__ = "daily_api_quota"

    id = Column(Integer, primary_key=True, index=True)

    # Date
    date = Column(String, unique=True, nullable=False, index=True)  # YYYY-MM-DD

    # Quota info
    daily_limit = Column(Integer, default=7500)
    requests_used = Column(Integer, default=0)
    requests_remaining = Column(Integer, default=7500)

    # Distribution by endpoint
    fixtures_requests = Column(Integer, default=0)
    statistics_requests = Column(Integer, default=0)
    standings_requests = Column(Integer, default=0)
    other_requests = Column(Integer, default=0)

    # Metadata
    last_updated = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<DailyAPIQuota(date='{self.date}', used={self.requests_used}/{self.daily_limit})>"
