"""Sentiment Agent schemas."""

from pydantic import BaseModel, Field
from typing import List


class SentimentOutput(BaseModel):
    sentiment_home: float = 0.0
    sentiment_away: float = 0.0
    pressure_home: float = 0.5
    pressure_away: float = 0.5
    sentiment_factors_home: List[str] = Field(default_factory=list)
    sentiment_factors_away: List[str] = Field(default_factory=list)
    sentiment_narrative: str = ""
