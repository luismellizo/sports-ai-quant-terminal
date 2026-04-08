"""Context Agent package."""

from backend.agents.context.agent import ContextAgent
from backend.agents.registry import register

register("context", ContextAgent)
register("ContextAgent", ContextAgent)
