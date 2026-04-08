"""
Sports AI — Shared Exceptions
"""


class SportsAIException(Exception):
    base_message = "Sports AI Error"

    def __init__(self, message: str = "", agent: str = "", context: str = ""):
        self.agent = agent
        self.context = context
        full_msg = self.base_message
        if agent:
            full_msg += f" [{agent}]"
        if message:
            full_msg += f": {message}"
        super().__init__(full_msg)


class AgentExecutionError(SportsAIException):
    base_message = "Agent execution failed"


class AgentTimeoutError(SportsAIException):
    base_message = "Agent timed out"


class PipelineError(SportsAIException):
    base_message = "Pipeline execution failed"


class ContextError(SportsAIException):
    base_message = "Context validation failed"


class APIError(SportsAIException):
    base_message = "External API error"


class ConfigurationError(SportsAIException):
    base_message = "Configuration error"
