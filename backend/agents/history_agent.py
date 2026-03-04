"""
Sports AI — Agent 3: Historical Data Agent
Fetches and analyzes team performance history from API-Football.
"""

from typing import Dict, Any, List
from backend.agents.base_agent import BaseAgent
from backend.services.api_football_client import get_api_football_client
from backend.services.feature_engineering import FeatureEngineeringService


class HistoryAgent(BaseAgent):
    """Analyzes historical match data for both teams."""

    def __init__(self):
        super().__init__()
        self.fe = FeatureEngineeringService()

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        api = get_api_football_client()
        home_id = context.get("home_team_id")
        away_id = context.get("away_team_id")

        if not home_id or not away_id:
            self.logger.warning("Team IDs not found — using league-average fallback stats")
            return self._default_stats(context)

        # Fetch data in parallel-style (sequential for simplicity)
        home_last_20 = await api.get_fixtures(team_id=home_id, last=20)
        away_last_20 = await api.get_fixtures(team_id=away_id, last=20)
        h2h = await api.get_h2h(home_id, away_id, last=20)

        # If API returned no fixtures, use fallback
        if not home_last_20 and not away_last_20:
            self.logger.warning("No fixture data from API — using league-average fallback stats")
            return self._default_stats(context)

        # Process results
        home_results = self._parse_results(home_last_20, home_id)
        away_results = self._parse_results(away_last_20, away_id)
        h2h_results = self._parse_results(h2h, home_id)

        # Calculate stats for home team
        home_stats = {
            "form_score": self.fe.calculate_form_score(home_results[:5], True),
            "goal_average": self.fe.calculate_goal_average(home_results[:10], True),
            "defense_rating": self.fe.calculate_defense_rating(home_results[:10], True),
            "attack_rating": self.fe.calculate_attack_rating(home_results[:10], True),
            "momentum": self.fe.calculate_momentum(home_results, True),
            "wins_last_5": sum(1 for r in home_results[:5] if r["goals_home"] > r["goals_away"]),
            "draws_last_5": sum(1 for r in home_results[:5] if r["goals_home"] == r["goals_away"]),
            "losses_last_5": sum(1 for r in home_results[:5] if r["goals_home"] < r["goals_away"]),
            "goals_scored_last_5": sum(r["goals_home"] for r in home_results[:5]),
            "goals_conceded_last_5": sum(r["goals_away"] for r in home_results[:5]),
        }

        # Calculate stats for away team
        away_stats = {
            "form_score": self.fe.calculate_form_score(away_results[:5], False),
            "goal_average": self.fe.calculate_goal_average(away_results[:10], False),
            "defense_rating": self.fe.calculate_defense_rating(away_results[:10], False),
            "attack_rating": self.fe.calculate_attack_rating(away_results[:10], False),
            "momentum": self.fe.calculate_momentum(away_results, False),
            "wins_last_5": sum(1 for r in away_results[:5] if r["goals_away"] > r["goals_home"]),
            "draws_last_5": sum(1 for r in away_results[:5] if r["goals_away"] == r["goals_home"]),
            "losses_last_5": sum(1 for r in away_results[:5] if r["goals_away"] < r["goals_home"]),
            "goals_scored_last_5": sum(r["goals_away"] for r in away_results[:5]),
            "goals_conceded_last_5": sum(r["goals_home"] for r in away_results[:5]),
        }

        # H2H analysis
        h2h_home_wins = sum(1 for r in h2h_results if r["goals_home"] > r["goals_away"])
        h2h_draws = sum(1 for r in h2h_results if r["goals_home"] == r["goals_away"])
        h2h_away_wins = len(h2h_results) - h2h_home_wins - h2h_draws

        return {
            "home_stats": home_stats,
            "away_stats": away_stats,
            "home_results": home_results[:5],
            "away_results": away_results[:5],
            "h2h_results": h2h_results,
            "h2h_summary": {
                "total_matches": len(h2h_results),
                "home_wins": h2h_home_wins,
                "draws": h2h_draws,
                "away_wins": h2h_away_wins,
            },
        }

    @staticmethod
    def _default_stats(context: Dict) -> Dict:
        """Return realistic league-average fallback stats when API data is unavailable."""
        return {
            "home_stats": {
                "form_score": 55.0,
                "goal_average": 1.4,
                "defense_rating": 52.0,
                "attack_rating": 56.0,
                "momentum": 0.1,
                "wins_last_5": 2,
                "draws_last_5": 1,
                "losses_last_5": 2,
                "goals_scored_last_5": 6,
                "goals_conceded_last_5": 5,
            },
            "away_stats": {
                "form_score": 48.0,
                "goal_average": 1.1,
                "defense_rating": 47.0,
                "attack_rating": 49.0,
                "momentum": -0.05,
                "wins_last_5": 1,
                "draws_last_5": 2,
                "losses_last_5": 2,
                "goals_scored_last_5": 4,
                "goals_conceded_last_5": 6,
            },
            "home_results": [],
            "away_results": [],
            "h2h_results": [],
            "h2h_summary": {
                "total_matches": 0,
                "home_wins": 0,
                "draws": 0,
                "away_wins": 0,
            },
        }

    @staticmethod
    def _parse_results(fixtures: List[Dict], reference_team_id: int) -> List[Dict]:
        """Parse API-Football fixture data into simplified result format."""
        results = []
        for f in fixtures:
            teams = f.get("teams", {})
            goals = f.get("goals", {})

            home_id = teams.get("home", {}).get("id")
            is_home = home_id == reference_team_id

            results.append({
                "fixture_id": f.get("fixture", {}).get("id"),
                "date": f.get("fixture", {}).get("date"),
                "goals_home": goals.get("home", 0) or 0,
                "goals_away": goals.get("away", 0) or 0,
                "is_home": is_home,
                "home_team": teams.get("home", {}).get("name"),
                "away_team": teams.get("away", {}).get("name"),
            })
        return results
