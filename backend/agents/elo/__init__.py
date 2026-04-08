"""ELO Agent package."""

from backend.agents.elo.agent import EloAgent
from backend.agents.registry import register

register("elo", EloAgent)
register("EloAgent", EloAgent)
