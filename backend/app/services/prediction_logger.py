"""
📊 PREDICTION LOGGER SERVICE
Sistema de logging completo para predições ML com análise de performance
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from app.models import PredictionLog, ModelPerformance, Match, Prediction, Team
from app.services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)

class PredictionLogger:
    """Serviço para logging e análise de predições ML"""
    
    def __init__(self, db: Session):
        self.db = db
        self.analytics = AnalyticsService(db)
    
    def log_prediction(self, 
                      match_id: int,
                      prediction_data: Dict[str, Any],
                      model_name: str = "enhanced_random_forest",
                      model_version: str = "v2.0") -> PredictionLog:
        """
        Registra uma predição no log para análise posterior
        
        Args:
            match_id: ID do jogo
            prediction_data: Dados da predição
            model_name: Nome do modelo utilizado
            model_version: Versão do modelo
        """
        try:
            # Buscar dados do jogo
            match = self.db.query(Match).filter(Match.id == match_id).first()
            if not match:
                raise ValueError(f"Match {match_id} not found")
            
            # Extrair features utilizadas (se disponível)
            features_used = prediction_data.get('features_used', [])
            feature_values = prediction_data.get('feature_values', {})
            
            # Criar log da predição
            prediction_log = PredictionLog(
                match_id=match_id,
                predicted_outcome=prediction_data.get('predicted_outcome'),
                confidence_score=prediction_data.get('confidence_score', 0.0),
                predicted_probability=prediction_data.get('predicted_probability', 0.0),
                match_date=match.match_date,
                home_team_id=match.home_team_id,
                away_team_id=match.away_team_id,
                league=match.league,
                features_used=features_used,
                feature_values=feature_values,
                model_name=model_name,
                model_version=model_version,
                analysis_summary=prediction_data.get('reasoning'),
                key_factors=prediction_data.get('key_factors', {}),
                market_conditions=prediction_data.get('market_conditions', {}),
                created_at=datetime.now()
            )
            
            self.db.add(prediction_log)
            self.db.commit()
            self.db.refresh(prediction_log)
            
            logger.info(f"✅ Prediction logged: Match {match_id}, Outcome: {prediction_log.predicted_outcome}, Confidence: {prediction_log.confidence_score}")
            
            return prediction_log
            
        except Exception as e:
            logger.error(f"❌ Error logging prediction for match {match_id}: {e}")
            self.db.rollback()
            raise
    
    def update_prediction_with_result(self, 
                                    prediction_log_id: int,
                                    actual_outcome: str,
                                    home_score: int,
                                    away_score: int,
                                    match_status: str = "finished") -> PredictionLog:
        """
        Atualiza uma predição com o resultado real do jogo
        
        Args:
            prediction_log_id: ID do log da predição
            actual_outcome: Resultado real (home, away, draw)
            home_score: Placar final do time da casa
            away_score: Placar final do time visitante
            match_status: Status do jogo
        """
        try:
            prediction_log = self.db.query(PredictionLog).filter(
                PredictionLog.id == prediction_log_id
            ).first()
            
            if not prediction_log:
                raise ValueError(f"PredictionLog {prediction_log_id} not found")
            
            # Atualizar com resultado real
            prediction_log.actual_outcome = actual_outcome
            prediction_log.actual_home_score = home_score
            prediction_log.actual_away_score = away_score
            prediction_log.match_status = match_status
            
            # Calcular se a predição estava correta
            prediction_log.was_correct = (prediction_log.predicted_outcome == actual_outcome)
            
            # Calcular métricas de performance
            prediction_log.confidence_vs_accuracy = self._calculate_confidence_accuracy_diff(
                prediction_log.confidence_score, 
                prediction_log.was_correct
            )
            
            prediction_log.prediction_error = self._calculate_prediction_error(
                prediction_log.predicted_outcome,
                actual_outcome,
                prediction_log.confidence_score
            )
            
            # Gerar feedback para ML
            prediction_log.feedback_score = self._calculate_feedback_score(prediction_log)
            prediction_log.learning_insights = self._generate_learning_insights(prediction_log)
            prediction_log.feature_importance_feedback = self._analyze_feature_importance(prediction_log)
            
            prediction_log.analyzed_at = datetime.now()
            prediction_log.updated_at = datetime.now()
            
            self.db.commit()
            self.db.refresh(prediction_log)
            
            logger.info(f"✅ Prediction updated with result: Log {prediction_log_id}, Correct: {prediction_log.was_correct}")
            
            return prediction_log
            
        except Exception as e:
            logger.error(f"❌ Error updating prediction result for log {prediction_log_id}: {e}")
            self.db.rollback()
            raise
    
    def analyze_finished_matches(self, days_back: int = 7) -> List[PredictionLog]:
        """
        Analisa jogos finalizados dos últimos dias e atualiza predições
        
        Args:
            days_back: Quantos dias para trás analisar
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            # Buscar predições de jogos finalizados que ainda não foram analisadas
            unfinished_logs = self.db.query(PredictionLog).join(Match).filter(
                Match.status == 'finished',
                PredictionLog.analyzed_at.is_(None),
                Match.match_date >= cutoff_date
            ).all()
            
            logger.info(f"🔍 Found {len(unfinished_logs)} unfinished prediction logs to analyze")
            
            analyzed_logs = []
            for log in unfinished_logs:
                try:
                    match = log.match
                    if match.home_score is not None and match.away_score is not None:
                        # Determinar resultado real
                        if match.home_score > match.away_score:
                            actual_outcome = 'home'
                        elif match.away_score > match.home_score:
                            actual_outcome = 'away'
                        else:
                            actual_outcome = 'draw'
                        
                        # Atualizar log com resultado
                        updated_log = self.update_prediction_with_result(
                            log.id,
                            actual_outcome,
                            match.home_score,
                            match.away_score,
                            match.status
                        )
                        
                        analyzed_logs.append(updated_log)
                        
                except Exception as e:
                    logger.error(f"❌ Error analyzing log {log.id}: {e}")
                    continue
            
            logger.info(f"✅ Analyzed {len(analyzed_logs)} prediction logs")
            return analyzed_logs
            
        except Exception as e:
            logger.error(f"❌ Error analyzing finished matches: {e}")
            return []
    
    def generate_model_performance_report(self, 
                                        model_name: str,
                                        model_version: str,
                                        days_back: int = 30) -> ModelPerformance:
        """
        Gera relatório de performance do modelo
        
        Args:
            model_name: Nome do modelo
            model_version: Versão do modelo
            days_back: Período de análise em dias
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            # Buscar predições analisadas do período
            analyzed_logs = self.db.query(PredictionLog).filter(
                PredictionLog.model_name == model_name,
                PredictionLog.model_version == model_version,
                PredictionLog.analyzed_at.isnot(None),
                PredictionLog.created_at >= cutoff_date
            ).all()
            
            if not analyzed_logs:
                logger.warning(f"No analyzed predictions found for {model_name} {model_version}")
                return None
            
            # Calcular métricas
            total_predictions = len(analyzed_logs)
            correct_predictions = len([log for log in analyzed_logs if log.was_correct])
            accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0
            
            avg_confidence = sum(log.confidence_score for log in analyzed_logs) / total_predictions
            
            # Calcular correlação confiança vs acurácia
            confidence_accuracy_correlation = self._calculate_confidence_accuracy_correlation(analyzed_logs)
            
            # Métricas por tipo de predição
            home_win_logs = [log for log in analyzed_logs if log.predicted_outcome == 'home']
            away_win_logs = [log for log in analyzed_logs if log.predicted_outcome == 'away']
            draw_logs = [log for log in analyzed_logs if log.predicted_outcome == 'draw']
            
            home_win_accuracy = len([log for log in home_win_logs if log.was_correct]) / len(home_win_logs) if home_win_logs else 0
            away_win_accuracy = len([log for log in away_win_logs if log.was_correct]) / len(away_win_logs) if away_win_logs else 0
            draw_accuracy = len([log for log in draw_logs if log.was_correct]) / len(draw_logs) if draw_logs else 0
            
            # Performance por liga
            league_performance = self._calculate_league_performance(analyzed_logs)
            
            # Gerar insights
            key_insights = self._generate_key_insights(analyzed_logs)
            recommended_improvements = self._generate_improvement_recommendations(analyzed_logs)
            feature_importance_analysis = self._analyze_feature_importance_aggregate(analyzed_logs)
            
            # Criar relatório de performance
            performance_report = ModelPerformance(
                model_name=model_name,
                model_version=model_version,
                analysis_period_start=cutoff_date,
                analysis_period_end=datetime.now(),
                total_predictions=total_predictions,
                correct_predictions=correct_predictions,
                accuracy=accuracy,
                avg_confidence=avg_confidence,
                confidence_accuracy_correlation=confidence_accuracy_correlation,
                home_win_accuracy=home_win_accuracy,
                away_win_accuracy=away_win_accuracy,
                draw_accuracy=draw_accuracy,
                league_performance=league_performance,
                key_insights=key_insights,
                recommended_improvements=recommended_improvements,
                feature_importance_analysis=feature_importance_analysis,
                created_at=datetime.now()
            )
            
            self.db.add(performance_report)
            self.db.commit()
            self.db.refresh(performance_report)
            
            logger.info(f"✅ Generated performance report for {model_name} {model_version}: {accuracy:.2%} accuracy")
            
            return performance_report
            
        except Exception as e:
            logger.error(f"❌ Error generating performance report: {e}")
            self.db.rollback()
            raise
    
    def _calculate_confidence_accuracy_diff(self, confidence: float, was_correct: bool) -> float:
        """Calcula diferença entre confiança e acurácia"""
        accuracy = 1.0 if was_correct else 0.0
        return confidence - accuracy
    
    def _calculate_prediction_error(self, predicted: str, actual: str, confidence: float) -> float:
        """Calcula erro da predição"""
        if predicted == actual:
            return 1.0 - confidence  # Erro baixo se correto com alta confiança
        else:
            return confidence  # Erro alto se incorreto com alta confiança
    
    def _calculate_feedback_score(self, prediction_log: PredictionLog) -> float:
        """Calcula score de feedback para o modelo"""
        base_score = 1.0 if prediction_log.was_correct else 0.0
        
        # Ajustar baseado na confiança
        if prediction_log.was_correct:
            # Recompensar alta confiança em predições corretas
            confidence_bonus = prediction_log.confidence_score * 0.2
        else:
            # Penalizar alta confiança em predições incorretas
            confidence_bonus = -prediction_log.confidence_score * 0.3
        
        return max(0.0, min(1.0, base_score + confidence_bonus))
    
    def _generate_learning_insights(self, prediction_log: PredictionLog) -> Dict[str, Any]:
        """Gera insights de aprendizado para o modelo"""
        insights = {
            "prediction_quality": "high" if prediction_log.was_correct and prediction_log.confidence_score > 0.7 else "medium",
            "confidence_calibration": "well_calibrated" if abs(prediction_log.confidence_vs_accuracy) < 0.2 else "poorly_calibrated",
            "outcome_type": prediction_log.predicted_outcome,
            "league": prediction_log.league,
            "key_learning": []
        }
        
        if prediction_log.was_correct:
            insights["key_learning"].append("Model performed well on this prediction")
        else:
            insights["key_learning"].append("Model needs improvement for this type of match")
        
        return insights
    
    def _analyze_feature_importance(self, prediction_log: PredictionLog) -> Dict[str, Any]:
        """Analisa importância das features para esta predição"""
        if not prediction_log.feature_values:
            return {}
        
        # Análise básica das features utilizadas
        return {
            "features_used": prediction_log.features_used or [],
            "feature_count": len(prediction_log.feature_values),
            "analysis_quality": "good" if len(prediction_log.feature_values) > 10 else "limited"
        }
    
    def _calculate_confidence_accuracy_correlation(self, logs: List[PredictionLog]) -> float:
        """Calcula correlação entre confiança e acurácia"""
        if len(logs) < 2:
            return 0.0
        
        confidences = [log.confidence_score for log in logs]
        accuracies = [1.0 if log.was_correct else 0.0 for log in logs]
        
        # Cálculo simples de correlação
        n = len(logs)
        sum_conf = sum(confidences)
        sum_acc = sum(accuracies)
        sum_conf_acc = sum(c * a for c, a in zip(confidences, accuracies))
        sum_conf_sq = sum(c * c for c in confidences)
        sum_acc_sq = sum(a * a for a in accuracies)
        
        numerator = n * sum_conf_acc - sum_conf * sum_acc
        denominator = ((n * sum_conf_sq - sum_conf * sum_conf) * (n * sum_acc_sq - sum_acc * sum_acc)) ** 0.5
        
        return numerator / denominator if denominator != 0 else 0.0
    
    def _calculate_league_performance(self, logs: List[PredictionLog]) -> Dict[str, Dict[str, float]]:
        """Calcula performance por liga"""
        league_stats = {}
        
        for log in logs:
            league = log.league
            if league not in league_stats:
                league_stats[league] = {"total": 0, "correct": 0}
            
            league_stats[league]["total"] += 1
            if log.was_correct:
                league_stats[league]["correct"] += 1
        
        # Converter para percentuais
        for league in league_stats:
            total = league_stats[league]["total"]
            correct = league_stats[league]["correct"]
            league_stats[league]["accuracy"] = correct / total if total > 0 else 0.0
            league_stats[league]["total_predictions"] = total
        
        return league_stats
    
    def _generate_key_insights(self, logs: List[PredictionLog]) -> List[str]:
        """Gera insights principais do modelo"""
        insights = []
        
        total = len(logs)
        correct = len([log for log in logs if log.was_correct])
        accuracy = correct / total if total > 0 else 0
        
        insights.append(f"Overall accuracy: {accuracy:.2%}")
        
        # Insight sobre confiança
        avg_confidence = sum(log.confidence_score for log in logs) / total
        insights.append(f"Average confidence: {avg_confidence:.2%}")
        
        # Insight sobre calibração
        well_calibrated = len([log for log in logs if abs(log.confidence_vs_accuracy) < 0.2])
        calibration_rate = well_calibrated / total if total > 0 else 0
        insights.append(f"Confidence calibration: {calibration_rate:.2%}")
        
        return insights
    
    def _generate_improvement_recommendations(self, logs: List[PredictionLog]) -> List[str]:
        """Gera recomendações de melhoria"""
        recommendations = []
        
        # Analisar predições incorretas
        incorrect_logs = [log for log in logs if not log.was_correct]
        
        if len(incorrect_logs) > len(logs) * 0.4:  # Mais de 40% incorretas
            recommendations.append("Model accuracy is below acceptable threshold - consider retraining")
        
        # Analisar calibração de confiança
        poorly_calibrated = len([log for log in logs if abs(log.confidence_vs_accuracy) > 0.3])
        if poorly_calibrated > len(logs) * 0.3:  # Mais de 30% mal calibradas
            recommendations.append("Confidence calibration needs improvement - adjust confidence scoring")
        
        # Analisar performance por liga
        league_performance = self._calculate_league_performance(logs)
        for league, stats in league_performance.items():
            if stats["accuracy"] < 0.5 and stats["total_predictions"] > 5:
                recommendations.append(f"Poor performance in {league} - consider league-specific features")
        
        return recommendations
    
    def _analyze_feature_importance_aggregate(self, logs: List[PredictionLog]) -> Dict[str, Any]:
        """Analisa importância das features agregada"""
        all_features = []
        for log in logs:
            if log.features_used:
                all_features.extend(log.features_used)
        
        if not all_features:
            return {"message": "No feature data available"}
        
        # Contar frequência de features
        feature_counts = {}
        for feature in all_features:
            feature_counts[feature] = feature_counts.get(feature, 0) + 1
        
        # Ordenar por frequência
        sorted_features = sorted(feature_counts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "total_features_used": len(set(all_features)),
            "most_common_features": sorted_features[:10],
            "feature_usage_distribution": feature_counts
        }
