"""NLP Agent package."""

from backend.agents.nlp.agent import NLPAgent
from backend.agents.registry import register

register("nlp", NLPAgent)
register("NLPAgent", NLPAgent)
