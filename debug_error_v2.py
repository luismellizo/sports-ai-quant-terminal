import sys
import os
from typing import Any, Dict, List, Optional

# Simulating the fixed environment
class MockClient:
    def _to_int(self, value: Any, default: Any = None) -> int:
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def _clean_text(self, text: Any, default: str = "") -> str:
        if not text: return default
        return str(text).strip()

    def _ensure_dict(self, value: Any) -> Dict[str, Any]:
        if isinstance(value, dict):
            return value
        if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
            return value[0]
        return {}

    def _parse_standing_row(self, row: Dict[str, Any], group_name: Optional[str] = None) -> Optional[Dict]:
        if not isinstance(row, dict):
            return None

        # Fixed logic
        overall = self._ensure_dict(row.get("overall"))
        home = self._ensure_dict(row.get("home"))
        away = self._ensure_dict(row.get("away"))
        total = self._ensure_dict(row.get("total"))

        try:
            played = self._to_int(overall.get("games_played"), 0)
            parsed = {
                "rank": self._to_int(row.get("position"), 0),
                "played": played,
                "home": {
                    "played": self._to_int(home.get("games_played"), 0),
                    "win": self._to_int(home.get("wins"), 0),
                },
                "away": {
                    "played": self._to_int(away.get("games_played"), 0),
                }
            }
            return parsed
        except Exception as e:
            print(f"Error caught: {e}")
            return None

client = MockClient()
bad_row = {
    "position": 1,
    "name": "Test Team",
    "overall": {"games_played": 10},
    "home": [], # Empty list - should not fail
    "away": [{"games_played": 5}], # List with dict - should use first element
    "total": None # None - should not fail
}

print("Running with complex row format:")
result = client._parse_standing_row(bad_row)
if result:
    print("SUCCESS: Result produced without error")
    print(f"Result: {result}")
else:
    print("FAILURE: No result produced")
