"""
Sports AI — Agent 1: NLP Interpretation Agent
Parses natural language input to extract match details using LLM.
"""

import json
from typing import Dict, Any
from backend.agents.base_agent import BaseAgent
from backend.llm.llm_router import get_llm_router

NLP_SYSTEM_PROMPT = """Eres un agente de NLP de análisis deportivo. Tu trabajo es extraer información de partidos de consultas en lenguaje natural sobre partidos de fútbol.

Extrae los siguientes campos y devuelve ÚNICAMENTE un objeto JSON:
{
  "team_home": "nombre del equipo local",
  "team_away": "nombre del equipo visitante", 
  "league": "nombre de la liga o null",
  "date": "fecha del partido YYYY-MM-DD o null",
  "bet_type": "match_winner | over_under | both_to_score | null"
}

Reglas:
- El primer equipo mencionado suele ser el equipo local
- Reconoce nombres de equipos comunes y abreviaturas (Barca=Barcelona, Real=Real Madrid, etc.)
- Si no se especifica la liga, establece null
- Si no se especifica la fecha, establece null (el sistema buscará el próximo partido)
- Por defecto, bet_type es "match_winner" si no se especifica
- Devuelve ÚNICAMENTE el JSON, sin texto adicional"""


class NLPAgent(BaseAgent):
    """Interprets user input to extract match information."""

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        query = context.get("query", "")
        self.logger.info(f"Parsing query: '{query}'")

        llm = get_llm_router()
        response = await llm.chat(
            system_prompt=NLP_SYSTEM_PROMPT,
            user_message=query,
            temperature=0.1,
        )

        # Parse JSON response
        try:
            # Clean potential markdown wrapping
            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
            parsed = json.loads(clean)
        except (json.JSONDecodeError, IndexError):
            self.logger.warning(f"Failed to parse LLM response, using fallback parser")
            parsed = self._fallback_parse(query)

        return {
            "team_home": parsed.get("team_home", ""),
            "team_away": parsed.get("team_away", ""),
            "league": parsed.get("league"),
            "date": parsed.get("date"),
            "bet_type": parsed.get("bet_type", "match_winner"),
        }

    def _fallback_parse(self, query: str) -> Dict:
        """Simple regex-free fallback parser."""
        # Remove common prefixes
        q = query.lower().strip()
        for prefix in ["analiza", "analyze", "predice", "predict", "mejor apuesta para",
                        "best bet for", "analizar", "predecir"]:
            q = q.replace(prefix, "").strip()

        # Split by common separators
        for sep in [" vs ", " vs. ", " contra ", " v ", " - "]:
            if sep in q:
                parts = q.split(sep, 1)
                return {
                    "team_home": parts[0].strip().title(),
                    "team_away": parts[1].strip().title(),
                    "league": None,
                    "date": None,
                    "bet_type": "match_winner",
                }

        return {"team_home": q.title(), "team_away": "", "league": None, "date": None, "bet_type": "match_winner"}
