"""
Sports AI — Agent 4: Lineup Intelligence Agent
Analyzes available lineups, injuries, and suspensions.
Uses DeepSeek for tactical impact analysis of absences and formations.
"""

import json
from typing import Dict, Any, List
from backend.agents.base_agent import BaseAgent
from backend.services.api_football_client import get_api_football_client
from backend.llm.llm_router import get_llm_router

LINEUP_SYSTEM_PROMPT = """Eres un analista táctico de fútbol de élite. Recibirás datos REALES de alineaciones, lesiones y formaciones de un partido.

Tu trabajo es generar un análisis táctico profundo:
1. Impacto de cada baja significativa en el esquema táctico del equipo
2. Cómo las lesiones afectan la profundidad de banquillo y rotaciones
3. Comparación táctica de formaciones (si están disponibles)
4. Ventajas/desventajas posicionales específicas
5. Predicción de cómo las bajas pueden afectar el rendimiento ofensivo y defensivo

Devuelve ÚNICAMENTE un objeto JSON:
{
  "lineup_narrative": "párrafo de 4-6 líneas con el análisis táctico completo",
  "home_tactical_analysis": "2-3 líneas sobre la situación táctica del local",
  "away_tactical_analysis": "2-3 líneas sobre la situación táctica del visitante",
  "key_absences_impact": ["impacto1", "impacto2", "impacto3"],
  "tactical_advantage": "local/visitante/neutral — con justificación",
  "formation_matchup": "análisis de cómo interactúan las formaciones"
}"""


class LineupAgent(BaseAgent):
    """Analyzes lineups and injuries with tactical LLM analysis."""

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

        # ── DeepSeek: tactical analysis ──
        llm_analysis = await self._analyze_lineups_with_llm(
            context, home_lineup, away_lineup,
            injuries_home, injuries_away
        )

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
            "lineup_narrative": llm_analysis.get("lineup_narrative", ""),
            "home_tactical_analysis": llm_analysis.get("home_tactical_analysis", ""),
            "away_tactical_analysis": llm_analysis.get("away_tactical_analysis", ""),
            "key_absences_impact": llm_analysis.get("key_absences_impact", []),
            "tactical_advantage": llm_analysis.get("tactical_advantage", ""),
            "formation_matchup": llm_analysis.get("formation_matchup", ""),
        }

    async def _analyze_lineups_with_llm(
        self, context, home_lineup, away_lineup, injuries_home, injuries_away
    ) -> Dict:
        """Use DeepSeek for tactical analysis."""
        home = context.get("team_home", "Home")
        away = context.get("team_away", "Away")

        prompt_parts = [f"Match: {home} vs {away}\n"]

        # Home lineup
        prompt_parts.append(f"--- {home} Lineup ---")
        prompt_parts.append(f"Formation: {home_lineup.get('formation', 'Not available')}")
        prompt_parts.append(f"Coach: {home_lineup.get('coach', 'Unknown')}")
        if home_lineup.get("starting_xi"):
            for p in home_lineup["starting_xi"]:
                prompt_parts.append(f"  {p.get('pos', '?')} - #{p.get('number', '?')} {p.get('name', '?')}")

        # Away lineup
        prompt_parts.append(f"\n--- {away} Lineup ---")
        prompt_parts.append(f"Formation: {away_lineup.get('formation', 'Not available')}")
        prompt_parts.append(f"Coach: {away_lineup.get('coach', 'Unknown')}")
        if away_lineup.get("starting_xi"):
            for p in away_lineup["starting_xi"]:
                prompt_parts.append(f"  {p.get('pos', '?')} - #{p.get('number', '?')} {p.get('name', '?')}")

        # Injuries
        prompt_parts.append(f"\n--- {home} Injuries ({len(injuries_home)} total) ---")
        for inj in injuries_home[:10]:
            player = inj.get("player", {})
            prompt_parts.append(
                f"  - {player.get('name', '?')} | Type: {player.get('type', '?')} | Reason: {player.get('reason', '?')}"
            )

        prompt_parts.append(f"\n--- {away} Injuries ({len(injuries_away)} total) ---")
        for inj in injuries_away[:10]:
            player = inj.get("player", {})
            prompt_parts.append(
                f"  - {player.get('name', '?')} | Type: {player.get('type', '?')} | Reason: {player.get('reason', '?')}"
            )

        prompt = "\n".join(prompt_parts)

        llm = get_llm_router()
        response = await llm.chat(
            system_prompt=LINEUP_SYSTEM_PROMPT,
            user_message=prompt,
            temperature=0.4,
        )

        try:
            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(clean)
        except (json.JSONDecodeError, IndexError):
            self.logger.warning("Failed to parse lineup LLM response")
            return {}

    @staticmethod
    def _parse_lineup(lineups: List[Dict], team_id: int) -> Dict:
        """Parse lineup data for a specific team."""
        for lineup in lineups:
            if lineup.get("team", {}).get("id") == team_id:
                return {
                    "formation": lineup.get("formation", "Unknown"),
                    "coach": lineup.get("coach", {}).get("name", "Unknown"),
                    "starting_xi": [
                        {"name": p.get("player", {}).get("name"), "number": p.get("player", {}).get("number"), "pos": p.get("player", {}).get("pos")}
                        for p in lineup.get("startXI", [])
                    ],
                    "substitutes": [
                        {"name": p.get("player", {}).get("name"), "number": p.get("player", {}).get("number"), "pos": p.get("player", {}).get("pos")}
                        for p in lineup.get("substitutes", [])
                    ],
                }
        return {"formation": "Unknown", "coach": "Unknown", "starting_xi": [], "substitutes": []}

    @staticmethod
    def _parse_injuries(injuries: List[Dict]) -> List[Dict]:
        """Parse injury data into simplified format."""
        return [
            {"player": i.get("player", {}).get("name", "Unknown"), "type": i.get("player", {}).get("type", "Unknown"), "reason": i.get("player", {}).get("reason", "Unknown")}
            for i in injuries[:10]
        ]

    @staticmethod
    def _calculate_injury_impact(injuries: List[Dict]) -> float:
        """Estimate team strength impact from injuries."""
        if not injuries:
            return 0.0
        count = len(injuries)
        impact = min(0.5, count * 0.05)
        return round(-impact, 3)
