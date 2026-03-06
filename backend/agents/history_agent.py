"""
Sports AI — Agent 3: Historical Data Agent
Fetches and analyzes team performance history from API-Football.
Uses DeepSeek to generate rich historical narrative and pattern analysis.
"""

import json
from typing import Dict, Any, List
from backend.agents.base_agent import BaseAgent
from backend.services.api_football_client import get_api_football_client
from backend.services.feature_engineering import FeatureEngineeringService
from backend.llm.llm_router import get_llm_router

HISTORY_SYSTEM_PROMPT = """Eres un analista deportivo experto en datos históricos de fútbol. Recibirás datos REALES de partidos recientes y enfrentamientos directos (H2H).

Tu trabajo es generar un análisis profundo basado ÚNICAMENTE en los datos proporcionados:
1. Forma reciente de cada equipo con contexto (¿están en racha? ¿en declive?)
2. Análisis del H2H: ¿hay dominancia? ¿patrones de goles? ¿empates frecuentes?
3. Tendencias de goles (equipos ofensivos vs defensivos)
4. Momentum real basado en la secuencia de resultados

Devuelve ÚNICAMENTE un objeto JSON:
{
  "history_narrative": "párrafo de 4-6 líneas analizando el historial con datos específicos",
  "home_form_analysis": "2-3 líneas sobre la forma del local con resultados reales",
  "away_form_analysis": "2-3 líneas sobre la forma del visitante con resultados reales",
  "h2h_analysis": "2-3 líneas sobre el historial directo con datos específicos",
  "key_historical_patterns": ["patrón1", "patrón2", "patrón3"],
  "goals_trend": "descripción de la tendencia de goles en los partidos recientes",
  "upset_risk": "bajo/medio/alto — basado en datos históricos con justificación"
}"""


class HistoryAgent(BaseAgent):
    """Analyzes historical match data with real API data and LLM narrative."""

    def __init__(self):
        super().__init__()
        self.fe = FeatureEngineeringService()

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        api = get_api_football_client()
        home_id = context.get("home_team_id")
        away_id = context.get("away_team_id")

        if not home_id or not away_id:
            self.logger.warning("Team IDs not found — cannot build API history stats")
            return self._insufficient_data_stats("No se pudieron identificar ambos equipos en la API.")

        # Fetch data from API-Football
        home_last_20 = await api.get_fixtures(team_id=home_id, last=20)
        away_last_20 = await api.get_fixtures(team_id=away_id, last=20)
        h2h = await api.get_h2h(home_id, away_id, last=20)

        if not home_last_20 and not away_last_20:
            self.logger.warning("No fixture data from API — history unavailable")
            return self._insufficient_data_stats("No hay histórico reciente disponible desde la API.")

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

        h2h_summary = {
            "total_matches": len(h2h_results),
            "home_wins": h2h_home_wins,
            "draws": h2h_draws,
            "away_wins": h2h_away_wins,
        }

        history_data_source = "api" if home_last_20 and away_last_20 else "partial_api"

        # ── DeepSeek: historical analysis ──
        llm_analysis = await self._analyze_history_with_llm(
            context, home_results, away_results, h2h_results,
            home_stats, away_stats, h2h_summary
        )

        return {
            "home_stats": home_stats,
            "away_stats": away_stats,
            "home_results": home_results[:5],
            "away_results": away_results[:5],
            "h2h_results": h2h_results,
            "h2h_summary": h2h_summary,
            "history_narrative": llm_analysis.get("history_narrative", ""),
            "home_form_analysis": llm_analysis.get("home_form_analysis", ""),
            "away_form_analysis": llm_analysis.get("away_form_analysis", ""),
            "h2h_analysis": llm_analysis.get("h2h_analysis", ""),
            "key_historical_patterns": llm_analysis.get("key_historical_patterns", []),
            "goals_trend": llm_analysis.get("goals_trend", ""),
            "upset_risk": llm_analysis.get("upset_risk", ""),
            "history_data_source": history_data_source,
            "history_data_available": True,
        }

    async def _analyze_history_with_llm(
        self, context, home_results, away_results, h2h_results,
        home_stats, away_stats, h2h_summary
    ) -> Dict:
        """Use DeepSeek to analyze historical data."""
        home = context.get("team_home", "Home")
        away = context.get("team_away", "Away")

        prompt_parts = [f"Match: {home} vs {away}\n"]

        # Home recent results
        prompt_parts.append(f"--- {home} Last 5 Matches ---")
        for i, r in enumerate(home_results[:5]):
            result = "W" if r["goals_home"] > r["goals_away"] else ("D" if r["goals_home"] == r["goals_away"] else "L")
            prompt_parts.append(
                f"  {i+1}. {r.get('home_team', '?')} {r['goals_home']}-{r['goals_away']} {r.get('away_team', '?')} [{result}]"
            )
        prompt_parts.append(
            f"Stats: {home_stats['wins_last_5']}W-{home_stats['draws_last_5']}D-{home_stats['losses_last_5']}L | "
            f"GF:{home_stats['goals_scored_last_5']} GA:{home_stats['goals_conceded_last_5']} | "
            f"Form: {home_stats['form_score']}/100 | Momentum: {home_stats['momentum']}"
        )

        # Away recent results
        prompt_parts.append(f"\n--- {away} Last 5 Matches ---")
        for i, r in enumerate(away_results[:5]):
            result = "W" if r["goals_away"] > r["goals_home"] else ("D" if r["goals_away"] == r["goals_home"] else "L")
            prompt_parts.append(
                f"  {i+1}. {r.get('home_team', '?')} {r['goals_home']}-{r['goals_away']} {r.get('away_team', '?')} [{result}]"
            )
        prompt_parts.append(
            f"Stats: {away_stats['wins_last_5']}W-{away_stats['draws_last_5']}D-{away_stats['losses_last_5']}L | "
            f"GF:{away_stats['goals_scored_last_5']} GA:{away_stats['goals_conceded_last_5']} | "
            f"Form: {away_stats['form_score']}/100 | Momentum: {away_stats['momentum']}"
        )

        # H2H
        prompt_parts.append(f"\n--- Head to Head (last {len(h2h_results)} matches) ---")
        for i, r in enumerate(h2h_results[:10]):
            prompt_parts.append(
                f"  {i+1}. {r.get('home_team', '?')} {r['goals_home']}-{r['goals_away']} {r.get('away_team', '?')}"
            )
        prompt_parts.append(
            f"H2H Summary: {h2h_summary['home_wins']}W-{h2h_summary['draws']}D-{h2h_summary['away_wins']}L (from {home}'s perspective)"
        )

        prompt = "\n".join(prompt_parts)

        llm = get_llm_router()
        response = await llm.chat(
            system_prompt=HISTORY_SYSTEM_PROMPT,
            user_message=prompt,
            temperature=0.4,
        )

        try:
            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(clean)
        except (json.JSONDecodeError, IndexError):
            self.logger.warning("Failed to parse history LLM response")
            return {}

    @staticmethod
    def _insufficient_data_stats(reason: str) -> Dict:
        """Return a deterministic empty payload when API history is unavailable."""
        neutral_stats = {
            "form_score": 50.0,
            "goal_average": 0.0,
            "defense_rating": 50.0,
            "attack_rating": 50.0,
            "momentum": 0.0,
            "wins_last_5": 0,
            "draws_last_5": 0,
            "losses_last_5": 0,
            "goals_scored_last_5": 0,
            "goals_conceded_last_5": 0,
        }
        return {
            "home_stats": neutral_stats,
            "away_stats": neutral_stats.copy(),
            "home_results": [], "away_results": [], "h2h_results": [],
            "h2h_summary": {"total_matches": 0, "home_wins": 0, "draws": 0, "away_wins": 0},
            "history_narrative": "Histórico no disponible: no se obtuvieron partidos desde la API.",
            "home_form_analysis": "",
            "away_form_analysis": "",
            "h2h_analysis": "",
            "key_historical_patterns": [],
            "goals_trend": "",
            "upset_risk": "",
            "history_data_source": "missing",
            "history_data_available": False,
            "history_data_warning": reason,
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
