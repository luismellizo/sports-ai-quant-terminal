"""
Sports AI — Agent 8: ELO Rating Agent
Calculates dynamic ELO ratings for both teams.
"""

from typing import Dict, Any
from backend.agents.base_agent import BaseAgent

# Base ELO ratings for known leagues (defaults)
LEAGUE_BASE_ELO = {
    # Europe - Top 5
    "Premier League": 1700,
    "La Liga": 1680,
    "Serie A": 1650,
    "Bundesliga": 1660,
    "Ligue 1": 1620,
    # Europe - Other
    "Eredivisie": 1600,
    "Primeira Liga": 1610,
    "Liga Portugal": 1610,
    "Super Lig": 1580,
    "Belgian Pro League": 1570,
    "Scottish Premiership": 1550,
    # European cups
    "Champions League": 1750,
    "Europa League": 1650,
    "Conference League": 1600,
    # South America
    "Liga Profesional Argentina": 1620,
    "Primera División": 1620,
    "Serie A": 1650,
    "Brasileirão": 1630,
    "Liga BetPlay": 1560,
    "Liga 1": 1540,
    "Primera A": 1560,
    "Liga MX": 1580,
    "Copa Libertadores": 1680,
    "Copa Sudamericana": 1600,
    # North America
    "MLS": 1560,
    # Asia
    "J1 League": 1560,
    "K League 1": 1550,
    "Saudi Pro League": 1570,
}

DEFAULT_BASE_ELO = 1550  # For unknown leagues
K_FACTOR = 32  # ELO K-factor


class EloAgent(BaseAgent):
    """Calculates dynamic ELO ratings based on recent results."""

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        home_stats = context.get("home_stats", {})
        away_stats = context.get("away_stats", {})
        league = context.get("league_name", "")
        home_results = context.get("home_results", [])
        away_results = context.get("away_results", [])

        # Starting ELO based on league
        base_elo = LEAGUE_BASE_ELO.get(league, DEFAULT_BASE_ELO)
        home_elo = base_elo + self._elo_from_form(home_stats)
        away_elo = base_elo + self._elo_from_form(away_stats)

        # Adjust based on recent results
        home_elo = self._adjust_elo_from_results(home_elo, home_results, True)
        away_elo = self._adjust_elo_from_results(away_elo, away_results, False)

        # Calculate expected results
        elo_diff = home_elo - away_elo
        expected_home = 1.0 / (1.0 + 10 ** (-elo_diff / 400))
        expected_away = 1.0 - expected_home

        return {
            "home_elo": round(home_elo, 1),
            "away_elo": round(away_elo, 1),
            "elo_difference": round(elo_diff, 1),
            "elo_expected_home": round(expected_home, 4),
            "elo_expected_away": round(expected_away, 4),
        }

    @staticmethod
    def _elo_from_form(stats: Dict) -> float:
        """Convert form metrics to ELO adjustment."""
        form = stats.get("form_score", 50.0)
        attack = stats.get("attack_rating", 50.0)
        defense = stats.get("defense_rating", 50.0)

        # Map 0-100 form to -100 to +100 ELO adjustment
        form_adj = (form - 50) * 2
        attack_adj = (attack - 50) * 0.5
        defense_adj = (defense - 50) * 0.5

        return form_adj + attack_adj + defense_adj

    @staticmethod
    def _adjust_elo_from_results(elo: float, results: list, is_home: bool) -> float:
        """Fine-tune ELO based on recent match results."""
        for i, match in enumerate(results[:5]):
            weight = K_FACTOR * (0.8 ** i)  # Recent matches weighted more
            gf = match.get("goals_home", 0) if is_home else match.get("goals_away", 0)
            ga = match.get("goals_away", 0) if is_home else match.get("goals_home", 0)

            if gf > ga:  # Win
                elo += weight * 0.3
            elif gf < ga:  # Loss
                elo -= weight * 0.3
            # Draw: no change

            # Goal difference bonus
            goal_diff = gf - ga
            elo += goal_diff * weight * 0.05

        return elo
