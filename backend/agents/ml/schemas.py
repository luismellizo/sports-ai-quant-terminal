"""ML Agent schemas."""

from pydantic import BaseModel, Field
from typing import Optional, List


class MLOutput(BaseModel):
    ml_home_win: float = 0.33
    ml_draw: float = 0.33
    ml_away_win: float = 0.33
    api_prediction_available: bool = False
    api_advice: str = ""
    ml_narrative: str = ""
    model_agreement: str = ""
    confidence_in_prediction: str = ""
