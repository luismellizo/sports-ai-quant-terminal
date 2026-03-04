"""
Sports AI — Odds Service
Calculates implied probabilities, market averages, and odds movement.
"""

from typing import List, Dict, Optional
from backend.models.odds import MarketOdds, BookmakerOdds
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class OddsService:
    """Service for processing and analyzing betting odds."""

    @staticmethod
    def parse_api_odds(api_response: List[Dict]) -> Optional[MarketOdds]:
        """
        Parse odds from API-Football response into MarketOdds model.

        API-Football returns odds grouped by bookmaker with bet types.
        We extract the 1X2 (Match Winner) market.
        """
        if not api_response:
            return None

        bookmaker_odds = []
        fixture_id = 0

        for entry in api_response:
            fixture_id = entry.get("fixture", {}).get("id", 0)
            for bm in entry.get("bookmakers", []):
                bm_name = bm.get("name", "Unknown")
                for bet in bm.get("bets", []):
                    if bet.get("name") == "Match Winner":
                        values = {v["value"]: float(v["odd"]) for v in bet.get("values", [])}
                        if "Home" in values and "Draw" in values and "Away" in values:
                            bookmaker_odds.append(BookmakerOdds(
                                bookmaker=bm_name,
                                home_win=values["Home"],
                                draw=values["Draw"],
                                away_win=values["Away"],
                            ))

        if not bookmaker_odds:
            return None

        # Calculate averages
        n = len(bookmaker_odds)
        avg_home = sum(b.home_win for b in bookmaker_odds) / n
        avg_draw = sum(b.draw for b in bookmaker_odds) / n
        avg_away = sum(b.away_win for b in bookmaker_odds) / n

        # Calculate implied probabilities (remove overround)
        raw_total = (1/avg_home) + (1/avg_draw) + (1/avg_away)
        impl_home = (1/avg_home) / raw_total
        impl_draw = (1/avg_draw) / raw_total
        impl_away = (1/avg_away) / raw_total

        market = MarketOdds(
            fixture_id=fixture_id,
            bookmakers=bookmaker_odds,
            avg_home_win=round(avg_home, 3),
            avg_draw=round(avg_draw, 3),
            avg_away_win=round(avg_away, 3),
            implied_prob_home=round(impl_home, 4),
            implied_prob_draw=round(impl_draw, 4),
            implied_prob_away=round(impl_away, 4),
        )

        logger.info(
            f"Parsed odds from {n} bookmakers: "
            f"H={avg_home:.2f} D={avg_draw:.2f} A={avg_away:.2f}"
        )
        return market

    @staticmethod
    def calculate_implied_probability(odds: float) -> float:
        """Convert decimal odds to implied probability."""
        if odds <= 1.0:
            return 1.0
        return 1.0 / odds

    @staticmethod
    def calculate_value_edge(model_prob: float, market_odds: float) -> float:
        """
        Calculate value edge.
        Positive edge = value bet opportunity.
        """
        implied_prob = 1.0 / market_odds if market_odds > 1 else 1.0
        return model_prob - implied_prob

    @staticmethod
    def kelly_criterion(
        probability: float,
        odds: float,
        fraction: float = 0.25,
    ) -> float:
        """
        Calculate Kelly Criterion stake.

        Args:
            probability: Model's estimated probability
            odds: Decimal odds
            fraction: Kelly fraction (0.25 = quarter Kelly for safety)

        Returns:
            Recommended stake as fraction of bankroll
        """
        if odds <= 1 or probability <= 0 or probability >= 1:
            return 0.0

        b = odds - 1  # net odds on a $1 bet
        q = 1 - probability

        kelly = (b * probability - q) / b

        # Apply fraction and floor at 0
        return max(0.0, round(kelly * fraction, 4))
