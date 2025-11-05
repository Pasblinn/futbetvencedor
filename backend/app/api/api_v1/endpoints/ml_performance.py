"""
📊 ML PERFORMANCE ENDPOINTS
Endpoints para análise de performance e feedback do ML
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from app.core.database import get_db
from app.models import PredictionLog, ModelPerformance, Match
from app.services.prediction_logger import PredictionLogger

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/performance/overview")
async def get_ml_performance_overview(
    days_back: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    📊 Overview de Performance do ML
    
    Retorna métricas gerais de performance dos modelos ML
    """
    try:
        logger_service = PredictionLogger(db)
        
        # Buscar logs analisados do período
        cutoff_date = datetime.now() - timedelta(days=days_back)
        analyzed_logs = db.query(PredictionLog).filter(
            PredictionLog.analyzed_at.isnot(None),
            PredictionLog.created_at >= cutoff_date
        ).all()
        
        if not analyzed_logs:
            return {
                "message": "Nenhuma predição analisada no período",
                "period_days": days_back,
                "total_predictions": 0
            }
        
        # Calcular métricas gerais
        total_predictions = len(analyzed_logs)
        correct_predictions = len([log for log in analyzed_logs if log.was_correct])
        accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0
        
        avg_confidence = sum(log.confidence_score for log in analyzed_logs) / total_predictions
        avg_feedback_score = sum(log.feedback_score for log in analyzed_logs) / total_predictions
        
        # Performance por modelo
        models = {}
        for log in analyzed_logs:
            model_key = f"{log.model_name}_{log.model_version}"
            if model_key not in models:
                models[model_key] = {"total": 0, "correct": 0, "confidence_sum": 0}
            
            models[model_key]["total"] += 1
            if log.was_correct:
                models[model_key]["correct"] += 1
            models[model_key]["confidence_sum"] += log.confidence_score
        
        # Calcular acurácia por modelo
        model_performance = {}
        for model_key, stats in models.items():
            model_performance[model_key] = {
                "accuracy": stats["correct"] / stats["total"] if stats["total"] > 0 else 0,
                "avg_confidence": stats["confidence_sum"] / stats["total"],
                "total_predictions": stats["total"]
            }
        
        # Performance por liga
        leagues = {}
        for log in analyzed_logs:
            league = log.league
            if league not in leagues:
                leagues[league] = {"total": 0, "correct": 0}
            leagues[league]["total"] += 1
            if log.was_correct:
                leagues[league]["correct"] += 1
        
        league_performance = {}
        for league, stats in leagues.items():
            league_performance[league] = {
                "accuracy": stats["correct"] / stats["total"] if stats["total"] > 0 else 0,
                "total_predictions": stats["total"]
            }
        
        return {
            "period_days": days_back,
            "analysis_date": datetime.now().isoformat(),
            "total_predictions": total_predictions,
            "overall_accuracy": round(accuracy, 3),
            "avg_confidence": round(avg_confidence, 3),
            "avg_feedback_score": round(avg_feedback_score, 3),
            "model_performance": model_performance,
            "league_performance": league_performance,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error getting ML performance overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance/detailed")
async def get_detailed_ml_performance(
    model_name: Optional[str] = Query(None),
    model_version: Optional[str] = Query(None),
    days_back: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    📊 Performance Detalhada do ML
    
    Retorna análise detalhada de performance com insights
    """
    try:
        logger_service = PredictionLogger(db)
        
        # Gerar relatório de performance
        if model_name and model_version:
            performance_report = logger_service.generate_model_performance_report(
                model_name, model_version, days_back
            )
            
            if not performance_report:
                raise HTTPException(
                    status_code=404, 
                    detail=f"No performance data found for {model_name} {model_version}"
                )
            
            return {
                "model_name": performance_report.model_name,
                "model_version": performance_report.model_version,
                "analysis_period": {
                    "start": performance_report.analysis_period_start.isoformat(),
                    "end": performance_report.analysis_period_end.isoformat()
                },
                "metrics": {
                    "total_predictions": performance_report.total_predictions,
                    "correct_predictions": performance_report.correct_predictions,
                    "accuracy": performance_report.accuracy,
                    "avg_confidence": performance_report.avg_confidence,
                    "confidence_accuracy_correlation": performance_report.confidence_accuracy_correlation
                },
                "outcome_analysis": {
                    "home_win_accuracy": performance_report.home_win_accuracy,
                    "away_win_accuracy": performance_report.away_win_accuracy,
                    "draw_accuracy": performance_report.draw_accuracy
                },
                "league_performance": performance_report.league_performance,
                "insights": {
                    "key_insights": performance_report.key_insights,
                    "recommended_improvements": performance_report.recommended_improvements,
                    "feature_importance_analysis": performance_report.feature_importance_analysis
                },
                "generated_at": performance_report.created_at.isoformat(),
                "success": True
            }
        else:
            # Retornar performance de todos os modelos
            cutoff_date = datetime.now() - timedelta(days=days_back)
            performance_reports = db.query(ModelPerformance).filter(
                ModelPerformance.analysis_period_start >= cutoff_date
            ).order_by(ModelPerformance.created_at.desc()).all()
            
            reports_data = []
            for report in performance_reports:
                reports_data.append({
                    "model_name": report.model_name,
                    "model_version": report.model_version,
                    "accuracy": report.accuracy,
                    "total_predictions": report.total_predictions,
                    "avg_confidence": report.avg_confidence,
                    "generated_at": report.created_at.isoformat()
                })
            
            return {
                "period_days": days_back,
                "performance_reports": reports_data,
                "success": True
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting detailed ML performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/learning/insights")
async def get_ml_learning_insights(
    days_back: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    🧠 Insights de Aprendizado do ML
    
    Retorna insights e recomendações para melhoria do modelo
    """
    try:
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        # Buscar logs analisados
        analyzed_logs = db.query(PredictionLog).filter(
            PredictionLog.analyzed_at.isnot(None),
            PredictionLog.created_at >= cutoff_date
        ).all()
        
        if not analyzed_logs:
            return {
                "message": "Nenhuma predição analisada no período",
                "period_days": days_back,
                "insights": []
            }
        
        # Analisar padrões de erro
        incorrect_logs = [log for log in analyzed_logs if not log.was_correct]
        high_confidence_errors = [log for log in incorrect_logs if log.confidence_score > 0.7]
        
        # Análise de calibração
        well_calibrated = len([log for log in analyzed_logs if abs(log.confidence_vs_accuracy) < 0.2])
        calibration_rate = well_calibrated / len(analyzed_logs)
        
        # Análise por liga
        league_errors = {}
        for log in incorrect_logs:
            league = log.league
            if league not in league_errors:
                league_errors[league] = 0
            league_errors[league] += 1
        
        # Gerar insights
        insights = []
        
        if len(high_confidence_errors) > len(incorrect_logs) * 0.3:
            insights.append({
                "type": "confidence_calibration",
                "severity": "high",
                "message": "Muitos erros com alta confiança - modelo superconfiante",
                "recommendation": "Ajustar algoritmo de confiança"
            })
        
        if calibration_rate < 0.7:
            insights.append({
                "type": "calibration",
                "severity": "medium",
                "message": f"Calibração de confiança baixa ({calibration_rate:.1%})",
                "recommendation": "Melhorar calibração de confiança"
            })
        
        # Insights por liga
        for league, error_count in league_errors.items():
            league_total = len([log for log in analyzed_logs if log.league == league])
            error_rate = error_count / league_total if league_total > 0 else 0
            
            if error_rate > 0.5 and league_total > 10:
                insights.append({
                    "type": "league_performance",
                    "severity": "medium",
                    "message": f"Performance ruim em {league} ({error_rate:.1%} de erros)",
                    "recommendation": f"Considerar features específicas para {league}"
                })
        
        return {
            "period_days": days_back,
            "analysis_date": datetime.now().isoformat(),
            "total_analyzed": len(analyzed_logs),
            "incorrect_predictions": len(incorrect_logs),
            "high_confidence_errors": len(high_confidence_errors),
            "calibration_rate": round(calibration_rate, 3),
            "league_error_analysis": league_errors,
            "insights": insights,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error getting ML learning insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/predictions/logs")
async def get_prediction_logs(
    limit: int = Query(50, ge=1, le=200),
    analyzed_only: bool = Query(False),
    model_name: Optional[str] = Query(None),
    league: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    📋 Logs de Predições
    
    Retorna logs detalhados de predições para análise
    """
    try:
        query = db.query(PredictionLog)
        
        # Filtros
        if analyzed_only:
            query = query.filter(PredictionLog.analyzed_at.isnot(None))
        
        if model_name:
            query = query.filter(PredictionLog.model_name == model_name)
        
        if league:
            query = query.filter(PredictionLog.league == league)
        
        # Ordenar e limitar
        logs = query.order_by(PredictionLog.created_at.desc()).limit(limit).all()
        
        logs_data = []
        for log in logs:
            logs_data.append({
                "id": log.id,
                "match_id": log.match_id,
                "predicted_outcome": log.predicted_outcome,
                "actual_outcome": log.actual_outcome,
                "confidence_score": log.confidence_score,
                "was_correct": log.was_correct,
                "prediction_error": log.prediction_error,
                "feedback_score": log.feedback_score,
                "league": log.league,
                "model_name": log.model_name,
                "model_version": log.model_version,
                "created_at": log.created_at.isoformat(),
                "analyzed_at": log.analyzed_at.isoformat() if log.analyzed_at else None
            })
        
        return {
            "logs": logs_data,
            "total_returned": len(logs_data),
            "filters": {
                "analyzed_only": analyzed_only,
                "model_name": model_name,
                "league": league
            },
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error getting prediction logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze/finished-matches")
async def analyze_finished_matches(
    days_back: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """
    🔄 Analisar Jogos Finalizados

    Força análise de jogos finalizados para atualizar métricas
    """
    try:
        logger_service = PredictionLogger(db)

        # Analisar jogos finalizados
        analyzed_logs = logger_service.analyze_finished_matches(days_back)

        return {
            "message": f"Análise concluída",
            "analyzed_predictions": len(analyzed_logs),
            "period_days": days_back,
            "success": True
        }

    except Exception as e:
        logger.error(f"Error analyzing finished matches: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze/green-red")
async def analyze_green_red(
    export_report: bool = Query(False, description="Exportar relatório JSON"),
    db: Session = Depends(get_db)
):
    """
    🟢🔴 Analisar GREEN/RED

    Executa análise GREEN/RED em todos os jogos finalizados.
    Marca predictions como GREEN (acerto) ou RED (erro).
    """
    try:
        from app.models import Prediction

        # Buscar jogos finalizados
        finished_matches = db.query(Match).filter(
            Match.status.in_(['FT', 'FINISHED']),
            Match.home_score.isnot(None),
            Match.away_score.isnot(None)
        ).all()

        greens = 0
        reds = 0
        total_analyzed = 0
        updated_predictions = []

        for match in finished_matches:
            # Buscar prediction
            prediction = db.query(Prediction).filter(
                Prediction.match_id == match.id,
                Prediction.market_type == '1X2'
            ).first()

            if not prediction:
                continue

            # Determinar resultado real
            if match.home_score > match.away_score:
                actual_outcome = '1'
            elif match.home_score < match.away_score:
                actual_outcome = '2'
            else:
                actual_outcome = 'X'

            # Comparar com prediction
            is_correct = (prediction.predicted_outcome == actual_outcome)

            # Atualizar prediction
            prediction.actual_outcome = actual_outcome
            prediction.is_winner = is_correct

            # Calcular lucro/prejuízo se houver odds
            if hasattr(prediction, 'actual_odds') and prediction.actual_odds:
                if is_correct:
                    # GREEN: ganhou (odds - 1) * stake
                    prediction.profit_loss = (prediction.actual_odds - 1) * 100  # stake = 100
                else:
                    # RED: perdeu stake
                    prediction.profit_loss = -100

            total_analyzed += 1
            if is_correct:
                greens += 1
                result = "GREEN"
            else:
                reds += 1
                result = "RED"

            updated_predictions.append({
                "match_id": match.id,
                "teams": f"{match.home_team.name if match.home_team else '?'} vs {match.away_team.name if match.away_team else '?'}",
                "score": f"{match.home_score}-{match.away_score}",
                "predicted": prediction.predicted_outcome,
                "actual": actual_outcome,
                "result": result,
                "confidence": float(prediction.confidence_score) if prediction.confidence_score else None
            })

        db.commit()

        # Calcular estatísticas
        accuracy = (greens / total_analyzed * 100) if total_analyzed > 0 else 0

        result_data = {
            "message": "Análise GREEN/RED concluída",
            "total_finished_matches": len(finished_matches),
            "total_analyzed": total_analyzed,
            "greens": greens,
            "reds": reds,
            "accuracy": round(accuracy, 2),
            "green_percentage": round((greens / total_analyzed * 100), 2) if total_analyzed > 0 else 0,
            "red_percentage": round((reds / total_analyzed * 100), 2) if total_analyzed > 0 else 0,
            "success": True
        }

        # Incluir detalhes se solicitado
        if export_report:
            result_data["predictions"] = updated_predictions

        logger.info(f"✅ Análise GREEN/RED concluída: {total_analyzed} predictions analisadas ({greens} GREEN, {reds} RED)")

        return result_data

    except Exception as e:
        logger.error(f"Error analyzing GREEN/RED: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/green-red")
async def get_green_red_stats(
    db: Session = Depends(get_db)
):
    """
    📊 Estatísticas GREEN/RED

    Retorna estatísticas atuais de GREEN/RED
    """
    try:
        from app.models import Prediction

        # Total de predictions com resultado
        total = db.query(Prediction).filter(
            Prediction.actual_outcome.isnot(None)
        ).count()

        # Greens (acertos)
        greens = db.query(Prediction).filter(
            Prediction.is_winner == True
        ).count()

        # Reds (erros)
        reds = db.query(Prediction).filter(
            Prediction.is_winner == False
        ).count()

        # Predictions pendentes (sem resultado ainda)
        pending = db.query(Prediction).filter(
            Prediction.actual_outcome.is_(None)
        ).count()

        # Accuracy
        accuracy = (greens / total * 100) if total > 0 else 0

        # Lucro/prejuízo total
        total_profit = db.query(func.sum(Prediction.profit_loss)).filter(
            Prediction.profit_loss.isnot(None)
        ).scalar() or 0

        return {
            "total_analyzed": total,
            "greens": greens,
            "reds": reds,
            "pending": pending,
            "accuracy": round(accuracy, 2),
            "green_percentage": round((greens / total * 100), 2) if total > 0 else 0,
            "red_percentage": round((reds / total * 100), 2) if total > 0 else 0,
            "total_profit_loss": round(float(total_profit), 2),
            "roi": round((total_profit / (total * 100) * 100), 2) if total > 0 else 0,
            "success": True
        }

    except Exception as e:
        logger.error(f"Error getting GREEN/RED stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
