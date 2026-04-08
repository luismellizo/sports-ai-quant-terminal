"""
Sports AI — Agent Registry
Registry for all agents with metadata for orchestration.
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import Dict, Type, Optional

from backend.agents.core.base import BaseAgent


_AGENTS: Dict[str, Type[BaseAgent]] = {}
_DISCOVERED = False


def register(name: str, cls: Type[BaseAgent]) -> None:
    _AGENTS[name] = cls


def get(name: str) -> Optional[Type[BaseAgent]]:
    if name not in _AGENTS:
        discover_agents()
    return _AGENTS.get(name)


def get_agent(name: str) -> Optional[BaseAgent]:
    cls = get(name)
    if cls is None:
        return None
    return cls()


def all_agents() -> Dict[str, Type[BaseAgent]]:
    if not _DISCOVERED:
        discover_agents()
    return _AGENTS.copy()


def discover_agents(force: bool = False) -> Dict[str, Type[BaseAgent]]:
    """
    Import all agent packages so their registration side effects run.

    The module registry remains the source of truth for the active runtime,
    while package __init__ files register the concrete implementations.
    """
    global _DISCOVERED

    if _DISCOVERED and not force:
        return _AGENTS.copy()

    package = importlib.import_module("backend.agents")
    for module_info in pkgutil.iter_modules(package.__path__):
        if not module_info.ispkg:
            continue
        if module_info.name in {"core", "shared"}:
            continue
        importlib.import_module(f"backend.agents.{module_info.name}")

    _DISCOVERED = True
    return _AGENTS.copy()


def clear_registry() -> None:
    _AGENTS.clear()
    global _DISCOVERED
    _DISCOVERED = False
