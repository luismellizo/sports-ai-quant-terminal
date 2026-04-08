"""Market Edge Agent package."""

from backend.agents.market_edge.agent import MarketEdgeAgent
from backend.agents.registry import register

register("market_edge", MarketEdgeAgent)
register("MarketEdgeAgent", MarketEdgeAgent)
