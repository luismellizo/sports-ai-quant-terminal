"""Risk Agent package."""

from backend.agents.risk.agent import RiskAgent
from backend.agents.registry import register

register("risk", RiskAgent)
register("RiskAgent", RiskAgent)
