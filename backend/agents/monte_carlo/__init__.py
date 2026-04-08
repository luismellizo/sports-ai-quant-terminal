"""Monte Carlo Agent package."""

from backend.agents.monte_carlo.agent import MonteCarloAgent
from backend.agents.registry import register

register("monte_carlo", MonteCarloAgent)
register("MonteCarloAgent", MonteCarloAgent)
