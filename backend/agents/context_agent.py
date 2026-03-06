"""
Sports AI — Agent 2: Match Context Agent
Identifies competitive context: league, tournament stage, rivalry, match importance.
Uses API-Football standings + team statistics + DeepSeek for deep contextual analysis.
"""

import json
from typing import Dict, Any, List
from backend.agents.base_agent import BaseAgent
from backend.services.api_football_client import get_api_football_client
from backend.llm.llm_router import get_llm_router

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

CONTEXT_SYSTEM_PROMPT = """Eres un analista deportivo experto en contexto competitivo de fútbol. Dado un partido con datos reales de la temporada, genera un análisis contextual profundo.

Debes analizar:
1. La importancia del partido según la posición de ambos equipos en la tabla
2. Qué se juega cada equipo (descenso, clasificación europea, título, etc.)
3. El momento de temporada y la urgencia de puntos
4. Si es un derby/clásico, el factor emocional adicional
5. Ventaja/desventaja de localía basado en estadísticas reales de la temporada
6. Rendimiento como local vs visitante según las stats oficiales

Devuelve ÚNICAMENTE un objeto JSON:
{
  "context_narrative": "párrafo de 3-5 líneas con el análisis contextual profundo",
  "match_importance_score": 0.0-1.0,
  "home_motivation": "alta/media/baja — con razón",
  "away_motivation": "alta/media/baja — con razón",
  "key_context_factors": ["factor1", "factor2", "factor3"],
  "tactical_context": "una línea sobre qué implica tácticamente este contexto"
}"""


class ContextAgent(BaseAgent):
    """Identifies match competitive context with real data and LLM analysis."""

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

        # ── NEW: Fetch standings and team statistics ──
        league_id = league_info.get("id")
        season = league_info.get("season")
        standings_data = {}
        home_season_stats = None
        away_season_stats = None

        if league_id and season:
            # Get league standings
            raw_standings = await api.get_standings(league_id, season)
            if raw_standings:
                standings_data = self._parse_standings(raw_standings, home_id, away_id)

            # Get full season statistics for each team
            if home_id:
                home_season_stats = await api.get_team_statistics(home_id, league_id, season)
            if away_id:
                away_season_stats = await api.get_team_statistics(away_id, league_id, season)

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

        # ── DeepSeek: contextual analysis ──
        llm_analysis = await self._analyze_context_with_llm(
            context, standings_data, home_season_stats, away_season_stats,
            league_info, is_rivalry, rivalry_name, round_name
        )

        return {
            "home_team_data": home_team,
            "away_team_data": away_team,
            "home_team_id": home_id,
            "away_team_id": away_id,
            "fixture": fixture,
            "fixture_id": fixture.get("fixture", {}).get("id") if fixture else None,
            "league_id": league_id,
            "league_name": league_info.get("name", context.get("league", "Unknown")),
            "league_country": league_info.get("country"),
            "season": season,
            "round": league_info.get("round"),
            "is_derby": is_rivalry,
            "is_rivalry": is_rivalry,
            "rivalry_name": rivalry_name,
            "competition_stage": round_name or "regular_season",
            "match_importance": llm_analysis.get("match_importance_score", importance),
            "standings": standings_data,
            "home_season_stats": home_season_stats,
            "away_season_stats": away_season_stats,
            "context_narrative": llm_analysis.get("context_narrative", ""),
            "home_motivation": llm_analysis.get("home_motivation", ""),
            "away_motivation": llm_analysis.get("away_motivation", ""),
            "key_context_factors": llm_analysis.get("key_context_factors", []),
            "tactical_context": llm_analysis.get("tactical_context", ""),
        }

    async def _analyze_context_with_llm(
        self, context, standings, home_stats, away_stats,
        league_info, is_rivalry, rivalry_name, round_name
    ) -> Dict:
        """Use DeepSeek to generate deep contextual analysis."""
        home = context.get("team_home", "Unknown")
        away = context.get("team_away", "Unknown")

        # Build rich prompt with real data
        prompt_parts = [f"Match: {home} vs {away}"]
        prompt_parts.append(f"League: {league_info.get('name', 'Unknown')}")
        prompt_parts.append(f"Round: {round_name or 'Unknown'}")
        prompt_parts.append(f"Is Rivalry: {is_rivalry} ({rivalry_name or 'N/A'})")

        if standings:
            prompt_parts.append(f"\n--- Standings ---")
            if standings.get("home"):
                h = standings["home"]
                prompt_parts.append(
                    f"{home}: Position {h.get('rank')}/{h.get('total_teams')} | "
                    f"{h.get('points')} pts | {h.get('played')} PJ | "
                    f"Form: {h.get('form', 'N/A')} | GD: {h.get('goalsDiff', 0)}"
                )
            if standings.get("away"):
                a = standings["away"]
                prompt_parts.append(
                    f"{away}: Position {a.get('rank')}/{a.get('total_teams')} | "
                    f"{a.get('points')} pts | {a.get('played')} PJ | "
                    f"Form: {a.get('form', 'N/A')} | GD: {a.get('goalsDiff', 0)}"
                )

        if home_stats:
            h_fix = home_stats.get("fixtures", {})
            h_goals = home_stats.get("goals", {})
            prompt_parts.append(f"\n--- {home} Season Stats ---")
            prompt_parts.append(
                f"Record: W{h_fix.get('wins', {}).get('total', 0)} "
                f"D{h_fix.get('draws', {}).get('total', 0)} "
                f"L{h_fix.get('loses', {}).get('total', 0)}"
            )
            prompt_parts.append(
                f"Home Record: W{h_fix.get('wins', {}).get('home', 0)} "
                f"D{h_fix.get('draws', {}).get('home', 0)} "
                f"L{h_fix.get('loses', {}).get('home', 0)}"
            )
            prompt_parts.append(
                f"Goals For: {h_goals.get('for', {}).get('total', {}).get('total', 0)} | "
                f"Goals Against: {h_goals.get('against', {}).get('total', {}).get('total', 0)}"
            )
            if home_stats.get("lineups"):
                fav = home_stats["lineups"][0] if home_stats["lineups"] else {}
                prompt_parts.append(f"Favorite Formation: {fav.get('formation', 'N/A')} (used {fav.get('played', 0)} times)")

        if away_stats:
            a_fix = away_stats.get("fixtures", {})
            a_goals = away_stats.get("goals", {})
            prompt_parts.append(f"\n--- {away} Season Stats ---")
            prompt_parts.append(
                f"Record: W{a_fix.get('wins', {}).get('total', 0)} "
                f"D{a_fix.get('draws', {}).get('total', 0)} "
                f"L{a_fix.get('loses', {}).get('total', 0)}"
            )
            prompt_parts.append(
                f"Away Record: W{a_fix.get('wins', {}).get('away', 0)} "
                f"D{a_fix.get('draws', {}).get('away', 0)} "
                f"L{a_fix.get('loses', {}).get('away', 0)}"
            )
            prompt_parts.append(
                f"Goals For: {a_goals.get('for', {}).get('total', {}).get('total', 0)} | "
                f"Goals Against: {a_goals.get('against', {}).get('total', {}).get('total', 0)}"
            )
            if away_stats.get("lineups"):
                fav = away_stats["lineups"][0] if away_stats["lineups"] else {}
                prompt_parts.append(f"Favorite Formation: {fav.get('formation', 'N/A')} (used {fav.get('played', 0)} times)")

        prompt = "\n".join(prompt_parts)

        llm = get_llm_router()
        response = await llm.chat(
            system_prompt=CONTEXT_SYSTEM_PROMPT,
            user_message=prompt,
            temperature=0.4,
        )

        try:
            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(clean)
        except (json.JSONDecodeError, IndexError):
            self.logger.warning("Failed to parse context LLM response")
            return {}

    @staticmethod
    def _parse_standings(raw_standings: List[Dict], home_id: int, away_id: int) -> Dict:
        """Parse standings to find both teams' positions."""
        result = {}
        for entry in raw_standings:
            league = entry.get("league", {})
            for group_standings in league.get("standings", []):
                total_teams = len(group_standings)
                for team_standing in group_standings:
                    tid = team_standing.get("team", {}).get("id")
                    if tid == home_id:
                        result["home"] = {**team_standing, "total_teams": total_teams}
                    elif tid == away_id:
                        result["away"] = {**team_standing, "total_teams": total_teams}
        return result
