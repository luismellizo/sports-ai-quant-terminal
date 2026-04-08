// Sports AI — TypeScript Types

export interface AgentEvent {
    index: number;
    name: string;
    label: string;
    status: 'pending' | 'running' | 'completed' | 'error' | 'timeout' | 'skipped';
    execution_time_ms?: number;
}

export interface ProbabilityDistribution {
    home_win: number;
    draw: number;
    away_win: number;
}

export interface ExpectedGoals {
    home: number;
    away: number;
}

export interface ScoreProb {
    home_goals: number;
    away_goals: number;
    probability: number;
}

export interface MarketEdge {
    bet_type: string;
    model_probability: number;
    market_probability: number;
    edge: number;
    odds: number;
    is_value_bet: boolean;
}

export interface BetRecommendation {
    bet_type: string;
    team: string;
    probability: number;
    market_odds: number;
    value_edge: number;
    recommended_stake_pct: number;
    confidence: string;
    risk_level: string;
    confidence_score: number;
    recommendation_style?: string;
}

export interface MonteCarloData {
    simulations: number;
    home_win_pct: number;
    draw_pct: number;
    away_win_pct: number;
    most_likely_score: string;
    goal_distribution: Record<string, number>;
    score_distribution: ScoreProb[];
}

export interface EloData {
    home: number;
    away: number;
    difference: number;
}

export interface SentimentData {
    home: number;
    away: number;
    narrative: string;
}

export interface H2HData {
    total_matches: number;
    home_wins: number;
    draws: number;
    away_wins: number;
}

export interface FixtureResolutionAlternative {
    score: number;
    home_team: string;
    away_team: string;
    fixture_id: number | null;
    fixture_date: string | null;
    league_name: string | null;
}

export interface FixtureResolution {
    status: string;
    confidence: number;
    confirmation_message: string;
    alternatives: FixtureResolutionAlternative[];
    warnings: string[];
}

export interface PredictionResult {
    id: string;
    query: string;
    home_team: string;
    away_team: string;
    league: string;
    fixture_id?: number | null;
    agents: AgentEvent[];
    probabilities: ProbabilityDistribution;
    expected_goals: ExpectedGoals;
    score_matrix: ScoreProb[];
    monte_carlo: MonteCarloData;
    market_edges: MarketEdge[];
    best_bet: BetRecommendation | null;
    elo: EloData;
    h2h: H2HData;
    sentiment: SentimentData;
    insights: MatchInsights;
    fixture_resolution?: FixtureResolution;
    data_quality?: Record<string, string>;
    timings?: {
        total_ms: number;
        by_agent: Record<string, number>;
        by_stage: Record<string, number>;
        timestamp: string;
    };
    errors?: Record<string, string>;
    total_execution_time_ms: number;
}

export interface MatchInsights {
    lineup_summary: string;
    history_summary: string;
    home_injury_count: number;
    away_injury_count: number;
    home_stats: TeamStatsSummary;
    away_stats: TeamStatsSummary;
}

export interface TeamStatsSummary {
    wins_last_5: number;
    draws_last_5: number;
    losses_last_5: number;
    goals_scored_last_5: number;
    goals_conceded_last_5: number;
}

export interface SSEEvent {
    event: 'pipeline_start' | 'stage_start' | 'stage_complete' | 'agent_start' | 'agent_complete' | 'error' | 'pipeline_complete';
    data: unknown;
}
