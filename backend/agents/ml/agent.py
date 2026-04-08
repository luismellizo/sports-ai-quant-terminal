"""
Sports AI — ML Agent
Uses API signals + cross-validation with DeepSeek.
"""

import json
from typing import Dict, Any

from backend.agents.core.base import BaseAgent
from backend.agents.core.contracts import AgentContext
from backend.services.api_football_client import get_api_football_client
from backend.llm.llm_router import get_llm_router


ML_SYSTEM_PROMPT = """Eres un analista cuantitativo de fútbol especializado en machine learning y modelos predictivos.

Devuelve ÚNICAMENTE un objeto JSON:
{
  "ml_narrative": "3-4 líneas de análisis comparativo entre modelos",
  "consensus_home_win": 0.0-1.0,
  "consensus_draw": 0.0-1.0,
  "consensus_away_win": 0.0-1.0,
  "model_agreement": "alto/medio/bajo — con datos específicos",
  "api_prediction_summary": "resumen de qué predice la API o proxy de mercado",
  "key_prediction_factors": ["factor1", "factor2", "factor3"],
  "confidence_in_prediction": "alta/media/baja — justificación"
}"""


class MLAgent(BaseAgent):
    name = "MLAgent"
    is_critical = False
    timeout_seconds = 60.0

    async def execute(self, ctx: AgentContext) -> Dict[str, Any]:
        api = get_api_football_client()
        fixture_id = ctx.data.get("fixture_id")

        api_prediction = None
        if fixture_id:
            api_prediction = await api.get_predictions(fixture_id)

        api_probs = {}
        api_advice = ""
        if api_prediction:
            predictions = api_prediction.get("predictions", {})
            api_advice = predictions.get("advice", "")
            percent = predictions.get("percent", {})
            api_probs = {
                "home_win": self._parse_percent(percent.get("home")),
                "draw": self._parse_percent(percent.get("draw")),
                "away_win": self._parse_percent(percent.get("away")),
            }

        if not api_probs:
            implied = ctx.data.get("implied_probabilities", {})
            home_implied = implied.get("home")
            draw_implied = implied.get("draw")
            away_implied = implied.get("away")
            if all(v is not None for v in (home_implied, draw_implied, away_implied)):
                api_probs = {
                    "home_win": float(home_implied),
                    "draw": float(draw_implied),
                    "away_win": float(away_implied),
                }
                api_advice = "Proxy de mercado (probabilidades implícitas)."

        poisson_probs = {
            "home_win": ctx.data.get("poisson_home_win", 0.33),
            "draw": ctx.data.get("poisson_draw", 0.33),
            "away_win": ctx.data.get("poisson_away_win", 0.33),
        }

        llm_analysis = await self._cross_validate_with_llm(
            ctx.data, api_probs, poisson_probs, api_advice
        )

        ml_home = llm_analysis.get("consensus_home_win")
        ml_draw = llm_analysis.get("consensus_draw")
        ml_away = llm_analysis.get("consensus_away_win")

        if ml_home is None or ml_draw is None or ml_away is None:
            if api_probs:
                ml_home = api_probs["home_win"] * 0.6 + poisson_probs["home_win"] * 0.4
                ml_draw = api_probs["draw"] * 0.6 + poisson_probs["draw"] * 0.4
                ml_away = api_probs["away_win"] * 0.6 + poisson_probs["away_win"] * 0.4
            else:
                ml_home, ml_draw, ml_away = (
                    poisson_probs["home_win"],
                    poisson_probs["draw"],
                    poisson_probs["away_win"],
                )

        ml_data_source = (
            "api+poisson"
            if api_prediction and api_probs
            else ("odds_proxy+poisson" if api_probs else "poisson_only")
        )

        return {
            "ml_home_win": round(ml_home, 4),
            "ml_draw": round(ml_draw, 4),
            "ml_away_win": round(ml_away, 4),
            "api_prediction": api_probs,
            "api_prediction_available": bool(api_probs),
            "api_advice": api_advice,
            "ml_narrative": llm_analysis.get("ml_narrative", ""),
            "model_agreement": llm_analysis.get("model_agreement", ""),
            "api_prediction_summary": llm_analysis.get("api_prediction_summary", ""),
            "key_prediction_factors": llm_analysis.get("key_prediction_factors", []),
            "confidence_in_prediction": llm_analysis.get(
                "confidence_in_prediction", ""
            ),
            "ml_data_source": ml_data_source,
        }

    async def _cross_validate_with_llm(
        self, context, api_probs, poisson_probs, api_advice
    ):
        home = context.get("team_home", "Home")
        away = context.get("team_away", "Away")
        prompt_parts = [
            f"Match: {home} vs {away}\n--- Poisson Model ---",
            f"{home}: {poisson_probs['home_win']:.1%} | Draw: {poisson_probs['draw']:.1%} | {away}: {poisson_probs['away_win']:.1%}",
            f"xG: {context.get('expected_goals_home', 0):.2f} - {context.get('expected_goals_away', 0):.2f}",
        ]
        if api_probs:
            prompt_parts.append("\n--- API/Market Prediction ---")
            prompt_parts.append(
                f"{home}: {api_probs.get('home_win', 0):.1%} | Draw: {api_probs.get('draw', 0):.1%} | {away}: {api_probs.get('away_win', 0):.1%}"
            )
            if api_advice:
                prompt_parts.append(f"Advice: {api_advice}")
        llm = get_llm_router()
        response = await llm.chat(
            system_prompt=ML_SYSTEM_PROMPT,
            user_message="\n".join(prompt_parts),
            temperature=0.3,
        )
        try:
            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(clean)
        except (json.JSONDecodeError, IndexError):
            return {}

    @staticmethod
    def _parse_percent(raw_value):
        if raw_value is None:
            return 0.0
        clean = str(raw_value).replace("%", "").strip()
        try:
            return max(0.0, min(1.0, float(clean) / 100.0))
        except ValueError:
            return 0.0
