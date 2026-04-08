"""
Sports AI — Sentiment Agent
Analyzes team sentiment using real Google News RSS headlines + LLM interpretation.
Falls back to stats-only analysis if news are unavailable.
"""

import json
from typing import Dict, Any, List

from backend.agents.core.base import BaseAgent
from backend.agents.core.contracts import AgentContext
from backend.llm.llm_router import get_llm_router
from backend.services.news_rss_service import NewsRSSService


SENTIMENT_SYSTEM_PROMPT = """Eres un agente de análisis de sentimiento deportivo. Dados dos equipos, estima el sentimiento y los factores de presión.

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
Índice de presión: 0.0 (sin presión) a 1.0 (presión extrema)

Si hay noticias recientes disponibles, úsalas como señal prioritaria sobre las estadísticas.
Presta especial atención a: lesiones de jugadores clave, crisis de resultados, cambios de entrenador,
rumores de vestuario, o racha positiva reciente."""


def _format_headlines(headlines: List[str], team_name: str) -> str:
    """Formatea los titulares para incluirlos en el prompt del LLM."""
    if not headlines:
        return ""
    lines = "\n".join(f"• {h}" for h in headlines[:8])
    return f"\n\n--- Noticias Recientes {team_name} ---\n{lines}"


class SentimentAgent(BaseAgent):
    name = "SentimentAgent"
    is_critical = False
    timeout_seconds = 60.0

    def __init__(self):
        super().__init__()
        self._news_service = NewsRSSService()

    async def execute(self, ctx: AgentContext) -> Dict[str, Any]:
        team_home = ctx.data.get("team_home", "Unknown")
        team_away = ctx.data.get("team_away", "Unknown")
        league = ctx.data.get("league_name", "Unknown League")
        h2h = ctx.data.get("h2h_summary", {})
        home_stats = ctx.data.get("home_stats", {})
        away_stats = ctx.data.get("away_stats", {})

        if not ctx.data.get("history_data_available", False):
            return {
                "sentiment_home": 0.0,
                "sentiment_away": 0.0,
                "pressure_home": 0.5,
                "pressure_away": 0.5,
                "sentiment_factors_home": [],
                "sentiment_factors_away": [],
                "sentiment_narrative": "Sentiment analysis unavailable: insufficient historical data.",
                "sentiment_data_source": "missing",
                "news_home": [],
                "news_away": [],
            }

        # Obtener noticias reales de Google News RSS para ambos equipos en paralelo
        news_headlines = {"home": [], "away": []}
        try:
            news_headlines = await self._news_service.get_match_headlines(
                home_team=team_home,
                away_team=team_away,
                lang="es",
            )
            self.logger.info(
                f"📰 Noticias cargadas — {team_home}: {len(news_headlines['home'])} "
                f"| {team_away}: {len(news_headlines['away'])}"
            )
        except Exception as exc:
            self.logger.warning(f"No se pudieron obtener noticias RSS: {exc}")

        has_news = bool(news_headlines["home"] or news_headlines["away"])

        # Construir prompt base con estadísticas
        prompt = (
            f"Match: {team_home} vs {team_away}\n"
            f"League: {league}\n"
            f"Home form: W{home_stats.get('wins_last_5', 0)} "
            f"D{home_stats.get('draws_last_5', 0)} "
            f"L{home_stats.get('losses_last_5', 0)}\n"
            f"Away form: W{away_stats.get('wins_last_5', 0)} "
            f"D{away_stats.get('draws_last_5', 0)} "
            f"L{away_stats.get('losses_last_5', 0)}\n"
            f"H2H: {h2h.get('total_matches', 0)} matches "
            f"(H:{h2h.get('home_wins', 0)} D:{h2h.get('draws', 0)} A:{h2h.get('away_wins', 0)})\n"
            f"Is rivalry: {ctx.data.get('is_rivalry', False)}"
        )

        # Enriquecer prompt con noticias RSS si están disponibles
        if has_news:
            prompt += _format_headlines(news_headlines["home"], team_home)
            prompt += _format_headlines(news_headlines["away"], team_away)

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
                "home_sentiment": 0.0,
                "away_sentiment": 0.0,
                "home_pressure_index": 0.5,
                "away_pressure_index": 0.5,
                "key_factors_home": [],
                "key_factors_away": [],
                "narrative": "Sentiment analysis unavailable.",
            }

        data_source = "rss+llm" if has_news else "llm_only"

        return {
            "sentiment_home": data.get("home_sentiment", 0.0),
            "sentiment_away": data.get("away_sentiment", 0.0),
            "pressure_home": data.get("home_pressure_index", 0.5),
            "pressure_away": data.get("away_pressure_index", 0.5),
            "sentiment_factors_home": data.get("key_factors_home", []),
            "sentiment_factors_away": data.get("key_factors_away", []),
            "sentiment_narrative": data.get("narrative", ""),
            "sentiment_data_source": data_source,
            # Guardamos los titulares para posible visualización en frontend
            "news_home": news_headlines["home"],
            "news_away": news_headlines["away"],
        }
