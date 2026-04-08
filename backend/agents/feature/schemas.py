"""Feature Agent schemas."""

from pydantic import BaseModel, Field
from typing import List, Optional


class FeatureVector(BaseModel):
    features: List[float] = Field(default_factory=list)
    feature_names: List[str] = Field(default_factory=list)


class FeatureOutput(BaseModel):
    features: FeatureVector = Field(default_factory=FeatureVector)
    feature_data_available: bool = True
