import asyncio
from backend.services.api_football_client import get_api_football_client

async def main():
    api = get_api_football_client()
    query = "ESTUDIANTES RC"
    print(f"Buscando '{query}':")
    candidates = await api.search_teams(query)
    import json
    print(json.dumps(candidates, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
