"""ML Agent package."""

from backend.agents.ml.agent import MLAgent
from backend.agents.registry import register

register("ml", MLAgent)
register("MLAgent", MLAgent)
