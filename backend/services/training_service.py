"""
Sports AI — Training Service
Ensemble model training and prediction with Logistic Regression, Random Forest, and XGBoost.
"""

import os
import numpy as np
import joblib
from typing import Dict, Optional, Tuple
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.preprocessing import StandardScaler
from backend.config.settings import get_settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Feature names expected by the models
FEATURE_NAMES = [
    "home_form", "away_form", "form_difference",
    "home_goal_avg", "away_goal_avg", "goal_difference",
    "home_attack", "away_attack", "home_defense", "away_defense",
    "xg_difference", "elo_difference",
    "home_momentum", "away_momentum",
    "market_movement",
    "injury_impact_home", "injury_impact_away", "injury_difference",
    "home_advantage",
]

# Labels: 0=Home Win, 1=Draw, 2=Away Win
LABELS = {0: "Home Win", 1: "Draw", 2: "Away Win"}


class TrainingService:
    """Ensemble ML model for match prediction."""

    def __init__(self):
        self.scaler = StandardScaler()
        self.models = {
            "logistic_regression": LogisticRegression(
                max_iter=1000, C=1.0
            ),
            "random_forest": RandomForestClassifier(
                n_estimators=200, max_depth=10, random_state=42, n_jobs=-1
            ),
            "xgboost": XGBClassifier(
                n_estimators=200, max_depth=6, learning_rate=0.1,
                use_label_encoder=False, eval_metric="mlogloss",
                random_state=42, verbosity=0,
            ),
        }
        self.weights = {
            "logistic_regression": 0.2,
            "random_forest": 0.35,
            "xgboost": 0.45,
        }
        self._is_trained = False

    def _generate_synthetic_data(self, n_samples: int = 5000) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate synthetic training data for initial model setup.
        In production, this would be replaced with real historical match data.
        """
        np.random.seed(42)
        X = np.random.randn(n_samples, len(FEATURE_NAMES))

        # Home advantage bias
        X[:, FEATURE_NAMES.index("home_advantage")] = 1.0

        # Generate labels with realistic distribution (~45% H, 25% D, 30% A)
        y = np.zeros(n_samples, dtype=int)
        form_diff = X[:, FEATURE_NAMES.index("form_difference")]
        elo_diff = X[:, FEATURE_NAMES.index("elo_difference")]

        score = form_diff * 0.3 + elo_diff * 0.5 + np.random.randn(n_samples) * 0.8

        y[score > 0.3] = 0   # Home win
        y[(score >= -0.3) & (score <= 0.3)] = 1  # Draw
        y[score < -0.3] = 2  # Away win

        return X, y

    def train(self, X: np.ndarray = None, y: np.ndarray = None) -> Dict:
        """
        Train the ensemble model.

        If no data provided, uses synthetic data for initialization.
        """
        if X is None or y is None:
            logger.info("No training data provided — generating synthetic data")
            X, y = self._generate_synthetic_data()

        X_scaled = self.scaler.fit_transform(X)

        results = {}
        for name, model in self.models.items():
            model.fit(X_scaled, y)
            accuracy = model.score(X_scaled, y)
            results[name] = round(accuracy, 4)
            logger.info(f"Trained {name}: accuracy={accuracy:.4f}")

        self._is_trained = True
        self._save_models()
        return results

    def predict(self, features: Dict[str, float]) -> Dict[str, float]:
        """
        Generate ensemble prediction.

        Returns:
            Dict with keys 'home_win', 'draw', 'away_win' probabilities.
        """
        if not self._is_trained:
            self._load_models()
            if not self._is_trained:
                logger.warning("Models not trained — training with synthetic data")
                self.train()

        # Build feature vector in correct order
        X = np.array([[features.get(name, 0.0) for name in FEATURE_NAMES]])
        X_scaled = self.scaler.transform(X)

        # Ensemble predictions
        ensemble_probs = np.zeros(3)
        for name, model in self.models.items():
            probs = model.predict_proba(X_scaled)[0]
            ensemble_probs += probs * self.weights[name]

        # Normalize
        total = ensemble_probs.sum()
        if total > 0:
            ensemble_probs /= total

        result = {
            "home_win": round(float(ensemble_probs[0]), 4),
            "draw": round(float(ensemble_probs[1]), 4),
            "away_win": round(float(ensemble_probs[2]), 4),
        }

        logger.info(f"Ensemble prediction: H={result['home_win']:.2%} D={result['draw']:.2%} A={result['away_win']:.2%}")
        return result

    def _save_models(self):
        """Save trained models to disk."""
        model_dir = settings.model_path
        os.makedirs(model_dir, exist_ok=True)
        joblib.dump(self.scaler, os.path.join(model_dir, "scaler.pkl"))
        for name, model in self.models.items():
            joblib.dump(model, os.path.join(model_dir, f"{name}.pkl"))
        logger.info(f"Models saved to {model_dir}")

    def _load_models(self):
        """Load trained models from disk."""
        model_dir = settings.model_path
        scaler_path = os.path.join(model_dir, "scaler.pkl")
        if not os.path.exists(scaler_path):
            return
        try:
            self.scaler = joblib.load(scaler_path)
            for name in self.models:
                model_path = os.path.join(model_dir, f"{name}.pkl")
                if os.path.exists(model_path):
                    self.models[name] = joblib.load(model_path)
            self._is_trained = True
            logger.info("Models loaded from disk")
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
