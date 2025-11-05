#!/usr/bin/env python3
"""
🔄 ANALISADOR DE PREDIÇÕES ML
Script para reanalisar predições após jogos e gerar feedback para ML

Funcionalidades:
1. Analisa jogos finalizados dos últimos dias
2. Compara predições com resultados reais
3. Gera relatórios de performance
4. Cria feedback para melhoria do ML
5. Atualiza métricas de aprendizado
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import get_db
from app.models import Match, Prediction, PredictionLog, ModelPerformance
from app.services.prediction_logger import PredictionLogger
from app.services.api_football_service import APIFootballService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PredictionAnalyzer:
    """Analisador de predições ML com feedback automático"""
    
    def __init__(self):
        self.api_service = APIFootballService()
        self.api_service.rate_limit_delay = 0.5
        
    async def run_full_analysis(self, days_back: int = 7):
        """Executa análise completa de predições"""
        logger.info("🔄 Iniciando análise completa de predições...")
        
        start_time = datetime.now()
        
        try:
            db = next(get_db())
            logger_service = PredictionLogger(db)
            
            # 1. Atualizar resultados de jogos finalizados
            updated_matches = await self.update_finished_matches(db, days_back)
            
            # 2. Analisar predições com resultados atualizados
            analyzed_logs = logger_service.analyze_finished_matches(days_back)
            
            # 3. Gerar relatórios de performance
            performance_reports = await self.generate_performance_reports(logger_service)
            
            # 4. Gerar insights de melhoria
            improvement_insights = await self.generate_improvement_insights(db, analyzed_logs)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info("🎉 Análise completa finalizada!")
            logger.info(f"📊 Estatísticas:")
            logger.info(f"   - Jogos atualizados: {updated_matches}")
            logger.info(f"   - Predições analisadas: {len(analyzed_logs)}")
            logger.info(f"   - Relatórios gerados: {len(performance_reports)}")
            logger.info(f"   - Tempo total: {duration:.2f}s")
            
            return {
                'updated_matches': updated_matches,
                'analyzed_predictions': len(analyzed_logs),
                'performance_reports': len(performance_reports),
                'improvement_insights': improvement_insights,
                'duration_seconds': duration
            }
            
        except Exception as e:
            logger.error(f"❌ Erro na análise completa: {e}")
            return None
        finally:
            db.close()
    
    async def update_finished_matches(self, db: Session, days_back: int) -> int:
        """Atualiza resultados de jogos finalizados"""
        logger.info(f"🔍 Atualizando jogos finalizados dos últimos {days_back} dias...")
        
        updated_count = 0
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        try:
            # Buscar jogos que podem ter sido finalizados
            potential_finished_matches = db.query(Match).filter(
                Match.status.in_(['SCHEDULED', 'LIVE']),
                Match.match_date < datetime.now() - timedelta(hours=2),  # Jogos que deveriam ter terminado
                Match.match_date >= cutoff_date
            ).limit(50).all()  # Limitar para não sobrecarregar a API
            
            logger.info(f"🎯 Encontrados {len(potential_finished_matches)} jogos para verificar")
            
            for match in potential_finished_matches:
                try:
                    # Buscar resultado atualizado na API
                    updated_match = await self.get_match_result_from_api(match)
                    
                    if updated_match:
                        # Atualizar no banco
                        match.status = updated_match.get('status', match.status)
                        match.home_score = updated_match.get('home_score', match.home_score)
                        match.away_score = updated_match.get('away_score', match.away_score)
                        match.minute = updated_match.get('minute', match.minute)
                        match.updated_at = datetime.now()
                        
                        updated_count += 1
                        
                        logger.info(f"✅ Jogo atualizado: {match.home_team.name if match.home_team else 'TBD'} vs {match.away_team.name if match.away_team else 'TBD'} - {match.home_score}-{match.away_score}")
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao atualizar jogo {match.id}: {e}")
                    continue
            
            db.commit()
            logger.info(f"💾 {updated_count} jogos atualizados no banco")
            
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar jogos finalizados: {e}")
            db.rollback()
        
        return updated_count
    
    async def get_match_result_from_api(self, match: Match) -> dict:
        """Busca resultado atualizado do jogo na API"""
        try:
            if not match.external_id:
                return None
            
            # Buscar detalhes do jogo na API-Sports
            fixture_details = await self.api_service.get_fixture_details(int(match.external_id))
            
            if not fixture_details:
                return None
            
            # Extrair informações atualizadas
            fixture = fixture_details.get('fixture', {})
            teams = fixture_details.get('teams', {})
            
            return {
                'status': fixture.get('status', {}).get('short', match.status),
                'home_score': teams.get('home', {}).get('goals'),
                'away_score': teams.get('away', {}).get('goals'),
                'minute': fixture.get('status', {}).get('elapsed')
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar resultado do jogo {match.external_id}: {e}")
            return None
    
    async def generate_performance_reports(self, logger_service: PredictionLogger) -> list:
        """Gera relatórios de performance dos modelos"""
        logger.info("📊 Gerando relatórios de performance...")
        
        reports = []
        models_to_analyze = [
            {'name': 'enhanced_random_forest', 'version': 'v2.0'},
            {'name': 'random_forest_enhanced', 'version': 'v1.0'},
            {'name': 'gradient_boosting', 'version': 'v1.0'}
        ]
        
        for model in models_to_analyze:
            try:
                report = logger_service.generate_model_performance_report(
                    model['name'],
                    model['version'],
                    days_back=30
                )
                
                if report:
                    reports.append(report)
                    logger.info(f"✅ Relatório gerado para {model['name']} {model['version']}: {report.accuracy:.2%} acurácia")
                
            except Exception as e:
                logger.error(f"❌ Erro ao gerar relatório para {model['name']}: {e}")
                continue
        
        return reports
    
    async def generate_improvement_insights(self, db: Session, analyzed_logs: list) -> dict:
        """Gera insights de melhoria para o ML"""
        logger.info("🧠 Gerando insights de melhoria...")
        
        if not analyzed_logs:
            return {"message": "Nenhuma predição analisada para gerar insights"}
        
        insights = {
            "total_analyzed": len(analyzed_logs),
            "accuracy_overall": 0,
            "confidence_calibration": 0,
            "league_performance": {},
            "outcome_analysis": {},
            "recommendations": []
        }
        
        try:
            # Calcular acurácia geral
            correct_predictions = len([log for log in analyzed_logs if log.was_correct])
            insights["accuracy_overall"] = correct_predictions / len(analyzed_logs)
            
            # Analisar calibração de confiança
            well_calibrated = len([log for log in analyzed_logs if abs(log.confidence_vs_accuracy) < 0.2])
            insights["confidence_calibration"] = well_calibrated / len(analyzed_logs)
            
            # Performance por liga
            leagues = {}
            for log in analyzed_logs:
                league = log.league
                if league not in leagues:
                    leagues[league] = {"total": 0, "correct": 0}
                leagues[league]["total"] += 1
                if log.was_correct:
                    leagues[league]["correct"] += 1
            
            for league, stats in leagues.items():
                insights["league_performance"][league] = {
                    "accuracy": stats["correct"] / stats["total"] if stats["total"] > 0 else 0,
                    "total_predictions": stats["total"]
                }
            
            # Análise por tipo de resultado
            outcomes = {"home": 0, "away": 0, "draw": 0}
            correct_outcomes = {"home": 0, "away": 0, "draw": 0}
            
            for log in analyzed_logs:
                outcome = log.predicted_outcome
                outcomes[outcome] += 1
                if log.was_correct:
                    correct_outcomes[outcome] += 1
            
            for outcome in outcomes:
                total = outcomes[outcome]
                correct = correct_outcomes[outcome]
                insights["outcome_analysis"][outcome] = {
                    "accuracy": correct / total if total > 0 else 0,
                    "total_predictions": total
                }
            
            # Gerar recomendações
            if insights["accuracy_overall"] < 0.6:
                insights["recommendations"].append("Acurácia geral baixa - considerar retreinamento do modelo")
            
            if insights["confidence_calibration"] < 0.7:
                insights["recommendations"].append("Calibração de confiança ruim - ajustar scoring de confiança")
            
            # Recomendações por liga
            for league, perf in insights["league_performance"].items():
                if perf["accuracy"] < 0.5 and perf["total_predictions"] > 5:
                    insights["recommendations"].append(f"Performance ruim em {league} - considerar features específicas da liga")
            
            logger.info(f"✅ Insights gerados: {insights['accuracy_overall']:.2%} acurácia geral")
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar insights: {e}")
            insights["error"] = str(e)
        
        return insights
    
    async def export_learning_data(self, db: Session, output_file: str = "ml_learning_data.json"):
        """Exporta dados de aprendizado para arquivo JSON"""
        logger.info(f"📤 Exportando dados de aprendizado para {output_file}...")
        
        try:
            # Buscar logs de predições analisadas
            analyzed_logs = db.query(PredictionLog).filter(
                PredictionLog.analyzed_at.isnot(None)
            ).order_by(PredictionLog.created_at.desc()).limit(1000).all()
            
            learning_data = {
                "export_timestamp": datetime.now().isoformat(),
                "total_predictions": len(analyzed_logs),
                "predictions": []
            }
            
            for log in analyzed_logs:
                prediction_data = {
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
                    "features_used": log.features_used,
                    "feature_values": log.feature_values,
                    "learning_insights": log.learning_insights,
                    "created_at": log.created_at.isoformat(),
                    "analyzed_at": log.analyzed_at.isoformat() if log.analyzed_at else None
                }
                
                learning_data["predictions"].append(prediction_data)
            
            # Salvar arquivo
            import json
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(learning_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Dados exportados: {len(analyzed_logs)} predições em {output_file}")
            
            return learning_data
            
        except Exception as e:
            logger.error(f"❌ Erro ao exportar dados: {e}")
            return None

async def main():
    """Função principal"""
    analyzer = PredictionAnalyzer()
    
    print("🔄 ANALISADOR DE PREDIÇÕES ML")
    print("=" * 50)
    
    # Executar análise completa
    result = await analyzer.run_full_analysis(days_back=7)
    
    if result:
        print(f"\n🎯 RESULTADO DA ANÁLISE:")
        print(f"   Jogos atualizados: {result['updated_matches']}")
        print(f"   Predições analisadas: {result['analyzed_predictions']}")
        print(f"   Relatórios gerados: {result['performance_reports']}")
        print(f"   Tempo: {result['duration_seconds']:.2f}s")
        
        # Exportar dados de aprendizado
        db = next(get_db())
        try:
            learning_data = await analyzer.export_learning_data(db)
            if learning_data:
                print(f"   Dados exportados: {learning_data['total_predictions']} predições")
        finally:
            db.close()
    else:
        print("❌ Falha na análise de predições")

if __name__ == "__main__":
    asyncio.run(main())
