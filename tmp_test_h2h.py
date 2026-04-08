import asyncio
import json
from backend.services.api_football_client import get_api_football_client
from backend.agents.history.agent import HistoryAgent
from backend.agents.core.contracts import AgentContext

async def main():
    api = get_api_football_client()
    
    context = AgentContext(
        fixture_id=123,
        query="Test query",
        prediction_id="test_pred",
        data={
            "home_team_id": 2341092, # Man City
            "away_team_id": 2341082, # Liverpool
            "team_home": "Manchester City",
            "team_away": "Liverpool"
        }
    )
    
    agent = HistoryAgent()
    result = await agent.execute(context)
    
    print(json.dumps({
        "h2h_enriched_stats_keys": list(result.get("h2h_enriched_stats", {}).keys()),
        "biggest_victory_home": result.get("h2h_enriched_stats", {}).get("biggest_victory", {}).get("team1", {}),
        "history_narrative": result.get("history_narrative", ""),
    }, indent=2, ensure_ascii=False))
    
    await api.close()

if __name__ == "__main__":
    asyncio.run(main())
