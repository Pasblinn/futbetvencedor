from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models import Match, Odds
from app.services.odds_service import OddsService

router = APIRouter()

@router.get("/sports")
async def get_available_sports():
    """Get available sports from odds API"""
    odds_service = OddsService()

    try:
        sports = await odds_service.get_sports()
        return {"sports": sports}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch sports: {str(e)}")

@router.get("/current/{sport}")
async def get_current_odds(
    sport: str = "soccer_epl",
    regions: str = Query("us,uk,eu", description="Comma-separated regions"),
    markets: str = Query("h2h,spreads,totals,btts", description="Comma-separated markets")
):
    """Get current odds for a specific sport"""
    odds_service = OddsService()

    try:
        odds = await odds_service.get_odds(sport, regions, markets)
        return {"sport": sport, "odds": odds, "count": len(odds)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch odds: {str(e)}")

@router.get("/match/{match_external_id}")
async def get_match_odds(match_external_id: str):
    """Get odds for a specific match"""
    odds_service = OddsService()

    try:
        odds = await odds_service.get_match_odds(match_external_id)

        if not odds:
            raise HTTPException(status_code=404, detail="No odds found for this match")

        return {"match_id": match_external_id, "odds": odds}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch match odds: {str(e)}")

@router.get("/match/{match_external_id}/comparison")
async def get_odds_comparison(match_external_id: str):
    """Compare odds across different bookmakers for a match"""
    odds_service = OddsService()

    try:
        comparison = await odds_service.get_bookmaker_comparison(match_external_id)

        if not comparison:
            raise HTTPException(status_code=404, detail="No odds comparison available for this match")

        return comparison

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compare odds: {str(e)}")

@router.get("/match/{match_external_id}/movement")
async def get_odds_movement(match_external_id: str):
    """Track odds movement over time for a match"""
    odds_service = OddsService()

    try:
        movement = await odds_service.track_odds_movement(match_external_id)

        return {
            "match_id": match_external_id,
            "movement_history": movement,
            "data_points": len(movement)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to track odds movement: {str(e)}")

@router.post("/match/{match_external_id}/value-bets")
async def calculate_value_bets(
    match_external_id: str,
    predicted_probabilities: dict
):
    """Calculate value bets based on predicted probabilities"""
    odds_service = OddsService()

    try:
        value_bets = await odds_service.calculate_value_bets(match_external_id, predicted_probabilities)

        return {
            "match_id": match_external_id,
            "predicted_probabilities": predicted_probabilities,
            "value_bets": value_bets,
            "value_bet_count": len(value_bets)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate value bets: {str(e)}")

@router.get("/database/match/{match_id}")
async def get_stored_odds(
    match_id: int,
    db: Session = Depends(get_db),
    bookmaker: Optional[str] = None,
    market: Optional[str] = None
):
    """Get stored odds for a match from database"""
    match = db.query(Match).filter(Match.id == match_id).first()

    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    query = db.query(Odds).filter(Odds.match_id == match_id, Odds.is_active == True)

    if bookmaker:
        query = query.filter(Odds.bookmaker == bookmaker)
    if market:
        query = query.filter(Odds.market == market)

    odds = query.order_by(Odds.odds_timestamp.desc()).all()

    return {
        "match_id": match_id,
        "match": {
            "home_team": match.home_team.name,
            "away_team": match.away_team.name,
            "match_date": match.match_date,
            "status": match.status
        },
        "odds": [
            {
                "id": odd.id,
                "bookmaker": odd.bookmaker,
                "market": odd.market,
                "home_win": odd.home_win,
                "draw": odd.draw,
                "away_win": odd.away_win,
                "over_2_5": odd.over_2_5,
                "under_2_5": odd.under_2_5,
                "btts_yes": odd.btts_yes,
                "btts_no": odd.btts_no,
                "corners_over_9_5": odd.corners_over_9_5,
                "corners_under_9_5": odd.corners_under_9_5,
                "odds_timestamp": odd.odds_timestamp,
                "additional_markets": odd.additional_markets
            }
            for odd in odds
        ],
        "count": len(odds)
    }

@router.get("/database/bookmakers")
async def get_bookmakers(db: Session = Depends(get_db)):
    """Get list of available bookmakers from database"""
    bookmakers = db.query(Odds.bookmaker).distinct().all()

    return {
        "bookmakers": [bookmaker[0] for bookmaker in bookmakers if bookmaker[0]]
    }

@router.get("/database/markets")
async def get_markets(db: Session = Depends(get_db)):
    """Get list of available markets from database"""
    markets = db.query(Odds.market).distinct().all()

    return {
        "markets": [market[0] for market in markets if market[0]]
    }

@router.get("/arbitrage/{match_external_id}")
async def find_arbitrage_opportunities(match_external_id: str):
    """Find arbitrage opportunities for a match"""
    odds_service = OddsService()

    try:
        comparison = await odds_service.get_bookmaker_comparison(match_external_id)

        if not comparison:
            raise HTTPException(status_code=404, detail="No odds comparison available for this match")

        arbitrage_opportunities = []
        best_odds = comparison.get("best_odds", {})

        # Check for 1X2 arbitrage
        if all(key in best_odds for key in ["home_win", "draw", "away_win"]):
            home_odds = best_odds["home_win"]["odds"]
            draw_odds = best_odds["draw"]["odds"]
            away_odds = best_odds["away_win"]["odds"]

            if home_odds > 0 and draw_odds > 0 and away_odds > 0:
                total_probability = (1/home_odds) + (1/draw_odds) + (1/away_odds)

                if total_probability < 1.0:  # Arbitrage opportunity
                    profit_margin = (1 - total_probability) * 100

                    arbitrage_opportunities.append({
                        "market": "1X2",
                        "profit_margin": round(profit_margin, 2),
                        "selections": [
                            {
                                "selection": "Home Win",
                                "odds": home_odds,
                                "bookmaker": best_odds["home_win"]["bookmaker"],
                                "stake_percentage": round((1/home_odds) / total_probability * 100, 2)
                            },
                            {
                                "selection": "Draw",
                                "odds": draw_odds,
                                "bookmaker": best_odds["draw"]["bookmaker"],
                                "stake_percentage": round((1/draw_odds) / total_probability * 100, 2)
                            },
                            {
                                "selection": "Away Win",
                                "odds": away_odds,
                                "bookmaker": best_odds["away_win"]["bookmaker"],
                                "stake_percentage": round((1/away_odds) / total_probability * 100, 2)
                            }
                        ]
                    })

        # Check for Over/Under 2.5 arbitrage
        if "over_2_5" in best_odds and "under_2_5" in best_odds:
            over_odds = best_odds["over_2_5"]["odds"]
            under_odds = best_odds["under_2_5"]["odds"]

            if over_odds > 0 and under_odds > 0:
                total_probability = (1/over_odds) + (1/under_odds)

                if total_probability < 1.0:  # Arbitrage opportunity
                    profit_margin = (1 - total_probability) * 100

                    arbitrage_opportunities.append({
                        "market": "Over/Under 2.5",
                        "profit_margin": round(profit_margin, 2),
                        "selections": [
                            {
                                "selection": "Over 2.5",
                                "odds": over_odds,
                                "bookmaker": best_odds["over_2_5"]["bookmaker"],
                                "stake_percentage": round((1/over_odds) / total_probability * 100, 2)
                            },
                            {
                                "selection": "Under 2.5",
                                "odds": under_odds,
                                "bookmaker": best_odds["under_2_5"]["bookmaker"],
                                "stake_percentage": round((1/under_odds) / total_probability * 100, 2)
                            }
                        ]
                    })

        return {
            "match_id": match_external_id,
            "arbitrage_opportunities": arbitrage_opportunities,
            "opportunity_count": len(arbitrage_opportunities),
            "total_profit_potential": sum(arb["profit_margin"] for arb in arbitrage_opportunities)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find arbitrage opportunities: {str(e)}")