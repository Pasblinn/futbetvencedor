from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timezone, timedelta

from app.core.database import get_db
from app.models import Team, Match, Prediction
from app.services.analytics_service import AnalyticsService

router = APIRouter()

# Timezone de Brasília (BRT = UTC-3)
BRT = timezone(timedelta(hours=-3))

def to_brasilia_time(dt: datetime) -> str:
    """Converte datetime UTC para horário de Brasília (BRT)"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    brt_time = dt.astimezone(BRT)
    return brt_time.isoformat()

@router.get("/overview")
async def get_analytics_overview(db: Session = Depends(get_db)):
    """
    📊 Dashboard Analytics Overview
    Retorna estatísticas gerais do sistema para o Dashboard
    """
    try:
        from app.models import Prediction
        from app.models.statistics import MatchStatistics
        from datetime import datetime, timedelta
        from sqlalchemy import func

        # Contar jogos
        total_games = db.query(Match).count()

        # Jogos ao vivo (LIVE status)
        live_games = db.query(Match).filter(Match.status == 'LIVE').count()

        # Predições disponíveis com recomendação BET (oportunidades)
        opportunities = db.query(Prediction).filter(
            Prediction.market_type == '1X2',
            Prediction.final_recommendation.in_(['BET', 'STRONG_BET', 'MONITOR'])
        ).count()

        # Calcular confiança média
        avg_confidence_result = db.query(
            func.avg(Prediction.confidence_score)
        ).filter(
            Prediction.market_type == '1X2'
        ).scalar()
        avg_confidence = float(avg_confidence_result) if avg_confidence_result else 0.0

        # Taxa de sucesso (predições corretas)
        total_predictions_validated = db.query(Prediction).filter(
            Prediction.is_validated == True,
            Prediction.actual_outcome.isnot(None)
        ).count()

        successful_predictions = db.query(Prediction).filter(
            Prediction.is_validated == True,
            Prediction.is_winner == True
        ).count()

        success_rate = (successful_predictions / total_predictions_validated * 100) if total_predictions_validated > 0 else 0.0

        # Performance de hoje
        today = datetime.now().date()
        today_matches = db.query(Match).filter(
            func.date(Match.match_date) == today,
            Match.status == 'FT',
            Match.home_score.isnot(None),
            Match.away_score.isnot(None)
        ).all()

        today_wins = sum(1 for m in today_matches if m.home_score > m.away_score)
        today_losses = sum(1 for m in today_matches if m.home_score < m.away_score)
        today_draws = sum(1 for m in today_matches if m.home_score == m.away_score)

        # Performance da semana
        week_ago = datetime.now() - timedelta(days=7)
        week_predictions = db.query(Prediction).filter(
            Prediction.predicted_at >= week_ago,
            Prediction.market_type == '1X2'
        ).all()

        week_successful = sum(1 for p in week_predictions if p.is_winner)
        week_total = len(week_predictions)
        week_accuracy = (week_successful / week_total * 100) if week_total > 0 else 0.0

        return {
            "total_games": total_games,
            "live_games": live_games,
            "opportunities": opportunities,
            "avg_confidence": round(avg_confidence, 2),
            "success_rate": round(success_rate, 1),
            "last_update": datetime.now().isoformat(),
            "performance": {
                "today": {
                    "wins": today_wins,
                    "losses": today_losses,
                    "draws": today_draws
                },
                "this_week": {
                    "total_predictions": week_total,
                    "successful": week_successful,
                    "accuracy": round(week_accuracy, 1)
                }
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get overview: {str(e)}")

@router.get("/team/{team_id}/form")
async def get_team_form(
    team_id: int,
    db: Session = Depends(get_db),
    matches_count: int = Query(15, ge=5, le=30)
):
    """Get detailed form analysis for a team"""

    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    analytics_service = AnalyticsService(db)

    try:
        form_data = await analytics_service.analyze_team_form(team_id, matches_count)
        return {
            "team_id": team_id,
            "team_name": team.name,
            "form_analysis": form_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze team form: {str(e)}")

@router.get("/team/{team_id}/xg-metrics")
async def get_team_xg_metrics(
    team_id: int,
    db: Session = Depends(get_db),
    matches_count: int = Query(15, ge=5, le=30)
):
    """Get Expected Goals metrics for a team"""

    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    analytics_service = AnalyticsService(db)

    try:
        xg_data = await analytics_service.calculate_xg_metrics(team_id, matches_count)
        return {
            "team_id": team_id,
            "team_name": team.name,
            "xg_metrics": xg_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate xG metrics: {str(e)}")

@router.get("/team/{team_id}/corners")
async def get_team_corners_analysis(
    team_id: int,
    db: Session = Depends(get_db),
    matches_count: int = Query(15, ge=5, le=30)
):
    """Get corner kick analysis for a team"""

    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    analytics_service = AnalyticsService(db)

    try:
        corner_data = await analytics_service.analyze_corners_performance(team_id, matches_count)
        return {
            "team_id": team_id,
            "team_name": team.name,
            "corners_analysis": corner_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze corners: {str(e)}")

@router.get("/head-to-head/{team1_id}/{team2_id}")
async def get_head_to_head_analysis(
    team1_id: int,
    team2_id: int,
    db: Session = Depends(get_db),
    matches_count: int = Query(10, ge=3, le=20)
):
    """Get head-to-head analysis between two teams"""

    team1 = db.query(Team).filter(Team.id == team1_id).first()
    team2 = db.query(Team).filter(Team.id == team2_id).first()

    if not team1:
        raise HTTPException(status_code=404, detail="Team 1 not found")
    if not team2:
        raise HTTPException(status_code=404, detail="Team 2 not found")

    analytics_service = AnalyticsService(db)

    try:
        h2h_data = await analytics_service.analyze_head_to_head(team1_id, team2_id, matches_count)
        return {
            "team1": {
                "id": team1_id,
                "name": team1.name
            },
            "team2": {
                "id": team2_id,
                "name": team2.name
            },
            "head_to_head": h2h_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze head-to-head: {str(e)}")

@router.get("/match/{match_id}/comprehensive")
async def get_comprehensive_match_analysis(match_id: int, db: Session = Depends(get_db)):
    """Get comprehensive analysis for a specific match"""

    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    analytics_service = AnalyticsService(db)

    try:
        # Get all analysis components
        home_form = await analytics_service.analyze_team_form(match.home_team_id)
        away_form = await analytics_service.analyze_team_form(match.away_team_id)
        h2h_analysis = await analytics_service.analyze_head_to_head(match.home_team_id, match.away_team_id)
        home_xg = await analytics_service.calculate_xg_metrics(match.home_team_id)
        away_xg = await analytics_service.calculate_xg_metrics(match.away_team_id)
        home_corners = await analytics_service.analyze_corners_performance(match.home_team_id)
        away_corners = await analytics_service.analyze_corners_performance(match.away_team_id)

        return {
            "match": {
                "id": match_id,
                "home_team": match.home_team.name,
                "away_team": match.away_team.name,
                "match_date": match.match_date,
                "league": match.league,
                "venue": match.venue
            },
            "analysis": {
                "form": {
                    "home": home_form,
                    "away": away_form
                },
                "head_to_head": h2h_analysis,
                "expected_goals": {
                    "home": home_xg,
                    "away": away_xg
                },
                "corners": {
                    "home": home_corners,
                    "away": away_corners
                }
            },
            "summary": {
                "home_advantages": _identify_team_advantages(home_form, away_form, h2h_analysis, True),
                "away_advantages": _identify_team_advantages(away_form, home_form, h2h_analysis, False),
                "key_metrics": _calculate_key_metrics(home_form, away_form, home_xg, away_xg)
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate comprehensive analysis: {str(e)}")

def _identify_team_advantages(team_form: dict, opponent_form: dict, h2h: dict, is_home: bool) -> list:
    """Identify key advantages for a team"""
    advantages = []

    # Form advantages
    team_ppg = team_form.get("points_per_game", 0)
    opponent_ppg = opponent_form.get("points_per_game", 0)

    if team_ppg > opponent_ppg + 0.5:
        advantages.append(f"Superior recent form ({team_ppg:.1f} vs {opponent_ppg:.1f} PPG)")

    # Goal scoring
    team_gpg = team_form.get("goals_per_game", 0)
    opponent_conceded = opponent_form.get("goals_conceded_per_game", 0)

    if team_gpg > opponent_conceded + 0.3:
        advantages.append(f"Strong attack vs weak defense ({team_gpg:.1f} goals/game vs {opponent_conceded:.1f} conceded/game)")

    # Defensive record
    team_conceded = team_form.get("goals_conceded_per_game", 0)
    opponent_gpg = opponent_form.get("goals_per_game", 0)

    if team_conceded < opponent_gpg - 0.3:
        advantages.append(f"Strong defense vs weak attack ({team_conceded:.1f} conceded/game vs {opponent_gpg:.1f} goals/game)")

    # H2H record
    if h2h.get("matches_analyzed", 0) >= 3:
        if is_home:
            win_rate = h2h.get("team1_win_rate", 0)
        else:
            win_rate = h2h.get("team2_win_rate", 0)

        if win_rate > 0.6:
            advantages.append(f"Dominant H2H record ({win_rate:.1%} win rate)")

    # Home advantage (if applicable)
    if is_home:
        advantages.append("Home advantage")

    return advantages

def _calculate_key_metrics(home_form: dict, away_form: dict, home_xg: dict, away_xg: dict) -> dict:
    """Calculate key metrics for the match"""
    return {
        "form_advantage": {
            "home_ppg": home_form.get("points_per_game", 0),
            "away_ppg": away_form.get("points_per_game", 0),
            "difference": home_form.get("points_per_game", 0) - away_form.get("points_per_game", 0)
        },
        "attacking_strength": {
            "home_gpg": home_form.get("goals_per_game", 0),
            "away_gpg": away_form.get("goals_per_game", 0),
            "home_xg_avg": home_xg.get("avg_xg_for", 0),
            "away_xg_avg": away_xg.get("avg_xg_for", 0)
        },
        "defensive_strength": {
            "home_conceded_pg": home_form.get("goals_conceded_per_game", 0),
            "away_conceded_pg": away_form.get("goals_conceded_per_game", 0),
            "home_xga_avg": home_xg.get("avg_xg_against", 0),
            "away_xga_avg": away_xg.get("avg_xg_against", 0)
        },
        "recent_form": {
            "home_form_string": home_form.get("form_string", ""),
            "away_form_string": away_form.get("form_string", ""),
            "home_form_trend": home_form.get("form_trend", 0),
            "away_form_trend": away_form.get("form_trend", 0)
        }
    }


@router.get("/history")
async def get_past_matches_with_results(
    db: Session = Depends(get_db),
    days_back: int = Query(30, ge=1, le=365, description="Quantos dias atrás buscar"),
    limit: int = Query(50, ge=1, le=200, description="Limite de jogos")
):
    """
    📜 Histórico de Jogos Passados com Resultados

    Retorna jogos finalizados com suas predictions e resultados reais (greens/reds)
    Para análise de performance histórica da ML
    """
    from datetime import datetime, timedelta

    # Calcular data limite
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)

    # Buscar jogos finalizados
    finished_matches = db.query(Match).filter(
        Match.status.in_(['FT', 'AET', 'PEN']),
        Match.match_date >= start_date,
        Match.match_date <= end_date,
        Match.home_score.isnot(None),
        Match.away_score.isnot(None)
    ).order_by(Match.match_date.desc()).limit(limit).all()

    results = []

    for match in finished_matches:
        # Buscar prediction deste jogo
        prediction = db.query(Prediction).filter(
            Prediction.match_id == match.id,
            Prediction.market_type == '1X2'
        ).first()

        # Determinar resultado real do jogo
        if match.home_score > match.away_score:
            actual_result = '1'  # Casa ganhou
        elif match.home_score < match.away_score:
            actual_result = '2'  # Fora ganhou
        else:
            actual_result = 'X'  # Empate

        # Se tem prediction, verificar se acertou (green) ou errou (red)
        is_green = None
        prediction_data = None

        if prediction:
            predicted_outcome = prediction.predicted_outcome
            is_green = (predicted_outcome == actual_result)

            prediction_data = {
                'predicted_outcome': predicted_outcome,
                'predicted_probability': prediction.predicted_probability,
                'confidence_score': prediction.confidence_score,
                'final_recommendation': prediction.final_recommendation
            }

        results.append({
            'match_id': match.id,
            'home_team': match.home_team,
            'away_team': match.away_team,
            'league': match.league,
            'match_date': to_brasilia_time(match.match_date),
            'status': match.status,
            'score': {
                'home': match.home_score,
                'away': match.away_score
            },
            'actual_result': actual_result,
            'had_prediction': prediction is not None,
            'prediction': prediction_data,
            'result_type': 'GREEN ✅' if is_green else 'RED ❌' if is_green is False else 'SEM PREDICTION'
        })

    # Calcular estatísticas gerais
    total_with_predictions = sum(1 for r in results if r['had_prediction'])
    total_greens = sum(1 for r in results if r['result_type'] == 'GREEN ✅')
    total_reds = sum(1 for r in results if r['result_type'] == 'RED ❌')
    accuracy = (total_greens / total_with_predictions * 100) if total_with_predictions > 0 else 0

    return {
        'matches': results,
        'total': len(results),
        'summary': {
            'total_analyzed': len(results),
            'with_predictions': total_with_predictions,
            'greens': total_greens,
            'reds': total_reds,
            'accuracy': round(accuracy, 1),
            'period': f'Últimos {days_back} dias'
        }
    }