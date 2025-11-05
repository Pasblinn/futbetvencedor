import itertools
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import Match, Prediction, BetCombination
from app.services.prediction_service import PredictionService
from app.services.odds_service import OddsService
import math
from dataclasses import dataclass

@dataclass
class BetSelection:
    match_id: int
    match_name: str
    market: str
    selection: str
    probability: float
    odds: float
    confidence: float
    match_date: datetime

class CombinationService:
    def __init__(self, db: Session):
        self.db = db
        self.prediction_service = PredictionService(db)
        self.odds_service = OddsService()

    async def generate_daily_combinations(self, target_date: datetime = None, min_odds: float = 1.5, max_odds: float = 2.0, min_confidence: float = 0.65) -> Dict:
        """Generate betting combinations for a specific day"""

        if target_date is None:
            target_date = datetime.now()

        # Get matches for the target date
        matches = self.db.query(Match).filter(
            Match.match_date >= target_date.replace(hour=0, minute=0, second=0),
            Match.match_date < target_date.replace(hour=23, minute=59, second=59),
            Match.status == "SCHEDULED"
        ).all()

        if not matches:
            return {"error": "No matches found for the specified date"}

        # Generate predictions for all matches
        all_selections = []

        for match in matches:
            try:
                prediction_data = await self.prediction_service.generate_match_prediction(match.id)
                selections = self._extract_bet_selections(match, prediction_data, min_confidence)
                all_selections.extend(selections)
            except Exception as e:
                continue  # Skip matches with prediction errors

        if not all_selections:
            return {"error": "No qualifying selections found"}

        # Filter selections by confidence
        high_confidence_selections = [s for s in all_selections if s.confidence >= min_confidence]

        # Generate combinations
        combinations_data = {
            "date": target_date.strftime("%Y-%m-%d"),
            "total_matches": len(matches),
            "total_selections": len(all_selections),
            "high_confidence_selections": len(high_confidence_selections),
            "combinations": {
                "doubles": await self._generate_doubles(high_confidence_selections, min_odds, max_odds),
                "trebles": await self._generate_trebles(high_confidence_selections, min_odds, max_odds),
                "multiples": await self._generate_multiples(high_confidence_selections, min_odds, max_odds, 4),
            },
            "single_bets": self._generate_single_bets(high_confidence_selections, min_odds, max_odds),
            "analysis": {
                "avg_confidence": np.mean([s.confidence for s in high_confidence_selections]) if high_confidence_selections else 0,
                "market_distribution": self._analyze_market_distribution(high_confidence_selections),
                "risk_assessment": self._assess_daily_risk(high_confidence_selections)
            }
        }

        return combinations_data

    def _extract_bet_selections(self, match: Match, prediction_data: Dict, min_confidence: float) -> List[BetSelection]:
        """Extract viable bet selections from match prediction"""
        selections = []

        # Match outcome selections
        outcome = prediction_data.get("match_outcome", {})
        if outcome.get("confidence", 0) >= min_confidence:
            if outcome.get("predicted_outcome") == "1":
                selections.append(BetSelection(
                    match_id=match.id,
                    match_name=f"{prediction_data['home_team']} vs {prediction_data['away_team']}",
                    market="1X2",
                    selection="Home Win",
                    probability=outcome.get("home_win_probability", 0),
                    odds=outcome.get("home_win_odds", 0),
                    confidence=outcome.get("confidence", 0),
                    match_date=match.match_date
                ))
            elif outcome.get("predicted_outcome") == "X":
                selections.append(BetSelection(
                    match_id=match.id,
                    match_name=f"{prediction_data['home_team']} vs {prediction_data['away_team']}",
                    market="1X2",
                    selection="Draw",
                    probability=outcome.get("draw_probability", 0),
                    odds=outcome.get("draw_odds", 0),
                    confidence=outcome.get("confidence", 0),
                    match_date=match.match_date
                ))
            elif outcome.get("predicted_outcome") == "2":
                selections.append(BetSelection(
                    match_id=match.id,
                    match_name=f"{prediction_data['home_team']} vs {prediction_data['away_team']}",
                    market="1X2",
                    selection="Away Win",
                    probability=outcome.get("away_win_probability", 0),
                    odds=outcome.get("away_win_odds", 0),
                    confidence=outcome.get("confidence", 0),
                    match_date=match.match_date
                ))

        # Goals predictions
        goals = prediction_data.get("goals_prediction", {})

        # Over/Under 2.5 with high confidence
        if goals.get("over_2_5_probability", 0) >= 0.65:
            selections.append(BetSelection(
                match_id=match.id,
                match_name=f"{prediction_data['home_team']} vs {prediction_data['away_team']}",
                market="Total Goals",
                selection="Over 2.5",
                probability=goals.get("over_2_5_probability", 0),
                odds=goals.get("over_2_5_odds", 0),
                confidence=goals.get("over_2_5_probability", 0),
                match_date=match.match_date
            ))
        elif goals.get("under_2_5_probability", 0) >= 0.65:
            selections.append(BetSelection(
                match_id=match.id,
                match_name=f"{prediction_data['home_team']} vs {prediction_data['away_team']}",
                market="Total Goals",
                selection="Under 2.5",
                probability=goals.get("under_2_5_probability", 0),
                odds=goals.get("under_2_5_odds", 0),
                confidence=goals.get("under_2_5_probability", 0),
                match_date=match.match_date
            ))

        # BTTS predictions
        btts = prediction_data.get("btts_prediction", {})
        if btts.get("confidence", 0) >= min_confidence:
            if btts.get("predicted_outcome") == "Yes":
                selections.append(BetSelection(
                    match_id=match.id,
                    match_name=f"{prediction_data['home_team']} vs {prediction_data['away_team']}",
                    market="BTTS",
                    selection="Yes",
                    probability=btts.get("btts_yes_probability", 0),
                    odds=btts.get("btts_yes_odds", 0),
                    confidence=btts.get("confidence", 0),
                    match_date=match.match_date
                ))
            else:
                selections.append(BetSelection(
                    match_id=match.id,
                    match_name=f"{prediction_data['home_team']} vs {prediction_data['away_team']}",
                    market="BTTS",
                    selection="No",
                    probability=btts.get("btts_no_probability", 0),
                    odds=btts.get("btts_no_odds", 0),
                    confidence=btts.get("confidence", 0),
                    match_date=match.match_date
                ))

        # Corners predictions
        corners = prediction_data.get("corners_prediction", {})
        if corners.get("over_9_5_probability", 0) >= 0.7:
            selections.append(BetSelection(
                match_id=match.id,
                match_name=f"{prediction_data['home_team']} vs {prediction_data['away_team']}",
                market="Corners",
                selection="Over 9.5",
                probability=corners.get("over_9_5_probability", 0),
                odds=corners.get("over_9_5_odds", 0),
                confidence=corners.get("over_9_5_probability", 0),
                match_date=match.match_date
            ))

        return selections

    async def _generate_doubles(self, selections: List[BetSelection], min_odds: float, max_odds: float) -> List[Dict]:
        """Generate double bet combinations"""
        doubles = []

        for combo in itertools.combinations(selections, 2):
            sel1, sel2 = combo

            # Skip if same match
            if sel1.match_id == sel2.match_id:
                continue

            # Calculate combined odds
            combined_odds = sel1.odds * sel2.odds

            # Check if within target range
            if min_odds <= combined_odds <= max_odds:
                combined_probability = sel1.probability * sel2.probability
                combined_confidence = (sel1.confidence + sel2.confidence) / 2

                # Additional filters
                if combined_confidence >= 0.6 and combined_probability >= 0.25:
                    expected_value = (combined_probability * combined_odds) - 1

                    if expected_value > 0.05:  # At least 5% positive expected value
                        doubles.append({
                            "id": f"double_{sel1.match_id}_{sel2.match_id}",
                            "type": "double",
                            "selections": [
                                {
                                    "match_id": sel1.match_id,
                                    "match_name": sel1.match_name,
                                    "market": sel1.market,
                                    "selection": sel1.selection,
                                    "odds": sel1.odds,
                                    "probability": sel1.probability
                                },
                                {
                                    "match_id": sel2.match_id,
                                    "match_name": sel2.match_name,
                                    "market": sel2.market,
                                    "selection": sel2.selection,
                                    "odds": sel2.odds,
                                    "probability": sel2.probability
                                }
                            ],
                            "combined_odds": round(combined_odds, 2),
                            "combined_probability": round(combined_probability, 4),
                            "combined_confidence": round(combined_confidence, 3),
                            "expected_value": round(expected_value, 4),
                            "kelly_percentage": min(expected_value / (combined_odds - 1), 0.15),
                            "risk_level": self._calculate_risk_level(combined_confidence, len(combo)),
                            "correlation_check": self._check_correlation(sel1, sel2)
                        })

        # Sort by expected value descending
        doubles.sort(key=lambda x: x["expected_value"], reverse=True)
        return doubles[:20]  # Return top 20

    async def _generate_trebles(self, selections: List[BetSelection], min_odds: float, max_odds: float) -> List[Dict]:
        """Generate treble bet combinations"""
        trebles = []

        for combo in itertools.combinations(selections, 3):
            sel1, sel2, sel3 = combo

            # Skip if any matches are the same
            match_ids = {sel1.match_id, sel2.match_id, sel3.match_id}
            if len(match_ids) != 3:
                continue

            # Calculate combined odds
            combined_odds = sel1.odds * sel2.odds * sel3.odds

            # Check if within target range
            if min_odds <= combined_odds <= max_odds:
                combined_probability = sel1.probability * sel2.probability * sel3.probability
                combined_confidence = (sel1.confidence + sel2.confidence + sel3.confidence) / 3

                # More conservative filters for trebles
                if combined_confidence >= 0.65 and combined_probability >= 0.15:
                    expected_value = (combined_probability * combined_odds) - 1

                    if expected_value > 0.03:  # At least 3% positive expected value
                        trebles.append({
                            "id": f"treble_{sel1.match_id}_{sel2.match_id}_{sel3.match_id}",
                            "type": "treble",
                            "selections": [
                                {
                                    "match_id": sel.match_id,
                                    "match_name": sel.match_name,
                                    "market": sel.market,
                                    "selection": sel.selection,
                                    "odds": sel.odds,
                                    "probability": sel.probability
                                } for sel in combo
                            ],
                            "combined_odds": round(combined_odds, 2),
                            "combined_probability": round(combined_probability, 4),
                            "combined_confidence": round(combined_confidence, 3),
                            "expected_value": round(expected_value, 4),
                            "kelly_percentage": min(expected_value / (combined_odds - 1), 0.10),
                            "risk_level": self._calculate_risk_level(combined_confidence, len(combo)),
                            "diversification_score": self._calculate_diversification(combo)
                        })

        # Sort by expected value descending
        trebles.sort(key=lambda x: x["expected_value"], reverse=True)
        return trebles[:15]  # Return top 15

    async def _generate_multiples(self, selections: List[BetSelection], min_odds: float, max_odds: float, size: int) -> List[Dict]:
        """Generate multiple bet combinations (4+ selections)"""
        multiples = []

        for combo in itertools.combinations(selections, size):
            # Skip if any matches are the same
            match_ids = {sel.match_id for sel in combo}
            if len(match_ids) != size:
                continue

            # Calculate combined odds
            combined_odds = 1.0
            for sel in combo:
                combined_odds *= sel.odds

            # Check if within target range
            if min_odds <= combined_odds <= max_odds:
                combined_probability = 1.0
                for sel in combo:
                    combined_probability *= sel.probability

                combined_confidence = sum(sel.confidence for sel in combo) / len(combo)

                # Very conservative filters for multiples
                if combined_confidence >= 0.70 and combined_probability >= 0.08:
                    expected_value = (combined_probability * combined_odds) - 1

                    if expected_value > 0.02:  # At least 2% positive expected value
                        multiples.append({
                            "id": f"multiple_{size}_{'_'.join(str(sel.match_id) for sel in combo)}",
                            "type": f"{size}-fold",
                            "selections": [
                                {
                                    "match_id": sel.match_id,
                                    "match_name": sel.match_name,
                                    "market": sel.market,
                                    "selection": sel.selection,
                                    "odds": sel.odds,
                                    "probability": sel.probability
                                } for sel in combo
                            ],
                            "combined_odds": round(combined_odds, 2),
                            "combined_probability": round(combined_probability, 4),
                            "combined_confidence": round(combined_confidence, 3),
                            "expected_value": round(expected_value, 4),
                            "kelly_percentage": min(expected_value / (combined_odds - 1), 0.05),
                            "risk_level": self._calculate_risk_level(combined_confidence, len(combo)),
                            "diversification_score": self._calculate_diversification(combo)
                        })

        # Sort by expected value descending
        multiples.sort(key=lambda x: x["expected_value"], reverse=True)
        return multiples[:10]  # Return top 10

    def _generate_single_bets(self, selections: List[BetSelection], min_odds: float, max_odds: float) -> List[Dict]:
        """Generate high-value single bet recommendations"""
        singles = []

        for sel in selections:
            if min_odds <= sel.odds <= max_odds:
                expected_value = (sel.probability * sel.odds) - 1

                if expected_value > 0.08:  # At least 8% positive expected value for singles
                    singles.append({
                        "match_id": sel.match_id,
                        "match_name": sel.match_name,
                        "market": sel.market,
                        "selection": sel.selection,
                        "odds": sel.odds,
                        "probability": sel.probability,
                        "confidence": sel.confidence,
                        "expected_value": round(expected_value, 4),
                        "kelly_percentage": min(expected_value / (sel.odds - 1), 0.25),
                        "risk_level": "LOW" if sel.confidence > 0.8 else ("MEDIUM" if sel.confidence > 0.7 else "HIGH")
                    })

        # Sort by expected value descending
        singles.sort(key=lambda x: x["expected_value"], reverse=True)
        return singles[:10]

    def _check_correlation(self, sel1: BetSelection, sel2: BetSelection) -> Dict:
        """Check for correlation between two selections"""
        correlation_risk = "LOW"
        correlation_note = "No significant correlation detected"

        # Same match different markets (high correlation)
        if sel1.match_id == sel2.match_id:
            correlation_risk = "HIGH"
            correlation_note = "Same match - selections are correlated"

        # Goals and BTTS correlation
        elif (sel1.market == "Total Goals" and sel2.market == "BTTS") or \
             (sel1.market == "BTTS" and sel2.market == "Total Goals"):
            if (sel1.selection in ["Over 2.5", "Over 3.5"] and sel2.selection == "Yes") or \
               (sel2.selection in ["Over 2.5", "Over 3.5"] and sel1.selection == "Yes"):
                correlation_risk = "MEDIUM"
                correlation_note = "Goals and BTTS selections may be correlated"

        return {
            "risk": correlation_risk,
            "note": correlation_note
        }

    def _calculate_risk_level(self, confidence: float, num_selections: int) -> str:
        """Calculate overall risk level for a combination"""
        if confidence >= 0.75 and num_selections <= 2:
            return "LOW"
        elif confidence >= 0.65 and num_selections <= 3:
            return "MEDIUM"
        else:
            return "HIGH"

    def _calculate_diversification(self, selections: Tuple[BetSelection, ...]) -> float:
        """Calculate diversification score (0-1, higher is better)"""
        # Count unique markets
        unique_markets = len(set(sel.market for sel in selections))

        # Count unique leagues (if available)
        # For now, assume all matches are from different leagues
        unique_leagues = len(set(sel.match_id for sel in selections))

        # Diversification score
        market_score = unique_markets / len(selections)
        league_score = 1.0  # Assume good league diversification

        return round((market_score + league_score) / 2, 2)

    def _analyze_market_distribution(self, selections: List[BetSelection]) -> Dict:
        """Analyze distribution of selections across markets"""
        if not selections:
            return {}

        market_counts = {}
        for sel in selections:
            market_counts[sel.market] = market_counts.get(sel.market, 0) + 1

        total = len(selections)
        return {
            market: {
                "count": count,
                "percentage": round((count / total) * 100, 1)
            }
            for market, count in market_counts.items()
        }

    def _assess_daily_risk(self, selections: List[BetSelection]) -> Dict:
        """Assess overall risk for the day's selections"""
        if not selections:
            return {"overall_risk": "HIGH", "factors": ["No selections available"]}

        # Calculate average confidence
        avg_confidence = np.mean([sel.confidence for sel in selections])

        # Check for over-concentration in specific markets
        market_dist = self._analyze_market_distribution(selections)
        max_market_percentage = max(market["percentage"] for market in market_dist.values()) if market_dist else 0

        risk_factors = []
        risk_score = 0.0

        if avg_confidence < 0.65:
            risk_factors.append("Low average confidence across selections")
            risk_score += 0.3

        if max_market_percentage > 60:
            risk_factors.append("Over-concentration in single market type")
            risk_score += 0.2

        if len(selections) < 5:
            risk_factors.append("Limited number of quality selections")
            risk_score += 0.1

        # Check time concentration (all matches at similar times)
        match_hours = [sel.match_date.hour for sel in selections]
        hour_variance = np.var(match_hours) if len(match_hours) > 1 else 24

        if hour_variance < 4:  # All matches within similar timeframes
            risk_factors.append("Matches concentrated in similar time periods")
            risk_score += 0.1

        overall_risk = "LOW" if risk_score < 0.2 else ("MEDIUM" if risk_score < 0.5 else "HIGH")

        return {
            "overall_risk": overall_risk,
            "risk_score": round(risk_score, 2),
            "factors": risk_factors,
            "avg_confidence": round(avg_confidence, 3),
            "selection_count": len(selections),
            "market_concentration": f"{max_market_percentage}%" if market_dist else "N/A"
        }