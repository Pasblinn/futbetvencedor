#!/usr/bin/env python3
"""
🎯 DEMONSTRAÇÃO DO SISTEMA ML COMPLETO
Script para demonstrar todas as funcionalidades do sistema de logging e feedback ML

Funcionalidades demonstradas:
1. Sistema de logging de predições
2. Análise de performance
3. Feedback automático para ML
4. Endpoints de monitoramento
5. Exportação de dados de aprendizado
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import get_db
from app.models import PredictionLog, ModelPerformance, Match, Prediction
from app.services.prediction_logger import PredictionLogger

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MLSystemDemo:
    """Demonstração completa do sistema ML"""
    
    def __init__(self):
        pass
    
    async def run_complete_demo(self):
        """Executa demonstração completa do sistema"""
        print("🎯 DEMONSTRAÇÃO DO SISTEMA ML COMPLETO")
        print("=" * 60)
        
        db = next(get_db())
        
        try:
            # 1. Mostrar estatísticas atuais
            print("\n1️⃣ ESTATÍSTICAS ATUAIS DO SISTEMA")
            await self.show_system_stats(db)
            
            # 2. Demonstrar sistema de logging
            print("\n2️⃣ SISTEMA DE LOGGING DE PREDIÇÕES")
            await self.demonstrate_logging_system(db)
            
            # 3. Mostrar análise de performance
            print("\n3️⃣ ANÁLISE DE PERFORMANCE")
            await self.demonstrate_performance_analysis(db)
            
            # 4. Demonstrar feedback para ML
            print("\n4️⃣ SISTEMA DE FEEDBACK PARA ML")
            await self.demonstrate_ml_feedback(db)
            
            # 5. Mostrar endpoints disponíveis
            print("\n5️⃣ ENDPOINTS DISPONÍVEIS")
            await self.show_available_endpoints()
            
            # 6. Demonstrar exportação de dados
            print("\n6️⃣ EXPORTAÇÃO DE DADOS DE APRENDIZADO")
            await self.demonstrate_data_export(db)
            
            print("\n🎉 DEMONSTRAÇÃO COMPLETA FINALIZADA!")
            print("=" * 60)
            
        except Exception as e:
            logger.error(f"❌ Erro na demonstração: {e}")
        finally:
            db.close()
    
    async def show_system_stats(self, db: Session):
        """Mostra estatísticas atuais do sistema"""
        try:
            # Contar predições
            total_predictions = db.query(Prediction).count()
            
            # Contar logs
            total_logs = db.query(PredictionLog).count()
            analyzed_logs = db.query(PredictionLog).filter(
                PredictionLog.analyzed_at.isnot(None)
            ).count()
            
            # Contar jogos
            total_matches = db.query(Match).count()
            finished_matches = db.query(Match).filter(
                Match.status == 'finished'
            ).count()
            
            print(f"   📊 Predições totais: {total_predictions}")
            print(f"   📝 Logs de predições: {total_logs}")
            print(f"   ✅ Logs analisados: {analyzed_logs}")
            print(f"   ⚽ Jogos totais: {total_matches}")
            print(f"   🏁 Jogos finalizados: {finished_matches}")
            
            # Calcular integração
            integration_rate = (total_logs / total_predictions * 100) if total_predictions > 0 else 0
            print(f"   🔗 Taxa de integração: {integration_rate:.1f}%")
            
        except Exception as e:
            print(f"   ❌ Erro ao obter estatísticas: {e}")
    
    async def demonstrate_logging_system(self, db: Session):
        """Demonstra o sistema de logging"""
        try:
            logger_service = PredictionLogger(db)
            
            # Mostrar logs recentes
            recent_logs = db.query(PredictionLog).order_by(
                PredictionLog.created_at.desc()
            ).limit(3).all()
            
            print(f"   📋 Últimos {len(recent_logs)} logs de predições:")
            
            for log in recent_logs:
                status = "✅ Analisado" if log.analyzed_at else "⏳ Pendente"
                print(f"      - Match {log.match_id}: {log.predicted_outcome} "
                      f"(Confiança: {log.confidence_score:.2%}) - {status}")
            
            # Mostrar distribuição por modelo
            models = db.query(PredictionLog.model_name, 
                            db.func.count(PredictionLog.id)).group_by(
                PredictionLog.model_name
            ).all()
            
            print(f"   🤖 Distribuição por modelo:")
            for model, count in models:
                print(f"      - {model}: {count} predições")
            
        except Exception as e:
            print(f"   ❌ Erro na demonstração de logging: {e}")
    
    async def demonstrate_performance_analysis(self, db: Session):
        """Demonstra análise de performance"""
        try:
            # Buscar logs analisados
            analyzed_logs = db.query(PredictionLog).filter(
                PredictionLog.analyzed_at.isnot(None)
            ).all()
            
            if analyzed_logs:
                # Calcular métricas
                total = len(analyzed_logs)
                correct = len([log for log in analyzed_logs if log.was_correct])
                accuracy = correct / total if total > 0 else 0
                
                avg_confidence = sum(log.confidence_score for log in analyzed_logs) / total
                avg_feedback = sum(log.feedback_score for log in analyzed_logs) / total
                
                print(f"   📊 Métricas de Performance:")
                print(f"      - Acurácia: {accuracy:.2%}")
                print(f"      - Confiança média: {avg_confidence:.2%}")
                print(f"      - Feedback médio: {avg_feedback:.2%}")
                
                # Performance por liga
                leagues = {}
                for log in analyzed_logs:
                    league = log.league
                    if league not in leagues:
                        leagues[league] = {"total": 0, "correct": 0}
                    leagues[league]["total"] += 1
                    if log.was_correct:
                        leagues[league]["correct"] += 1
                
                print(f"   🏆 Performance por liga:")
                for league, stats in leagues.items():
                    league_accuracy = stats["correct"] / stats["total"] if stats["total"] > 0 else 0
                    print(f"      - {league}: {league_accuracy:.2%} ({stats['correct']}/{stats['total']})")
            else:
                print(f"   ⚠️ Nenhuma predição analisada ainda")
                print(f"   💡 Execute o script de análise para processar jogos finalizados")
            
        except Exception as e:
            print(f"   ❌ Erro na análise de performance: {e}")
    
    async def demonstrate_ml_feedback(self, db: Session):
        """Demonstra sistema de feedback para ML"""
        try:
            # Buscar logs com feedback
            feedback_logs = db.query(PredictionLog).filter(
                PredictionLog.feedback_score.isnot(None)
            ).limit(5).all()
            
            if feedback_logs:
                print(f"   🧠 Exemplos de Feedback para ML:")
                
                for log in feedback_logs:
                    feedback_type = "✅ Positivo" if log.feedback_score > 0.5 else "❌ Negativo"
                    print(f"      - Match {log.match_id}: {feedback_type} "
                          f"(Score: {log.feedback_score:.2f})")
                    
                    if log.learning_insights:
                        insights = log.learning_insights
                        if isinstance(insights, dict) and 'key_learning' in insights:
                            for learning in insights['key_learning'][:1]:  # Mostrar apenas 1
                                print(f"        💡 {learning}")
                
                # Mostrar insights agregados
                high_feedback = len([log for log in feedback_logs if log.feedback_score > 0.7])
                low_feedback = len([log for log in feedback_logs if log.feedback_score < 0.3])
                
                print(f"   📈 Distribuição de Feedback:")
                print(f"      - Alto feedback (>0.7): {high_feedback}")
                print(f"      - Baixo feedback (<0.3): {low_feedback}")
            else:
                print(f"   ⚠️ Nenhum feedback gerado ainda")
                print(f"   💡 Feedback é gerado automaticamente após análise de jogos")
            
        except Exception as e:
            print(f"   ❌ Erro na demonstração de feedback: {e}")
    
    async def show_available_endpoints(self):
        """Mostra endpoints disponíveis"""
        endpoints = [
            ("GET", "/api/v1/ml/performance/overview", "Overview de performance do ML"),
            ("GET", "/api/v1/ml/performance/detailed", "Performance detalhada por modelo"),
            ("GET", "/api/v1/ml/learning/insights", "Insights de aprendizado"),
            ("GET", "/api/v1/ml/predictions/logs", "Logs de predições"),
            ("POST", "/api/v1/ml/analyze/finished-matches", "Forçar análise de jogos finalizados")
        ]
        
        print(f"   🌐 Endpoints de ML Performance:")
        for method, endpoint, description in endpoints:
            print(f"      {method} {endpoint}")
            print(f"         → {description}")
    
    async def demonstrate_data_export(self, db: Session):
        """Demonstra exportação de dados"""
        try:
            # Buscar dados para exportação
            logs_to_export = db.query(PredictionLog).filter(
                PredictionLog.analyzed_at.isnot(None)
            ).limit(10).all()
            
            if logs_to_export:
                export_data = {
                    "export_timestamp": datetime.now().isoformat(),
                    "total_predictions": len(logs_to_export),
                    "predictions": []
                }
                
                for log in logs_to_export:
                    prediction_data = {
                        "id": log.id,
                        "match_id": log.match_id,
                        "predicted_outcome": log.predicted_outcome,
                        "actual_outcome": log.actual_outcome,
                        "confidence_score": log.confidence_score,
                        "was_correct": log.was_correct,
                        "feedback_score": log.feedback_score,
                        "league": log.league,
                        "model_name": log.model_name,
                        "created_at": log.created_at.isoformat()
                    }
                    export_data["predictions"].append(prediction_data)
                
                # Salvar arquivo de demonstração
                demo_file = "ml_demo_export.json"
                with open(demo_file, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                
                print(f"   📤 Dados exportados para: {demo_file}")
                print(f"   📊 {len(logs_to_export)} predições exportadas")
                print(f"   💾 Arquivo pronto para análise externa ou retreinamento")
            else:
                print(f"   ⚠️ Nenhum dado analisado para exportação")
                print(f"   💡 Execute análise de jogos finalizados primeiro")
            
        except Exception as e:
            print(f"   ❌ Erro na exportação: {e}")
    
    def show_usage_instructions(self):
        """Mostra instruções de uso"""
        print("\n📚 INSTRUÇÕES DE USO DO SISTEMA:")
        print("=" * 60)
        print("1. 🔄 Análise Automática:")
        print("   python analyze_predictions.py")
        print()
        print("2. 📊 Monitoramento via API:")
        print("   curl http://localhost:8000/api/v1/ml/performance/overview")
        print()
        print("3. 📝 Logs de Predições:")
        print("   curl http://localhost:8000/api/v1/ml/predictions/logs")
        print()
        print("4. 🧠 Insights de Aprendizado:")
        print("   curl http://localhost:8000/api/v1/ml/learning/insights")
        print()
        print("5. 🔄 Forçar Análise:")
        print("   curl -X POST http://localhost:8000/api/v1/ml/analyze/finished-matches")

async def main():
    """Função principal"""
    demo = MLSystemDemo()
    
    # Executar demonstração
    await demo.run_complete_demo()
    
    # Mostrar instruções
    demo.show_usage_instructions()

if __name__ == "__main__":
    asyncio.run(main())
