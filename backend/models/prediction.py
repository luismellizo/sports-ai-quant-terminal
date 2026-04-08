"""
Sports AI — Prediction Model
Pydantic schemas for predictions and analysis results.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    EXTREME = "EXTREME"


class ConfidenceLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY HIGH"


class AgentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"


class AgentResult(BaseModel):
    """Result from a single agent execution."""
    agent_name: str
    status: AgentStatus = AgentStatus.PENDING
    execution_time_ms: float = 0
    data: Dict = Field(default_factory=dict)
    error: Optional[str] = None


class ProbabilityDistribution(BaseModel):
    """Match outcome probabilities."""
    home_win: float = Field(0.0, ge=0, le=1)
    draw: float = Field(0.0, ge=0, le=1)
    away_win: float = Field(0.0, ge=0, le=1)


class ExpectedGoals(BaseModel):
    """Expected goals for each team."""
    home: float = 0.0
    away: float = 0.0


class ScoreProb(BaseModel):
    """Probability for a specific score."""
    home_goals: int
    away_goals: int
    probability: float


class MarketEdge(BaseModel):
    """Market inefficiency detection."""
    bet_type: str
    model_probability: float
    market_probability: float
    edge: float
    odds: float
    is_value_bet: bool = False


class BetRecommendation(BaseModel):
    """Final bet recommendation."""
    bet_type: str
    team: str
    probability: float
    market_odds: float
    value_edge: float
    recommended_stake_pct: float
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    risk_level: RiskLevel = RiskLevel.MEDIUM
    confidence_score: float = Field(0.0, ge=0, le=10)
    recommendation_style: str = ""


class MonteCarloResult(BaseModel):
    """Monte Carlo simulation results."""
    simulations: int = 50000
    home_win_pct: float = 0.0
    draw_pct: float = 0.0
    away_win_pct: float = 0.0
    avg_goals_home: float = 0.0
    avg_goals_away: float = 0.0
    most_likely_score: str = "0-0"
    goal_distribution: Dict[str, float] = Field(default_factory=dict)
    score_distribution: List[ScoreProb] = Field(default_factory=list)


class TeamStatsSummary(BaseModel):
    """Resumen numérico táctico de un equipo."""
    wins_last_5: int = 0
    draws_last_5: int = 0
    losses_last_5: int = 0
    goals_scored_last_5: int = 0
    goals_conceded_last_5: int = 0


class MatchInsights(BaseModel):
    """Análisis cualitativo y contexto de alineaciones/historial."""
    lineup_summary: str = ""
    history_summary: str = ""
    home_injury_count: int = 0
    away_injury_count: int = 0
    home_stats: TeamStatsSummary = Field(default_factory=TeamStatsSummary)
    away_stats: TeamStatsSummary = Field(default_factory=TeamStatsSummary)


class PredictionResult(BaseModel):
    """Complete prediction output from the pipeline."""
    id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Input
    query: str
    home_team: str
    away_team: str
    league: Optional[str] = None

    # Agent results timeline
    agents: List[AgentResult] = Field(default_factory=list)

    # Core predictions
    probabilities: ProbabilityDistribution = Field(default_factory=ProbabilityDistribution)
    expected_goals: ExpectedGoals = Field(default_factory=ExpectedGoals)
    score_matrix: List[ScoreProb] = Field(default_factory=list)
    monte_carlo: MonteCarloResult = Field(default_factory=MonteCarloResult)

    # Market analysis
    market_edges: List[MarketEdge] = Field(default_factory=list)

    # Final recommendation
    best_bet: Optional[BetRecommendation] = None
    
    # Textual Insights
    insights: MatchInsights = Field(default_factory=MatchInsights)

    # Metadata
    total_execution_time_ms: float = 0
    pipeline_version: str = "1.0.0"
