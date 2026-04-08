"""
Sports AI — Odds Agent
Fetches and processes betting odds from the market.
"""

from typing import Dict, Any

from backend.agents.core.base import BaseAgent
from backend.agents.core.contracts import AgentContext
from backend.services.api_football_client import get_api_football_client
from backend.services.odds_service import OddsService


class OddsAgent(BaseAgent):
    name = "OddsAgent"
    is_critical = False
    timeout_seconds = 15.0

    def __init__(self):
        super().__init__()
        self.odds_service = OddsService()

    async def execute(self, ctx: AgentContext) -> Dict[str, Any]:
        api = get_api_football_client()
        fixture_id = ctx.data.get("fixture_id")

        if not fixture_id:
            return {
                "market_odds": {},
                "implied_probabilities": {},
                "odds_movement": {},
                "overround": None,
                "bookmaker_count": 0,
                "odds_data_source": "missing",
                "odds_data_available": False,
                "odds_warning": "No fixture_id available for odds lookup.",
            }

        raw_odds = await api.get_odds(fixture_id=fixture_id)
        market = self.odds_service.parse_api_odds(raw_odds)

        if not market:
            return {
                "market_odds": {},
                "implied_probabilities": {},
                "odds_movement": {},
                "overround": None,
                "bookmaker_count": 0,
                "odds_data_source": "missing",
                "odds_data_available": False,
                "odds_warning": "API returned no bookmaker odds for this fixture.",
            }

        return {
            "market_odds": {
                "home_win": market.avg_home_win,
                "draw": market.avg_draw,
                "away_win": market.avg_away_win,
            },
            "implied_probabilities": {
                "home": market.implied_prob_home,
                "draw": market.implied_prob_draw,
                "away": market.implied_prob_away,
            },
            "odds_movement": {
                "home": market.movement_home,
                "draw": market.movement_draw,
                "away": market.movement_away,
            },
            "overround": round(market.overround, 4),
            "bookmaker_count": len(market.bookmakers),
            "odds_data_source": "api",
            "odds_data_available": True,
        }
