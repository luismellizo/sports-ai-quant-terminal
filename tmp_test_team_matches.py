import asyncio
from backend.services.api_football_client import get_api_football_client

async def main():
    api = get_api_football_client()
    data = await api._request("soccer/teams/9974/matches")
    import json
    print(json.dumps(data, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
