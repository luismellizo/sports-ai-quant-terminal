"""
Sports AI — NLP Agent
Natural Language Processing for user queries.
"""

import re
from typing import Dict, Any

from backend.agents.core.base import BaseAgent
from backend.agents.core.contracts import AgentContext, AgentOutcome, AgentStatus
from backend.agents.registry import register


class NLPAgent(BaseAgent):
    name = "NLPAgent"
    is_critical = True
    timeout_seconds = 10.0

    async def execute(self, ctx: AgentContext) -> Dict[str, Any]:
        query = ctx.query.lower()

        teams = self._extract_teams(query)
        if not teams:
            raise ValueError("No teams found in query")

        league = self._extract_league(query)
        date_hint = self._extract_date_hint(query)

        return {
            "teams_raw": teams,
            "team_home": teams[0] if len(teams) > 0 else "",
            "team_away": teams[1] if len(teams) > 1 else teams[0],
            "league_hint": league,
            "date_hint": date_hint,
            "nlp_parsed": True,
        }

    def _extract_teams(self, query: str) -> list:
        team_patterns = [
            r"(?:analiza?|predice?|pronostico|pronóstico)\s+(?:para|del|match|partido|el\s+partido(?:\s+de)?|el\s+juego)?\s*(?:entre\s+)?(?:de\s+)?([a-záéíóúñ0-9\.\s\'\-]+?)\s+(?:vs|v\s*:?\s*|contra|y)\s+([a-záéíóúñ0-9\.\s\'\-]+?)(?:\s+(?:hoy|mañana|este|el|para|de)|\s*[\?¿]|\s*$)",
            r"(?:partido\s+entre|match\s+entre|entre|match|partido(?: \s+de)?)\s+(?:de\s+)?([a-záéíóúñ0-9\.\s\'\-]+?)\s+(?:y|y\s+contra|vs|v|contra)\s+([a-záéíóúñ0-9\.\s\'\-]+?)(?:\s+(?:hoy|mañana|este|el|para|de)|\s*[\?¿]|\s*$)",
            r"([a-záéíóúñ0-9\.\s\'\-]+?)\s+(?:vs|v\s*:?\s*|contra)\s+([a-záéíóúñ0-9\.\s\'\-]+?)(?:\s+(?:hoy|mañana|este|el|para|de)|\s*[\?¿]|\s*$)",
        ]
        for pattern in team_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                home = match.group(1).strip()
                away = match.group(2).strip()
                if home and away:
                    return [home, away]
        common_teams = [
            "barcelona",
            "real madrid",
            "atlético madrid",
            "sevilla",
            "valencia",
            "arsenal",
            "chelsea",
            "liverpool",
            "manchester",
            "city",
            "united",
            "bayern",
            "dortmund",
            " PSG",
            "milan",
            "inter",
            "juventus",
            "river plate",
            "boca juniors",
            "racing",
            "independiente",
        ]
        found = [t for t in common_teams if t in query]
        return found[:2] if len(found) >= 2 else found

    def _extract_league(self, query: str) -> str:
        leagues = {
            "la liga": ["la liga", "liga española", "español"],
            "premier league": ["premier", "inglés", "ingles"],
            "serie a": ["serie a", "italiano"],
            "bundesliga": ["bundesliga", "alemán"],
            "ligue 1": ["ligue 1", "francés"],
            "copa libertadores": ["libertadores", "copa"],
            "liga mx": ["liga mx", "mx", "mexicano"],
        }
        for league_name, keywords in leagues.items():
            if any(kw in query for kw in keywords):
                return league_name
        return ""

    def _extract_date_hint(self, query: str) -> str:
        date_patterns = [
            (r"mañana", "tomorrow"),
            (r"hoy", "today"),
            (r"despu[eé]s?\s+de\s+mañana", "day_after_tomorrow"),
            (r"este\s+(?:fin\s+de\s+semana|sábado|domingo)", "this_weekend"),
        ]
        for pattern, hint in date_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return hint
        return "upcoming"


register("nlp", NLPAgent)
register("NLPAgent", NLPAgent)
