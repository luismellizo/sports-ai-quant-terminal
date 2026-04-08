"""
Sports AI — Lineup Agent
Analyzes lineups, injuries, and tactical analysis.
"""

import json
from typing import Dict, Any, List

from backend.agents.core.base import BaseAgent
from backend.agents.core.contracts import AgentContext, AgentStatus
from backend.services.api_football_client import get_api_football_client
from backend.llm.llm_router import get_llm_router


LINEUP_SYSTEM_PROMPT = """Eres un analista táctico de fútbol de élite.
Recibirás datos de formaciones y lesiones de un partido. Si los datos están incompletos, utiliza tu base de conocimiento para estimar la alineación típica y estilo de juego reciente de cada equipo.

Devuelve ÚNICAMENTE un objeto JSON con este formato estricto:
{
  "lineup_narrative": "Párrafo de 4-6 líneas describiendo: 1) Formación esperada o confirmada. 2) Impacto de ausencias. 3) Enfoque táctico principal.",
  "home_tactical_analysis": "2-3 líneas sobre la situación táctica del local",
  "away_tactical_analysis": "2-3 líneas sobre la situación táctica del visitante",
  "key_absences_impact": ["impacto1", "impacto2"],
  "tactical_advantage": "local/visitante/neutral - con justificación",
  "formation_matchup": "análisis de cómo interactúan las formaciones esperadas"
}"""


class LineupAgent(BaseAgent):
    name = "LineupAgent"
    is_critical = False
    timeout_seconds = 120.0

    async def execute(self, ctx: AgentContext) -> Dict[str, Any]:
        api = get_api_football_client()
        fixture_id = ctx.data.get("fixture_id")
        home_id = ctx.data.get("home_team_id")
        away_id = ctx.data.get("away_team_id")
        league_id = ctx.data.get("league_id")

        lineups = []
        injuries_home = []
        injuries_away = []
        league_squad_stats = {}

        if fixture_id:
            lineups = await api.get_lineups(fixture_id)
        if home_id:
            injuries_home = await api.get_injuries(team_id=home_id)
        if away_id:
            injuries_away = await api.get_injuries(team_id=away_id)
        if league_id:
            league_squad_stats = await api.get_league_squad_stats(league_id)

        squad_index = self._build_squad_stats_index(league_squad_stats or {})

        home_lineup = self._parse_lineup(lineups, home_id)
        away_lineup = self._parse_lineup(lineups, away_id)

        parsed_injuries_home = self._parse_injuries(injuries_home, home_id, squad_index)
        parsed_injuries_away = self._parse_injuries(injuries_away, away_id, squad_index)

        home_injury_impact = self._calculate_injury_impact(injuries_home, home_id, squad_index)
        away_injury_impact = self._calculate_injury_impact(injuries_away, away_id, squad_index)

        lineup_data_available = bool(lineups or injuries_home or injuries_away)

        # Siempre llamamos al LLM para que el Front tenga narrativa táctica
        llm_analysis = await self._analyze_lineups_with_llm(
            ctx.data, home_lineup, away_lineup, parsed_injuries_home, parsed_injuries_away, lineup_data_available
        )

        # Si falló el parseo JSON y devolvió {}, generamos una fallback
        if not llm_analysis.get("lineup_narrative"):
             llm_analysis["lineup_narrative"] = f"Alineaciones oficiales no confirmadas aún. El análisis táctico se basará en el esquema habitual 4-3-3 vs 4-2-3-1 de ambos equipos y las bajas de último minuto."

        return {
            "home_lineup": home_lineup,
            "away_lineup": away_lineup,
            "injuries_home": parsed_injuries_home,
            "injuries_away": parsed_injuries_away,
            "home_injury_count": len(injuries_home),
            "away_injury_count": len(injuries_away),
            "home_injury_impact": home_injury_impact,
            "away_injury_impact": away_injury_impact,
            "lineup_available": len(lineups) > 0,
            "lineup_narrative": llm_analysis.get("lineup_narrative", ""),
            "home_tactical_analysis": llm_analysis.get("home_tactical_analysis", ""),
            "away_tactical_analysis": llm_analysis.get("away_tactical_analysis", ""),
            "key_absences_impact": llm_analysis.get("key_absences_impact", []),
            "tactical_advantage": llm_analysis.get("tactical_advantage", ""),
            "formation_matchup": llm_analysis.get("formation_matchup", ""),
            "lineup_data_source": "api" if lineup_data_available else "missing",
            "lineup_data_available": lineup_data_available,
        }

    async def _analyze_lineups_with_llm(
        self, context, home_lineup, away_lineup, injuries_home, injuries_away, available
    ):
        home = context.get("team_home", "Home")
        away = context.get("team_away", "Away")
        
        status_msg = "ALINEACIONES CONFIRMADAS VIA API:" if available else "ALINEACIONES AÚN NO CONFIRMADAS (ESPECULAR FORMACIONES TÍPICAS):"

        prompt_parts = [
            f"Match: {home} vs {away}",
            f"Status: {status_msg}",
            f"--- {home} Lineup",
            f"Formation: {home_lineup.get('formation', 'N/A')}",
            f"--- {away} Lineup",
            f"Formation: {away_lineup.get('formation', 'N/A')}",
            f"\n{home} Injuries/Absences ({len(injuries_home)}): " + ", ".join([i['details'] for i in injuries_home]),
            f"\n{away} Injuries/Absences ({len(injuries_away)}): " + ", ".join([i['details'] for i in injuries_away]),
        ]
        llm = get_llm_router()
        response = await llm.chat(
            system_prompt=LINEUP_SYSTEM_PROMPT,
            user_message="\n".join(prompt_parts),
            temperature=0.4,
        )
        try:
            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
            if clean.startswith("json"):
                clean = clean.replace("json\n", "", 1)
            parsed = json.loads(clean)
            return parsed
        except Exception:
            return {}

    @staticmethod
    def _parse_lineup(lineups, team_id):
        for lineup in lineups:
            if lineup.get("team", {}).get("id") == team_id:
                return {
                    "formation": lineup.get("formation", "Unknown"),
                    "coach": lineup.get("coach", {}).get("name", "Unknown"),
                    "starting_xi": [
                        {
                            "name": p.get("player", {}).get("name"),
                            "number": p.get("player", {}).get("number"),
                            "pos": p.get("player", {}).get("pos"),
                        }
                        for p in lineup.get("startXI", [])
                    ],
                    "substitutes": [
                        {
                            "name": p.get("player", {}).get("name"),
                            "number": p.get("player", {}).get("number"),
                            "pos": p.get("player", {}).get("pos"),
                        }
                        for p in lineup.get("substitutes", [])
                    ],
                }
        return {
            "formation": "Unknown",
            "coach": "Unknown",
            "starting_xi": [],
            "substitutes": [],
        }

    @staticmethod
    def _parse_injuries(injuries, team_id, squad_index):
        team_stats = squad_index.get(team_id, {})
        parsed_list = []
        for i in injuries[:10]:
            p_name = i.get("player", {}).get("name", "Unknown")
            p_type = i.get("player", {}).get("type", "Unknown")
            p_reason = i.get("player", {}).get("reason", "Unknown")
            
            details = f"{p_name} ({p_type}: {p_reason})"
            p_stats = team_stats.get(p_name.lower())
            if p_stats:
                rating = p_stats["rating"]
                mins = p_stats["minutes_played"]
                details += f" [Rating {rating:.2f}, {mins} mins played]"
                
            parsed_list.append({
                "player": p_name,
                "type": p_type,
                "reason": p_reason,
                "details": details
            })
        return parsed_list

    @staticmethod
    def _calculate_injury_impact(injuries, team_id, squad_index):
        if not injuries:
            return 0.0
            
        team_stats = squad_index.get(team_id, {})
        impact = 0.0
        
        for injury in injuries:
            p_name = injury.get("player", {}).get("name", "Unknown")
            p_stats = team_stats.get(p_name.lower())
            
            if p_stats:
                mins = p_stats["minutes_played"]
                rating = p_stats["rating"]
                
                base = 0.05
                if mins >= 900:
                    base += 0.03
                elif mins >= 400:
                    base += 0.01
                    
                if rating >= 7.0:
                    base += 0.04
                elif rating >= 6.5:
                    base += 0.01
                    
                impact += base
            else:
                impact += 0.05
                
        return round(-min(0.5, impact), 3)

    @staticmethod
    def _build_squad_stats_index(league_squad_stats: Dict[str, Any]) -> Dict[int, Dict[str, Any]]:
        index = {}
        if not league_squad_stats:
            return index
            
        teams = league_squad_stats.get("team", [])
        if not isinstance(teams, list):
            teams = [teams]
            
        for team in teams:
            try:
                t_id = int(team.get("id", 0))
            except (ValueError, TypeError):
                continue
            
            player_obj = team.get("squad", {}).get("player", [])
            players = player_obj if isinstance(player_obj, list) else [player_obj]
            
            p_dict = {}
            for p in players:
                p_name = p.get("name", "")
                if p_name:
                    p_dict[p_name.lower()] = {
                        "rating": float(p.get("rating") or "0"),
                        "minutes_played": int(p.get("minutes_played") or "0"),
                        "appearences": int(p.get("appearences") or "0"),
                    }
            index[t_id] = p_dict
        return index
