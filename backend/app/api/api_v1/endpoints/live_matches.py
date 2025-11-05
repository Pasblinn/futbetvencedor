"""
🔴 LIVE MATCHES - Endpoint para monitoramento de jogos ao vivo
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import logging

from app.core.database import get_db
from app.core.rate_limiter import limiter
from app.models import Match, Odds, Prediction

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/live")
@limiter.limit("60/minute")
async def get_live_matches(
    request: Request,
    db: Session = Depends(get_db),
    limit: int = 100
):
    """
    🔴 Jogos AO VIVO com placares e odds em tempo real

    Retorna todos os jogos que estão acontecendo AGORA:
    - Placares atualizados
    - Odds da Bet365
    - Predictions (se existirem)
    - Status do jogo (1H, 2H, HT, etc)

    Rate limit: 60/min
    """

    # Buscar jogos AO VIVO
    live_statuses = ['LIVE', '1H', '2H', 'HT', 'BT', 'ET', 'P', 'SUSP', 'INT']

    live_matches = db.query(Match).filter(
        Match.status.in_(live_statuses)
    ).order_by(Match.match_date.desc()).limit(limit).all()

    results = []

    for match in live_matches:
        # Buscar odds mais recentes
        latest_odds = db.query(Odds).filter(
            Odds.match_id == match.id,
            Odds.market == '1X2'
        ).order_by(Odds.odds_timestamp.desc()).first()

        # Buscar prediction (se existir)
        prediction = db.query(Prediction).filter(
            Prediction.match_id == match.id,
            Prediction.market_type == '1X2'
        ).first()

        match_data = {
            'id': match.id,
            'external_id': match.external_id,
            'home_team': {
                'id': match.home_team.id,
                'name': match.home_team.name,
                'logo': match.home_team.logo_url
            },
            'away_team': {
                'id': match.away_team.id,
                'name': match.away_team.name,
                'logo': match.away_team.logo_url
            },
            'home_score': match.home_score,
            'away_score': match.away_score,
            'status': match.status,
            'minute': None,  # TODO: Extract from match data
            'match_date': match.match_date.isoformat() if match.match_date else None,
            'venue': match.venue,
            'odds': {
                'home': float(latest_odds.home_win) if latest_odds and latest_odds.home_win else None,
                'draw': float(latest_odds.draw) if latest_odds and latest_odds.draw else None,
                'away': float(latest_odds.away_win) if latest_odds and latest_odds.away_win else None,
                'updated_at': latest_odds.odds_timestamp.isoformat() if latest_odds else None
            } if latest_odds else None,
            'prediction': {
                'predicted_outcome': prediction.predicted_outcome,
                'confidence': float(prediction.confidence_score) if prediction.confidence_score else None,
                'probability_home': float(prediction.probability_home) if prediction.probability_home else None,
                'probability_draw': float(prediction.probability_draw) if prediction.probability_draw else None,
                'probability_away': float(prediction.probability_away) if prediction.probability_away else None,
            } if prediction else None
        }

        results.append(match_data)

    return {
        'success': True,
        'total': len(results),
        'live_now': len(results),
        'matches': results,
        'last_updated': datetime.now().isoformat()
    }

@router.get("/today")
@limiter.limit("60/minute")
async def get_today_matches(
    request: Request,
    db: Session = Depends(get_db),
    include_finished: bool = False
):
    """
    📅 Jogos de HOJE (passados, ao vivo e futuros)

    Retorna todos os jogos de hoje:
    - Finalizados (se include_finished=true)
    - Ao vivo
    - Próximos jogos

    Rate limit: 60/min
    """
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    query = db.query(Match).filter(
        and_(
            Match.match_date >= today_start,
            Match.match_date < today_end
        )
    )

    if not include_finished:
        query = query.filter(Match.status != 'FT')

    matches = query.order_by(Match.match_date).all()

    results = []

    for match in matches:
        # Buscar odds
        latest_odds = db.query(Odds).filter(
            Odds.match_id == match.id,
            Odds.market == '1X2'
        ).order_by(Odds.odds_timestamp.desc()).first()

        # Buscar prediction
        prediction = db.query(Prediction).filter(
            Prediction.match_id == match.id,
            Prediction.market_type == '1X2'
        ).first()

        match_data = {
            'id': match.id,
            'external_id': match.external_id,
            'home_team': {
                'id': match.home_team.id,
                'name': match.home_team.name,
                'logo': match.home_team.logo_url
            },
            'away_team': {
                'id': match.away_team.id,
                'name': match.away_team.name,
                'logo': match.away_team.logo_url
            },
            'home_score': match.home_score,
            'away_score': match.away_score,
            'status': match.status,
            'match_date': match.match_date.isoformat() if match.match_date else None,
            'venue': match.venue,
            'odds': {
                'home': float(latest_odds.home_win) if latest_odds and latest_odds.home_win else None,
                'draw': float(latest_odds.draw) if latest_odds and latest_odds.draw else None,
                'away': float(latest_odds.away_win) if latest_odds and latest_odds.away_win else None,
            } if latest_odds else None,
            'prediction': {
                'predicted_outcome': prediction.predicted_outcome,
                'confidence': float(prediction.confidence_score) if prediction.confidence_score else None,
            } if prediction else None
        }

        results.append(match_data)

    # Separar por status
    live_matches = [m for m in results if m['status'] in ['LIVE', '1H', '2H', 'HT']]
    upcoming_matches = [m for m in results if m['status'] in ['NS', 'TBD', 'SCHEDULED']]
    finished_matches = [m for m in results if m['status'] == 'FT']

    return {
        'success': True,
        'total': len(results),
        'live': len(live_matches),
        'upcoming': len(upcoming_matches),
        'finished': len(finished_matches),
        'matches': {
            'live': live_matches,
            'upcoming': upcoming_matches,
            'finished': finished_matches if include_finished else []
        },
        'last_updated': datetime.now().isoformat()
    }

@router.get("/upcoming")
@limiter.limit("60/minute")
async def get_upcoming_matches(
    request: Request,
    db: Session = Depends(get_db),
    hours_ahead: int = 24,
    limit: int = 50
):
    """
    🔮 Próximos jogos (futuro)

    Retorna jogos que vão começar nas próximas N horas

    Rate limit: 60/min
    """
    now = datetime.now()
    future_time = now + timedelta(hours=hours_ahead)

    upcoming = db.query(Match).filter(
        and_(
            Match.match_date > now,
            Match.match_date <= future_time,
            Match.status.in_(['NS', 'TBD', 'SCHEDULED'])
        )
    ).order_by(Match.match_date).limit(limit).all()

    results = []

    for match in upcoming:
        latest_odds = db.query(Odds).filter(
            Odds.match_id == match.id,
            Odds.market == '1X2'
        ).order_by(Odds.odds_timestamp.desc()).first()

        prediction = db.query(Prediction).filter(
            Prediction.match_id == match.id,
            Prediction.market_type == '1X2'
        ).first()

        # Calculate time until match starts
        time_until = match.match_date - now
        hours_until = time_until.total_seconds() / 3600

        match_data = {
            'id': match.id,
            'external_id': match.external_id,
            'home_team': {
                'name': match.home_team.name,
                'logo': match.home_team.logo_url
            },
            'away_team': {
                'name': match.away_team.name,
                'logo': match.away_team.logo_url
            },
            'match_date': match.match_date.isoformat(),
            'hours_until': round(hours_until, 1),
            'status': match.status,
            'odds': {
                'home': float(latest_odds.home_win) if latest_odds and latest_odds.home_win else None,
                'draw': float(latest_odds.draw) if latest_odds and latest_odds.draw else None,
                'away': float(latest_odds.away_win) if latest_odds and latest_odds.away_win else None,
            } if latest_odds else None,
            'prediction': {
                'predicted_outcome': prediction.predicted_outcome,
                'confidence': float(prediction.confidence_score) if prediction.confidence_score else None,
            } if prediction else None
        }

        results.append(match_data)

    return {
        'success': True,
        'total': len(results),
        'matches': results,
        'hours_ahead': hours_ahead,
        'last_updated': datetime.now().isoformat()
    }


@router.get("/stats")
@limiter.limit("100/minute")
async def get_live_stats(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    📊 ESTATÍSTICAS AO VIVO

    Busca estatísticas em tempo real dos jogos ao vivo:
    - ⚽ Placar atualizado
    - ⏱️ Minuto do jogo
    - 📈 Estatísticas completas (posse, chutes, escanteios, cartões)
    - 🎯 Eventos recentes (gols, cartões, substituições)

    Atualizado em tempo real via API-Sports

    Rate limit: 100/min
    """
    from app.services.live_stats_service import LiveStatsService

    try:
        service = LiveStatsService(db)
        live_matches = service.get_live_matches()

        return {
            'success': True,
            'total': len(live_matches),
            'matches': live_matches,
            'last_updated': datetime.now().isoformat(),
            'refresh_interval': 60  # Segundos - recomendado atualizar a cada 1 min
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'matches': [],
            'total': 0
        }


@router.post("/cleanup-stuck")
@limiter.limit("10/hour")
async def cleanup_stuck_matches(
    request: Request,
    db: Session = Depends(get_db),
    hours_threshold: int = 2
):
    """
    🔧 LIMPEZA DE PARTIDAS TRAVADAS

    Corrige partidas que ficaram "travadas" com status LIVE/2H
    mas que já deveriam estar finalizadas.

    Esta operação:
    - Busca partidas com status LIVE que começaram há mais de N horas
    - Atualiza o status para 'FT' (Full Time)
    - Retorna relatório de partidas corrigidas

    **Parâmetros:**
    - hours_threshold: Horas após início para considerar travado (default: 2)

    **Rate limit:** 10/hora (proteção contra abuso)

    **Uso recomendado:** Executar automaticamente a cada hora via scheduler
    """
    try:
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_threshold)

        # Buscar partidas travadas (mesmos status do endpoint /live)
        live_statuses = ['LIVE', '1H', '2H', 'HT', 'BT', 'ET', 'P', 'SUSP', 'INT']
        stuck_matches = db.query(Match).filter(
            and_(
                Match.status.in_(live_statuses),
                Match.match_date < cutoff_time
            )
        ).all()

        if not stuck_matches:
            return {
                'success': True,
                'message': 'Nenhuma partida travada encontrada',
                'fixed_count': 0,
                'fixed_matches': []
            }

        # Corrigir cada partida
        fixed_matches = []
        for match in stuck_matches:
            try:
                old_status = match.status
                match.status = 'FT'
                db.commit()

                fixed_matches.append({
                    'id': match.id,
                    'league': match.league,
                    'home_team': match.home_team.name if match.home_team else 'Unknown',
                    'away_team': match.away_team.name if match.away_team else 'Unknown',
                    'old_status': old_status,
                    'new_status': 'FT',
                    'match_date': match.match_date.isoformat() if match.match_date else None,
                    'score': f"{match.home_score}-{match.away_score}"
                })

            except Exception as e:
                logger.error(f"Erro ao corrigir match {match.id}: {e}")
                db.rollback()

        return {
            'success': True,
            'message': f'{len(fixed_matches)} partida(s) corrigida(s)',
            'fixed_count': len(fixed_matches),
            'fixed_matches': fixed_matches,
            'hours_threshold': hours_threshold,
            'cleanup_time': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Erro na limpeza de partidas travadas: {e}")
        return {
            'success': False,
            'error': str(e),
            'fixed_count': 0
        }
