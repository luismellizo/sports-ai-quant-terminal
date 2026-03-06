"""
Sports AI — Agent 12: Market Inefficiency Agent
Detects value bets by comparing model probabilities vs market odds.
Uses DeepSeek to explain WHY the market may be wrong.
"""

import json
from typing import Dict, Any, List
from backend.agents.base_agent import BaseAgent
from backend.services.odds_service import OddsService
from backend.models.prediction import MarketEdge
from backend.llm.llm_router import get_llm_router

MARKET_EDGE_SYSTEM_PROMPT = """Eres un analista de mercados de apuestas deportivas experto en detectar ineficiencias. Recibirás la comparación REAL entre las probabilidades de nuestros modelos y las cuotas del mercado.

Tu trabajo es:
1. Identificar y explicar cada value bet detectado (edge > 5%)
2. Explicar POR QUÉ el mercado podría estar equivocado en cada caso
3. Analizar si el edge es sostenible o podría ser un falso positivo
4. Evaluar los riesgos del edge detectado
5. Considerar factores que nuestros modelos podrían no capturar

Devuelve ÚNICAMENTE un objeto JSON:
{
  "market_narrative": "3-5 líneas analizando las ineficiencias del mercado con datos y odds específicos",
  "value_bet_analysis": "análisis detallado del mejor value bet encontrado",
  "market_sentiment": "qué dice el mercado sobre este partido y por qué",
  "false_positive_risk": "bajo/medio/alto — riesgo de que el edge sea ilusorio",
  "recommended_bet_type": "1X2/Over-Under/BTTS o ninguno con justificación",
  "market_blind_spots": ["factor no capturado 1", "factor no capturado 2"]
}"""


class MarketEdgeAgent(BaseAgent):
    """Detects market inefficiencies with LLM analysis."""

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        model_probs = self._aggregate_probabilities(context)
        market_odds = context.get("market_odds", {})
        implied = context.get("implied_probabilities", {})

        edges = []

        home_edge = self._calculate_edge(
            "Gana Local", model_probs["home_win"],
            implied.get("home", 0.45), market_odds.get("home_win", 2.10),
        )
        edges.append(home_edge)

        draw_edge = self._calculate_edge(
            "Empate", model_probs["draw"],
            implied.get("draw", 0.28), market_odds.get("draw", 3.30),
        )
        edges.append(draw_edge)

        away_edge = self._calculate_edge(
            "Gana Visita", model_probs["away_win"],
            implied.get("away", 0.27), market_odds.get("away_win", 3.50),
        )
        edges.append(away_edge)

        edges.sort(key=lambda x: x["edge"], reverse=True)
        value_bets = [e for e in edges if e["is_value_bet"]]

        # ── DeepSeek: market analysis ──
        llm_analysis = await self._analyze_market_with_llm(
            context, edges, model_probs, market_odds, implied
        )

        return {
            "market_edges": edges,
            "value_bets": value_bets,
            "best_edge": edges[0] if edges else None,
            "model_probabilities": model_probs,
            "market_narrative": llm_analysis.get("market_narrative", ""),
            "value_bet_analysis": llm_analysis.get("value_bet_analysis", ""),
            "market_sentiment": llm_analysis.get("market_sentiment", ""),
            "false_positive_risk": llm_analysis.get("false_positive_risk", ""),
            "recommended_bet_type": llm_analysis.get("recommended_bet_type", ""),
            "market_blind_spots": llm_analysis.get("market_blind_spots", []),
        }

    async def _analyze_market_with_llm(
        self, context, edges, model_probs, market_odds, implied
    ) -> Dict:
        home = context.get("team_home", "Home")
        away = context.get("team_away", "Away")

        edges_text = "\n".join([
            f"  {e['bet_type']}: Model={e['model_probability']:.1%} vs Market={e['market_probability']:.1%} "
            f"→ Edge={e['edge']:+.1%} | Odds={e['odds']} | {'✅ VALUE BET' if e['is_value_bet'] else '❌ No value'}"
            for e in edges
        ])

        prompt = (
            f"Match: {home} vs {away}\n\n"
            f"--- Model Probabilities (Aggregated from Poisson+ML+MC+ELO) ---\n"
            f"  {home}: {model_probs['home_win']:.1%}\n"
            f"  Draw: {model_probs['draw']:.1%}\n"
            f"  {away}: {model_probs['away_win']:.1%}\n\n"
            f"--- Market Odds ---\n"
            f"  {home}: {market_odds.get('home_win', 'N/A')}\n"
            f"  Draw: {market_odds.get('draw', 'N/A')}\n"
            f"  {away}: {market_odds.get('away_win', 'N/A')}\n\n"
            f"--- Implied vs Model (Edges) ---\n{edges_text}\n\n"
            f"--- Context ---\n"
            f"  Bookmaker count: {context.get('bookmaker_count', 0)}\n"
            f"  Overround: {context.get('overround', 'N/A')}\n"
            f"  API Advice: {context.get('api_advice', 'N/A')}\n"
            f"  API Winner: {context.get('api_winner', {}).get('name', 'N/A')}"
        )

        llm = get_llm_router()
        response = await llm.chat(system_prompt=MARKET_EDGE_SYSTEM_PROMPT, user_message=prompt, temperature=0.3)

        try:
            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(clean)
        except (json.JSONDecodeError, IndexError):
            self.logger.warning("Failed to parse market edge LLM response")
            return {}

    def _aggregate_probabilities(self, context: Dict) -> Dict[str, float]:
        weights = {"poisson": 0.25, "ml": 0.35, "mc": 0.25, "elo": 0.15}

        home_prob = (
            context.get("poisson_home_win", 0.4) * weights["poisson"]
            + context.get("ml_home_win", 0.4) * weights["ml"]
            + (context.get("mc_home_win", 40.0) / 100.0) * weights["mc"]
            + context.get("elo_expected_home", 0.5) * weights["elo"]
        )
        draw_prob = (
            context.get("poisson_draw", 0.25) * weights["poisson"]
            + context.get("ml_draw", 0.3) * weights["ml"]
            + (context.get("mc_draw", 25.0) / 100.0) * weights["mc"]
            + 0.15 * weights["elo"]
        )
        away_prob = (
            context.get("poisson_away_win", 0.35) * weights["poisson"]
            + context.get("ml_away_win", 0.3) * weights["ml"]
            + (context.get("mc_away_win", 35.0) / 100.0) * weights["mc"]
            + context.get("elo_expected_away", 0.5) * weights["elo"]
        )

        total = home_prob + draw_prob + away_prob
        if total > 0:
            home_prob /= total
            draw_prob /= total
            away_prob /= total

        return {
            "home_win": round(home_prob, 4),
            "draw": round(draw_prob, 4),
            "away_win": round(away_prob, 4),
        }

    @staticmethod
    def _calculate_edge(bet_type, model_prob, market_prob, market_odds) -> Dict:
        edge = model_prob - market_prob
        return {
            "bet_type": bet_type,
            "model_probability": round(model_prob, 4),
            "market_probability": round(market_prob, 4),
            "edge": round(edge, 4),
            "odds": market_odds,
            "is_value_bet": edge > 0.05,
        }
