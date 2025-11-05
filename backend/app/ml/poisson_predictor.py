"""
Poisson Distribution Predictor for Football Match Outcomes

This module implements the Poisson distribution model for predicting
football match outcomes based on team attacking and defensive strengths.

The Poisson distribution is particularly suitable for modeling the number
of goals scored in football matches, as it describes the probability of a
given number of events happening in a fixed interval of time.
"""

import numpy as np
from scipy.stats import poisson
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class PoissonPredictor:
    """
    Poisson-based football match predictor.

    Uses the Poisson distribution to model goal probabilities based on:
    - Team attacking strength
    - Team defensive strength
    - Home advantage
    - League average goals
    """

    def __init__(self, home_advantage: float = 1.3):
        """
        Initialize the Poisson predictor.

        Args:
            home_advantage: Multiplier for home team strength (typically 1.2-1.4)
        """
        self.home_advantage = home_advantage
        self.max_goals = 10  # Maximum goals to consider in calculations

    def calculate_attack_strength(
        self,
        goals_scored_avg: float,
        league_avg_goals: float
    ) -> float:
        """
        Calculate team's attacking strength relative to league average.

        Args:
            goals_scored_avg: Team's average goals scored
            league_avg_goals: League average goals per match

        Returns:
            Attack strength coefficient
        """
        if league_avg_goals == 0:
            return 1.0
        return goals_scored_avg / league_avg_goals

    def calculate_defense_strength(
        self,
        goals_conceded_avg: float,
        league_avg_goals: float
    ) -> float:
        """
        Calculate team's defensive strength relative to league average.

        Args:
            goals_conceded_avg: Team's average goals conceded
            league_avg_goals: League average goals per match

        Returns:
            Defense strength coefficient
        """
        if league_avg_goals == 0:
            return 1.0
        return goals_conceded_avg / league_avg_goals

    def predict_expected_goals(
        self,
        attack_strength: float,
        defense_strength_opponent: float,
        league_avg_goals: float,
        is_home: bool = True
    ) -> float:
        """
        Predict expected goals using Poisson model.

        Args:
            attack_strength: Attacking team's strength coefficient
            defense_strength_opponent: Defending team's strength coefficient
            league_avg_goals: League average goals per match
            is_home: Whether the attacking team is playing at home

        Returns:
            Expected number of goals (lambda parameter for Poisson)
        """
        home_multiplier = self.home_advantage if is_home else 1.0
        expected_goals = (
            attack_strength *
            defense_strength_opponent *
            league_avg_goals *
            home_multiplier
        )
        return max(0.1, expected_goals)  # Ensure positive lambda

    def calculate_match_probabilities(
        self,
        home_expected_goals: float,
        away_expected_goals: float
    ) -> Dict[str, float]:
        """
        Calculate match outcome probabilities using Poisson distribution.

        Args:
            home_expected_goals: Expected goals for home team (lambda_home)
            away_expected_goals: Expected goals for away team (lambda_away)

        Returns:
            Dictionary with probabilities for home win, draw, away win
        """
        prob_home_win = 0.0
        prob_draw = 0.0
        prob_away_win = 0.0

        # Calculate probabilities for all realistic score combinations
        for home_goals in range(self.max_goals + 1):
            for away_goals in range(self.max_goals + 1):
                # Poisson probability mass function
                prob_home_score = poisson.pmf(home_goals, home_expected_goals)
                prob_away_score = poisson.pmf(away_goals, away_expected_goals)

                # Joint probability of this exact score
                prob_score = prob_home_score * prob_away_score

                # Accumulate probabilities
                if home_goals > away_goals:
                    prob_home_win += prob_score
                elif home_goals == away_goals:
                    prob_draw += prob_score
                else:
                    prob_away_win += prob_score

        return {
            'home_win': prob_home_win,
            'draw': prob_draw,
            'away_win': prob_away_win,
            'home_expected_goals': home_expected_goals,
            'away_expected_goals': away_expected_goals
        }

    def calculate_over_under_probabilities(
        self,
        home_expected_goals: float,
        away_expected_goals: float,
        threshold: float = 2.5
    ) -> Dict[str, float]:
        """
        Calculate over/under goal probabilities.

        Args:
            home_expected_goals: Expected goals for home team
            away_expected_goals: Expected goals for away team
            threshold: Goals threshold (e.g., 2.5, 3.5)

        Returns:
            Dictionary with over and under probabilities
        """
        prob_under = 0.0

        # Sum probabilities for all scores under threshold
        for home_goals in range(self.max_goals + 1):
            for away_goals in range(self.max_goals + 1):
                total_goals = home_goals + away_goals

                if total_goals < threshold:
                    prob_home_score = poisson.pmf(home_goals, home_expected_goals)
                    prob_away_score = poisson.pmf(away_goals, away_expected_goals)
                    prob_under += prob_home_score * prob_away_score

        prob_over = 1.0 - prob_under

        return {
            f'over_{threshold}': prob_over,
            f'under_{threshold}': prob_under
        }

    def calculate_btts_probability(
        self,
        home_expected_goals: float,
        away_expected_goals: float
    ) -> Dict[str, float]:
        """
        Calculate Both Teams To Score (BTTS) probability.

        Args:
            home_expected_goals: Expected goals for home team
            away_expected_goals: Expected goals for away team

        Returns:
            Dictionary with BTTS yes/no probabilities
        """
        # Probability that home team scores 0 goals
        prob_home_zero = poisson.pmf(0, home_expected_goals)

        # Probability that away team scores 0 goals
        prob_away_zero = poisson.pmf(0, away_expected_goals)

        # Probability at least one team doesn't score
        prob_btts_no = (
            prob_home_zero +
            prob_away_zero -
            (prob_home_zero * prob_away_zero)
        )

        prob_btts_yes = 1.0 - prob_btts_no

        return {
            'btts_yes': prob_btts_yes,
            'btts_no': prob_btts_no
        }

    def predict_match(
        self,
        home_team_data: Dict[str, float],
        away_team_data: Dict[str, float],
        league_avg_goals: float = 2.7
    ) -> Dict[str, any]:
        """
        Full match prediction using Poisson distribution.

        Args:
            home_team_data: Dict with 'goals_scored_avg' and 'goals_conceded_avg'
            away_team_data: Dict with 'goals_scored_avg' and 'goals_conceded_avg'
            league_avg_goals: Average goals per match in the league

        Returns:
            Complete prediction including all markets
        """
        # Calculate team strengths
        home_attack = self.calculate_attack_strength(
            home_team_data['goals_scored_avg'],
            league_avg_goals
        )
        home_defense = self.calculate_defense_strength(
            home_team_data['goals_conceded_avg'],
            league_avg_goals
        )

        away_attack = self.calculate_attack_strength(
            away_team_data['goals_scored_avg'],
            league_avg_goals
        )
        away_defense = self.calculate_defense_strength(
            away_team_data['goals_conceded_avg'],
            league_avg_goals
        )

        # Calculate expected goals
        home_expected = self.predict_expected_goals(
            home_attack,
            away_defense,
            league_avg_goals,
            is_home=True
        )

        away_expected = self.predict_expected_goals(
            away_attack,
            home_defense,
            league_avg_goals,
            is_home=False
        )

        # Calculate all probabilities
        match_probs = self.calculate_match_probabilities(
            home_expected,
            away_expected
        )

        over_under_2_5 = self.calculate_over_under_probabilities(
            home_expected,
            away_expected,
            threshold=2.5
        )

        over_under_3_5 = self.calculate_over_under_probabilities(
            home_expected,
            away_expected,
            threshold=3.5
        )

        btts = self.calculate_btts_probability(
            home_expected,
            away_expected
        )

        # Determine most likely outcome
        max_prob = max(
            match_probs['home_win'],
            match_probs['draw'],
            match_probs['away_win']
        )

        if match_probs['home_win'] == max_prob:
            prediction = '1'
            confidence = match_probs['home_win']
        elif match_probs['draw'] == max_prob:
            prediction = 'X'
            confidence = match_probs['draw']
        else:
            prediction = '2'
            confidence = match_probs['away_win']

        return {
            'prediction': prediction,
            'confidence': confidence,
            'probabilities': {
                'home': match_probs['home_win'],
                'draw': match_probs['draw'],
                'away': match_probs['away_win']
            },
            'expected_goals': {
                'home': home_expected,
                'away': away_expected,
                'total': home_expected + away_expected
            },
            'markets': {
                'over_under': {
                    '2.5': over_under_2_5,
                    '3.5': over_under_3_5
                },
                'btts': btts
            },
            'team_strengths': {
                'home': {
                    'attack': home_attack,
                    'defense': home_defense
                },
                'away': {
                    'attack': away_attack,
                    'defense': away_defense
                }
            }
        }


def integrate_poisson_with_ensemble(
    ensemble_prediction: Dict[str, float],
    poisson_prediction: Dict[str, any],
    poisson_weight: float = 0.3
) -> Dict[str, float]:
    """
    Integrate Poisson predictions with ensemble model predictions.

    Args:
        ensemble_prediction: Predictions from ensemble model
        poisson_prediction: Predictions from Poisson model
        poisson_weight: Weight for Poisson model (0-1)

    Returns:
        Combined predictions
    """
    ensemble_weight = 1.0 - poisson_weight

    combined = {
        'home': (
            ensemble_prediction.get('home', 0.33) * ensemble_weight +
            poisson_prediction['probabilities']['home'] * poisson_weight
        ),
        'draw': (
            ensemble_prediction.get('draw', 0.33) * ensemble_weight +
            poisson_prediction['probabilities']['draw'] * poisson_weight
        ),
        'away': (
            ensemble_prediction.get('away', 0.33) * ensemble_weight +
            poisson_prediction['probabilities']['away'] * poisson_weight
        )
    }

    # Normalize to ensure probabilities sum to 1
    total = sum(combined.values())
    if total > 0:
        combined = {k: v / total for k, v in combined.items()}

    return combined
