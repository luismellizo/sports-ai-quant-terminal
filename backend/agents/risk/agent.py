"""
Sports AI — Risk Agent
Calculates stake, confidence, and risk with LLM narrative.
"""

import json
from typing import Dict, Any

from backend.agents.core.base import BaseAgent
from backend.agents.core.contracts import AgentContext
from backend.services.odds_service import OddsService
from backend.llm.llm_router import get_llm_router


RISK_SYSTEM_PROMPT = """Eres un gestor de riesgo profesional de un fondo de apuestas deportivas.

Devuelve ÚNICAMENTE un objeto JSON:
{
  "risk_narrative": "3-5 líneas con la recomendación profesional completa",
  "stake_justification": "por qué el stake recomendado es apropiado",
  "key_risks": ["riesgo1", "riesgo2", "riesgo3"],
  "risk_mitigation": "cómo mitigar los riesgos identificados",
  "professional_verdict": "APOSTAR/PASAR/MONITOREAR — con justificación",
  "bankroll_advice": "consejo específico de gestión de bankroll"
}"""


class RiskAgent(BaseAgent):
    name = "RiskAgent"
    is_critical = False
    timeout_seconds = 60.0

    async def execute(self, ctx: AgentContext) -> Dict[str, Any]:
        model_probs = self._normalize_model_probabilities(ctx.data)
        market_odds = ctx.data.get("market_odds", {}) or self._fallback_market_odds(
            model_probs
        )
        edges = ctx.data.get("market_edges", []) or self._build_edges(
            model_probs, market_odds
        )
        best_edge = ctx.data.get("best_edge") or (
            max(edges, key=lambda e: e.get("edge", -1.0)) if edges else None
        )
        team_home = ctx.data.get("team_home", "Home")
        team_away = ctx.data.get("team_away", "Away")
        match_importance = ctx.data.get("match_importance", 0.5)

        if not model_probs:
            return {
                "best_bet": None,
                "risk_narrative": "",
                "professional_verdict": "PASAR — No hay probabilidades de modelo.",
                "bet_profile": None,
            }

        if not best_edge or not edges:
            return {
                "best_bet": None,
                "risk_narrative": "",
                "professional_verdict": "PASAR — No se pudo construir un escenario de apuesta.",
                "bet_profile": None,
            }

        bet_type = best_edge["bet_type"]
        if bet_type in ("Home Win", "Gana Local"):
            bet_type = "Gana Local"
            team = team_home
            prob = model_probs.get("home_win", 0.4)
            odds = market_odds.get("home_win", 2.10)
        elif bet_type in ("Away Win", "Gana Visita"):
            bet_type = "Gana Visita"
            team = team_away
            prob = model_probs.get("away_win", 0.3)
            odds = market_odds.get("away_win", 3.50)
        else:
            bet_type = "Empate"
            team = "Empate"
            prob = model_probs.get("draw", 0.25)
            odds = market_odds.get("draw", 3.30)

        kelly_stake = OddsService.kelly_criterion(prob, odds, fraction=0.25)
        edge = best_edge.get("edge", 0.0)
        if edge <= 0.05:
            kelly_stake = max(kelly_stake, 0.005)

        confidence_score = self._calculate_confidence(
            edge=edge,
            prob=prob,
            match_importance=match_importance,
            bookmaker_count=ctx.data.get("bookmaker_count", 0),
        )

        if kelly_stake <= 0.01 or edge <= 0:
            risk_level = "EXTREME"
        elif kelly_stake <= 0.02 and edge < 0.05:
            risk_level = "HIGH"
        elif kelly_stake <= 0.04:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        if confidence_score >= 8.0:
            confidence = "VERY HIGH"
        elif confidence_score >= 6.5:
            confidence = "HIGH"
        elif confidence_score >= 4.5:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"

        recommendation_style = (
            "GANARLA"
            if (
                confidence_score >= 7.0
                and prob >= 0.50
                and risk_level in ("LOW", "MEDIUM")
            )
            else "ARRIESGARSE"
        )

        recommendation = {
            "bet_type": bet_type,
            "team": team,
            "probability": round(prob, 4),
            "market_odds": odds,
            "value_edge": round(edge, 4),
            "recommended_stake_pct": round(kelly_stake * 100, 2),
            "confidence": confidence,
            "risk_level": risk_level,
            "confidence_score": round(confidence_score, 1),
            "recommendation_style": recommendation_style,
        }

        llm_analysis = await self._assess_risk_with_llm(
            ctx.data, recommendation, kelly_stake, edge, confidence_score
        )

        professional_verdict = llm_analysis.get("professional_verdict", "")
        if not professional_verdict:
            professional_verdict = f"APOSTAR — perfil {'conservador' if recommendation_style == 'GANARLA' else 'agresivo'}."

        return {
            "best_bet": recommendation,
            "risk_narrative": llm_analysis.get("risk_narrative", ""),
            "stake_justification": llm_analysis.get("stake_justification", ""),
            "key_risks": llm_analysis.get("key_risks", []),
            "risk_mitigation": llm_analysis.get("risk_mitigation", ""),
            "professional_verdict": professional_verdict,
            "bankroll_advice": llm_analysis.get("bankroll_advice", ""),
            "bet_profile": recommendation_style,
        }

    async def _assess_risk_with_llm(
        self, context, recommendation, kelly_stake, edge, confidence_score
    ):
        home = context.get("team_home", "Home")
        away = context.get("team_away", "Away")
        rec = recommendation
        prompt = f"Match: {home} vs {away}\nLeague: {context.get('league_name', 'Unknown')}\n\n--- Recommendation ---\n  Bet: {rec['bet_type']} ({rec['team']})\n  Model Probability: {rec['probability']:.1%}\n  Market Odds: {rec['market_odds']}\n  Value Edge: {rec['value_edge']:+.1%}\n  Kelly Stake: {rec['recommended_stake_pct']:.2f}%\n  Confidence: {rec['confidence']} ({confidence_score:.1f}/10)\n  Risk Level: {rec['risk_level']}\n\n--- Context ---\n  Match Importance: {context.get('match_importance', 0.5):.2f}\n  ELO Difference: {context.get('elo_difference', 0):+.1f}\n  Home Injuries: {context.get('home_injury_count', 0)}\n  Away Injuries: {context.get('away_injury_count', 0)}\n  Is Rivalry: {context.get('is_rivalry', False)}\n  API Advice: {context.get('api_advice', 'N/A')}\n\n--- Simulation ---\n  MC: H={context.get('mc_home_win', 0):.1f}% D={context.get('mc_draw', 0):.1f}% A={context.get('mc_away_win', 0):.1f}%\n  Most Likely Score: {context.get('mc_most_likely_score', 'N/A')}"
        llm = get_llm_router()
        response = await llm.chat(
            system_prompt=RISK_SYSTEM_PROMPT, user_message=prompt, temperature=0.3
        )
        try:
            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(clean)
        except (json.JSONDecodeError, IndexError):
            return {}

    @staticmethod
    def _calculate_confidence(edge, prob, match_importance, bookmaker_count):
        score = 5.0
        score += min(2.0, max(-2.0, edge * 20))
        if prob > 0.6:
            score += 1.5
        elif prob > 0.5:
            score += 0.8
        elif prob < 0.3:
            score -= 0.5
        score += (match_importance - 0.5) * 1.0
        if bookmaker_count >= 10:
            score += 1.0
        elif bookmaker_count >= 5:
            score += 0.5
        elif bookmaker_count == 0:
            score -= 1.0
        return max(0.0, min(10.0, score))

    @staticmethod
    def _normalize_model_probabilities(context):
        probs = context.get("model_probabilities", {}) or {}
        home = probs.get("home_win")
        draw = probs.get("draw")
        away = probs.get("away_win")
        if home is None or draw is None or away is None:
            home = context.get("ml_home_win", context.get("poisson_home_win"))
            draw = context.get("ml_draw", context.get("poisson_draw"))
            away = context.get("ml_away_win", context.get("poisson_away_win"))
        if home is None or draw is None or away is None:
            return {}
        total = float(home) + float(draw) + float(away)
        if total <= 0:
            return {}
        return {
            "home_win": float(home) / total,
            "draw": float(draw) / total,
            "away_win": float(away) / total,
        }

    @staticmethod
    def _fallback_market_odds(model_probs):
        if not model_probs:
            return {}

        def fair_odd(prob):
            p = max(0.05, min(0.90, float(prob)))
            return round(1.0 / p, 2)

        return {
            "home_win": fair_odd(model_probs.get("home_win", 0.33)),
            "draw": fair_odd(model_probs.get("draw", 0.33)),
            "away_win": fair_odd(model_probs.get("away_win", 0.33)),
        }

    @staticmethod
    def _build_edges(model_probs, market_odds):
        if not model_probs or not market_odds:
            return []

        def implied(odd):
            return 1.0 / odd if odd and odd > 1 else 1.0

        edges = []
        pairs = [
            ("Gana Local", "home_win", "home_win"),
            ("Empate", "draw", "draw"),
            ("Gana Visita", "away_win", "away_win"),
        ]
        for label, prob_key, odd_key in pairs:
            prob = float(model_probs.get(prob_key, 0.0))
            odd = float(market_odds.get(odd_key, 0.0))
            market_prob = implied(odd)
            edge = prob - market_prob
            edges.append(
                {
                    "bet_type": label,
                    "model_probability": round(prob, 4),
                    "market_probability": round(market_prob, 4),
                    "edge": round(edge, 4),
                    "odds": odd,
                    "is_value_bet": edge > 0.05,
                }
            )
        return sorted(edges, key=lambda item: item["edge"], reverse=True)
