"""
Sports AI — Prompt Utilities
Shared utilities for building and formatting prompts.
"""

from typing import Dict, Any, Optional, List


SYSTEM_PROMPTS = {
    "nlp": "You are an NLP agent that parses user queries about football matches. Extract team names, date hints, and league information.",
    "fixture_resolver": "You are a fixture resolution agent. Given team names, find the correct upcoming match.",
    "context": "You are a context agent providing competitive analysis including standings and team statistics.",
    "history": "You are a history agent providing detailed historical H2H analysis.",
    "lineup": "You are a lineup agent providing tactical analysis including injuries and expected formations.",
    "sentiment": "You are a sentiment analysis agent evaluating news and media coverage.",
    "elo": "You are an ELO rating agent providing mathematical analysis of team strengths.",
    "odds": "You are an odds analysis agent evaluating market probabilities.",
    "feature": "You are a feature engineering agent preparing data for ML models.",
    "poisson": "You are a Poisson model agent calculating expected goals probabilities.",
    "ml": "You are an ML prediction agent cross-validating with API predictions.",
    "monte_carlo": "You are a Monte Carlo simulation agent running 50,000 virtual match simulations.",
    "market_edge": "You are a market edge detection agent finding value bets.",
    "risk": "You are a risk management agent providing staking recommendations.",
    "synthesis": "You are a synthesis agent providing executive summaries of predictions.",
}


def build_prompt(agent: str, template: str, context: Dict[str, Any]) -> str:
    """Build a prompt from a template and context."""
    system = SYSTEM_PROMPTS.get(agent, "")
    try:
        filled = template.format(**context)
    except KeyError:
        filled = template
    return f"{system}\n\n{filled}"


def truncate_prompt(prompt: str, max_length: int = 4000) -> str:
    """Truncate prompt to maximum length."""
    if len(prompt) <= max_length:
        return prompt
    return prompt[:max_length] + "\n\n[truncated...]"


def format_bullet_list(items: List[str], prefix: str = "- ") -> str:
    """Format a list as bullet points."""
    return "\n".join(f"{prefix}{item}" for item in items)


def format_key_value(kv: Dict[str, Any], indent: int = 2) -> str:
    """Format a dict as key-value pairs."""
    spacer = " " * indent
    return "\n".join(f"{spacer}{k}: {v}" for k, v in kv.items())


def build_context_summary(ctx: Dict[str, Any]) -> str:
    """Build a text summary of context for prompts."""
    lines = ["Context Summary:"]
    for key in ["team_home", "team_away", "league_name", "fixture_id"]:
        if key in ctx:
            lines.append(f"  {key}: {ctx[key]}")
    return "\n".join(lines)
