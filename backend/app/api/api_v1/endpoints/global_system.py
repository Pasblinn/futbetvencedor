"""
🌍 API ENDPOINTS - SISTEMA GLOBAL DE FUTEBOL
Endpoints para gerenciar o sistema escalável de análise mundial
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from typing import Dict, List, Optional
from datetime import datetime, date, timedelta
from app.services.global_match_system import global_match_system, run_daily_analysis, start_global_monitoring

router = APIRouter()

@router.get("/status")
async def get_system_status():
    """
    📊 Status do Sistema Global

    Retorna informações completas sobre:
    - Ligas suportadas
    - Jogos ativos e monitorados
    - Previsões geradas
    - Status do monitoramento ao vivo
    """
    try:
        status = await global_match_system.get_system_status()
        return {
            "success": True,
            "system": status,
            "message": "Sistema operacional - monitorando futebol mundial"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar status: {str(e)}")

@router.post("/discover-matches")
async def discover_matches_globally(
    days_ahead: int = Query(7, ge=1, le=30, description="Dias à frente para descobrir jogos"),
    background_tasks: BackgroundTasks = None
):
    """
    🔍 Descoberta Global de Jogos

    Busca jogos de todas as ligas suportadas nos próximos N dias:
    - Premier League, La Liga, Bundesliga, Serie A, Ligue 1
    - Champions League, Europa League
    - Copa Libertadores, Copa Sul-Americana
    - Brasileirão, MLS, Liga MX
    - E muito mais!
    """
    try:
        # Executar descoberta
        matches = await global_match_system.discover_matches_globally(days_ahead)

        return {
            "success": True,
            "matches_discovered": len(matches),
            "period": f"Próximos {days_ahead} dias",
            "matches": [
                {
                    "id": match.id,
                    "home_team": match.home_team_name,
                    "away_team": match.away_team_name,
                    "league": match.league_name,
                    "country": next((l.country for l in global_match_system.supported_leagues if l.id == match.league_id), "Unknown"),
                    "date": match.match_date.isoformat(),
                    "status": match.status,
                    "venue": match.venue
                }
                for match in matches
            ],
            "leagues_coverage": list(set(match.league_name for match in matches)),
            "message": f"{len(matches)} jogos descobertos em {len(set(match.league_name for match in matches))} ligas"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na descoberta: {str(e)}")

@router.post("/generate-predictions")
async def generate_predictions_for_date(
    target_date: Optional[date] = Query(None, description="Data para gerar previsões (padrão: hoje)"),
    background_tasks: BackgroundTasks = None
):
    """
    🧠 Geração de Previsões em Massa

    Gera previsões para TODOS os jogos de uma data específica:
    - Análise de 13+ mercados por jogo
    - Probabilidades calculadas com ML
    - Recomendações de apostas
    - Combinações otimizadas
    """
    try:
        if not target_date:
            target_date = datetime.now()
        else:
            target_date = datetime.combine(target_date, datetime.min.time())

        # Gerar previsões
        predictions = await global_match_system.generate_predictions_for_all_matches(target_date)

        if not predictions:
            return {
                "success": False,
                "message": f"Nenhum jogo encontrado para {target_date.strftime('%Y-%m-%d')}",
                "predictions_generated": 0
            }

        # Calcular estatísticas
        leagues_analyzed = set()
        top_recommendations = []

        for match_id, prediction_data in predictions.items():
            league = prediction_data['match_info']['league']
            leagues_analyzed.add(league)

            # Extrair recomendações fortes
            preds = prediction_data['predictions']

            # Dupla chance com alta probabilidade
            if preds.get('double_chance', {}).get('x2', 0) > 0.65:
                top_recommendations.append({
                    "match": f"{prediction_data['match_info']['home_team']} vs {prediction_data['match_info']['away_team']}",
                    "market": "X2 (Empate ou Visitante)",
                    "probability": preds['double_chance']['x2'],
                    "league": league
                })

            # Under 2.5 com alta probabilidade
            if preds.get('over_under_goals', {}).get('under_2_5', 0) > 0.6:
                top_recommendations.append({
                    "match": f"{prediction_data['match_info']['home_team']} vs {prediction_data['match_info']['away_team']}",
                    "market": "Under 2.5 Gols",
                    "probability": preds['over_under_goals']['under_2_5'],
                    "league": league
                })

        # Ordenar recomendações por probabilidade
        top_recommendations.sort(key=lambda x: x['probability'], reverse=True)

        return {
            "success": True,
            "date": target_date.strftime('%Y-%m-%d'),
            "predictions_generated": len(predictions),
            "leagues_analyzed": list(leagues_analyzed),
            "matches": [
                {
                    "match_id": match_id,
                    "home_team": data['match_info']['home_team'],
                    "away_team": data['match_info']['away_team'],
                    "league": data['match_info']['league'],
                    "confidence": data['predictions'].get('confidence_overall', 0.5),
                    "top_prediction": data['predictions']['1x2']['prediction']
                }
                for match_id, data in predictions.items()
            ],
            "top_recommendations": top_recommendations[:10],  # Top 10
            "summary": {
                "total_matches": len(predictions),
                "leagues_covered": len(leagues_analyzed),
                "high_confidence_picks": len([p for p in predictions.values() if p['predictions'].get('confidence_overall', 0) > 0.6]),
                "strong_recommendations": len(top_recommendations)
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar previsões: {str(e)}")

@router.get("/live-monitoring")
async def get_live_monitoring_status():
    """
    🔴 Status do Monitoramento Ao Vivo

    Retorna status atual do monitoramento global:
    - Jogos sendo monitorados em tempo real
    - Últimas atualizações
    - Resultados coletados
    """
    try:
        live_matches = global_match_system.live_matches
        active_matches = [match for match in global_match_system.active_matches.values()
                         if match.status in ['IN_PLAY', 'PAUSED', 'LIVE']]

        return {
            "success": True,
            "live_monitoring_active": len(live_matches) > 0,
            "matches_being_monitored": len(active_matches),
            "live_matches": [
                {
                    "match_id": match_id,
                    "minute": data.minute,
                    "score": f"{data.home_score}-{data.away_score}",
                    "status": data.status,
                    "last_updated": data.last_updated.isoformat()
                }
                for match_id, data in live_matches.items()
            ],
            "upcoming_matches": [
                {
                    "home_team": match.home_team_name,
                    "away_team": match.away_team_name,
                    "league": match.league_name,
                    "kickoff": match.match_date.isoformat(),
                    "predictions_ready": match.predictions_generated
                }
                for match in active_matches[:5]  # Próximos 5
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no status de monitoramento: {str(e)}")

@router.post("/start-monitoring")
async def start_global_monitoring_endpoint(background_tasks: BackgroundTasks):
    """
    🔴 Iniciar Monitoramento Global

    Inicia o monitoramento contínuo de jogos ao vivo em todas as ligas:
    - Atualização a cada 30 segundos
    - Coleta automática de resultados
    - Preparação de dados para retreino
    """
    try:
        # Iniciar monitoramento em background
        background_tasks.add_task(start_global_monitoring)

        return {
            "success": True,
            "message": "Monitoramento global iniciado",
            "monitoring_scope": "Todas as ligas suportadas",
            "update_interval": "30 segundos",
            "features": [
                "Monitoramento em tempo real",
                "Coleta automática de resultados",
                "Dados para retreino de ML",
                "Alertas de jogos importantes"
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao iniciar monitoramento: {str(e)}")

@router.post("/daily-analysis")
async def run_daily_analysis_endpoint(background_tasks: BackgroundTasks):
    """
    📊 Análise Diária Completa

    Executa pipeline completo de análise diária:
    1. Descoberta de jogos em todas as ligas
    2. Geração de previsões para todos os mercados
    3. Atualização do status do sistema
    4. Preparação para monitoramento
    """
    try:
        # Executar análise em background
        background_tasks.add_task(run_daily_analysis)

        return {
            "success": True,
            "message": "Análise diária iniciada",
            "process": [
                "🔍 Descobrindo jogos globalmente",
                "🧠 Gerando previsões com ML",
                "📊 Analisando 13+ mercados por jogo",
                "🎯 Criando recomendações otimizadas",
                "💾 Salvando dados estruturados"
            ],
            "estimated_duration": "5-15 minutos",
            "scope": "Mundial - todas as ligas suportadas"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na análise diária: {str(e)}")

@router.get("/leagues")
async def get_supported_leagues():
    """
    🏆 Ligas Suportadas

    Lista todas as ligas e competições monitoradas pelo sistema
    """
    return {
        "success": True,
        "total_leagues": len(global_match_system.supported_leagues),
        "leagues": [
            {
                "id": league.id,
                "name": league.name,
                "country": league.country,
                "tier": league.tier,
                "active": league.active,
                "api_code": league.api_code
            }
            for league in global_match_system.supported_leagues
        ],
        "coverage": {
            "continents": list(set(league.country for league in global_match_system.supported_leagues)),
            "tier_1_leagues": len([l for l in global_match_system.supported_leagues if l.tier == 1]),
            "tier_2_leagues": len([l for l in global_match_system.supported_leagues if l.tier == 2])
        }
    }

@router.get("/predictions/{match_id}")
async def get_match_prediction_by_id(match_id: str):
    """
    🎯 Previsão de Jogo Específico

    Retorna previsão detalhada para um jogo específico
    """
    try:
        # Buscar jogo
        if match_id not in global_match_system.active_matches:
            raise HTTPException(status_code=404, detail="Jogo não encontrado")

        match = global_match_system.active_matches[match_id]

        if not match.predictions_generated:
            raise HTTPException(status_code=404, detail="Previsões ainda não foram geradas para este jogo")

        # Aqui você buscaria as previsões salvas ou geraria na hora
        # Por simplicidade, vou gerar uma resposta básica

        return {
            "success": True,
            "match_info": {
                "id": match.id,
                "home_team": match.home_team_name,
                "away_team": match.away_team_name,
                "league": match.league_name,
                "date": match.match_date.isoformat(),
                "venue": match.venue
            },
            "predictions_available": match.predictions_generated,
            "message": "Use o endpoint /generate-predictions para obter previsões detalhadas"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar previsão: {str(e)}")

@router.get("/today")
async def get_today_analysis():
    """
    📅 Análise de Hoje

    Retorna resumo completo dos jogos e previsões para hoje
    """
    try:
        today = datetime.now()

        # Jogos de hoje
        today_matches = [
            match for match in global_match_system.active_matches.values()
            if match.match_date.date() == today.date()
        ]

        # Separar por status
        scheduled = [m for m in today_matches if m.status in ['SCHEDULED', 'TIMED']]
        live = [m for m in today_matches if m.status in ['IN_PLAY', 'PAUSED', 'LIVE']]
        finished = [m for m in today_matches if m.status in ['FINISHED', 'FULL_TIME']]

        # Ligas representadas
        leagues_today = list(set(match.league_name for match in today_matches))

        return {
            "success": True,
            "date": today.strftime('%Y-%m-%d'),
            "summary": {
                "total_matches": len(today_matches),
                "scheduled": len(scheduled),
                "live": len(live),
                "finished": len(finished),
                "leagues_active": len(leagues_today)
            },
            "leagues_today": leagues_today,
            "live_matches": [
                {
                    "home_team": match.home_team_name,
                    "away_team": match.away_team_name,
                    "league": match.league_name,
                    "status": match.status
                }
                for match in live
            ],
            "upcoming_matches": [
                {
                    "home_team": match.home_team_name,
                    "away_team": match.away_team_name,
                    "league": match.league_name,
                    "kickoff": match.match_date.strftime('%H:%M'),
                    "predictions_ready": match.predictions_generated
                }
                for match in scheduled[:10]  # Próximos 10
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na análise de hoje: {str(e)}")