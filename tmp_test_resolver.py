import asyncio
from backend.agents.fixture_resolver.agent import FixtureResolverAgent
from backend.agents.core.contracts import AgentContext

async def main():
    agent = FixtureResolverAgent()
    ctx = AgentContext(
        id="test",
        session_id="test_session",
        query="test",
        prediction_id="test_pred",
        data={
            "team_home": "Estudiantes RC",
            "team_away": "San Martín Tucumán"
        }
    )
    result = await agent.execute(ctx)
    print("Agent Result:")
    import json
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
