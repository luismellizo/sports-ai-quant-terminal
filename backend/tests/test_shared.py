"""
Sports AI — Tests for Shared Utilities
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestPromptUtils:
    def test_truncate_prompt(self):
        from backend.agents.shared.prompt_utils import truncate_prompt

        long_text = "a" * 5000
        result = truncate_prompt(long_text, max_length=100)
        assert result.endswith("[truncated...]")
        assert len(result) > 100

    def test_format_bullet_list(self):
        from backend.agents.shared.prompt_utils import format_bullet_list

        result = format_bullet_list(["item1", "item2"])
        assert "- item1" in result
        assert "- item2" in result


class TestParsing:
    def test_extract_json(self):
        from backend.agents.shared.parsing import extract_json

        text = 'Here is the answer: {"teams": ["A", "B"]}'
        result = extract_json(text)
        assert result is not None
        assert result.get("teams") == ["A", "B"]

    def test_extract_number(self):
        from backend.agents.shared.parsing import extract_number

        assert extract_number("The odds are 2.5 to 1") == 2.5
        assert extract_number("No number here") is None

    def test_extract_probabilities(self):
        from backend.agents.shared.parsing import extract_probabilities

        result = extract_probabilities("home: 45%, draw: 30%, away: 25%")
        assert result["home_win"] == 0.45
        assert result["draw"] == 0.30
        assert result["away_win"] == 0.25


class TestContextMerge:
    def test_merge_context(self):
        from backend.agents.shared.context_merge import merge_context

        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = merge_context(base, override, strategy="replace")
        assert result["a"] == 1
        assert result["b"] == 3
        assert result["c"] == 4


class TestExceptions:
    def test_sports_ai_exception(self):
        from backend.agents.shared.exceptions import SportsAIException

        exc = SportsAIException("Test error", agent="test_agent")
        assert "Test error" in str(exc)
        assert exc.agent == "test_agent"

    def test_agent_timeout(self):
        from backend.agents.shared.exceptions import AgentTimeoutError

        exc = AgentTimeoutError("nlp")
        assert "nlp" in str(exc)
        assert "timed out" in str(exc)
