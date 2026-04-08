import asyncio
from backend.services.api_football_client import get_api_football_client

async def main():
    api = get_api_football_client()
    home_id = 2337811
    fixtures = await api.get_fixtures(team_id=home_id)
    print(f"Fixtures for team_id {home_id}:")
    for f in fixtures[:20]:
        home_t = f.get('teams', {}).get('home', {}).get('name')
        away_t = f.get('teams', {}).get('away', {}).get('name')
        status = f.get('fixture', {}).get('status', {}).get('short')
        print(f"[{status}] {home_t} vs {away_t} ({f.get('fixture', {}).get('date')})")
        if "San Martin T." in home_t or "San Martin T." in away_t:
            print("FOUND SHARED FIXTURE")

if __name__ == "__main__":
    asyncio.run(main())
