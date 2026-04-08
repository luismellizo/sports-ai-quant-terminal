"""NLP Agent schemas."""

from pydantic import BaseModel, Field
from typing import Optional


class NLPParsedQuery(BaseModel):
    team_home: str
    team_away: str
    league_hint: str = ""
    date_hint: str = "upcoming"
    raw_query: str
    parsed_successfully: bool = True


class NLPOutput(BaseModel):
    teams_raw: list = Field(default_factory=list)
    team_home: str = ""
    team_away: str = ""
    league_hint: str = ""
    date_hint: str = "upcoming"
    nlp_parsed: bool = False
