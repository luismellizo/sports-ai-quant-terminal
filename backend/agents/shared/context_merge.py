"""
Sports AI — Context Merge Utilities
Deterministic merge strategies for agent context updates.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


def merge_context(
    base: Dict[str, Any], update: Dict[str, Any], strategy: str = "replace"
) -> Dict[str, Any]:
    """
    Merge update into base using specified strategy.

    Strategies:
    - replace: overwrite existing keys
    - accumulate: for lists, extend; for dicts, recurse
    - append: always append to lists
    """
    if strategy == "replace":
        return {**base, **update}

    result = {**base}
    for key, value in update.items():
        if key not in result:
            result[key] = value
        elif isinstance(value, dict) and isinstance(result[key], dict):
            result[key] = merge_context(result[key], value, strategy)
        elif isinstance(value, list) and isinstance(result[key], list):
            if strategy == "accumulate":
                result[key] = result[key] + value
            elif strategy == "append":
                if isinstance(value, list):
                    result[key].extend(value)
                else:
                    result[key].append(value)
        else:
            result[key] = value
    return result


def merge_agent_outcomes(outcomes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge multiple agent outcomes into a single context dict."""
    merged: Dict[str, Any] = {}
    for outcome in outcomes:
        if "data" in outcome:
            merged = merge_context(merged, outcome["data"])
        if "narrative" in outcome:
            agent = outcome.get("agent_name", "unknown").lower()
            merged[f"{agent}_narrative"] = outcome["narrative"]
    return merged


def validate_context_keys(ctx: Dict[str, Any], required_keys: List[str]) -> List[str]:
    """Return list of missing required keys."""
    return [k for k in required_keys if k not in ctx]


def extract_timings(ctx: Dict[str, Any]) -> Dict[str, float]:
    """Extract timing information from context."""
    timings = {}
    for key, value in ctx.items():
        if "_time_ms" in key or key.endswith("_duration"):
            timings[key] = value
    return timings


def build_timing_summary(
    timings: Dict[str, float], stage_timings: Dict[str, float]
) -> Dict[str, Any]:
    """Build a summary of all timings for the prediction result."""
    total = sum(timings.values()) if timings else 0
    return {
        "total_ms": round(total, 2),
        "by_agent": timings,
        "by_stage": stage_timings,
        "timestamp": datetime.utcnow().isoformat(),
    }
