"""Risk Agent schemas."""

from pydantic import BaseModel, Field
from typing import Optional


class BetRecommendation(BaseModel):
    bet_type: str
    team: str
    probability: float
    market_odds: float
    value_edge: float
    recommended_stake_pct: float
    confidence: str = "MEDIUM"
    risk_level: str = "MEDIUM"
    confidence_score: float = 0.0
    recommendation_style: str = ""


class RiskOutput(BaseModel):
    best_bet: Optional[BetRecommendation] = None
    risk_narrative: str = ""
    professional_verdict: str = ""
    bet_profile: Optional[str] = None
