"""Lineup Agent package."""

from backend.agents.lineup.agent import LineupAgent
from backend.agents.registry import register

register("lineup", LineupAgent)
register("LineupAgent", LineupAgent)
