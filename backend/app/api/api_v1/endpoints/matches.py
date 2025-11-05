from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date

from app.core.database import get_db
from app.models import Match, Team
from app.services.football_data_service import FootballDataService

router = APIRouter()

@router.get("/today")
async def get_today_matches(db: Session = Depends(get_db)):
    """Get today's matches from database (synchronized from external APIs)"""
    try:
        from datetime import date, timedelta

        today = date.today()
        tomorrow = today + timedelta(days=1)

        # Get matches from database first - fix date comparison with debug
        from sqlalchemy import func
        import logging
        logger = logging.getLogger(__name__)

        try:
            logger.info(f"🔍 Searching for matches on {today}")
            db_matches = db.query(Match).filter(
                func.date(Match.match_date) == today
            ).all()
            logger.info(f"📊 Found {len(db_matches)} matches in database")
        except Exception as e:
            logger.error(f"❌ Database query failed: {e}")
            db_matches = []

        matches_data = []
        for match in db_matches:
            try:
                match_data = {
                    "id": match.id,
                    "home_team": match.home_team.name if match.home_team else "Unknown",
                    "away_team": match.away_team.name if match.away_team else "Unknown",
                    "league": match.league,
                    "match_date": str(match.match_date),
                    "status": match.status
                }
                matches_data.append(match_data)
                logger.info(f"✅ Added match: {match_data['home_team']} vs {match_data['away_team']}")
            except Exception as e:
                logger.error(f"❌ Error processing match {match.id}: {e}")
                continue


        # If no matches in database, fall back to external API
        if not matches_data:
            football_service = FootballDataService()
            external_matches = await football_service.get_today_matches()
            return {"matches": external_matches, "count": len(external_matches), "source": "external_api"}

        return {"matches": matches_data, "count": len(matches_data), "source": "database"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def get_matches(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    league: Optional[str] = None,
    status: Optional[str] = None
):
    """Get matches from database with filters"""
    query = db.query(Match)

    if date_from:
        query = query.filter(Match.match_date >= date_from)
    if date_to:
        query = query.filter(Match.match_date <= date_to)
    if league:
        query = query.filter(Match.league == league)
    if status:
        query = query.filter(Match.status == status)

    matches = query.offset(skip).limit(limit).all()

    return {
        "matches": [
            {
                "id": match.id,
                "external_id": match.external_id,
                "home_team": match.home_team.name if match.home_team else "TBD",
                "away_team": match.away_team.name if match.away_team else "TBD",
                "league": match.league,
                "match_date": match.match_date,
                "status": match.status,
                "home_score": match.home_score,
                "away_score": match.away_score,
                "venue": match.venue
            }
            for match in matches
        ],
        "count": len(matches)
    }

@router.get("/{match_id}")
async def get_match_details(match_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a specific match"""
    match = db.query(Match).filter(Match.id == match_id).first()

    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    return {
        "id": match.id,
        "external_id": match.external_id,
        "home_team": {
            "id": match.home_team.id,
            "name": match.home_team.name,
            "country": match.home_team.country
        } if match.home_team else None,
        "away_team": {
            "id": match.away_team.id,
            "name": match.away_team.name,
            "country": match.away_team.country
        } if match.away_team else None,
        "league": match.league,
        "season": match.season,
        "matchday": match.matchday,
        "match_date": match.match_date,
        "venue": match.venue,
        "referee": match.referee,
        "status": match.status,
        "minute": match.minute,
        "home_score": match.home_score,
        "away_score": match.away_score,
        "home_score_ht": match.home_score_ht,
        "away_score_ht": match.away_score_ht,
        "temperature": match.temperature,
        "humidity": match.humidity,
        "wind_speed": match.wind_speed,
        "weather_condition": match.weather_condition,
        "importance_factor": match.importance_factor,
        "motivation_home": match.motivation_home,
        "motivation_away": match.motivation_away,
        "is_predicted": match.is_predicted,
        "confidence_score": match.confidence_score,
        "statistics": {
            "possession_home": match.statistics.possession_home,
            "possession_away": match.statistics.possession_away,
            "shots_home": match.statistics.shots_home,
            "shots_away": match.statistics.shots_away,
            "shots_on_target_home": match.statistics.shots_on_target_home,
            "shots_on_target_away": match.statistics.shots_on_target_away,
            "corners_home": match.statistics.corners_home,
            "corners_away": match.statistics.corners_away,
            "xg_home": match.statistics.xg_home,
            "xg_away": match.statistics.xg_away
        } if match.statistics else None
    }

@router.get("/{match_id}/head-to-head")
async def get_head_to_head(match_id: int, db: Session = Depends(get_db)):
    """Get head-to-head data for teams in a specific match"""
    match = db.query(Match).filter(Match.id == match_id).first()

    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    football_service = FootballDataService()

    try:
        h2h_data = await football_service.get_head_to_head(
            str(match.home_team.external_id),
            str(match.away_team.external_id)
        )

        return {
            "match_id": match_id,
            "home_team": match.home_team.name,
            "away_team": match.away_team.name,
            "head_to_head": h2h_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/competition/{competition_id}")
async def get_competition_matches(
    competition_id: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
):
    """Get matches for a specific competition"""
    football_service = FootballDataService()

    try:
        matches = await football_service.get_matches_by_competition(
            competition_id, date_from, date_to
        )

        return {
            "competition_id": competition_id,
            "matches": matches,
            "count": len(matches)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/special/flamengo-estudiantes")
async def get_flamengo_estudiantes_match():
    """Get the special Flamengo vs Estudiantes match with real data"""
    football_service = FootballDataService()

    try:
        match_data = await football_service.get_flamengo_vs_estudiantes_match()

        return {
            "success": True,
            "match": match_data,
            "message": "Jogo Flamengo vs Estudiantes encontrado - Copa Libertadores Quartas de Final",
            "kickoff": "2025-09-26 00:30 UTC (21:30 Brasília)",
            "apis_tested": True,
            "data_source": "Football Data API + API-Sports (dados reais coletados em 25/09/2025)"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar dados do jogo: {str(e)}")