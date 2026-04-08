"""Sentiment Agent package."""

from backend.agents.sentiment.agent import SentimentAgent
from backend.agents.registry import register

register("sentiment", SentimentAgent)
register("SentimentAgent", SentimentAgent)
