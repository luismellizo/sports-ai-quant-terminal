"""Fixture Resolver Agent package."""

from backend.agents.fixture_resolver.agent import FixtureResolverAgent
from backend.agents.registry import register

register("fixture_resolver", FixtureResolverAgent)
register("FixtureResolverAgent", FixtureResolverAgent)
