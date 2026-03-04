"""
Sports AI — Agent 5: News & Sentiment Agent
Analyzes team sentiment and pressure using LLM-based inference.
"""

from typing import Dict, Any
from backend.agents.base_agent import BaseAgent
from backend.llm.llm_router import get_llm_router
import json

SENTIMENT_SYSTEM_PROMPT = """Eres un agente de análisis de sentimiento deportivo. Dados dos equipos de fútbol que están por jugar un partido, estima el sentimiento y los factores de presión para cada equipo.

Considera estos factores (incluso sin noticias en tiempo real, usa tu conocimiento general):
- Moral actual del equipo e impulso de resultados recientes
- Estabilidad del entrenador y cambios tácticos
- Actividad en el mercado de fichajes y dinámica de jugadores
- Presión de la afición y de los medios comunicacionales
- Rendimiento histórico en situaciones similares

Devuelve ÚNICAMENTE un objeto JSON:
{
  "home_sentiment": 0.0,
  "away_sentiment": 0.0,
  "home_pressure_index": 0.0,
  "away_pressure_index": 0.0,
  "key_factors_home": ["factor1", "factor2"],
  "key_factors_away": ["factor1", "factor2"],
  "narrative": "párrafo breve de análisis"
}

Sentimiento: -1.0 (muy negativo) a 1.0 (muy positivo)
Índice de presión: 0.0 (sin presión) a 1.0 (presión extrema)"""


class SentimentAgent(BaseAgent):
    """Analyzes team sentiment and pressure via LLM."""

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        team_home = context.get("team_home", "Unknown")
        team_away = context.get("team_away", "Unknown")
        league = context.get("league_name", "Unknown League")
        h2h = context.get("h2h_summary", {})
        home_stats = context.get("home_stats", {})
        away_stats = context.get("away_stats", {})

        prompt = (
            f"Match: {team_home} vs {team_away}\n"
            f"League: {league}\n"
            f"Home form (last 5): W{home_stats.get('wins_last_5', 0)} "
            f"D{home_stats.get('draws_last_5', 0)} L{home_stats.get('losses_last_5', 0)}\n"
            f"Away form (last 5): W{away_stats.get('wins_last_5', 0)} "
            f"D{away_stats.get('draws_last_5', 0)} L{away_stats.get('losses_last_5', 0)}\n"
            f"H2H: {h2h.get('total_matches', 0)} matches "
            f"(H:{h2h.get('home_wins', 0)} D:{h2h.get('draws', 0)} A:{h2h.get('away_wins', 0)})\n"
            f"Is rivalry: {context.get('is_rivalry', False)}"
        )

        llm = get_llm_router()
        response = await llm.chat(
            system_prompt=SENTIMENT_SYSTEM_PROMPT,
            user_message=prompt,
            temperature=0.4,
        )

        try:
            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
            data = json.loads(clean)
        except (json.JSONDecodeError, IndexError):
            data = {
                "home_sentiment": 0.1,
                "away_sentiment": 0.0,
                "home_pressure_index": 0.3,
                "away_pressure_index": 0.3,
                "key_factors_home": [],
                "key_factors_away": [],
                "narrative": "Sentiment analysis unavailable.",
            }

        return {
            "sentiment_home": data.get("home_sentiment", 0.0),
            "sentiment_away": data.get("away_sentiment", 0.0),
            "pressure_home": data.get("home_pressure_index", 0.3),
            "pressure_away": data.get("away_pressure_index", 0.3),
            "sentiment_factors_home": data.get("key_factors_home", []),
            "sentiment_factors_away": data.get("key_factors_away", []),
            "sentiment_narrative": data.get("narrative", ""),
        }
