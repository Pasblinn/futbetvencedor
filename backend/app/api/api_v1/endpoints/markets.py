"""
🎯 MARKETS API ENDPOINTS
Endpoints para mercados de apostas, análise Poisson e value bets
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.core.database import get_db
from app.models import Match, Team, Odds
from app.services.poisson_service import poisson_service
from app.services.value_bet_detector import value_bet_detector, ValueBet
from app.core.markets_config import (
    MARKET_NAMES,
    MARKET_CATEGORIES,
    get_all_markets,
    get_priority_markets
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/markets")
async def get_all_available_markets():
    """
    Lista todos os mercados disponíveis no sistema

    Returns:
        - Lista de mercados organizados por categoria
    """
    return {
        "total_markets": len(MARKET_NAMES),
        "categories": MARKET_CATEGORIES,
        "all_markets": MARKET_NAMES
    }


@router.get("/markets/{match_id}")
async def get_match_markets(
    match_id: int,
    db: Session = Depends(get_db)
):
    """
    Retorna todos os mercados e odds disponíveis para uma partida

    Args:
        match_id: ID da partida

    Returns:
        - Odds organizadas por mercado
    """
    # Buscar partida
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    # Buscar todas as odds
    odds_list = db.query(Odds).filter(Odds.match_id == match_id).all()

    # Organizar por mercado
    markets_data = {}
    for odd in odds_list:
        if odd.market_type not in markets_data:
            markets_data[odd.market_type] = {
                "market_name": MARKET_NAMES.get(odd.market_type, odd.market_type),
                "bookmakers": []
            }

        markets_data[odd.market_type]["bookmakers"].append({
            "bookmaker": odd.bookmaker,
            "odds": odd.odds_data,
            "updated_at": odd.updated_at
        })

    return {
        "match_id": match_id,
        "match_name": f"{match.home_team.name} vs {match.away_team.name}",
        "markets": markets_data,
        "total_markets": len(markets_data)
    }


@router.post("/analysis/poisson/{match_id}")
async def analyze_match_poisson(
    match_id: int,
    league_avg_goals: float = Query(2.7, description="Média de gols da liga"),
    db: Session = Depends(get_db)
):
    """
    Analisa uma partida usando distribuição de Poisson

    Args:
        match_id: ID da partida
        league_avg_goals: Média de gols da liga (default: 2.7)

    Returns:
        - Lambdas calculados
        - Probabilidades de todos os resultados
        - Odds justas (fair odds)
    """
    # Buscar partida
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    # Calcular médias de gols (simplificado - em produção usar histórico real)
    # Aqui vamos usar dados mockados, mas você deve implementar cálculo real
    home_goals_avg = 1.5  # TODO: Calcular do histórico
    away_goals_avg = 1.2
    home_conceded_avg = 1.0
    away_conceded_avg = 1.3

    # Análise Poisson
    prediction = poisson_service.analyze_match(
        home_goals_avg=home_goals_avg,
        away_goals_avg=away_goals_avg,
        home_conceded_avg=home_conceded_avg,
        away_conceded_avg=away_conceded_avg,
        league_avg=league_avg_goals
    )

    return {
        "match_id": match_id,
        "match_name": f"{match.home_team.name} vs {match.away_team.name}",
        "lambda_home": round(prediction.home_lambda, 3),
        "lambda_away": round(prediction.away_lambda, 3),
        "probabilities": {
            k: round(v * 100, 2) for k, v in prediction.probabilities.items()
        },
        "fair_odds": {
            k: round(v, 2) for k, v in prediction.fair_odds.items()
        },
        "generated_at": datetime.now().isoformat()
    }


@router.post("/value-bets/{match_id}")
async def detect_match_value_bets(
    match_id: int,
    min_edge: float = Query(5.0, description="Edge mínimo em % (default: 5%)"),
    min_confidence: float = Query(0.6, description="Confiança mínima (default: 0.6)"),
    db: Session = Depends(get_db)
):
    """
    Detecta value bets para uma partida específica

    Args:
        match_id: ID da partida
        min_edge: Edge mínimo para considerar value (%)
        min_confidence: Confiança mínima na predição

    Returns:
        - Lista de value bets identificados
        - Ordenados por edge (maior primeiro)
    """
    # Buscar partida
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    # Análise Poisson
    home_goals_avg = 1.5  # TODO: Calcular real
    away_goals_avg = 1.2
    home_conceded_avg = 1.0
    away_conceded_avg = 1.3

    poisson_prediction = poisson_service.analyze_match(
        home_goals_avg=home_goals_avg,
        away_goals_avg=away_goals_avg,
        home_conceded_avg=home_conceded_avg,
        away_conceded_avg=away_conceded_avg
    )

    # Buscar odds de mercado
    odds_list = db.query(Odds).filter(Odds.match_id == match_id).all()

    # Organizar odds por mercado
    market_odds = {}
    for odd in odds_list:
        if odd.market_type not in market_odds:
            market_odds[odd.market_type] = {}

        # Mapear odds_data para formato esperado
        for selection, odds_value in odd.odds_data.items():
            market_odds[odd.market_type][selection] = {
                'odds': float(odds_value),
                'bookmaker': odd.bookmaker
            }

    # Detectar value bets
    value_bets = value_bet_detector.detect_value_bets(
        match_id=match_id,
        match_name=f"{match.home_team.name} vs {match.away_team.name}",
        poisson_prediction=poisson_prediction,
        market_odds=market_odds,
        confidence=min_confidence
    )

    # Filtrar por edge mínimo
    filtered_bets = [vb for vb in value_bets if vb.edge >= min_edge]

    return {
        "match_id": match_id,
        "match_name": f"{match.home_team.name} vs {match.away_team.name}",
        "total_value_bets": len(filtered_bets),
        "value_bets": [vb.to_dict() for vb in filtered_bets],
        "top_3_bets": [vb.to_dict() for vb in value_bet_detector.get_top_value_bets(filtered_bets, limit=3, min_rating='MEDIUM')],
        "generated_at": datetime.now().isoformat()
    }


@router.get("/value-bets/scan")
async def scan_all_value_bets(
    min_edge: float = Query(10.0, description="Edge mínimo (%)"),
    limit: int = Query(20, description="Máximo de value bets a retornar"),
    db: Session = Depends(get_db)
):
    """
    Escaneia TODAS as partidas disponíveis procurando value bets

    Args:
        min_edge: Edge mínimo
        limit: Máximo de resultados

    Returns:
        - Top value bets de todas as partidas
    """
    # Buscar apenas partidas ATIVAS (não finalizadas, não canceladas, não adiadas)
    # Status permitidos: NS (não iniciado), 1H (1º tempo), 2H (2º tempo), HT (intervalo), LIVE
    # Também filtrar por data (apenas jogos de hoje e futuros)
    from datetime import datetime, timedelta
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    matches = db.query(Match).filter(
        Match.status.in_(['NS', '1H', '2H', 'HT', 'LIVE']),  # Apenas jogos ativos
        Match.match_date >= yesterday  # Apenas jogos recentes/futuros
    ).limit(50).all()

    all_value_bets = []

    for match in matches:
        try:
            # Análise simplificada (em produção, fazer cálculos reais)
            poisson_prediction = poisson_service.analyze_match(
                home_goals_avg=1.5,
                away_goals_avg=1.2,
                home_conceded_avg=1.0,
                away_conceded_avg=1.3
            )

            # Buscar odds
            odds_list = db.query(Odds).filter(Odds.match_id == match.id).all()

            if not odds_list:
                continue

            market_odds = {}
            for odd in odds_list:
                if odd.market_type not in market_odds:
                    market_odds[odd.market_type] = {}

                for selection, odds_value in odd.odds_data.items():
                    market_odds[odd.market_type][selection] = {
                        'odds': float(odds_value),
                        'bookmaker': odd.bookmaker
                    }

            # Detectar value bets
            value_bets = value_bet_detector.detect_value_bets(
                match_id=match.id,
                match_name=f"{match.home_team.name} vs {match.away_team.name}",
                poisson_prediction=poisson_prediction,
                market_odds=market_odds,
                confidence=0.7
            )

            # Adicionar apenas os com edge >= min_edge
            all_value_bets.extend([vb for vb in value_bets if vb.edge >= min_edge])

        except Exception as e:
            logger.error(f"Erro ao analisar match {match.id}: {e}")
            continue

    # 🔧 MELHORADO: Ordenação inteligente por rating + edge
    rating_priority = {'PREMIUM': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
    all_value_bets.sort(
        key=lambda x: (rating_priority.get(x.value_rating, 0), x.edge),
        reverse=True
    )

    # 🔧 MELHORADO: Diversificação - pegar no máximo 2 value bets por jogo
    diversified_vbs = []
    match_count = {}

    for vb in all_value_bets:
        if match_count.get(vb.match_id, 0) < 2:
            diversified_vbs.append(vb)
            match_count[vb.match_id] = match_count.get(vb.match_id, 0) + 1

        if len(diversified_vbs) >= limit:
            break

    return {
        "total_matches_analyzed": len(matches),
        "total_value_bets_found": len(all_value_bets),
        "value_bets": [vb.to_dict() for vb in diversified_vbs],
        "generated_at": datetime.now().isoformat()
    }


@router.post("/calculator/kelly")
async def calculate_kelly_stake(
    probability: float = Query(..., description="Nossa probabilidade (0-1)"),
    market_odds: float = Query(..., description="Odds do mercado (decimal)"),
    bankroll: float = Query(1000, description="Banca total"),
    fraction: float = Query(0.25, description="Fração do Kelly (default: 25%)")
):
    """
    Calcula o stake ideal usando Kelly Criterion

    Args:
        probability: Nossa probabilidade estimada (0-1)
        market_odds: Odds oferecidas pelo bookmaker
        bankroll: Tamanho da banca
        fraction: Fração do Kelly a usar (0.25 = 25%)

    Returns:
        - Stake recomendado
        - Kelly % da banca
        - Expected Value
    """
    # Calcular Kelly
    kelly_fraction = poisson_service._calculate_kelly(probability, market_odds, fraction)

    # Stake recomendado
    recommended_stake = bankroll * kelly_fraction

    # Expected Value
    ev = (probability * (market_odds - 1) * recommended_stake) - ((1 - probability) * recommended_stake)
    ev_percentage = (ev / recommended_stake) * 100 if recommended_stake > 0 else 0

    return {
        "probability": round(probability, 4),
        "market_odds": market_odds,
        "bankroll": bankroll,
        "kelly_fraction": round(kelly_fraction, 4),
        "kelly_percentage": round(kelly_fraction * 100, 2),
        "recommended_stake": round(recommended_stake, 2),
        "expected_value": round(ev, 2),
        "ev_percentage": round(ev_percentage, 2),
        "potential_profit": round(recommended_stake * (market_odds - 1), 2)
    }
