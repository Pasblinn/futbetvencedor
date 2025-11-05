"""
🎰 API ENDPOINTS - COMPARAÇÃO DE ODDS
Endpoints para comparar odds de múltiplas casas de apostas em tempo real
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import Dict, List, Optional
from datetime import datetime
from app.services.odds_comparison_service import odds_comparison_service

router = APIRouter()

@router.get("/match/{match_id}")
async def get_match_odds(match_id: str, home_team: str = Query(...), away_team: str = Query(...)):
    """
    🎯 Buscar Odds para um Jogo Específico

    Retorna odds de múltiplas casas de apostas para um jogo específico,
    incluindo as melhores odds disponíveis e oportunidades de arbitragem.
    """
    try:
        match_odds = await odds_comparison_service.get_match_odds(match_id, home_team, away_team)

        if not match_odds:
            return {
                "success": False,
                "message": f"Odds não encontradas para {home_team} vs {away_team}",
                "match_id": match_id
            }

        return {
            "success": True,
            "match_odds": {
                "match_id": match_odds.match_id,
                "home_team": match_odds.home_team,
                "away_team": match_odds.away_team,
                "league": match_odds.league,
                "match_date": match_odds.match_date.isoformat(),
                "bookmakers_count": len(match_odds.odds_data),
                "odds_data": [
                    {
                        "bookmaker": odds.bookmaker,
                        "market": odds.market,
                        "home_odds": odds.home_odds,
                        "draw_odds": odds.draw_odds,
                        "away_odds": odds.away_odds,
                        "over_under": odds.over_under,
                        "both_teams_score": odds.both_teams_score,
                        "asian_handicap": odds.asian_handicap,
                        "last_updated": odds.last_updated.isoformat()
                    }
                    for odds in match_odds.odds_data
                ],
                "best_odds": match_odds.best_odds,
                "arbitrage_opportunities": match_odds.arbitrage_opportunities
            },
            "message": f"Odds coletadas de {len(match_odds.odds_data)} casas de apostas"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar odds: {str(e)}")

@router.get("/live-updates/{match_id}")
async def get_live_odds_updates(match_id: str):
    """
    🔴 Atualizações de Odds ao Vivo

    Busca as últimas atualizações de odds para um jogo em andamento.
    """
    try:
        updates = await odds_comparison_service.get_live_odds_updates(match_id)
        return updates

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar atualizações: {str(e)}")

@router.post("/bulk-odds")
async def get_bulk_odds(matches: List[Dict[str, str]]):
    """
    📦 Buscar Odds em Massa

    Busca odds para múltiplos jogos simultaneamente.

    Exemplo de payload:
    ```json
    [
        {"id": "1", "home_team": "Flamengo", "away_team": "Palmeiras"},
        {"id": "2", "home_team": "Santos", "away_team": "Corinthians"}
    ]
    ```
    """
    try:
        if len(matches) > 20:
            raise HTTPException(status_code=400, detail="Máximo 20 jogos por requisição")

        results = await odds_comparison_service.get_multiple_matches_odds(matches)

        return {
            "success": True,
            "total_matches": len(matches),
            "successful_matches": len(results),
            "matches_odds": [
                {
                    "match_id": match_odds.match_id,
                    "home_team": match_odds.home_team,
                    "away_team": match_odds.away_team,
                    "bookmakers_count": len(match_odds.odds_data),
                    "best_odds": match_odds.best_odds,
                    "arbitrage_count": len(match_odds.arbitrage_opportunities),
                    "has_arbitrage": len(match_odds.arbitrage_opportunities) > 0
                }
                for match_odds in results
            ],
            "message": f"Odds coletadas para {len(results)}/{len(matches)} jogos"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar odds em massa: {str(e)}")

@router.get("/arbitrage-opportunities")
async def get_arbitrage_opportunities(
    min_profit: float = Query(0.5, description="Margem mínima de lucro em %"),
    limit: int = Query(10, description="Número máximo de oportunidades")
):
    """
    💰 Oportunidades de Arbitragem

    Busca oportunidades de arbitragem disponíveis no momento.
    """
    try:
        # Buscar jogos de hoje com odds
        today_matches = [
            {"id": "flamengo_estudiantes", "home_team": "Estudiantes de La Plata", "away_team": "CR Flamengo"},
            {"id": "barcelona_madrid", "home_team": "FC Barcelona", "away_team": "Real Madrid CF"},
            {"id": "liverpool_city", "home_team": "Liverpool FC", "away_team": "Manchester City FC"}
        ]

        matches_odds = await odds_comparison_service.get_multiple_matches_odds(today_matches)

        all_arbitrage_opps = []
        for match_odds in matches_odds:
            for arb in match_odds.arbitrage_opportunities:
                if arb['profit_margin'] >= min_profit:
                    all_arbitrage_opps.append({
                        "match": f"{match_odds.home_team} vs {match_odds.away_team}",
                        "league": match_odds.league,
                        "match_date": match_odds.match_date.isoformat(),
                        **arb
                    })

        # Ordenar por margem de lucro
        all_arbitrage_opps.sort(key=lambda x: x['profit_margin'], reverse=True)

        return {
            "success": True,
            "arbitrage_opportunities": all_arbitrage_opps[:limit],
            "total_found": len(all_arbitrage_opps),
            "filters": {
                "min_profit": min_profit,
                "limit": limit
            },
            "message": f"Encontradas {len(all_arbitrage_opps)} oportunidades de arbitragem"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar oportunidades: {str(e)}")

@router.get("/best-odds-summary")
async def get_best_odds_summary():
    """
    ⭐ Resumo das Melhores Odds

    Retorna um resumo das melhores odds disponíveis para jogos principais.
    """
    try:
        # Jogos principais para análise
        featured_matches = [
            {"id": "flamengo_estudiantes", "home_team": "Estudiantes de La Plata", "away_team": "CR Flamengo"},
            {"id": "palmeiras_santos", "home_team": "Palmeiras", "away_team": "Santos"},
            {"id": "corinthians_saopaulo", "home_team": "Corinthians", "away_team": "São Paulo"}
        ]

        matches_odds = await odds_comparison_service.get_multiple_matches_odds(featured_matches)

        best_odds_summary = []
        total_bookmakers = 0

        for match_odds in matches_odds:
            total_bookmakers += len(match_odds.odds_data)

            best_odds_summary.append({
                "match": f"{match_odds.home_team} vs {match_odds.away_team}",
                "match_id": match_odds.match_id,
                "league": match_odds.league or "Liga Principal",
                "match_date": match_odds.match_date.isoformat(),
                "bookmakers_analyzed": len(match_odds.odds_data),
                "best_odds": match_odds.best_odds,
                "arbitrage_available": len(match_odds.arbitrage_opportunities) > 0,
                "arbitrage_profit": max(
                    (arb['profit_margin'] for arb in match_odds.arbitrage_opportunities),
                    default=0
                ),
                "value_bets": [
                    {
                        "market": "Vitória Casa",
                        "best_odd": match_odds.best_odds.get("1X2", {}).get("home", 0),
                        "bookmaker": match_odds.best_odds.get("1X2", {}).get("bookmakers", {}).get("home", "N/A")
                    },
                    {
                        "market": "Empate",
                        "best_odd": match_odds.best_odds.get("1X2", {}).get("draw", 0),
                        "bookmaker": match_odds.best_odds.get("1X2", {}).get("bookmakers", {}).get("draw", "N/A")
                    },
                    {
                        "market": "Vitória Fora",
                        "best_odd": match_odds.best_odds.get("1X2", {}).get("away", 0),
                        "bookmaker": match_odds.best_odds.get("1X2", {}).get("bookmakers", {}).get("away", "N/A")
                    }
                ]
            })

        return {
            "success": True,
            "featured_matches": best_odds_summary,
            "summary_stats": {
                "total_matches_analyzed": len(matches_odds),
                "total_bookmakers_checked": total_bookmakers,
                "avg_bookmakers_per_match": round(total_bookmakers / max(len(matches_odds), 1), 1),
                "arbitrage_opportunities_found": sum(
                    len(match.arbitrage_opportunities) for match in matches_odds
                ),
                "last_updated": datetime.now().isoformat()
            },
            "message": f"Resumo de {len(matches_odds)} jogos principais analisados"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar resumo: {str(e)}")

@router.get("/bookmaker-comparison")
async def get_bookmaker_comparison(
    home_team: str = Query(...),
    away_team: str = Query(...)
):
    """
    📊 Comparação Entre Casas de Apostas

    Compara odds entre diferentes casas para um jogo específico.
    """
    try:
        match_id = f"{home_team.lower().replace(' ', '_')}_vs_{away_team.lower().replace(' ', '_')}"
        match_odds = await odds_comparison_service.get_match_odds(match_id, home_team, away_team)

        if not match_odds:
            raise HTTPException(status_code=404, detail="Odds não encontradas para este jogo")

        # Organizar dados por casa de aposta
        bookmaker_comparison = {}

        for odds in match_odds.odds_data:
            bookmaker_comparison[odds.bookmaker] = {
                "1x2": {
                    "home": odds.home_odds,
                    "draw": odds.draw_odds,
                    "away": odds.away_odds
                },
                "over_under": odds.over_under or {},
                "btts": odds.both_teams_score or {},
                "asian_handicap": odds.asian_handicap or {},
                "last_updated": odds.last_updated.isoformat(),
                "margin": round(
                    (1/odds.home_odds + 1/odds.draw_odds + 1/odds.away_odds - 1) * 100
                    if all([odds.home_odds, odds.draw_odds, odds.away_odds]) else 0,
                    2
                )
            }

        # Ranking das casas por margem
        bookmaker_ranking = sorted(
            [(name, data["margin"]) for name, data in bookmaker_comparison.items()],
            key=lambda x: x[1]
        )

        return {
            "success": True,
            "match": f"{home_team} vs {away_team}",
            "bookmaker_comparison": bookmaker_comparison,
            "bookmaker_ranking": {
                "best_margin": bookmaker_ranking[0] if bookmaker_ranking else None,
                "worst_margin": bookmaker_ranking[-1] if bookmaker_ranking else None,
                "all_rankings": bookmaker_ranking
            },
            "best_odds_highlight": match_odds.best_odds,
            "recommendation": {
                "best_home_odd": f"{match_odds.best_odds.get('1X2', {}).get('home', 0)} em {match_odds.best_odds.get('1X2', {}).get('bookmakers', {}).get('home', 'N/A')}",
                "best_draw_odd": f"{match_odds.best_odds.get('1X2', {}).get('draw', 0)} em {match_odds.best_odds.get('1X2', {}).get('bookmakers', {}).get('draw', 'N/A')}",
                "best_away_odd": f"{match_odds.best_odds.get('1X2', {}).get('away', 0)} em {match_odds.best_odds.get('1X2', {}).get('bookmakers', {}).get('away', 'N/A')}"
            },
            "message": f"Comparação entre {len(match_odds.odds_data)} casas de apostas"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na comparação: {str(e)}")