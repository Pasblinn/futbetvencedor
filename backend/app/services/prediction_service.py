import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import Team, Match, MatchStatistics, Prediction, Player, PlayerInjury
from app.services.analytics_service import AnalyticsService
from app.services.weather_service import WeatherService
from app.services.odds_service import OddsService
from app.services.real_prediction_engine import RealPredictionEngine
import math
from scipy import stats

class PredictionService:
    def __init__(self, db: Session = None):
        self.db = db
        if db:
            self.analytics = AnalyticsService(db)
        self.weather_service = WeatherService()
        self.odds_service = OddsService()

        # 🧠 NOVO MOTOR DE PREDIÇÕES REAIS
        self.real_engine = RealPredictionEngine(db)

    async def generate_real_time_prediction(self, match_id: int) -> Dict:
        """
        🚀 NOVA FUNÇÃO PRINCIPAL - Gera predições com dados AO VIVO
        Usa APIs reais: Football-Data.org + The Odds API + análise estatística avançada
        """
        print(f"🚀 Iniciando predição em tempo real para Match ID: {match_id}")

        # Buscar dados do jogo na base de dados
        match = self.db.query(Match).filter(Match.id == match_id).first()
        if not match:
            return await self._generate_prediction_from_external_data(str(match_id))

        # Usar motor real com dados AO VIVO
        real_prediction = await self.real_engine.generate_real_prediction(
            match_id=str(match_id),
            home_team_id=str(match.home_team_id) if match.home_team_id else "unknown",
            away_team_id=str(match.away_team_id) if match.away_team_id else "unknown",
            match_date=match.match_date,
            venue=match.venue
        )

        # Adicionar metadados do sistema
        real_prediction.update({
            "system_version": "REAL_TIME_V2.0",
            "database_match_id": match_id,
            "home_team_name": match.home_team.name if match.home_team else "Unknown",
            "away_team_name": match.away_team.name if match.away_team else "Unknown",
            "competition": match.competition if hasattr(match, 'competition') else "Unknown",
            "venue": match.venue,
            "match_date": match.match_date.isoformat() if match.match_date else None,
            "live_data_timestamp": datetime.now().isoformat()
        })

        print(f"✅ Predição real-time gerada com sucesso para {match.home_team.name if match.home_team else 'Home'} vs {match.away_team.name if match.away_team else 'Away'}")
        return real_prediction

    async def _generate_prediction_from_external_data(self, external_match_id: str) -> Dict:
        """
        🌐 Gera predição para jogos não encontrados na base local
        Usa apenas dados das APIs externas
        """
        print(f"🌐 Gerando predição com dados externos para Match ID: {external_match_id}")

        try:
            # Buscar dados do jogo diretamente das APIs
            # Por enquanto, retornar predição baseada em IDs externos
            return await self.real_engine.generate_real_prediction(
                match_id=external_match_id,
                home_team_id="external_home",
                away_team_id="external_away",
                match_date=datetime.now(),
                venue="Unknown Venue"
            )
        except Exception as e:
            print(f"❌ Erro na predição externa: {str(e)}")
            return {
                "error": "External data prediction failed",
                "match_id": external_match_id,
                "fallback_mode": True,
                "message": "Use generate_match_prediction() para dados da base local"
            }

    async def generate_match_prediction(self, match_id: int) -> Dict:
        """Generate comprehensive prediction for a match"""
        match = self.db.query(Match).filter(Match.id == match_id).first()
        if not match:
            raise ValueError(f"Match with ID {match_id} not found")

        # Gather all analysis components
        home_form = await self.analytics.analyze_team_form(match.home_team_id)
        away_form = await self.analytics.analyze_team_form(match.away_team_id)
        h2h_analysis = await self.analytics.analyze_head_to_head(match.home_team_id, match.away_team_id)
        home_xg = await self.analytics.calculate_xg_metrics(match.home_team_id)
        away_xg = await self.analytics.calculate_xg_metrics(match.away_team_id)
        home_corners = await self.analytics.analyze_corners_performance(match.home_team_id)
        away_corners = await self.analytics.analyze_corners_performance(match.away_team_id)

        # Get weather impact if venue is available
        weather_impact = {}
        if match.venue:
            try:
                weather_impact = await self.weather_service.get_match_weather(
                    match.venue.split(",")[0].strip(),
                    match.home_team.country or "GB",
                    match.match_date
                )
            except Exception:
                weather_impact = {"impact_assessment": {"overall_score": 0.0}}

        # Calculate injury impact
        injury_impact = await self._calculate_injury_impact(match.home_team_id, match.away_team_id)

        # Generate predictions for different markets
        prediction_data = {
            "match_id": match_id,
            "home_team": match.home_team.name,
            "away_team": match.away_team.name,
            "match_date": match.match_date.isoformat(),
            "analysis_timestamp": datetime.now().isoformat(),

            # Core predictions
            "match_outcome": await self._predict_match_outcome(home_form, away_form, h2h_analysis, home_xg, away_xg, weather_impact, injury_impact),
            "goals_prediction": await self._predict_goals(home_form, away_form, h2h_analysis, home_xg, away_xg, weather_impact),
            "btts_prediction": await self._predict_btts(home_form, away_form, h2h_analysis, home_xg, away_xg),
            "corners_prediction": await self._predict_corners(home_corners, away_corners, weather_impact),

            # Analysis components
            "form_analysis": {
                "home": home_form,
                "away": away_form
            },
            "h2h_analysis": h2h_analysis,
            "xg_analysis": {
                "home": home_xg,
                "away": away_xg
            },
            "weather_impact": weather_impact,
            "injury_impact": injury_impact,

            # Confidence and validation
            "overall_confidence": 0.0,
            "key_factors": [],
            "risk_assessment": {}
        }

        # Calculate overall confidence
        prediction_data["overall_confidence"] = self._calculate_overall_confidence(prediction_data)

        # Identify key factors
        prediction_data["key_factors"] = self._identify_key_factors(prediction_data)

        # Risk assessment
        prediction_data["risk_assessment"] = self._assess_prediction_risk(prediction_data)

        return prediction_data

    async def _predict_match_outcome(self, home_form: Dict, away_form: Dict, h2h: Dict, home_xg: Dict, away_xg: Dict, weather: Dict, injury: Dict) -> Dict:
        """Predict 1X2 outcome with probabilities"""

        # Base probabilities (home advantage)
        home_prob = 0.45
        draw_prob = 0.25
        away_prob = 0.30

        # Form adjustment
        home_form_factor = home_form.get("form_trend", 1.5) / 3.0  # Normalize to 0-1
        away_form_factor = away_form.get("form_trend", 1.5) / 3.0

        form_adjustment = (home_form_factor - away_form_factor) * 0.15

        # H2H adjustment
        h2h_adjustment = 0.0
        if h2h.get("matches_analyzed", 0) >= 3:
            h2h_home_rate = h2h.get("team1_win_rate", 0.33)
            h2h_away_rate = h2h.get("team2_win_rate", 0.33)
            h2h_adjustment = (h2h_home_rate - h2h_away_rate) * 0.1

        # xG adjustment
        xg_adjustment = 0.0
        if home_xg.get("avg_xg_for", 0) > 0 and away_xg.get("avg_xg_for", 0) > 0:
            home_xg_strength = home_xg.get("avg_xg_for", 1.0) - home_xg.get("avg_xg_against", 1.0)
            away_xg_strength = away_xg.get("avg_xg_for", 1.0) - away_xg.get("avg_xg_against", 1.0)
            xg_adjustment = (home_xg_strength - away_xg_strength) * 0.1

        # Weather adjustment
        weather_adjustment = 0.0
        weather_impact_score = weather.get("impact_assessment", {}).get("overall_score", 0.0)
        if weather_impact_score > 0.5:
            # Bad weather typically favors draws and defensive teams
            weather_adjustment = -0.05  # Slightly favor draw

        # Injury adjustment
        injury_adjustment = injury.get("net_impact", 0.0) * 0.1

        # Apply adjustments
        total_adjustment = form_adjustment + h2h_adjustment + xg_adjustment + weather_adjustment + injury_adjustment

        home_prob += total_adjustment
        away_prob -= total_adjustment * 0.7  # Slightly less impact on away team
        draw_prob += total_adjustment * 0.3   # Remaining goes to draw

        # Normalize probabilities
        total = home_prob + draw_prob + away_prob
        home_prob /= total
        draw_prob /= total
        away_prob /= total

        # Calculate odds
        home_odds = 1 / home_prob if home_prob > 0.01 else 100
        draw_odds = 1 / draw_prob if draw_prob > 0.01 else 100
        away_odds = 1 / away_prob if away_prob > 0.01 else 100

        return {
            "home_win_probability": round(home_prob, 4),
            "draw_probability": round(draw_prob, 4),
            "away_win_probability": round(away_prob, 4),
            "home_win_odds": round(home_odds, 2),
            "draw_odds": round(draw_odds, 2),
            "away_win_odds": round(away_odds, 2),
            "predicted_outcome": "1" if home_prob > max(draw_prob, away_prob) else ("X" if draw_prob > away_prob else "2"),
            "confidence": max(home_prob, draw_prob, away_prob),
            "factors_considered": {
                "form_adjustment": round(form_adjustment, 4),
                "h2h_adjustment": round(h2h_adjustment, 4),
                "xg_adjustment": round(xg_adjustment, 4),
                "weather_adjustment": round(weather_adjustment, 4),
                "injury_adjustment": round(injury_adjustment, 4)
            }
        }

    async def _predict_goals(self, home_form: Dict, away_form: Dict, h2h: Dict, home_xg: Dict, away_xg: Dict, weather: Dict) -> Dict:
        """Predict total goals and Over/Under markets"""

        # Base expected goals from form
        home_goals_form = home_form.get("goals_per_game", 1.2)
        home_conceded_form = home_form.get("goals_conceded_per_game", 1.2)
        away_goals_form = away_form.get("goals_per_game", 1.2)
        away_conceded_form = away_form.get("goals_conceded_per_game", 1.2)

        # Expected goals calculation
        expected_home_goals = (home_goals_form + away_conceded_form) / 2
        expected_away_goals = (away_goals_form + home_conceded_form) / 2

        # xG adjustment
        if home_xg.get("avg_xg_for", 0) > 0 and away_xg.get("avg_xg_for", 0) > 0:
            expected_home_goals = (expected_home_goals + home_xg.get("avg_xg_for", 0)) / 2
            expected_away_goals = (expected_away_goals + away_xg.get("avg_xg_for", 0)) / 2

        # H2H adjustment
        if h2h.get("avg_goals_per_match", 0) > 0:
            h2h_avg = h2h.get("avg_goals_per_match", 2.5)
            current_avg = expected_home_goals + expected_away_goals
            expected_total = (current_avg + h2h_avg) / 2
            ratio = expected_total / current_avg if current_avg > 0 else 1
            expected_home_goals *= ratio
            expected_away_goals *= ratio

        # Weather adjustment
        weather_impact = weather.get("impact_assessment", {}).get("overall_score", 0.0)
        if weather_impact > 0.3:
            # Bad weather reduces goals
            weather_factor = 1.0 - (weather_impact * 0.3)
            expected_home_goals *= weather_factor
            expected_away_goals *= weather_factor

        total_expected_goals = expected_home_goals + expected_away_goals

        # Calculate Over/Under probabilities using Poisson distribution
        over_1_5_prob = 1 - stats.poisson.cdf(1, total_expected_goals)
        over_2_5_prob = 1 - stats.poisson.cdf(2, total_expected_goals)
        over_3_5_prob = 1 - stats.poisson.cdf(3, total_expected_goals)

        return {
            "expected_home_goals": round(expected_home_goals, 2),
            "expected_away_goals": round(expected_away_goals, 2),
            "expected_total_goals": round(total_expected_goals, 2),
            "over_1_5_probability": round(over_1_5_prob, 4),
            "under_1_5_probability": round(1 - over_1_5_prob, 4),
            "over_2_5_probability": round(over_2_5_prob, 4),
            "under_2_5_probability": round(1 - over_2_5_prob, 4),
            "over_3_5_probability": round(over_3_5_prob, 4),
            "under_3_5_probability": round(1 - over_3_5_prob, 4),
            "over_1_5_odds": round(1 / over_1_5_prob if over_1_5_prob > 0.01 else 100, 2),
            "under_1_5_odds": round(1 / (1 - over_1_5_prob) if (1 - over_1_5_prob) > 0.01 else 100, 2),
            "over_2_5_odds": round(1 / over_2_5_prob if over_2_5_prob > 0.01 else 100, 2),
            "under_2_5_odds": round(1 / (1 - over_2_5_prob) if (1 - over_2_5_prob) > 0.01 else 100, 2)
        }

    async def _predict_btts(self, home_form: Dict, away_form: Dict, h2h: Dict, home_xg: Dict, away_xg: Dict) -> Dict:
        """Predict Both Teams to Score"""

        # Base scoring rates
        home_scoring_rate = min(home_form.get("goals_per_game", 1.0) / 1.5, 0.9)
        away_scoring_rate = min(away_form.get("goals_per_game", 1.0) / 1.5, 0.9)

        # Defensive records
        home_clean_sheet_rate = home_form.get("clean_sheet_rate", 0.3)
        away_clean_sheet_rate = away_form.get("clean_sheet_rate", 0.3)

        # Calculate BTTS probability
        btts_prob = home_scoring_rate * away_scoring_rate * (1 - home_clean_sheet_rate * 0.5) * (1 - away_clean_sheet_rate * 0.5)

        # H2H adjustment
        if h2h.get("btts_rate", 0) > 0:
            btts_prob = (btts_prob + h2h.get("btts_rate", 0.5)) / 2

        # xG adjustment
        if home_xg.get("avg_xg_for", 0) > 0 and away_xg.get("avg_xg_for", 0) > 0:
            xg_btts_prob = min(home_xg.get("avg_xg_for", 0) / 1.5, 0.9) * min(away_xg.get("avg_xg_for", 0) / 1.5, 0.9)
            btts_prob = (btts_prob + xg_btts_prob) / 2

        btts_prob = max(0.05, min(0.95, btts_prob))  # Keep within reasonable bounds

        return {
            "btts_yes_probability": round(btts_prob, 4),
            "btts_no_probability": round(1 - btts_prob, 4),
            "btts_yes_odds": round(1 / btts_prob if btts_prob > 0.01 else 100, 2),
            "btts_no_odds": round(1 / (1 - btts_prob) if (1 - btts_prob) > 0.01 else 100, 2),
            "predicted_outcome": "Yes" if btts_prob > 0.5 else "No",
            "confidence": max(btts_prob, 1 - btts_prob)
        }

    async def _predict_corners(self, home_corners: Dict, away_corners: Dict, weather: Dict) -> Dict:
        """Predict corner kick totals"""

        home_avg = home_corners.get("avg_corners_for", 5.0) + away_corners.get("avg_corners_against", 5.0)
        away_avg = away_corners.get("avg_corners_for", 5.0) + home_corners.get("avg_corners_against", 5.0)

        expected_total_corners = (home_avg + away_avg) / 4  # Average out the calculations

        # Weather adjustment
        weather_impact = weather.get("impact_assessment", {}).get("overall_score", 0.0)
        if weather_impact > 0.3:
            # Bad weather can increase corners due to defensive play
            expected_total_corners *= (1 + weather_impact * 0.2)

        # Calculate probabilities using Poisson distribution
        over_8_5_prob = 1 - stats.poisson.cdf(8, expected_total_corners)
        over_9_5_prob = 1 - stats.poisson.cdf(9, expected_total_corners)
        over_10_5_prob = 1 - stats.poisson.cdf(10, expected_total_corners)

        return {
            "expected_total_corners": round(expected_total_corners, 1),
            "over_8_5_probability": round(over_8_5_prob, 4),
            "under_8_5_probability": round(1 - over_8_5_prob, 4),
            "over_9_5_probability": round(over_9_5_prob, 4),
            "under_9_5_probability": round(1 - over_9_5_prob, 4),
            "over_10_5_probability": round(over_10_5_prob, 4),
            "under_10_5_probability": round(1 - over_10_5_prob, 4),
            "over_8_5_odds": round(1 / over_8_5_prob if over_8_5_prob > 0.01 else 100, 2),
            "over_9_5_odds": round(1 / over_9_5_prob if over_9_5_prob > 0.01 else 100, 2),
            "over_10_5_odds": round(1 / over_10_5_prob if over_10_5_prob > 0.01 else 100, 2)
        }

    async def _calculate_injury_impact(self, home_team_id: int, away_team_id: int) -> Dict:
        """Calculate impact of injuries on team performance"""

        # Get active injuries for both teams
        home_injuries = self.db.query(PlayerInjury).join(Player).filter(
            Player.team_id == home_team_id,
            PlayerInjury.is_active == True
        ).all()

        away_injuries = self.db.query(PlayerInjury).join(Player).filter(
            Player.team_id == away_team_id,
            PlayerInjury.is_active == True
        ).all()

        home_impact = sum(injury.impact_on_team or 0 for injury in home_injuries)
        away_impact = sum(injury.impact_on_team or 0 for injury in away_injuries)

        return {
            "home_injuries_count": len(home_injuries),
            "away_injuries_count": len(away_injuries),
            "home_impact": round(home_impact, 3),
            "away_impact": round(away_impact, 3),
            "net_impact": round(away_impact - home_impact, 3),  # Positive favors home team
            "injury_details": {
                "home": [
                    {
                        "player_name": injury.player.name,
                        "injury_type": injury.injury_type,
                        "severity": injury.severity,
                        "impact": injury.impact_on_team
                    } for injury in home_injuries
                ],
                "away": [
                    {
                        "player_name": injury.player.name,
                        "injury_type": injury.injury_type,
                        "severity": injury.severity,
                        "impact": injury.impact_on_team
                    } for injury in away_injuries
                ]
            }
        }

    def _calculate_overall_confidence(self, prediction_data: Dict) -> float:
        """Calculate overall confidence score for the prediction"""
        confidence_factors = []

        # Form analysis confidence
        home_form = prediction_data["form_analysis"]["home"]
        away_form = prediction_data["form_analysis"]["away"]

        if home_form.get("matches_analyzed", 0) >= 10 and away_form.get("matches_analyzed", 0) >= 10:
            confidence_factors.append(0.8)
        elif home_form.get("matches_analyzed", 0) >= 5 and away_form.get("matches_analyzed", 0) >= 5:
            confidence_factors.append(0.6)
        else:
            confidence_factors.append(0.3)

        # H2H confidence
        h2h_matches = prediction_data["h2h_analysis"].get("matches_analyzed", 0)
        if h2h_matches >= 5:
            confidence_factors.append(0.7)
        elif h2h_matches >= 3:
            confidence_factors.append(0.5)
        else:
            confidence_factors.append(0.2)

        # xG data availability
        home_xg = prediction_data["xg_analysis"]["home"]
        away_xg = prediction_data["xg_analysis"]["away"]

        if not home_xg.get("error") and not away_xg.get("error"):
            confidence_factors.append(0.8)
        else:
            confidence_factors.append(0.4)

        # Weather data confidence
        if prediction_data["weather_impact"].get("impact_assessment"):
            confidence_factors.append(0.6)
        else:
            confidence_factors.append(0.3)

        return round(sum(confidence_factors) / len(confidence_factors), 3)

    def _identify_key_factors(self, prediction_data: Dict) -> List[str]:
        """Identify the most important factors for this prediction"""
        factors = []

        # Check form differences
        home_form = prediction_data["form_analysis"]["home"]
        away_form = prediction_data["form_analysis"]["away"]

        home_form_trend = home_form.get("form_trend", 1.5)
        away_form_trend = away_form.get("form_trend", 1.5)

        if abs(home_form_trend - away_form_trend) > 0.5:
            if home_form_trend > away_form_trend:
                factors.append(f"Home team in significantly better form ({home_form.get('form_string', 'N/A')} vs {away_form.get('form_string', 'N/A')})")
            else:
                factors.append(f"Away team in significantly better form ({away_form.get('form_string', 'N/A')} vs {home_form.get('form_string', 'N/A')})")

        # Check H2H dominance
        h2h = prediction_data["h2h_analysis"]
        if h2h.get("matches_analyzed", 0) >= 3:
            if h2h.get("team1_win_rate", 0) > 0.6:
                factors.append(f"Home team dominates H2H record ({h2h.get('team1_wins', 0)}-{h2h.get('draws', 0)}-{h2h.get('team2_wins', 0)})")
            elif h2h.get("team2_win_rate", 0) > 0.6:
                factors.append(f"Away team dominates H2H record ({h2h.get('team2_wins', 0)}-{h2h.get('draws', 0)}-{h2h.get('team1_wins', 0)})")

        # Check weather impact
        weather_impact = prediction_data["weather_impact"].get("impact_assessment", {}).get("overall_score", 0)
        if weather_impact > 0.5:
            factors.append("Significant weather impact expected - favors defensive play")

        # Check injury impact
        injury_impact = prediction_data["injury_impact"].get("net_impact", 0)
        if abs(injury_impact) > 0.2:
            if injury_impact > 0:
                factors.append("Key injuries affecting away team")
            else:
                factors.append("Key injuries affecting home team")

        return factors[:5]  # Return top 5 factors

    def _assess_prediction_risk(self, prediction_data: Dict) -> Dict:
        """Assess the risk level of the predictions"""
        risk_factors = []
        risk_score = 0.0

        # Low data availability increases risk
        home_matches = prediction_data["form_analysis"]["home"].get("matches_analyzed", 0)
        away_matches = prediction_data["form_analysis"]["away"].get("matches_analyzed", 0)

        if home_matches < 5 or away_matches < 5:
            risk_factors.append("Limited recent form data")
            risk_score += 0.3

        # No H2H data increases risk
        if prediction_data["h2h_analysis"].get("matches_analyzed", 0) < 3:
            risk_factors.append("Limited head-to-head history")
            risk_score += 0.2

        # High weather impact increases risk
        weather_impact = prediction_data["weather_impact"].get("impact_assessment", {}).get("overall_score", 0)
        if weather_impact > 0.6:
            risk_factors.append("Severe weather conditions")
            risk_score += 0.4

        # Significant injuries increase risk
        injury_impact = abs(prediction_data["injury_impact"].get("net_impact", 0))
        if injury_impact > 0.3:
            risk_factors.append("Major injury concerns")
            risk_score += 0.3

        # Close predictions are riskier
        outcome_pred = prediction_data["match_outcome"]
        max_prob = max(
            outcome_pred.get("home_win_probability", 0),
            outcome_pred.get("draw_probability", 0),
            outcome_pred.get("away_win_probability", 0)
        )

        if max_prob < 0.45:
            risk_factors.append("Very close match prediction")
            risk_score += 0.4

        risk_level = "LOW" if risk_score < 0.3 else ("MEDIUM" if risk_score < 0.7 else "HIGH")

        return {
            "risk_score": round(risk_score, 2),
            "risk_level": risk_level,
            "risk_factors": risk_factors
        }