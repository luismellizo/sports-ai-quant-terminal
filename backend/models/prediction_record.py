"""
Sports AI — Prediction Record (SQLAlchemy)
Persists every prediction for the admin dashboard.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Text, BigInteger
from backend.config.database import Base


class PredictionRecord(Base):
    """Stores completed prediction results in PostgreSQL."""

    __tablename__ = "prediction_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prediction_id = Column(String(16), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)

    # Match info
    query = Column(Text, nullable=False)
    home_team = Column(String(128), nullable=False, default="")
    away_team = Column(String(128), nullable=False, default="")
    league = Column(String(128), nullable=True)

    # Summary fields (JSON blobs for flexibility)
    probabilities = Column(JSON, nullable=True)
    best_bet = Column(JSON, nullable=True)
    monte_carlo_summary = Column(JSON, nullable=True)
    executive_summary = Column(Text, nullable=True)
    verdict = Column(Text, nullable=True)

    # Metadata
    total_execution_time_ms = Column(Float, default=0)
    fixture_id = Column(BigInteger, nullable=True)

    # Result (filled when admin clicks "Llamar Resultado")
    result_data = Column(JSON, nullable=True)
