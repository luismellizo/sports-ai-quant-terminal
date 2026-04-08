"""Poisson Agent package."""

from backend.agents.poisson.agent import PoissonAgent
from backend.agents.registry import register

register("poisson", PoissonAgent)
register("PoissonAgent", PoissonAgent)
