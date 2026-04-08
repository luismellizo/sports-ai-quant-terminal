import sys
import os

# Simulating the environment
class MockClient:
    def _to_int(self, value, default=None):
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def _clean_text(self, text, default=""):
        if not text: return default
        return str(text).strip()

    def _parse_standing_row(self, row, group_name=None):
        if not isinstance(row, dict):
            return None

        overall = row.get("overall") or {}
        home = row.get("home") or {}
        away = row.get("away") or {}
        total = row.get("total") or {}

        # The error happens here if home is a list
        print(f"DEBUG: home type = {type(home)}")
        
        try:
            played = self._to_int(overall.get("games_played"), 0)
            parsed = {
                "rank": self._to_int(row.get("position"), 0),
                "played": played,
                "home": {
                    "played": self._to_int(home.get("games_played"), 0),
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
    "home": [{"games_played": 5}], # API returns a list for some reason
    "away": {"games_played": 5},
    "total": {"points": 30}
}
print("Running with bad row:")
client._parse_standing_row(bad_row)
