import asyncio
from backend.services.api_football_client import get_api_football_client

async def main():
    api = get_api_football_client()
    
    # 1. Search for generic terms
    home_teams = await api.search_teams("Estudiantes RC")
    away_teams = await api.search_teams("San Martin Tucuman")
    
    print("Estudiantes RC candidates:", [(t['team']['id'], t['team']['name']) for t in home_teams[:5]])
    print("San Martin Tucuman candidates:", [(t['team']['id'], t['team']['name']) for t in away_teams[:5]])
    
    if home_teams and away_teams:
        home_id = home_teams[0]['team']['id']
        fixtures = await api.get_fixtures(team_id=home_id)
        
        print(f"\nFixtures for home_id={home_id}:")
        for f in fixtures[:5]:
            home_t = f.get('teams', {}).get('home', {}).get('name')
            away_t = f.get('teams', {}).get('away', {}).get('name')
            print(f"- {home_t} vs {away_t} ({f.get('fixture', {}).get('date')})")
            
if __name__ == "__main__":
    asyncio.run(main())
