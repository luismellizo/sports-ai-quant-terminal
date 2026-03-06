"""
Sports AI — Agent 10: Machine Learning Agent
Uses API-derived signals + DeepSeek cross-validation analysis.
"""

import json
from typing import Dict, Any
from backend.agents.base_agent import BaseAgent
from backend.services.api_football_client import get_api_football_client
from backend.llm.llm_router import get_llm_router

ML_SYSTEM_PROMPT = """Eres un analista cuantitativo de fútbol especializado en machine learning y modelos predictivos. Recibirás múltiples fuentes de predicción REALES para un partido.

Tu trabajo es:
1. Comparar las probabilidades de API/mercado con nuestro modelo Poisson
2. Analizar discrepancias entre modelos y qué las causa
3. Generar una predicción consensuada ponderando ambas fuentes
4. Identificar áreas de alta certeza vs áreas de incertidumbre
5. Incluir el "advice" (consejo) de la API si está disponible

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
    """Uses API signals + cross-validation with DeepSeek."""

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        api = get_api_football_client()
        fixture_id = context.get("fixture_id")

        # Try direct API prediction endpoint first (if provider supports it)
        api_prediction = None
        if fixture_id:
            api_prediction = await api.get_predictions(fixture_id)

        # Extract API prediction data
        api_probs = {}
        api_advice = ""
        api_comparison = {}
        winner_data = {}

        if api_prediction:
            predictions = api_prediction.get("predictions", {})
            api_advice = predictions.get("advice", "")
            winner_data = predictions.get("winner", {})

            # Extract percentage predictions
            percent = predictions.get("percent", {})
            api_probs = {
                "home_win": self._parse_percent(percent.get("home")),
                "draw": self._parse_percent(percent.get("draw")),
                "away_win": self._parse_percent(percent.get("away")),
            }

            # Extract comparison data
            api_comparison = api_prediction.get("comparison", {})

        # Statpal has no direct fixture prediction endpoint in Soccer V2.
        # Fallback: use implied probabilities from real market odds as API signal.
        if not api_probs:
            implied = context.get("implied_probabilities", {})
            home_implied = implied.get("home")
            draw_implied = implied.get("draw")
            away_implied = implied.get("away")
            if all(v is not None for v in (home_implied, draw_implied, away_implied)):
                api_probs = {
                    "home_win": float(home_implied),
                    "draw": float(draw_implied),
                    "away_win": float(away_implied),
                }
                api_advice = "Proxy de mercado (probabilidades implícitas de Statpal 1X2)."

        # Get our Poisson predictions from context
        poisson_probs = {
            "home_win": context.get("poisson_home_win", 0.33),
            "draw": context.get("poisson_draw", 0.33),
            "away_win": context.get("poisson_away_win", 0.33),
        }

        # ── DeepSeek: cross-validation analysis ──
        llm_analysis = await self._cross_validate_with_llm(
            context, api_probs, poisson_probs, api_advice,
            api_comparison, winner_data
        )

        # Use consensus probabilities from LLM, or fallback to weighted average
        ml_home = llm_analysis.get("consensus_home_win")
        ml_draw = llm_analysis.get("consensus_draw")
        ml_away = llm_analysis.get("consensus_away_win")

        if ml_home is None or ml_draw is None or ml_away is None:
            # Weighted average: 60% API, 40% Poisson (if API available)
            if api_probs:
                ml_home = api_probs["home_win"] * 0.6 + poisson_probs["home_win"] * 0.4
                ml_draw = api_probs["draw"] * 0.6 + poisson_probs["draw"] * 0.4
                ml_away = api_probs["away_win"] * 0.6 + poisson_probs["away_win"] * 0.4
            else:
                ml_home = poisson_probs["home_win"]
                ml_draw = poisson_probs["draw"]
                ml_away = poisson_probs["away_win"]

        if api_prediction:
            ml_data_source = "api+poisson"
        elif api_probs:
            ml_data_source = "odds_proxy+poisson"
        else:
            ml_data_source = "poisson_only"

        return {
            "ml_home_win": round(ml_home, 4),
            "ml_draw": round(ml_draw, 4),
            "ml_away_win": round(ml_away, 4),
            "api_prediction": api_probs,
            "api_prediction_available": bool(api_probs),
            "api_advice": api_advice,
            "api_comparison": api_comparison,
            "api_winner": winner_data,
            "ml_narrative": llm_analysis.get("ml_narrative", ""),
            "model_agreement": llm_analysis.get("model_agreement", ""),
            "api_prediction_summary": llm_analysis.get("api_prediction_summary", ""),
            "key_prediction_factors": llm_analysis.get("key_prediction_factors", []),
            "confidence_in_prediction": llm_analysis.get("confidence_in_prediction", ""),
            "ml_data_source": ml_data_source,
        }

    async def _cross_validate_with_llm(
        self, context, api_probs, poisson_probs, api_advice,
        api_comparison, winner_data
    ) -> Dict:
        home = context.get("team_home", "Home")
        away = context.get("team_away", "Away")

        prompt_parts = [f"Match: {home} vs {away}\n"]

        # Our Poisson model
        prompt_parts.append("--- Our Poisson Model ---")
        prompt_parts.append(
            f"  {home}: {poisson_probs['home_win']:.1%} | "
            f"Draw: {poisson_probs['draw']:.1%} | "
            f"  {away}: {poisson_probs['away_win']:.1%}"
        )
        prompt_parts.append(f"  xG: {context.get('expected_goals_home', 0):.2f} - {context.get('expected_goals_away', 0):.2f}")

        # API/market predictions
        if api_probs:
            prompt_parts.append("\n--- API/Market Prediction ---")
            prompt_parts.append(
                f"  {home}: {api_probs.get('home_win', 0):.1%} | "
                f"Draw: {api_probs.get('draw', 0):.1%} | "
                f"  {away}: {api_probs.get('away_win', 0):.1%}"
            )
            if api_advice:
                prompt_parts.append(f"  API Advice: {api_advice}")
            if winner_data:
                prompt_parts.append(
                    f"  Predicted Winner: {winner_data.get('name', 'N/A')} "
                    f"(Comment: {winner_data.get('comment', 'N/A')})"
                )

            # Comparison metrics
            if api_comparison:
                prompt_parts.append("\n--- API Comparison Metrics ---")
                for metric, values in api_comparison.items():
                    if isinstance(values, dict):
                        prompt_parts.append(
                            f"  {metric}: {home}={values.get('home', 'N/A')} vs {away}={values.get('away', 'N/A')}"
                        )
        else:
            prompt_parts.append("\n[No API prediction signal available for this fixture]")

        # Add ELO for context
        prompt_parts.append(f"\n--- ELO Context ---")
        prompt_parts.append(
            f"  {home}: {context.get('home_elo', 'N/A')} | {away}: {context.get('away_elo', 'N/A')} | "
            f"Diff: {context.get('elo_difference', 0):+.1f}"
        )

        prompt = "\n".join(prompt_parts)

        llm = get_llm_router()
        response = await llm.chat(system_prompt=ML_SYSTEM_PROMPT, user_message=prompt, temperature=0.3)

        try:
            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(clean)
        except (json.JSONDecodeError, IndexError):
            self.logger.warning("Failed to parse ML LLM response")
            return {}

    @staticmethod
    def _parse_percent(raw_value: Any) -> float:
        """Parse percent values like '46%' into 0.46 with safe fallback."""
        if raw_value is None:
            return 0.0
        clean = str(raw_value).replace("%", "").strip()
        try:
            return max(0.0, min(1.0, float(clean) / 100.0))
        except ValueError:
            return 0.0
