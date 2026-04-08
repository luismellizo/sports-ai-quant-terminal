"""Odds Agent package."""

from backend.agents.odds.agent import OddsAgent
from backend.agents.registry import register

register("odds", OddsAgent)
register("OddsAgent", OddsAgent)
