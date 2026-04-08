"""Synthesis Agent schemas."""

from pydantic import BaseModel, Field
from typing import List


class SynthesisOutput(BaseModel):
    executive_summary: str = ""
    verdict: str = ""
    tactical_synthesis: str = ""
    critical_data_points: List[str] = Field(default_factory=list)
    decisive_factors: List[str] = Field(default_factory=list)
    risk_warnings: List[str] = Field(default_factory=list)
    final_recommendation: str = ""
    conviction_level: str = ""
