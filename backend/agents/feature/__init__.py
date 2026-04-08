"""Feature Agent package."""

from backend.agents.feature.agent import FeatureAgent
from backend.agents.registry import register

register("feature", FeatureAgent)
register("FeatureAgent", FeatureAgent)
