"""
Sports AI — Feature Engineering Service
Generates ML features from raw match data for predictive models.
"""

import numpy as np
from typing import Dict, List, Optional
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class FeatureEngineeringService:
    """Generates feature vectors for ML models from match context data."""

    @staticmethod
    def calculate_form_score(results: List[Dict], is_home: bool = True) -> float:
        """
        Calculate team form score from recent results.

        Weights: most recent match has highest weight.
        Win=3, Draw=1, Loss=0, weighted by recency.
        """
        if not results:
            return 50.0

        scores = []
        for match in results:
            goals_for = match.get("goals_home", 0) if is_home else match.get("goals_away", 0)
            goals_against = match.get("goals_away", 0) if is_home else match.get("goals_home", 0)

            if goals_for > goals_against:
                scores.append(3.0)
            elif goals_for == goals_against:
                scores.append(1.0)
            else:
                scores.append(0.0)

        # Apply exponential weights (most recent = highest weight)
        n = len(scores)
        weights = [np.exp(-0.2 * i) for i in range(n)]
        total_weight = sum(weights)

        weighted_score = sum(s * w for s, w in zip(scores, weights)) / total_weight
        return round((weighted_score / 3.0) * 100, 2)

    @staticmethod
    def calculate_goal_average(results: List[Dict], is_home: bool = True) -> float:
        """Calculate average goals scored."""
        if not results:
            return 0.0
        key = "goals_home" if is_home else "goals_away"
        goals = [m.get(key, 0) for m in results]
        return round(np.mean(goals), 3)

    @staticmethod
    def calculate_defense_rating(results: List[Dict], is_home: bool = True) -> float:
        """Calculate defensive rating (lower goals conceded = higher rating)."""
        if not results:
            return 50.0
        key = "goals_away" if is_home else "goals_home"
        conceded = [m.get(key, 0) for m in results]
        avg_conceded = np.mean(conceded)
        # 0 conceded = 100 rating, 3+ conceded = low rating
        return round(max(0, 100 - (avg_conceded * 30)), 2)

    @staticmethod
    def calculate_attack_rating(results: List[Dict], is_home: bool = True) -> float:
        """Calculate attack rating based on goals scored."""
        if not results:
            return 50.0
        key = "goals_home" if is_home else "goals_away"
        scored = [m.get(key, 0) for m in results]
        avg_scored = np.mean(scored)
        return round(min(100, avg_scored * 35), 2)

    @staticmethod
    def calculate_momentum(results: List[Dict], is_home: bool = True) -> float:
        """
        Calculate momentum (-1 to 1).
        Compares recent 3 vs previous 3 matches.
        """
        if len(results) < 6:
            return 0.0

        def form(matches):
            pts = 0
            for m in matches:
                gf = m.get("goals_home", 0) if is_home else m.get("goals_away", 0)
                ga = m.get("goals_away", 0) if is_home else m.get("goals_home", 0)
                if gf > ga:
                    pts += 3
                elif gf == ga:
                    pts += 1
            return pts

        recent = form(results[:3])
        previous = form(results[3:6])
        max_diff = 9  # max(3*3) - min(0)

        return round((recent - previous) / max_diff, 3)

    def generate_features(
        self,
        home_stats: Dict,
        away_stats: Dict,
        elo_diff: float = 0.0,
        market_movement: float = 0.0,
        injury_impact_home: float = 0.0,
        injury_impact_away: float = 0.0,
    ) -> Dict[str, float]:
        """
        Generate complete feature vector for ML models.

        Returns:
            Dictionary of features ready for model input.
        """
        features = {
            # Form
            "home_form": home_stats.get("form_score", 50.0),
            "away_form": away_stats.get("form_score", 50.0),
            "form_difference": (
                home_stats.get("form_score", 50.0)
                - away_stats.get("form_score", 50.0)
            ),

            # Goals
            "home_goal_avg": home_stats.get("goal_average", 1.0),
            "away_goal_avg": away_stats.get("goal_average", 1.0),
            "goal_difference": (
                home_stats.get("goal_average", 1.0)
                - away_stats.get("goal_average", 1.0)
            ),

            # xG proxy
            "home_attack": home_stats.get("attack_rating", 50.0),
            "away_attack": away_stats.get("attack_rating", 50.0),
            "home_defense": home_stats.get("defense_rating", 50.0),
            "away_defense": away_stats.get("defense_rating", 50.0),
            "xg_difference": (
                (home_stats.get("attack_rating", 50.0) - away_stats.get("defense_rating", 50.0))
                - (away_stats.get("attack_rating", 50.0) - home_stats.get("defense_rating", 50.0))
            ) / 100.0,

            # ELO
            "elo_difference": elo_diff,

            # Momentum
            "home_momentum": home_stats.get("momentum", 0.0),
            "away_momentum": away_stats.get("momentum", 0.0),

            # Market
            "market_movement": market_movement,

            # Injuries
            "injury_impact_home": injury_impact_home,
            "injury_impact_away": injury_impact_away,
            "injury_difference": injury_impact_home - injury_impact_away,

            # Home advantage
            "home_advantage": 1.0,
        }

        logger.info(f"Generated {len(features)} features for ML model")
        return features
