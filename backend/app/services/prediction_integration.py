import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.models.match import Match
from app.models.prediction import Prediction
from app.services.prediction_service import PredictionService

logger = logging.getLogger(__name__)

class PredictionIntegrationService:
    """
    Integration service for automatically generating predictions
    for synchronized match data from external APIs.
    """

    def __init__(self):
        self.prediction_service = None

    async def predict_match(self, match_id: int, home_team_id: int, away_team_id: int) -> Dict:
        """
        Generate prediction for a specific match using synchronized data.

        Args:
            match_id: ID of the match to predict
            home_team_id: ID of the home team
            away_team_id: ID of the away team

        Returns:
            Dictionary with prediction results and success status
        """
        try:
            with get_db_session() as db:
                # Initialize prediction service with database session
                prediction_service = PredictionService(db)

                # Check if match exists
                match = db.query(Match).filter(Match.id == match_id).first()
                if not match:
                    return {
                        "success": False,
                        "error": f"Match {match_id} not found",
                        "confidence": 0.0
                    }

                # Check if prediction already exists and is recent
                existing_prediction = db.query(Prediction).filter(
                    Prediction.match_id == match_id
                ).order_by(Prediction.created_at.desc()).first()

                # If prediction exists and is less than 4 hours old, return existing
                if existing_prediction and existing_prediction.created_at:
                    age = datetime.now() - existing_prediction.created_at
                    if age < timedelta(hours=4):
                        logger.info(f"Using existing prediction for match {match_id}")
                        return {
                            "success": True,
                            "prediction_id": existing_prediction.id,
                            "confidence": existing_prediction.confidence_score or 0.5,
                            "age_hours": age.total_seconds() / 3600,
                            "from_cache": True
                        }

                # Generate new prediction
                logger.info(f"Generating new prediction for match {match_id}: {match.home_team.name} vs {match.away_team.name}")

                prediction_data = await prediction_service.generate_match_prediction(match_id)

                # Extract key prediction values
                match_outcome = prediction_data.get("match_outcome", {})
                goals_prediction = prediction_data.get("goals_prediction", {})
                btts_prediction = prediction_data.get("btts_prediction", {})

                # Create new prediction record (usando campos corretos do modelo Prediction)
                new_prediction = Prediction(
                    match_id=match_id,
                    prediction_type="SINGLE",  # Prediction do sync é sempre SINGLE
                    market_type="1X2",  # Market type padrão
                    predicted_outcome=match_outcome.get("predicted_outcome", "1"),  # 1, X, 2
                    predicted_probability=match_outcome.get("home_win_probability", 0.33),
                    probability_home=match_outcome.get("home_win_probability", 0.33),
                    probability_draw=match_outcome.get("draw_probability", 0.33),
                    probability_away=match_outcome.get("away_win_probability", 0.34),
                    confidence_score=prediction_data.get("overall_confidence", 0.5),
                    key_factors={
                        "expected_home_goals": goals_prediction.get("expected_home_goals", 1.0),
                        "expected_away_goals": goals_prediction.get("expected_away_goals", 1.0),
                        "over_2_5_probability": goals_prediction.get("over_2_5_probability", 0.5),
                        "btts_yes_probability": btts_prediction.get("btts_yes_probability", 0.5),
                        "full_prediction_data": prediction_data
                    },
                    model_version="sync_v1.0",
                    is_validated=False
                )

                db.add(new_prediction)
                db.commit()
                db.refresh(new_prediction)

                logger.info(f"✅ Generated prediction for match {match_id} with confidence {new_prediction.confidence_score}")

                return {
                    "success": True,
                    "prediction_id": new_prediction.id,
                    "confidence": new_prediction.confidence_score,
                    "from_cache": False,
                    "prediction_summary": {
                        "most_likely_outcome": match_outcome.get("predicted_outcome", "Unknown"),
                        "home_win_prob": round(match_outcome.get("home_win_probability", 0) * 100, 1),
                        "draw_prob": round(match_outcome.get("draw_probability", 0) * 100, 1),
                        "away_win_prob": round(match_outcome.get("away_win_probability", 0) * 100, 1),
                        "predicted_score": f"{int(goals_prediction.get('expected_home_goals', 1))}-{int(goals_prediction.get('expected_away_goals', 1))}",
                        "over_2_5_prob": round(goals_prediction.get("over_2_5_probability", 0) * 100, 1),
                        "btts_prob": round(btts_prediction.get("btts_yes_probability", 0) * 100, 1)
                    }
                }

        except Exception as e:
            logger.error(f"❌ Failed to generate prediction for match {match_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "confidence": 0.0
            }

    async def bulk_predict_matches(self, match_ids: List[int]) -> Dict[str, any]:
        """
        Generate predictions for multiple matches in bulk.

        Args:
            match_ids: List of match IDs to predict

        Returns:
            Dictionary with overall results and individual match results
        """
        results = {
            "total_matches": len(match_ids),
            "successful_predictions": 0,
            "failed_predictions": 0,
            "from_cache": 0,
            "new_predictions": 0,
            "predictions": {},
            "errors": []
        }

        for match_id in match_ids:
            try:
                with get_db_session() as db:
                    match = db.query(Match).filter(Match.id == match_id).first()
                    if not match:
                        results["errors"].append(f"Match {match_id} not found")
                        results["failed_predictions"] += 1
                        continue

                    prediction_result = await self.predict_match(
                        match_id,
                        match.home_team_id,
                        match.away_team_id
                    )

                    if prediction_result.get("success"):
                        results["successful_predictions"] += 1
                        if prediction_result.get("from_cache"):
                            results["from_cache"] += 1
                        else:
                            results["new_predictions"] += 1

                        results["predictions"][match_id] = prediction_result
                    else:
                        results["failed_predictions"] += 1
                        results["errors"].append(f"Match {match_id}: {prediction_result.get('error', 'Unknown error')}")

            except Exception as e:
                results["failed_predictions"] += 1
                results["errors"].append(f"Match {match_id}: {str(e)}")

        logger.info(f"Bulk prediction completed: {results['successful_predictions']}/{results['total_matches']} successful")
        return results

    async def predict_upcoming_matches(self, days_ahead: int = 7) -> Dict[str, any]:
        """
        Generate predictions for all upcoming matches in the next N days.

        Args:
            days_ahead: Number of days ahead to predict (default: 7)

        Returns:
            Dictionary with prediction results
        """
        try:
            with get_db_session() as db:
                # Get upcoming matches
                start_date = datetime.now()
                end_date = start_date + timedelta(days=days_ahead)

                upcoming_matches = db.query(Match).filter(
                    Match.match_date >= start_date,
                    Match.match_date <= end_date,
                    Match.status == "SCHEDULED"
                ).all()

                if not upcoming_matches:
                    return {
                        "message": f"No upcoming matches found in the next {days_ahead} days",
                        "total_matches": 0,
                        "predictions": {}
                    }

                match_ids = [match.id for match in upcoming_matches]

                logger.info(f"Generating predictions for {len(match_ids)} upcoming matches")

                return await self.bulk_predict_matches(match_ids)

        except Exception as e:
            logger.error(f"❌ Failed to predict upcoming matches: {str(e)}")
            return {
                "error": str(e),
                "total_matches": 0,
                "predictions": {}
            }

    async def update_prediction_accuracy(self) -> Dict[str, any]:
        """
        Update prediction accuracy by comparing predictions with actual results.

        Returns:
            Dictionary with accuracy statistics
        """
        try:
            with get_db_session() as db:
                # Get finished matches with predictions from last 30 days
                cutoff_date = datetime.now() - timedelta(days=30)

                finished_matches = db.query(Match).filter(
                    Match.status == "FINISHED",
                    Match.match_date >= cutoff_date,
                    Match.home_score.isnot(None),
                    Match.away_score.isnot(None)
                ).all()

                total_predictions = 0
                correct_outcomes = 0
                correct_scores = 0
                btts_correct = 0
                over_2_5_correct = 0

                for match in finished_matches:
                    prediction = db.query(Prediction).filter(
                        Prediction.match_id == match.id
                    ).first()

                    if not prediction:
                        continue

                    total_predictions += 1

                    # Determine actual outcome
                    if match.home_score > match.away_score:
                        actual_outcome = "1"
                    elif match.home_score < match.away_score:
                        actual_outcome = "2"
                    else:
                        actual_outcome = "X"

                    # Determine predicted outcome
                    probs = [
                        prediction.home_win_probability,
                        prediction.draw_probability,
                        prediction.away_win_probability
                    ]
                    max_prob_index = probs.index(max(probs))
                    predicted_outcome = ["1", "X", "2"][max_prob_index]

                    # Check outcome accuracy
                    if predicted_outcome == actual_outcome:
                        correct_outcomes += 1

                    # Check exact score accuracy
                    if (prediction.predicted_score_home == match.home_score and
                        prediction.predicted_score_away == match.away_score):
                        correct_scores += 1

                    # Check BTTS accuracy
                    actual_btts = match.home_score > 0 and match.away_score > 0
                    predicted_btts = prediction.btts_yes_probability > 0.5
                    if actual_btts == predicted_btts:
                        btts_correct += 1

                    # Check Over 2.5 accuracy
                    actual_over_2_5 = (match.home_score + match.away_score) > 2.5
                    predicted_over_2_5 = prediction.over_2_5_probability > 0.5
                    if actual_over_2_5 == predicted_over_2_5:
                        over_2_5_correct += 1

                if total_predictions == 0:
                    return {
                        "message": "No predictions found for accuracy calculation",
                        "total_predictions": 0
                    }

                accuracy_stats = {
                    "total_predictions": total_predictions,
                    "outcome_accuracy": round(correct_outcomes / total_predictions * 100, 2),
                    "exact_score_accuracy": round(correct_scores / total_predictions * 100, 2),
                    "btts_accuracy": round(btts_correct / total_predictions * 100, 2),
                    "over_2_5_accuracy": round(over_2_5_correct / total_predictions * 100, 2),
                    "period": f"Last 30 days",
                    "updated_at": datetime.now().isoformat()
                }

                logger.info(f"Prediction accuracy updated: {accuracy_stats}")
                return accuracy_stats

        except Exception as e:
            logger.error(f"❌ Failed to update prediction accuracy: {str(e)}")
            return {
                "error": str(e),
                "total_predictions": 0
            }

    async def get_prediction_summary(self, match_id: int) -> Optional[Dict]:
        """
        Get a summary of the prediction for a specific match.

        Args:
            match_id: ID of the match

        Returns:
            Dictionary with prediction summary or None if not found
        """
        try:
            with get_db_session() as db:
                prediction = db.query(Prediction).filter(
                    Prediction.match_id == match_id
                ).order_by(Prediction.created_at.desc()).first()

                if not prediction:
                    return None

                match = db.query(Match).filter(Match.id == match_id).first()
                if not match:
                    return None

                return {
                    "match_id": match_id,
                    "home_team": match.home_team.name,
                    "away_team": match.away_team.name,
                    "match_date": match.match_date.isoformat(),
                    "prediction": {
                        "home_win_prob": round(prediction.home_win_probability * 100, 1),
                        "draw_prob": round(prediction.draw_probability * 100, 1),
                        "away_win_prob": round(prediction.away_win_probability * 100, 1),
                        "predicted_score": f"{prediction.predicted_score_home}-{prediction.predicted_score_away}",
                        "over_2_5_prob": round(prediction.over_2_5_probability * 100, 1),
                        "btts_prob": round(prediction.btts_yes_probability * 100, 1),
                        "confidence": round(prediction.confidence_score * 100, 1)
                    },
                    "created_at": prediction.created_at.isoformat(),
                    "model_version": prediction.model_version
                }

        except Exception as e:
            logger.error(f"❌ Failed to get prediction summary for match {match_id}: {str(e)}")
            return None

# Global instance
prediction_integration = PredictionIntegrationService()