"""
Sports AI — Agent 2: Match Context Agent
Identifies competitive context: league, tournament stage, rivalry, match importance.
"""

from typing import Dict, Any, List
from backend.agents.base_agent import BaseAgent
from backend.services.api_football_client import get_api_football_client

# Known rivalries database
RIVALRIES = {
    frozenset({"barcelona", "real madrid"}): "El Clásico",
    frozenset({"atletico madrid", "real madrid"}): "Derby of Madrid",
    frozenset({"ac milan", "inter"}): "Derby della Madonnina",
    frozenset({"liverpool", "manchester united"}): "North West Derby",
    frozenset({"arsenal", "tottenham"}): "North London Derby",
    frozenset({"boca juniors", "river plate"}): "Superclásico",
    frozenset({"celtic", "rangers"}): "Old Firm",
    frozenset({"bayern munich", "borussia dortmund"}): "Der Klassiker",
    frozenset({"psg", "olympique marseille"}): "Le Classique",
    frozenset({"roma", "lazio"}): "Derby della Capitale",
    frozenset({"benfica", "porto"}): "O Clássico",
    frozenset({"galatasaray", "fenerbahce"}): "Intercontinental Derby",
    frozenset({"flamengo", "vasco da gama"}): "Clássico dos Milhões",
    frozenset({"nacional", "millonarios"}): "El Clásico Colombiano",
}


class ContextAgent(BaseAgent):
    """Identifies match competitive context."""

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        team_home = context.get("team_home", "").lower()
        team_away = context.get("team_away", "").lower()

        api = get_api_football_client()

        # Search for teams
        home_results = await api.search_teams(context.get("team_home", ""))
        away_results = await api.search_teams(context.get("team_away", ""))

        home_team = home_results[0] if home_results else None
        away_team = away_results[0] if away_results else None

        home_id = home_team["team"]["id"] if home_team else None
        away_id = away_team["team"]["id"] if away_team else None

        # Find fixture
        fixture = None
        league_info = {}
        if home_id and away_id:
            # Search upcoming fixtures for home team
            fixtures = await api.get_fixtures(team_id=home_id, next_n=10)
            for f in fixtures:
                away_check = f.get("teams", {}).get("away", {}).get("id")
                if away_check == away_id:
                    fixture = f
                    break

            if fixture:
                league_info = fixture.get("league", {})

        # Check rivalry
        team_pair = frozenset({team_home, team_away})
        rivalry_name = None
        is_rivalry = False
        for pair, name in RIVALRIES.items():
            if pair.issubset(team_pair) or any(
                t1 in t2 or t2 in t1 for t1 in pair for t2 in team_pair
            ):
                rivalry_name = name
                is_rivalry = True
                break

        # Determine match importance
        importance = 0.5
        round_name = league_info.get("round", "").lower() if league_info else ""
        if "final" in round_name:
            importance = 1.0
        elif "semi" in round_name:
            importance = 0.9
        elif "quarter" in round_name:
            importance = 0.85
        elif is_rivalry:
            importance = 0.8

        return {
            "home_team_data": home_team,
            "away_team_data": away_team,
            "home_team_id": home_id,
            "away_team_id": away_id,
            "fixture": fixture,
            "fixture_id": fixture.get("fixture", {}).get("id") if fixture else None,
            "league_id": league_info.get("id"),
            "league_name": league_info.get("name", context.get("league", "Unknown")),
            "league_country": league_info.get("country"),
            "season": league_info.get("season"),
            "round": league_info.get("round"),
            "is_derby": is_rivalry,
            "is_rivalry": is_rivalry,
            "rivalry_name": rivalry_name,
            "competition_stage": round_name or "regular_season",
            "match_importance": importance,
        }
