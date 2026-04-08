"""History Agent package."""

from backend.agents.history.agent import HistoryAgent
from backend.agents.registry import register

register("history", HistoryAgent)
register("HistoryAgent", HistoryAgent)
