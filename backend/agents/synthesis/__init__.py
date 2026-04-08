"""Synthesis Agent package."""

from backend.agents.synthesis.agent import SynthesisAgent
from backend.agents.registry import register

register("synthesis", SynthesisAgent)
register("SynthesisAgent", SynthesisAgent)
