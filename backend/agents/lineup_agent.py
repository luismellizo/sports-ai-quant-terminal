"""
Sports AI — Agent 4: Lineup Intelligence Agent
Analyzes available lineups, injuries, and suspensions. Estimates team strength impact.
"""

from typing import Dict, Any, List
from backend.agents.base_agent import BaseAgent
from backend.services.api_football_client import get_api_football_client


class LineupAgent(BaseAgent):
    """Analyzes lineups and injuries to estimate team strength impact."""

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        api = get_api_football_client()
        fixture_id = context.get("fixture_id")
        home_id = context.get("home_team_id")
        away_id = context.get("away_team_id")

        lineups = []
        injuries_home = []
        injuries_away = []

        # Fetch lineups if fixture available
        if fixture_id:
            lineups = await api.get_lineups(fixture_id)

        # Fetch injuries
        if home_id:
            injuries_home = await api.get_injuries(team_id=home_id)
        if away_id:
            injuries_away = await api.get_injuries(team_id=away_id)

        # Parse lineups
        home_lineup = self._parse_lineup(lineups, home_id)
        away_lineup = self._parse_lineup(lineups, away_id)

        # Calculate injury impact
        home_injury_impact = self._calculate_injury_impact(injuries_home)
        away_injury_impact = self._calculate_injury_impact(injuries_away)

        return {
            "home_lineup": home_lineup,
            "away_lineup": away_lineup,
            "injuries_home": self._parse_injuries(injuries_home),
            "injuries_away": self._parse_injuries(injuries_away),
            "home_injury_count": len(injuries_home),
            "away_injury_count": len(injuries_away),
            "home_injury_impact": home_injury_impact,
            "away_injury_impact": away_injury_impact,
            "lineup_available": len(lineups) > 0,
        }

    @staticmethod
    def _parse_lineup(lineups: List[Dict], team_id: int) -> Dict:
        """Parse lineup data for a specific team."""
        for lineup in lineups:
            if lineup.get("team", {}).get("id") == team_id:
                return {
                    "formation": lineup.get("formation", "Unknown"),
                    "coach": lineup.get("coach", {}).get("name", "Unknown"),
                    "starting_xi": [
                        {
                            "name": p.get("player", {}).get("name"),
                            "number": p.get("player", {}).get("number"),
                            "pos": p.get("player", {}).get("pos"),
                        }
                        for p in lineup.get("startXI", [])
                    ],
                    "substitutes": [
                        {
                            "name": p.get("player", {}).get("name"),
                            "number": p.get("player", {}).get("number"),
                            "pos": p.get("player", {}).get("pos"),
                        }
                        for p in lineup.get("substitutes", [])
                    ],
                }
        return {"formation": "Unknown", "coach": "Unknown", "starting_xi": [], "substitutes": []}

    @staticmethod
    def _parse_injuries(injuries: List[Dict]) -> List[Dict]:
        """Parse injury data into simplified format."""
        return [
            {
                "player": i.get("player", {}).get("name", "Unknown"),
                "type": i.get("player", {}).get("type", "Unknown"),
                "reason": i.get("player", {}).get("reason", "Unknown"),
            }
            for i in injuries[:10]  # Limit to 10
        ]

    @staticmethod
    def _calculate_injury_impact(injuries: List[Dict]) -> float:
        """
        Estimate team strength impact from injuries.
        Returns a negative value (0 = no impact, -0.5 = severe).
        """
        if not injuries:
            return 0.0

        count = len(injuries)
        # Each injury reduces team strength; diminishing returns
        impact = min(0.5, count * 0.05)
        return round(-impact, 3)
