"""Market Edge Agent schemas."""

from pydantic import BaseModel, Field
from typing import List, Optional


class MarketEdgeData(BaseModel):
    bet_type: str
    model_probability: float
    market_probability: float
    edge: float
    odds: float
    is_value_bet: bool = False


class MarketEdgeOutput(BaseModel):
    market_edges: List[MarketEdgeData] = Field(default_factory=list)
    value_bets: List[MarketEdgeData] = Field(default_factory=list)
    best_edge: Optional[MarketEdgeData] = None
    model_probabilities: dict = Field(default_factory=dict)
    market_narrative: str = ""
    recommended_bet_type: str = "ninguno"
