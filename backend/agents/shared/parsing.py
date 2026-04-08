"""
Sports AI — Parsing Utilities
Shared parsing utilities for agent responses.
"""

import re
from typing import Dict, Any, Optional, List, Tuple


def extract_json(text: str) -> Optional[Dict[str, Any]]:
    """Extract JSON from text, handling markdown code blocks."""
    import json

    match = re.search(r"```(?:json)?\s*({.*?})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    match = re.search(r"({.*})", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    return None


def extract_number(text: str, pattern: str = r"[-+]?\d*\.\d+|\d+") -> Optional[float]:
    """Extract a number from text using regex pattern."""
    match = re.search(pattern, text)
    if match:
        try:
            return float(match.group())
        except ValueError:
            pass
    return None


def extract_probabilities(text: str) -> Dict[str, float]:
    """Extract home/draw/away probabilities from text."""
    probs = {"home_win": 0.0, "draw": 0.0, "away_win": 0.0}
    patterns = {
        "home_win": r"home.*?(\d+\.?\d*)\s*%",
        "draw": r"draw.*?(\d+\.?\d*)\s*%",
        "away_win": r"away.*?(\d+\.?\d*)\s*%",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            probs[key] = float(match.group(1)) / 100.0
    return probs


def extract_score(text: str) -> Tuple[int, int]:
    """Extract score from text (e.g., '2-1' or '2:1')."""
    match = re.search(r"(\d+)[-\:](\d+)", text)
    if match:
        return int(match.group(1)), int(match.group(2))
    return 0, 0


def parse_narrative_response(text: str) -> str:
    """Clean and parse a narrative response from LLM."""
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\[.*?\]", "", text)
    return text


def extract_list(text: str, pattern: str = r"(?:^|\n)\s*-\s*(.+?)$") -> List[str]:
    """Extract bullet list items from text."""
    matches = re.findall(pattern, text, re.MULTILINE)
    return [m.strip() for m in matches if m.strip()]


def safe_get(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Safely get a value from a dict with nested key support (e.g., 'a.b.c')."""
    keys = key.split(".")
    value = data
    for k in keys:
        if isinstance(value, dict):
            value = value.get(k)
        else:
            return default
        if value is None:
            return default
    return value
