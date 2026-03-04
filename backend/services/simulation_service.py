"""
Sports AI — Simulation Service
Monte Carlo simulation engine using Poisson distribution and Numba JIT.
"""

import numpy as np
from typing import Dict, List, Tuple
from scipy.stats import poisson
from backend.config.settings import get_settings
from backend.models.prediction import ScoreProb, MonteCarloResult
from backend.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

try:
    from numba import njit, prange

    @njit(parallel=True, cache=True)
    def _simulate_matches_numba(
        lambda_home: float,
        lambda_away: float,
        n_simulations: int,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Numba-accelerated Monte Carlo simulation."""
        home_goals = np.empty(n_simulations, dtype=np.int32)
        away_goals = np.empty(n_simulations, dtype=np.int32)
        for i in prange(n_simulations):
            home_goals[i] = np.random.poisson(lambda_home)
            away_goals[i] = np.random.poisson(lambda_away)
        return home_goals, away_goals

    USE_NUMBA = True
    logger.info("Numba JIT available — accelerated simulations enabled")
except ImportError:
    USE_NUMBA = False
    logger.warning("Numba not available — falling back to NumPy simulations")


class SimulationService:
    """Monte Carlo match simulation engine."""

    def __init__(self, n_simulations: int = None):
        self.n_simulations = n_simulations or settings.monte_carlo_simulations

    def simulate_match(
        self,
        lambda_home: float,
        lambda_away: float,
    ) -> MonteCarloResult:
        """
        Run Monte Carlo simulation of a match.

        Args:
            lambda_home: Expected goals for home team (Poisson λ)
            lambda_away: Expected goals for away team (Poisson λ)

        Returns:
            MonteCarloResult with full simulation statistics
        """
        n = self.n_simulations
        logger.info(f"Running {n:,} Monte Carlo simulations (λH={lambda_home:.2f}, λA={lambda_away:.2f})")

        # Run simulations
        if USE_NUMBA:
            home_goals, away_goals = _simulate_matches_numba(lambda_home, lambda_away, n)
        else:
            home_goals = np.random.poisson(lambda_home, n)
            away_goals = np.random.poisson(lambda_away, n)

        # Calculate outcomes
        home_wins = np.sum(home_goals > away_goals)
        draws = np.sum(home_goals == away_goals)
        away_wins = np.sum(home_goals < away_goals)

        # Score distribution (top scores)
        score_counts: Dict[str, int] = {}
        for hg, ag in zip(home_goals, away_goals):
            score_key = f"{hg}-{ag}"
            score_counts[score_key] = score_counts.get(score_key, 0) + 1

        # Sort by frequency and take top 25
        sorted_scores = sorted(score_counts.items(), key=lambda x: -x[1])[:25]
        score_probs = [
            ScoreProb(
                home_goals=int(s.split("-")[0]),
                away_goals=int(s.split("-")[1]),
                probability=round(c / n, 4),
            )
            for s, c in sorted_scores
        ]

        # Goal distribution
        max_goals = min(int(max(home_goals.max(), away_goals.max())) + 1, 8)
        goal_dist = {}
        for g in range(max_goals + 1):
            total_goals = home_goals + away_goals
            goal_dist[str(g)] = round(np.sum(total_goals == g) / n, 4)

        most_likely = sorted_scores[0][0] if sorted_scores else "1-0"

        result = MonteCarloResult(
            simulations=n,
            home_win_pct=round(home_wins / n * 100, 2),
            draw_pct=round(draws / n * 100, 2),
            away_win_pct=round(away_wins / n * 100, 2),
            avg_goals_home=round(float(np.mean(home_goals)), 2),
            avg_goals_away=round(float(np.mean(away_goals)), 2),
            most_likely_score=most_likely,
            goal_distribution=goal_dist,
            score_distribution=score_probs,
        )

        logger.info(
            f"Simulation complete: H={result.home_win_pct}% D={result.draw_pct}% A={result.away_win_pct}%"
        )
        return result

    @staticmethod
    def poisson_score_matrix(
        lambda_home: float,
        lambda_away: float,
        max_goals: int = 6,
    ) -> List[ScoreProb]:
        """
        Generate score probability matrix using Poisson distribution.

        Returns:
            List of ScoreProb for each possible score combination.
        """
        matrix = []
        for h in range(max_goals + 1):
            for a in range(max_goals + 1):
                prob = poisson.pmf(h, lambda_home) * poisson.pmf(a, lambda_away)
                matrix.append(ScoreProb(
                    home_goals=h,
                    away_goals=a,
                    probability=round(float(prob), 4),
                ))
        return sorted(matrix, key=lambda x: -x.probability)

    @staticmethod
    def calculate_expected_goals(
        attack_rating_home: float,
        defense_rating_away: float,
        attack_rating_away: float,
        defense_rating_home: float,
        league_avg_goals: float = 2.7,
    ) -> Tuple[float, float]:
        """
        Calculate expected goals using attack/defense ratings.

        The formula scales around the league average:
        - attack_rating=50, defense_rating=50 → λ ≈ league_avg/2 (≈1.35)
        - Higher attack or lower opponent defense → higher λ
        - Home advantage gives ~15% boost

        Returns:
            (lambda_home, lambda_away) for Poisson distribution
        """
        base = league_avg_goals / 2.0  # ~1.35 per team on average
        home_advantage = 1.15  # ~15% home advantage

        # Attack strength relative to average (50 = average → ratio = 1.0)
        # 70 attack → 1.4x, 30 attack → 0.6x
        home_attack_strength = attack_rating_home / 50.0
        away_attack_strength = attack_rating_away / 50.0

        # Defense weakness: higher defense_rating = better defense = fewer goals conceded
        # 70 defense → opponent scores 0.71x, 30 defense → opponent scores 1.43x
        away_defense_weakness = 50.0 / max(defense_rating_away, 10.0)
        home_defense_weakness = 50.0 / max(defense_rating_home, 10.0)

        # Expected goals: base × attack_strength × opponent_defense_weakness × advantage
        lambda_home = base * home_attack_strength * away_defense_weakness * home_advantage
        lambda_away = base * away_attack_strength * home_defense_weakness

        # Clamp to reasonable range (no team scores less than 0.5 or more than 4.0 xG)
        lambda_home = max(0.5, min(4.0, round(lambda_home, 3)))
        lambda_away = max(0.4, min(3.5, round(lambda_away, 3)))

        return lambda_home, lambda_away
