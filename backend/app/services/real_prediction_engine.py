"""
🧠 REAL PREDICTION ENGINE - CÉREBRO DO SISTEMA
Integração completa com APIs reais para análises e predições baseadas em dados ao vivo
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from scipy import stats
import math
import asyncio

# Serviços de dados reais
from app.services.football_data_service import FootballDataService
from app.services.odds_service import OddsService
from app.services.weather_service import WeatherService
from app.core.config import settings

class RealPredictionEngine:
    """
    Motor de predições com dados reais das APIs
    Combina Football-Data.org + The Odds API + análise estatística avançada
    """

    def __init__(self, db: Session = None):
        self.db = db
        self.football_data = FootballDataService()
        self.odds_service = OddsService()
        self.weather_service = WeatherService()

        # Parâmetros de análise
        self.min_matches_for_analysis = 5
        self.max_matches_analyzed = 15
        self.confidence_threshold = 0.65

    async def generate_real_prediction(self, match_id: str, home_team_id: str, away_team_id: str, match_date: datetime, venue: str = None) -> Dict:
        """
        🎯 FUNÇÃO PRINCIPAL - Gera predição completa com dados reais
        """
        print(f"🧠 Iniciando análise real para Match ID: {match_id}")

        try:
            # 1. COLETA DE DADOS REAIS
            prediction_data = await self._collect_real_data(home_team_id, away_team_id, match_date, venue)

            # 2. ANÁLISE ESTATÍSTICA AVANÇADA
            statistical_analysis = await self._advanced_statistical_analysis(prediction_data)

            # 3. INTEGRAÇÃO COM ODDS REAIS
            odds_analysis = await self._integrate_real_odds(home_team_id, away_team_id)

            # 4. CÁLCULO DE PREDIÇÕES
            predictions = await self._calculate_real_predictions(prediction_data, statistical_analysis, odds_analysis)

            # 5. SISTEMA DE CONFIANÇA DINÂMICO
            confidence_system = await self._dynamic_confidence_system(prediction_data, predictions)

            # 6. ANÁLISE DE RISCOS REAL
            risk_analysis = await self._real_risk_analysis(prediction_data, odds_analysis)

            # 7. RESULTADO FINAL
            final_prediction = {
                "match_id": match_id,
                "prediction_timestamp": datetime.now().isoformat(),
                "data_source": "REAL_APIS",
                "engine_version": "2.0",

                # Predições principais
                "match_outcome": predictions["match_outcome"],
                "goals_prediction": predictions["goals_prediction"],
                "btts_prediction": predictions["btts_prediction"],
                "corners_prediction": predictions["corners_prediction"],

                # Análise de dados
                "team_analysis": prediction_data["team_analysis"],
                "form_analysis": prediction_data["form_analysis"],
                "h2h_analysis": prediction_data["h2h_analysis"],
                "statistical_analysis": statistical_analysis,
                "odds_analysis": odds_analysis,
                "weather_impact": prediction_data.get("weather_impact", {}),

                # Sistema de confiança
                "confidence_system": confidence_system,
                "risk_analysis": risk_analysis,

                # Fatores-chave
                "key_factors": await self._identify_key_factors(prediction_data, predictions),
                "betting_recommendations": await self._generate_betting_recommendations(predictions, confidence_system, risk_analysis)
            }

            print(f"✅ Predição real gerada com sucesso - Confiança: {confidence_system['overall_confidence']}")
            return final_prediction

        except Exception as e:
            print(f"❌ Erro na predição real: {str(e)}")
            return await self._fallback_prediction(match_id, home_team_id, away_team_id)

    async def _collect_real_data(self, home_team_id: str, away_team_id: str, match_date: datetime, venue: str) -> Dict:
        """
        📊 Coleta dados reais de todas as APIs
        """
        print("📊 Coletando dados reais das APIs...")

        # Executar chamadas paralelas para otimizar performance
        tasks = [
            self._get_team_real_form(home_team_id, "home"),
            self._get_team_real_form(away_team_id, "away"),
            self._get_real_h2h_data(home_team_id, away_team_id),
            self._get_real_weather_data(venue, match_date) if venue else None
        ]

        # Remover tasks None
        tasks = [task for task in tasks if task is not None]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        home_form = results[0] if isinstance(results[0], dict) else {}
        away_form = results[1] if isinstance(results[1], dict) else {}
        h2h_data = results[2] if isinstance(results[2], dict) else {}
        weather_data = results[3] if len(results) > 3 and isinstance(results[3], dict) else {}

        return {
            "team_analysis": {
                "home": home_form,
                "away": away_form
            },
            "form_analysis": {
                "home": home_form.get("recent_form", {}),
                "away": away_form.get("recent_form", {})
            },
            "h2h_analysis": h2h_data,
            "weather_impact": weather_data,
            "data_quality": {
                "home_matches": home_form.get("matches_analyzed", 0),
                "away_matches": away_form.get("matches_analyzed", 0),
                "h2h_matches": h2h_data.get("matches_analyzed", 0),
                "weather_available": bool(weather_data)
            }
        }

    async def _get_team_real_form(self, team_id: str, side: str) -> Dict:
        """
        🏃‍♂️ Análise de forma real usando Football-Data.org
        """
        try:
            # Buscar partidas recentes do time
            matches = await self.football_data.get_team_matches(team_id, limit=self.max_matches_analyzed)

            if not matches:
                return {"error": "No matches found", "matches_analyzed": 0}

            # Filtrar apenas jogos finalizados
            finished_matches = [m for m in matches if m.get("status") == "FINISHED"]

            if len(finished_matches) < self.min_matches_for_analysis:
                return {"error": "Insufficient data", "matches_analyzed": len(finished_matches)}

            # Análise estatística detalhada
            analysis = await self._analyze_team_performance(finished_matches, team_id, side)
            analysis["matches_analyzed"] = len(finished_matches)
            analysis["data_source"] = "football-data.org"

            return analysis

        except Exception as e:
            print(f"⚠️ Erro ao analisar forma do time {team_id}: {str(e)}")
            return {"error": str(e), "matches_analyzed": 0}

    async def _analyze_team_performance(self, matches: List[Dict], team_id: str, side: str) -> Dict:
        """
        📈 Análise estatística profunda do desempenho
        """
        stats = {
            "goals_scored": [],
            "goals_conceded": [],
            "wins": 0,
            "draws": 0,
            "losses": 0,
            "clean_sheets": 0,
            "failed_to_score": 0,
            "home_games": 0,
            "away_games": 0,
            "form_points": [],
            "recent_form_string": "",
            "goal_difference": []
        }

        # Processar cada partida
        for match in matches[:self.max_matches_analyzed]:
            home_team_id = str(match.get("homeTeam", {}).get("id", ""))
            away_team_id = str(match.get("awayTeam", {}).get("id", ""))

            is_home = home_team_id == team_id
            is_away = away_team_id == team_id

            if not (is_home or is_away):
                continue

            # Gols
            home_score = match.get("score", {}).get("fullTime", {}).get("home", 0) or 0
            away_score = match.get("score", {}).get("fullTime", {}).get("away", 0) or 0

            if is_home:
                stats["goals_scored"].append(home_score)
                stats["goals_conceded"].append(away_score)
                stats["home_games"] += 1
                goal_diff = home_score - away_score
            else:
                stats["goals_scored"].append(away_score)
                stats["goals_conceded"].append(home_score)
                stats["away_games"] += 1
                goal_diff = away_score - home_score

            stats["goal_difference"].append(goal_diff)

            # Resultado
            if goal_diff > 0:
                stats["wins"] += 1
                stats["form_points"].append(3)
                stats["recent_form_string"] += "W"
            elif goal_diff == 0:
                stats["draws"] += 1
                stats["form_points"].append(1)
                stats["recent_form_string"] += "D"
            else:
                stats["losses"] += 1
                stats["form_points"].append(0)
                stats["recent_form_string"] += "L"

            # Clean sheets e falha em marcar
            if (is_home and away_score == 0) or (is_away and home_score == 0):
                stats["clean_sheets"] += 1

            if (is_home and home_score == 0) or (is_away and away_score == 0):
                stats["failed_to_score"] += 1

        # Calcular métricas
        total_games = len(stats["goals_scored"])

        if total_games == 0:
            return {"error": "No valid matches found"}

        # Métricas básicas
        avg_goals_scored = np.mean(stats["goals_scored"])
        avg_goals_conceded = np.mean(stats["goals_conceded"])
        avg_goal_difference = np.mean(stats["goal_difference"])

        # Forma recente (últimos 5 jogos)
        recent_points = stats["form_points"][-5:] if len(stats["form_points"]) >= 5 else stats["form_points"]
        form_trend = np.mean(recent_points) if recent_points else 0

        # Tendência de gols (regressão linear simples)
        if len(stats["goals_scored"]) >= 3:
            x = np.arange(len(stats["goals_scored"]))
            goals_trend = np.polyfit(x, stats["goals_scored"], 1)[0]  # Coeficiente angular
        else:
            goals_trend = 0

        return {
            "recent_form": {
                "matches_analyzed": total_games,
                "wins": stats["wins"],
                "draws": stats["draws"],
                "losses": stats["losses"],
                "win_rate": stats["wins"] / total_games,
                "form_string": stats["recent_form_string"][-10:],  # Últimos 10 jogos
                "form_trend": form_trend,
                "points_per_game": np.mean(stats["form_points"])
            },
            "attack_metrics": {
                "goals_per_game": round(avg_goals_scored, 2),
                "goals_trend": round(goals_trend, 3),
                "failed_to_score_rate": stats["failed_to_score"] / total_games,
                "games_over_1_5_goals": sum(1 for g in stats["goals_scored"] if g >= 2) / total_games,
                "games_over_2_5_goals": sum(1 for g in stats["goals_scored"] if g >= 3) / total_games
            },
            "defense_metrics": {
                "goals_conceded_per_game": round(avg_goals_conceded, 2),
                "clean_sheet_rate": stats["clean_sheets"] / total_games,
                "games_under_1_5_conceded": sum(1 for g in stats["goals_conceded"] if g <= 1) / total_games
            },
            "overall_metrics": {
                "goal_difference_per_game": round(avg_goal_difference, 2),
                "home_record": f"{stats['home_games']} games" if stats['home_games'] > 0 else "No home games",
                "away_record": f"{stats['away_games']} games" if stats['away_games'] > 0 else "No away games",
                "consistency_score": 1 - (np.std(stats["form_points"]) / 3) if len(stats["form_points"]) > 1 else 0.5
            }
        }

    async def _get_real_h2h_data(self, home_team_id: str, away_team_id: str) -> Dict:
        """
        🤝 Análise de confrontos diretos reais
        """
        try:
            h2h_matches = await self.football_data.get_head_to_head(home_team_id, away_team_id, limit=15)

            if not h2h_matches:
                return {"matches_analyzed": 0, "data_source": "football-data.org"}

            # Filtrar jogos finalizados
            finished_h2h = [m for m in h2h_matches if m.get("status") == "FINISHED"]

            if len(finished_h2h) == 0:
                return {"matches_analyzed": 0, "data_source": "football-data.org"}

            # Análise dos confrontos
            home_wins = 0
            away_wins = 0
            draws = 0
            total_goals = []
            btts_count = 0

            for match in finished_h2h:
                home_score = match.get("score", {}).get("fullTime", {}).get("home", 0) or 0
                away_score = match.get("score", {}).get("fullTime", {}).get("away", 0) or 0
                match_home_id = str(match.get("homeTeam", {}).get("id", ""))

                # Ajustar perspectiva (quem era mandante no histórico)
                if match_home_id == home_team_id:
                    # Home team era mandante
                    if home_score > away_score:
                        home_wins += 1
                    elif away_score > home_score:
                        away_wins += 1
                    else:
                        draws += 1
                else:
                    # Home team era visitante
                    if away_score > home_score:
                        home_wins += 1
                    elif home_score > away_score:
                        away_wins += 1
                    else:
                        draws += 1

                total_goals.append(home_score + away_score)
                if home_score > 0 and away_score > 0:
                    btts_count += 1

            total_matches = len(finished_h2h)

            return {
                "matches_analyzed": total_matches,
                "home_team_wins": home_wins,
                "away_team_wins": away_wins,
                "draws": draws,
                "home_win_rate": home_wins / total_matches,
                "away_win_rate": away_wins / total_matches,
                "draw_rate": draws / total_matches,
                "avg_goals_per_match": np.mean(total_goals) if total_goals else 0,
                "btts_rate": btts_count / total_matches,
                "over_2_5_rate": sum(1 for g in total_goals if g > 2.5) / total_matches,
                "data_source": "football-data.org",
                "most_recent_matches": finished_h2h[:5]  # 5 mais recentes para contexto
            }

        except Exception as e:
            print(f"⚠️ Erro na análise H2H: {str(e)}")
            return {"matches_analyzed": 0, "error": str(e)}

    async def _get_real_weather_data(self, venue: str, match_date: datetime) -> Dict:
        """
        🌤️ Dados meteorológicos reais (quando disponível)
        """
        try:
            if not venue or not settings.WEATHER_API_KEY or settings.WEATHER_API_KEY == "sua_chave_openweather_aqui":
                return {"available": False, "reason": "No API key or venue"}

            weather_data = await self.weather_service.get_match_weather(venue, "GB", match_date)
            return weather_data

        except Exception as e:
            print(f"⚠️ Erro nos dados meteorológicos: {str(e)}")
            return {"available": False, "error": str(e)}

    async def _advanced_statistical_analysis(self, prediction_data: Dict) -> Dict:
        """
        📊 Análise estatística avançada com cálculos reais
        """
        home_data = prediction_data["team_analysis"]["home"]
        away_data = prediction_data["team_analysis"]["away"]

        # Força de ataque vs defesa
        home_attack = home_data.get("attack_metrics", {}).get("goals_per_game", 1.0)
        home_defense = home_data.get("defense_metrics", {}).get("goals_conceded_per_game", 1.0)
        away_attack = away_data.get("attack_metrics", {}).get("goals_per_game", 1.0)
        away_defense = away_data.get("defense_metrics", {}).get("goals_conceded_per_game", 1.0)

        # Cálculo de xG esperado baseado na força real dos times
        home_xg = (home_attack + away_defense) / 2
        away_xg = (away_attack + home_defense) / 2

        # Análise de momentum (tendência recente)
        home_form_trend = home_data.get("recent_form", {}).get("form_trend", 1.5)
        away_form_trend = away_data.get("recent_form", {}).get("form_trend", 1.5)
        momentum_factor = (home_form_trend - away_form_trend) / 3.0

        # Consistência dos times
        home_consistency = home_data.get("overall_metrics", {}).get("consistency_score", 0.5)
        away_consistency = away_data.get("overall_metrics", {}).get("consistency_score", 0.5)

        return {
            "expected_goals": {
                "home_xg": round(home_xg, 2),
                "away_xg": round(away_xg, 2),
                "total_xg": round(home_xg + away_xg, 2)
            },
            "momentum_analysis": {
                "home_momentum": round(home_form_trend, 2),
                "away_momentum": round(away_form_trend, 2),
                "momentum_advantage": round(momentum_factor, 3)
            },
            "consistency_metrics": {
                "home_consistency": round(home_consistency, 3),
                "away_consistency": round(away_consistency, 3),
                "reliability_factor": round((home_consistency + away_consistency) / 2, 3)
            },
            "strength_comparison": {
                "attack_advantage": round((home_attack - away_attack), 2),
                "defense_advantage": round((away_defense - home_defense), 2),
                "overall_balance": round((home_attack - home_defense) - (away_attack - away_defense), 2)
            }
        }

    async def _integrate_real_odds(self, home_team_id: str, away_team_id: str) -> Dict:
        """
        💰 Integração com odds reais do The Odds API
        """
        try:
            # Buscar odds reais para o jogo
            odds_data = await self.odds_service.get_match_odds(f"{home_team_id}_vs_{away_team_id}")

            if not odds_data or "error" in odds_data:
                return {"available": False, "source": "the-odds-api", "reason": "No odds found"}

            # Processar odds para análise de valor
            market_analysis = await self._analyze_betting_market(odds_data)

            return {
                "available": True,
                "source": "the-odds-api",
                "raw_odds": odds_data,
                "market_analysis": market_analysis,
                "value_opportunities": await self._identify_value_bets(odds_data, market_analysis)
            }

        except Exception as e:
            print(f"⚠️ Erro na integração de odds: {str(e)}")
            return {"available": False, "error": str(e)}

    async def _analyze_betting_market(self, odds_data: Dict) -> Dict:
        """
        📈 Análise do mercado de apostas
        """
        # Converter odds para probabilidades implícitas
        home_odds = odds_data.get("home_win_odds", 2.0)
        draw_odds = odds_data.get("draw_odds", 3.0)
        away_odds = odds_data.get("away_win_odds", 2.5)

        home_prob = 1 / home_odds
        draw_prob = 1 / draw_odds
        away_prob = 1 / away_odds

        # Margem da casa de apostas
        total_prob = home_prob + draw_prob + away_prob
        bookmaker_margin = (total_prob - 1) * 100

        # Probabilidades verdadeiras (sem margem)
        true_home_prob = home_prob / total_prob
        true_draw_prob = draw_prob / total_prob
        true_away_prob = away_prob / total_prob

        return {
            "implied_probabilities": {
                "home_win": round(home_prob, 4),
                "draw": round(draw_prob, 4),
                "away_win": round(away_prob, 4)
            },
            "true_probabilities": {
                "home_win": round(true_home_prob, 4),
                "draw": round(true_draw_prob, 4),
                "away_win": round(true_away_prob, 4)
            },
            "market_metrics": {
                "bookmaker_margin": round(bookmaker_margin, 2),
                "market_efficiency": round((1 - bookmaker_margin/100) * 100, 1),
                "favorite": "home" if home_odds < min(draw_odds, away_odds) else ("away" if away_odds < draw_odds else "draw")
            }
        }

    async def _identify_value_bets(self, odds_data: Dict, market_analysis: Dict) -> List[Dict]:
        """
        💎 Identificação de apostas de valor
        """
        value_opportunities = []

        # Esta função será expandida quando tivermos nossas próprias probabilidades calculadas
        # Por enquanto, retorna análise básica do mercado

        margin = market_analysis["market_metrics"]["bookmaker_margin"]

        if margin < 5:
            value_opportunities.append({
                "type": "low_margin_market",
                "description": "Mercado com margem baixa - mais favorável ao apostador",
                "value_score": round((5 - margin) / 5, 2)
            })

        return value_opportunities

    async def _calculate_real_predictions(self, prediction_data: Dict, statistical_analysis: Dict, odds_analysis: Dict) -> Dict:
        """
        🎯 Cálculo das predições baseado em dados reais
        """
        # Dados dos times
        home_data = prediction_data["team_analysis"]["home"]
        away_data = prediction_data["team_analysis"]["away"]
        h2h_data = prediction_data["h2h_analysis"]

        # Predição de resultado (1X2)
        match_outcome = await self._predict_real_match_outcome(home_data, away_data, h2h_data, statistical_analysis, odds_analysis)

        # Predição de gols
        goals_prediction = await self._predict_real_goals(home_data, away_data, h2h_data, statistical_analysis)

        # Predição BTTS
        btts_prediction = await self._predict_real_btts(home_data, away_data, h2h_data, statistical_analysis)

        # Predição de escanteios (estimativa baseada nos dados disponíveis)
        corners_prediction = await self._predict_real_corners(home_data, away_data, statistical_analysis)

        return {
            "match_outcome": match_outcome,
            "goals_prediction": goals_prediction,
            "btts_prediction": btts_prediction,
            "corners_prediction": corners_prediction
        }

    async def _predict_real_match_outcome(self, home_data: Dict, away_data: Dict, h2h_data: Dict, stat_analysis: Dict, odds_analysis: Dict) -> Dict:
        """
        🥅 Predição de resultado baseada em dados reais
        """
        # Base: vantagem de jogar em casa
        home_prob = 0.42
        draw_prob = 0.28
        away_prob = 0.30

        # Ajuste por forma recente
        home_form = home_data.get("recent_form", {}).get("points_per_game", 1.5)
        away_form = away_data.get("recent_form", {}).get("points_per_game", 1.5)
        form_diff = (home_form - away_form) / 3.0  # Normalizar

        # Ajuste por momentum
        momentum_advantage = stat_analysis.get("momentum_analysis", {}).get("momentum_advantage", 0)

        # Ajuste por força de ataque/defesa
        strength_balance = stat_analysis.get("strength_comparison", {}).get("overall_balance", 0)

        # Ajuste por histórico H2H
        h2h_adjustment = 0
        if h2h_data.get("matches_analyzed", 0) >= 3:
            h2h_home_rate = h2h_data.get("home_win_rate", 0.33)
            h2h_away_rate = h2h_data.get("away_win_rate", 0.33)
            h2h_adjustment = (h2h_home_rate - h2h_away_rate) * 0.1

        # Aplicar ajustes
        total_adjustment = (form_diff * 0.15) + (momentum_advantage * 0.1) + (strength_balance * 0.05) + h2h_adjustment

        home_prob += total_adjustment
        away_prob -= total_adjustment * 0.7
        draw_prob += total_adjustment * 0.3

        # Normalizar
        total = home_prob + draw_prob + away_prob
        home_prob /= total
        draw_prob /= total
        away_prob /= total

        # Comparar com odds do mercado
        market_comparison = {}
        if odds_analysis.get("available"):
            market_probs = odds_analysis.get("market_analysis", {}).get("true_probabilities", {})
            if market_probs:
                market_comparison = {
                    "our_home_prob": round(home_prob, 4),
                    "market_home_prob": market_probs.get("home_win", 0),
                    "value_home": round(home_prob - market_probs.get("home_win", 0), 4),
                    "our_away_prob": round(away_prob, 4),
                    "market_away_prob": market_probs.get("away_win", 0),
                    "value_away": round(away_prob - market_probs.get("away_win", 0), 4)
                }

        return {
            "home_win_probability": round(home_prob, 4),
            "draw_probability": round(draw_prob, 4),
            "away_win_probability": round(away_prob, 4),
            "predicted_outcome": "1" if home_prob > max(draw_prob, away_prob) else ("X" if draw_prob > away_prob else "2"),
            "confidence": round(max(home_prob, draw_prob, away_prob), 4),
            "market_comparison": market_comparison,
            "factors_applied": {
                "form_adjustment": round(form_diff * 0.15, 4),
                "momentum_adjustment": round(momentum_advantage * 0.1, 4),
                "strength_adjustment": round(strength_balance * 0.05, 4),
                "h2h_adjustment": round(h2h_adjustment, 4)
            }
        }

    async def _predict_real_goals(self, home_data: Dict, away_data: Dict, h2h_data: Dict, stat_analysis: Dict) -> Dict:
        """
        ⚽ Predição de gols baseada em xG real
        """
        # Usar xG calculado da análise estatística
        home_xg = stat_analysis.get("expected_goals", {}).get("home_xg", 1.2)
        away_xg = stat_analysis.get("expected_goals", {}).get("away_xg", 1.0)
        total_xg = home_xg + away_xg

        # Ajuste por histórico H2H
        if h2h_data.get("matches_analyzed", 0) >= 3:
            h2h_avg_goals = h2h_data.get("avg_goals_per_match", total_xg)
            total_xg = (total_xg + h2h_avg_goals) / 2

        # Calcular probabilidades usando distribuição de Poisson
        over_1_5_prob = 1 - stats.poisson.cdf(1, total_xg)
        over_2_5_prob = 1 - stats.poisson.cdf(2, total_xg)
        over_3_5_prob = 1 - stats.poisson.cdf(3, total_xg)

        return {
            "expected_home_goals": round(home_xg, 2),
            "expected_away_goals": round(away_xg, 2),
            "expected_total_goals": round(total_xg, 2),
            "over_1_5_probability": round(over_1_5_prob, 4),
            "under_1_5_probability": round(1 - over_1_5_prob, 4),
            "over_2_5_probability": round(over_2_5_prob, 4),
            "under_2_5_probability": round(1 - over_2_5_prob, 4),
            "over_3_5_probability": round(over_3_5_prob, 4),
            "under_3_5_probability": round(1 - over_3_5_prob, 4),
            "most_likely_total": int(total_xg) if total_xg % 1 < 0.5 else int(total_xg) + 1
        }

    async def _predict_real_btts(self, home_data: Dict, away_data: Dict, h2h_data: Dict, stat_analysis: Dict) -> Dict:
        """
        🎯 Predição BTTS baseada em dados reais
        """
        # Taxa de gols por jogo de cada time
        home_scoring_rate = home_data.get("attack_metrics", {}).get("goals_per_game", 1.0)
        away_scoring_rate = away_data.get("attack_metrics", {}).get("goals_per_game", 1.0)

        # Taxa de clean sheets
        home_cs_rate = home_data.get("defense_metrics", {}).get("clean_sheet_rate", 0.3)
        away_cs_rate = away_data.get("defense_metrics", {}).get("clean_sheet_rate", 0.3)

        # Probabilidade básica de BTTS
        btts_prob = min(home_scoring_rate / 1.5, 0.9) * min(away_scoring_rate / 1.5, 0.9)
        btts_prob *= (1 - home_cs_rate * 0.5) * (1 - away_cs_rate * 0.5)

        # Ajuste por histórico H2H
        if h2h_data.get("matches_analyzed", 0) >= 3:
            h2h_btts_rate = h2h_data.get("btts_rate", btts_prob)
            btts_prob = (btts_prob + h2h_btts_rate) / 2

        # Manter dentro de limites realistas
        btts_prob = max(0.05, min(0.95, btts_prob))

        return {
            "btts_yes_probability": round(btts_prob, 4),
            "btts_no_probability": round(1 - btts_prob, 4),
            "predicted_outcome": "Yes" if btts_prob > 0.5 else "No",
            "confidence": round(max(btts_prob, 1 - btts_prob), 4),
            "contributing_factors": {
                "home_scoring_strength": home_scoring_rate,
                "away_scoring_strength": away_scoring_rate,
                "defensive_records": f"Home CS: {home_cs_rate:.1%}, Away CS: {away_cs_rate:.1%}"
            }
        }

    async def _predict_real_corners(self, home_data: Dict, away_data: Dict, stat_analysis: Dict) -> Dict:
        """
        🚩 Predição de escanteios (estimativa baseada em ataque/defesa)
        """
        # Estimativa baseada na força de ataque (times que atacam mais = mais escanteios)
        home_attack = home_data.get("attack_metrics", {}).get("goals_per_game", 1.0)
        away_attack = away_data.get("attack_metrics", {}).get("goals_per_game", 1.0)

        # Estimativa de escanteios baseada em padrões gerais (5-6 escanteios por gol marcado)
        estimated_corners = (home_attack + away_attack) * 5.5

        # Ajustar baseado na consistência dos times
        consistency = stat_analysis.get("consistency_metrics", {}).get("reliability_factor", 0.5)
        estimated_corners *= (0.8 + consistency * 0.4)  # Mais consistência = mais previsível

        # Probabilidades
        over_8_5_prob = 1 - stats.poisson.cdf(8, estimated_corners)
        over_9_5_prob = 1 - stats.poisson.cdf(9, estimated_corners)
        over_10_5_prob = 1 - stats.poisson.cdf(10, estimated_corners)

        return {
            "expected_total_corners": round(estimated_corners, 1),
            "over_8_5_probability": round(over_8_5_prob, 4),
            "under_8_5_probability": round(1 - over_8_5_prob, 4),
            "over_9_5_probability": round(over_9_5_prob, 4),
            "under_9_5_probability": round(1 - over_9_5_prob, 4),
            "over_10_5_probability": round(over_10_5_prob, 4),
            "under_10_5_probability": round(1 - over_10_5_prob, 4),
            "note": "Estimativa baseada em força de ataque dos times"
        }

    async def _dynamic_confidence_system(self, prediction_data: Dict, predictions: Dict) -> Dict:
        """
        🎯 Sistema de confiança dinâmico baseado na qualidade dos dados
        """
        confidence_factors = []

        # Qualidade dos dados
        data_quality = prediction_data.get("data_quality", {})

        home_matches = data_quality.get("home_matches", 0)
        away_matches = data_quality.get("away_matches", 0)
        h2h_matches = data_quality.get("h2h_matches", 0)

        # Confiança baseada no número de jogos analisados
        if home_matches >= 10 and away_matches >= 10:
            confidence_factors.append(("data_volume", 0.9))
        elif home_matches >= 5 and away_matches >= 5:
            confidence_factors.append(("data_volume", 0.7))
        else:
            confidence_factors.append(("data_volume", 0.4))

        # Confiança H2H
        if h2h_matches >= 5:
            confidence_factors.append(("h2h_history", 0.8))
        elif h2h_matches >= 3:
            confidence_factors.append(("h2h_history", 0.6))
        else:
            confidence_factors.append(("h2h_history", 0.3))

        # Confiança baseada na clareza da predição
        outcome_confidence = predictions.get("match_outcome", {}).get("confidence", 0.5)
        if outcome_confidence > 0.6:
            confidence_factors.append(("prediction_clarity", 0.8))
        elif outcome_confidence > 0.45:
            confidence_factors.append(("prediction_clarity", 0.6))
        else:
            confidence_factors.append(("prediction_clarity", 0.4))

        # Consistência dos times
        home_consistency = prediction_data["team_analysis"]["home"].get("overall_metrics", {}).get("consistency_score", 0.5)
        away_consistency = prediction_data["team_analysis"]["away"].get("overall_metrics", {}).get("consistency_score", 0.5)
        avg_consistency = (home_consistency + away_consistency) / 2
        confidence_factors.append(("team_consistency", avg_consistency))

        # Calcular confiança geral
        overall_confidence = sum(score for _, score in confidence_factors) / len(confidence_factors)

        # Classificação de confiança
        if overall_confidence >= 0.75:
            confidence_level = "HIGH"
        elif overall_confidence >= 0.55:
            confidence_level = "MEDIUM"
        else:
            confidence_level = "LOW"

        return {
            "overall_confidence": round(overall_confidence, 3),
            "confidence_level": confidence_level,
            "confidence_factors": dict(confidence_factors),
            "recommendation": self._get_confidence_recommendation(confidence_level, overall_confidence)
        }

    def _get_confidence_recommendation(self, level: str, score: float) -> str:
        """
        📋 Recomendação baseada no nível de confiança
        """
        if level == "HIGH":
            return "Alta confiança - Predições muito confiáveis com dados sólidos"
        elif level == "MEDIUM":
            return "Confiança moderada - Predições úteis, mas considere fatores adicionais"
        else:
            return "Baixa confiança - Use com cautela, dados limitados disponíveis"

    async def _real_risk_analysis(self, prediction_data: Dict, odds_analysis: Dict) -> Dict:
        """
        ⚠️ Análise de riscos baseada em dados reais
        """
        risk_factors = []
        risk_score = 0.0

        # Risco por dados limitados
        data_quality = prediction_data.get("data_quality", {})
        home_matches = data_quality.get("home_matches", 0)
        away_matches = data_quality.get("away_matches", 0)

        if home_matches < 8 or away_matches < 8:
            risk_factors.append("Dados limitados de forma recente")
            risk_score += 0.3

        # Risco por falta de histórico H2H
        h2h_matches = data_quality.get("h2h_matches", 0)
        if h2h_matches < 3:
            risk_factors.append("Histórico de confrontos limitado")
            risk_score += 0.2

        # Risco por inconsistência dos times
        home_data = prediction_data["team_analysis"]["home"]
        away_data = prediction_data["team_analysis"]["away"]

        home_consistency = home_data.get("overall_metrics", {}).get("consistency_score", 0.5)
        away_consistency = away_data.get("overall_metrics", {}).get("consistency_score", 0.5)

        if home_consistency < 0.4 or away_consistency < 0.4:
            risk_factors.append("Times com desempenho inconsistente")
            risk_score += 0.3

        # Risco por mercado de apostas (se disponível)
        if odds_analysis.get("available"):
            margin = odds_analysis.get("market_analysis", {}).get("market_metrics", {}).get("bookmaker_margin", 0)
            if margin > 8:
                risk_factors.append("Margem alta das casas de apostas")
                risk_score += 0.2

        # Determinar nível de risco
        if risk_score < 0.3:
            risk_level = "LOW"
        elif risk_score < 0.7:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"

        return {
            "risk_score": round(risk_score, 2),
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "risk_mitigation": self._get_risk_mitigation(risk_level, risk_factors)
        }

    def _get_risk_mitigation(self, level: str, factors: List[str]) -> List[str]:
        """
        🛡️ Estratégias de mitigação de risco
        """
        mitigation = []

        if "Dados limitados" in str(factors):
            mitigation.append("Aguardar mais jogos para análise mais precisa")

        if "inconsistente" in str(factors):
            mitigation.append("Focar em mercados de baixo risco (ex: total de gols)")

        if "Histórico" in str(factors):
            mitigation.append("Dar mais peso à forma recente dos times")

        if level == "HIGH":
            mitigation.append("Evitar apostas ou usar stakes muito baixos")

        return mitigation

    async def _identify_key_factors(self, prediction_data: Dict, predictions: Dict) -> List[str]:
        """
        🔑 Identificar fatores-chave da análise
        """
        factors = []

        home_data = prediction_data["team_analysis"]["home"]
        away_data = prediction_data["team_analysis"]["away"]

        # Diferença de forma
        home_points = home_data.get("recent_form", {}).get("points_per_game", 1.5)
        away_points = away_data.get("recent_form", {}).get("points_per_game", 1.5)

        if abs(home_points - away_points) > 0.7:
            better_form = "Home" if home_points > away_points else "Away"
            factors.append(f"{better_form} team em forma significativamente melhor")

        # Força de ataque
        home_attack = home_data.get("attack_metrics", {}).get("goals_per_game", 1.0)
        away_attack = away_data.get("attack_metrics", {}).get("goals_per_game", 1.0)

        if home_attack > 2.0:
            factors.append("Home team com ataque forte (>2.0 gols/jogo)")
        if away_attack > 2.0:
            factors.append("Away team com ataque forte (>2.0 gols/jogo)")

        # Defesa sólida
        home_cs_rate = home_data.get("defense_metrics", {}).get("clean_sheet_rate", 0.3)
        away_cs_rate = away_data.get("defense_metrics", {}).get("clean_sheet_rate", 0.3)

        if home_cs_rate > 0.5:
            factors.append("Home team com defesa sólida (>50% clean sheets)")
        if away_cs_rate > 0.5:
            factors.append("Away team com defesa sólida (>50% clean sheets)")

        # H2H dominância
        h2h_data = prediction_data["h2h_analysis"]
        if h2h_data.get("matches_analyzed", 0) >= 3:
            if h2h_data.get("home_win_rate", 0) > 0.6:
                factors.append(f"Home team domina H2H ({h2h_data.get('home_team_wins', 0)} vitórias)")
            elif h2h_data.get("away_win_rate", 0) > 0.6:
                factors.append(f"Away team domina H2H ({h2h_data.get('away_team_wins', 0)} vitórias)")

        return factors[:5]  # Top 5 fatores

    async def _generate_betting_recommendations(self, predictions: Dict, confidence_system: Dict, risk_analysis: Dict) -> List[Dict]:
        """
        💡 Gerar recomendações de apostas baseadas na análise
        """
        recommendations = []

        confidence_level = confidence_system["confidence_level"]
        risk_level = risk_analysis["risk_level"]

        # Recomendação principal (1X2)
        outcome = predictions["match_outcome"]
        outcome_confidence = outcome["confidence"]

        if confidence_level in ["HIGH", "MEDIUM"] and outcome_confidence > 0.55:
            recommended_bet = outcome["predicted_outcome"]
            probability = max(outcome["home_win_probability"], outcome["draw_probability"], outcome["away_win_probability"])

            recommendations.append({
                "market": "Match Result (1X2)",
                "recommendation": recommended_bet,
                "probability": probability,
                "confidence": confidence_level,
                "risk": risk_level,
                "reasoning": f"Análise indica {probability:.1%} de chance"
            })

        # Recomendação de gols
        goals = predictions["goals_prediction"]
        over_2_5_prob = goals["over_2_5_probability"]

        if over_2_5_prob > 0.65 or over_2_5_prob < 0.35:
            bet_type = "Over 2.5" if over_2_5_prob > 0.65 else "Under 2.5"
            prob = over_2_5_prob if over_2_5_prob > 0.65 else (1 - over_2_5_prob)

            recommendations.append({
                "market": "Total Goals O/U 2.5",
                "recommendation": bet_type,
                "probability": prob,
                "confidence": confidence_level,
                "risk": risk_level,
                "reasoning": f"xG analysis suggests {prob:.1%} chance"
            })

        # Recomendação BTTS
        btts = predictions["btts_prediction"]
        if btts["confidence"] > 0.6:
            recommendations.append({
                "market": "Both Teams to Score",
                "recommendation": btts["predicted_outcome"],
                "probability": max(btts["btts_yes_probability"], btts["btts_no_probability"]),
                "confidence": confidence_level,
                "risk": risk_level,
                "reasoning": f"Baseado em análise de força de ataque/defesa"
            })

        return recommendations

    async def _fallback_prediction(self, match_id: str, home_team_id: str, away_team_id: str) -> Dict:
        """
        🔄 Predição de fallback quando APIs falham
        """
        return {
            "match_id": match_id,
            "prediction_timestamp": datetime.now().isoformat(),
            "data_source": "FALLBACK_MODE",
            "engine_version": "2.0",

            "match_outcome": {
                "home_win_probability": 0.42,
                "draw_probability": 0.28,
                "away_win_probability": 0.30,
                "predicted_outcome": "1",
                "confidence": 0.42
            },

            "error": "Fallback mode - APIs indisponíveis",
            "recommendation": "Aguardar dados reais para análise mais precisa"
        }