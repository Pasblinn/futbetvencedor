import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import Team, Match, MatchStatistics, TeamStatistics
from app.services.football_data_service import FootballDataService
from app.services.weather_service import WeatherService
import math

class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db
        self.football_service = FootballDataService()
        self.weather_service = WeatherService()

    async def analyze_team_form(self, team_id: int, matches_count: int = 15) -> Dict:
        """Analyze team's recent form from last N matches"""
        team = self.db.query(Team).filter(Team.id == team_id).first()
        if not team:
            raise ValueError(f"Team with ID {team_id} not found")

        # Get recent matches
        recent_matches = self.db.query(Match).filter(
            (Match.home_team_id == team_id) | (Match.away_team_id == team_id),
            Match.status == "FINISHED"
        ).order_by(Match.match_date.desc()).limit(matches_count).all()

        if not recent_matches:
            return self._empty_form_analysis()

        form_data = {
            "matches_analyzed": len(recent_matches),
            "wins": 0,
            "draws": 0,
            "losses": 0,
            "goals_for": 0,
            "goals_against": 0,
            "clean_sheets": 0,
            "matches": []
        }

        for match in recent_matches:
            is_home = match.home_team_id == team_id
            team_score = match.home_score if is_home else match.away_score
            opponent_score = match.away_score if is_home else match.home_score

            # Determine result
            if team_score > opponent_score:
                result = "W"
                form_data["wins"] += 1
            elif team_score == opponent_score:
                result = "D"
                form_data["draws"] += 1
            else:
                result = "L"
                form_data["losses"] += 1

            form_data["goals_for"] += team_score
            form_data["goals_against"] += opponent_score

            if opponent_score == 0:
                form_data["clean_sheets"] += 1

            form_data["matches"].append({
                "date": match.match_date.isoformat(),
                "opponent_id": match.away_team_id if is_home else match.home_team_id,
                "is_home": is_home,
                "result": result,
                "score": f"{team_score}-{opponent_score}",
                "team_score": team_score,
                "opponent_score": opponent_score
            })

        # Calculate metrics
        total_matches = len(recent_matches)
        form_data["win_rate"] = form_data["wins"] / total_matches
        form_data["points"] = form_data["wins"] * 3 + form_data["draws"]
        form_data["points_per_game"] = form_data["points"] / total_matches
        form_data["goals_per_game"] = form_data["goals_for"] / total_matches
        form_data["goals_conceded_per_game"] = form_data["goals_against"] / total_matches
        form_data["goal_difference"] = form_data["goals_for"] - form_data["goals_against"]
        form_data["clean_sheet_rate"] = form_data["clean_sheets"] / total_matches

        # Calculate form trend (weighted recent matches more heavily)
        form_data["form_trend"] = self._calculate_form_trend(form_data["matches"])
        form_data["form_string"] = "".join([m["result"] for m in form_data["matches"][:5]])

        return form_data

    async def analyze_head_to_head(self, team1_id: int, team2_id: int, matches_count: int = 10) -> Dict:
        """Analyze head-to-head record between two teams"""
        h2h_matches = self.db.query(Match).filter(
            ((Match.home_team_id == team1_id) & (Match.away_team_id == team2_id)) |
            ((Match.home_team_id == team2_id) & (Match.away_team_id == team1_id)),
            Match.status == "FINISHED"
        ).order_by(Match.match_date.desc()).limit(matches_count).all()

        if not h2h_matches:
            return self._empty_h2h_analysis()

        h2h_data = {
            "matches_analyzed": len(h2h_matches),
            "team1_wins": 0,
            "draws": 0,
            "team2_wins": 0,
            "team1_goals": 0,
            "team2_goals": 0,
            "matches": []
        }

        for match in h2h_matches:
            team1_is_home = match.home_team_id == team1_id
            team1_score = match.home_score if team1_is_home else match.away_score
            team2_score = match.away_score if team1_is_home else match.home_score

            if team1_score > team2_score:
                h2h_data["team1_wins"] += 1
            elif team1_score == team2_score:
                h2h_data["draws"] += 1
            else:
                h2h_data["team2_wins"] += 1

            h2h_data["team1_goals"] += team1_score
            h2h_data["team2_goals"] += team2_score

            h2h_data["matches"].append({
                "date": match.match_date.isoformat(),
                "team1_is_home": team1_is_home,
                "score": f"{team1_score}-{team2_score}",
                "team1_score": team1_score,
                "team2_score": team2_score
            })

        # Calculate statistics
        total_matches = len(h2h_matches)
        h2h_data["team1_win_rate"] = h2h_data["team1_wins"] / total_matches
        h2h_data["team2_win_rate"] = h2h_data["team2_wins"] / total_matches
        h2h_data["draw_rate"] = h2h_data["draws"] / total_matches
        h2h_data["avg_goals_per_match"] = (h2h_data["team1_goals"] + h2h_data["team2_goals"]) / total_matches
        h2h_data["over_2_5_rate"] = sum(1 for m in h2h_data["matches"] if m["team1_score"] + m["team2_score"] > 2.5) / total_matches
        h2h_data["btts_rate"] = sum(1 for m in h2h_data["matches"] if m["team1_score"] > 0 and m["team2_score"] > 0) / total_matches

        return h2h_data

    async def calculate_xg_metrics(self, team_id: int, matches_count: int = 15) -> Dict:
        """Calculate Expected Goals metrics for a team"""
        recent_matches = self.db.query(Match).join(MatchStatistics).filter(
            (Match.home_team_id == team_id) | (Match.away_team_id == team_id),
            Match.status == "FINISHED"
        ).order_by(Match.match_date.desc()).limit(matches_count).all()

        if not recent_matches:
            return {"error": "No matches with xG data found"}

        xg_data = {
            "matches_analyzed": len(recent_matches),
            "total_xg_for": 0.0,
            "total_xg_against": 0.0,
            "total_goals_for": 0,
            "total_goals_against": 0,
            "matches": []
        }

        for match in recent_matches:
            is_home = match.home_team_id == team_id
            stats = match.statistics

            if stats:
                xg_for = stats.xg_home if is_home else stats.xg_away
                xg_against = stats.xg_away if is_home else stats.xg_home
                goals_for = match.home_score if is_home else match.away_score
                goals_against = match.away_score if is_home else match.home_score

                xg_data["total_xg_for"] += xg_for or 0
                xg_data["total_xg_against"] += xg_against or 0
                xg_data["total_goals_for"] += goals_for
                xg_data["total_goals_against"] += goals_against

                xg_data["matches"].append({
                    "date": match.match_date.isoformat(),
                    "xg_for": xg_for,
                    "xg_against": xg_against,
                    "goals_for": goals_for,
                    "goals_against": goals_against,
                    "xg_difference": (xg_for or 0) - (xg_against or 0)
                })

        # Calculate averages and performance metrics
        matches_count = len(xg_data["matches"])
        if matches_count > 0:
            xg_data["avg_xg_for"] = xg_data["total_xg_for"] / matches_count
            xg_data["avg_xg_against"] = xg_data["total_xg_against"] / matches_count
            xg_data["avg_goals_for"] = xg_data["total_goals_for"] / matches_count
            xg_data["avg_goals_against"] = xg_data["total_goals_against"] / matches_count

            # Performance vs expectation
            xg_data["finishing_efficiency"] = xg_data["total_goals_for"] / max(xg_data["total_xg_for"], 0.1)
            xg_data["defensive_efficiency"] = xg_data["total_xg_against"] / max(xg_data["total_goals_against"], 0.1)

        return xg_data

    async def analyze_corners_performance(self, team_id: int, matches_count: int = 15) -> Dict:
        """Analyze team's corner kick performance"""
        recent_matches = self.db.query(Match).join(MatchStatistics).filter(
            (Match.home_team_id == team_id) | (Match.away_team_id == team_id),
            Match.status == "FINISHED"
        ).order_by(Match.match_date.desc()).limit(matches_count).all()

        if not recent_matches:
            return {"error": "No matches with corner data found"}

        corner_data = {
            "matches_analyzed": len(recent_matches),
            "total_corners_for": 0,
            "total_corners_against": 0,
            "matches": []
        }

        for match in recent_matches:
            is_home = match.home_team_id == team_id
            stats = match.statistics

            if stats:
                corners_for = stats.corners_home if is_home else stats.corners_away
                corners_against = stats.corners_away if is_home else stats.corners_home

                corner_data["total_corners_for"] += corners_for or 0
                corner_data["total_corners_against"] += corners_against or 0

                corner_data["matches"].append({
                    "date": match.match_date.isoformat(),
                    "corners_for": corners_for,
                    "corners_against": corners_against,
                    "total_corners": (corners_for or 0) + (corners_against or 0)
                })

        # Calculate averages
        matches_count = len(corner_data["matches"])
        if matches_count > 0:
            corner_data["avg_corners_for"] = corner_data["total_corners_for"] / matches_count
            corner_data["avg_corners_against"] = corner_data["total_corners_against"] / matches_count
            corner_data["avg_total_corners"] = (corner_data["total_corners_for"] + corner_data["total_corners_against"]) / matches_count

            # Corner betting markets
            over_8_5_matches = sum(1 for m in corner_data["matches"] if m["total_corners"] > 8.5)
            over_9_5_matches = sum(1 for m in corner_data["matches"] if m["total_corners"] > 9.5)
            over_10_5_matches = sum(1 for m in corner_data["matches"] if m["total_corners"] > 10.5)

            corner_data["over_8_5_rate"] = over_8_5_matches / matches_count
            corner_data["over_9_5_rate"] = over_9_5_matches / matches_count
            corner_data["over_10_5_rate"] = over_10_5_matches / matches_count

        return corner_data

    def calculate_elo_rating_change(self, team1_rating: float, team2_rating: float, actual_result: float, k_factor: int = 32) -> Tuple[float, float]:
        """Calculate new Elo ratings based on match result"""
        # Expected score calculation
        expected1 = 1 / (1 + 10 ** ((team2_rating - team1_rating) / 400))
        expected2 = 1 - expected1

        # New ratings
        new_rating1 = team1_rating + k_factor * (actual_result - expected1)
        new_rating2 = team2_rating + k_factor * ((1 - actual_result) - expected2)

        return new_rating1, new_rating2

    def _calculate_form_trend(self, matches: List[Dict]) -> float:
        """Calculate form trend with recent matches weighted more heavily"""
        if not matches:
            return 0.0

        total_weight = 0
        weighted_score = 0

        for i, match in enumerate(matches):
            # Weight decreases as matches get older
            weight = 1.0 / (i + 1)
            total_weight += weight

            if match["result"] == "W":
                score = 3
            elif match["result"] == "D":
                score = 1
            else:
                score = 0

            weighted_score += score * weight

        return weighted_score / total_weight if total_weight > 0 else 0.0

    def _empty_form_analysis(self) -> Dict:
        """Return empty form analysis structure"""
        return {
            "matches_analyzed": 0,
            "wins": 0,
            "draws": 0,
            "losses": 0,
            "goals_for": 0,
            "goals_against": 0,
            "clean_sheets": 0,
            "win_rate": 0.0,
            "points": 0,
            "points_per_game": 0.0,
            "goals_per_game": 0.0,
            "goals_conceded_per_game": 0.0,
            "goal_difference": 0,
            "clean_sheet_rate": 0.0,
            "form_trend": 0.0,
            "form_string": "",
            "matches": []
        }

    def _empty_h2h_analysis(self) -> Dict:
        """Return empty H2H analysis structure"""
        return {
            "matches_analyzed": 0,
            "team1_wins": 0,
            "draws": 0,
            "team2_wins": 0,
            "team1_goals": 0,
            "team2_goals": 0,
            "team1_win_rate": 0.0,
            "team2_win_rate": 0.0,
            "draw_rate": 0.0,
            "avg_goals_per_match": 0.0,
            "over_2_5_rate": 0.0,
            "btts_rate": 0.0,
            "matches": []
        }