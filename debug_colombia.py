
import asyncio
import json
from backend.services.api_football_client import get_api_football_client

async def test():
    api = get_api_football_client()
    # Buscar el equipo Barranquilla para obtener sus partidos
    teams = await api.search_teams("Barranquilla")
    if not teams:
        print("No teams found for Barranquilla")
        return
        
    team_id = teams[0]['team']['id']
    print(f"Found team Barranquilla with ID: {team_id}")
    
    fixtures = await api.get_fixtures(team_id=team_id, next_n=5)
    for f in fixtures:
        home = f['teams']['home']['name']
        away = f['teams']['away']['name']
        f_id = f['fixture']['id']
        date = f['fixture']['date']
        print(f"Fixture: {home} vs {away} (ID: {f_id}) at {date}")

if __name__ == "__main__":
    asyncio.run(test())
