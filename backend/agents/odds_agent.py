"""
Sports AI — Agent 6: Market Odds Agent
Fetches and processes betting odds from the market.
"""

from typing import Dict, Any
from backend.agents.base_agent import BaseAgent
from backend.services.api_football_client import get_api_football_client
from backend.services.odds_service import OddsService


class OddsAgent(BaseAgent):
    """Fetches market odds and calculates implied probabilities."""

    def __init__(self):
        super().__init__()
        self.odds_service = OddsService()

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        api = get_api_football_client()
        fixture_id = context.get("fixture_id")

        if not fixture_id:
            self.logger.warning("No fixture ID — generating dynamic odds from context")
            return self._dynamic_odds(context)

        # Fetch odds from API-Football
        raw_odds = await api.get_odds(fixture_id=fixture_id)
        market = self.odds_service.parse_api_odds(raw_odds)

        if not market:
            self.logger.warning("No odds available — generating dynamic odds from context")
            return self._dynamic_odds(context)

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
        }

    @staticmethod
    def _dynamic_odds(context: Dict) -> Dict:
        """Generate realistic odds from available context (ELO, form, stats)."""
        # Use ELO expected probabilities if available
        elo_home = context.get("elo_expected_home", 0.0)
        elo_away = context.get("elo_expected_away", 0.0)

        # Use home/away stats if available
        home_stats = context.get("home_stats", {})
        away_stats = context.get("away_stats", {})
        home_form = home_stats.get("form_score", 50.0)
        away_form = away_stats.get("form_score", 50.0)

        if elo_home > 0 and elo_away > 0:
            # Derive from ELO (most reliable)
            home_prob = elo_home * 0.85 + 0.05  # Adjust slightly for home advantage
            draw_prob = 0.22 + 0.05 * (1 - abs(elo_home - elo_away) * 2)
            draw_prob = max(0.15, min(0.32, draw_prob))
            away_prob = max(0.08, 1.0 - home_prob - draw_prob)
            # Normalize
            total = home_prob + draw_prob + away_prob
            home_prob /= total
            draw_prob /= total
            away_prob /= total
        else:
            # Derive from form scores with home advantage
            form_ratio = home_form / max(home_form + away_form, 1)
            home_prob = form_ratio * 0.85 + 0.10  # Home advantage boost
            draw_prob = 0.24
            away_prob = max(0.10, 1.0 - home_prob - draw_prob)
            total = home_prob + draw_prob + away_prob
            home_prob /= total
            draw_prob /= total
            away_prob /= total

        # Convert probabilities to decimal odds (with 5% overround)
        overround = 1.05
        home_odds = round(overround / max(home_prob, 0.05), 2)
        draw_odds = round(overround / max(draw_prob, 0.05), 2)
        away_odds = round(overround / max(away_prob, 0.05), 2)

        return {
            "market_odds": {"home_win": home_odds, "draw": draw_odds, "away_win": away_odds},
            "implied_probabilities": {
                "home": round(home_prob, 4),
                "draw": round(draw_prob, 4),
                "away": round(away_prob, 4),
            },
            "odds_movement": {"home": 0.0, "draw": 0.0, "away": 0.0},
            "overround": 0.05,
            "bookmaker_count": 0,
        }
