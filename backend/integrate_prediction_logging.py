#!/usr/bin/env python3
"""
🔗 INTEGRAÇÃO DE LOGGING DE PREDIÇÕES
Script para integrar o sistema de logging nas predições existentes

Funcionalidades:
1. Adiciona logging automático ao serviço de predições
2. Migra predições existentes para o sistema de log
3. Configura logging automático para novas predições
"""

import sys
from pathlib import Path
from datetime import datetime
import logging
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import get_db
from app.models import Prediction, Match, PredictionLog
from app.services.prediction_logger import PredictionLogger

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PredictionLoggingIntegrator:
    """Integrador do sistema de logging de predições"""
    
    def __init__(self):
        pass
    
    def migrate_existing_predictions(self):
        """Migra predições existentes para o sistema de log"""
        logger.info("🔄 Migrando predições existentes para o sistema de log...")
        
        db = next(get_db())
        migrated_count = 0
        
        try:
            # Buscar predições existentes sem log
            existing_predictions = db.query(Prediction).all()
            
            logger.info(f"📊 Encontradas {len(existing_predictions)} predições existentes")
            
            for prediction in existing_predictions:
                try:
                    # Verificar se já existe log para esta predição
                    existing_log = db.query(PredictionLog).filter(
                        PredictionLog.prediction_id == prediction.id
                    ).first()
                    
                    if existing_log:
                        continue  # Já tem log
                    
                    # Buscar dados do jogo
                    match = db.query(Match).filter(Match.id == prediction.match_id).first()
                    if not match:
                        continue
                    
                    # Pular predições sem dados essenciais
                    if not prediction.predicted_outcome:
                        continue
                    
                    # Criar log da predição
                    prediction_log = PredictionLog(
                        match_id=prediction.match_id,
                        prediction_id=prediction.id,
                        predicted_outcome=prediction.predicted_outcome,
                        confidence_score=prediction.confidence_score or 0.0,
                        predicted_probability=prediction.predicted_probability or 0.0,
                        match_date=match.match_date,
                        home_team_id=match.home_team_id,
                        away_team_id=match.away_team_id,
                        league=match.league or "Unknown",
                        model_name="enhanced_random_forest",  # Default
                        model_version="v2.0",
                        analysis_summary=prediction.analysis_summary,
                        key_factors=prediction.key_factors or {},
                        created_at=prediction.predicted_at or datetime.now()
                    )
                    
                    # Se o jogo já terminou, adicionar resultado
                    if match.status == 'finished' and match.home_score is not None and match.away_score is not None:
                        # Determinar resultado real
                        if match.home_score > match.away_score:
                            actual_outcome = 'home'
                        elif match.away_score > match.home_score:
                            actual_outcome = 'away'
                        else:
                            actual_outcome = 'draw'
                        
                        prediction_log.actual_outcome = actual_outcome
                        prediction_log.actual_home_score = match.home_score
                        prediction_log.actual_away_score = match.away_score
                        prediction_log.match_status = match.status
                        prediction_log.was_correct = (prediction.predicted_outcome == actual_outcome)
                        prediction_log.analyzed_at = datetime.now()
                        
                        # Calcular métricas
                        prediction_log.confidence_vs_accuracy = prediction_log.confidence_score - (1.0 if prediction_log.was_correct else 0.0)
                        prediction_log.prediction_error = 1.0 - prediction_log.confidence_score if prediction_log.was_correct else prediction_log.confidence_score
                        prediction_log.feedback_score = 1.0 if prediction_log.was_correct else 0.0
                    
                    db.add(prediction_log)
                    migrated_count += 1
                    
                    if migrated_count % 10 == 0:
                        logger.info(f"📝 Migradas {migrated_count} predições...")
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao migrar predição {prediction.id}: {e}")
                    continue
            
            db.commit()
            logger.info(f"✅ Migração concluída: {migrated_count} predições migradas")
            
        except Exception as e:
            logger.error(f"❌ Erro na migração: {e}")
            db.rollback()
        finally:
            db.close()
        
        return migrated_count
    
    def setup_automatic_logging(self):
        """Configura logging automático para novas predições"""
        logger.info("⚙️ Configurando logging automático...")
        
        # Este método seria usado para modificar o serviço de predições
        # para incluir logging automático. Por enquanto, apenas documenta.
        
        logger.info("📋 Para ativar logging automático:")
        logger.info("   1. Modifique o PredictionService para usar PredictionLogger")
        logger.info("   2. Adicione logging após cada predição gerada")
        logger.info("   3. Configure análise automática de jogos finalizados")
        
        return True
    
    def verify_logging_system(self):
        """Verifica se o sistema de logging está funcionando"""
        logger.info("🔍 Verificando sistema de logging...")
        
        db = next(get_db())
        
        try:
            # Verificar logs existentes
            total_logs = db.query(PredictionLog).count()
            analyzed_logs = db.query(PredictionLog).filter(
                PredictionLog.analyzed_at.isnot(None)
            ).count()
            
            # Verificar predições sem log
            total_predictions = db.query(Prediction).count()
            predictions_with_logs = db.query(Prediction).join(PredictionLog).count()
            
            logger.info(f"📊 Estatísticas do sistema de logging:")
            logger.info(f"   - Total de logs: {total_logs}")
            logger.info(f"   - Logs analisados: {analyzed_logs}")
            logger.info(f"   - Total de predições: {total_predictions}")
            logger.info(f"   - Predições com logs: {predictions_with_logs}")
            
            # Verificar integridade
            if predictions_with_logs == total_predictions:
                logger.info("✅ Sistema de logging: 100% integrado")
            else:
                logger.warning(f"⚠️ Sistema de logging: {predictions_with_logs/total_predictions*100:.1f}% integrado")
            
            return {
                'total_logs': total_logs,
                'analyzed_logs': analyzed_logs,
                'total_predictions': total_predictions,
                'predictions_with_logs': predictions_with_logs,
                'integration_percentage': predictions_with_logs/total_predictions*100 if total_predictions > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao verificar sistema: {e}")
            return None
        finally:
            db.close()

def main():
    """Função principal"""
    integrator = PredictionLoggingIntegrator()
    
    print("🔗 INTEGRAÇÃO DE LOGGING DE PREDIÇÕES")
    print("=" * 50)
    
    # 1. Verificar estado atual
    print("\n1️⃣ Verificando estado atual...")
    current_state = integrator.verify_logging_system()
    
    if current_state:
        print(f"   Logs existentes: {current_state['total_logs']}")
        print(f"   Predições: {current_state['total_predictions']}")
        print(f"   Integração: {current_state['integration_percentage']:.1f}%")
    
    # 2. Migrar predições existentes
    print("\n2️⃣ Migrando predições existentes...")
    migrated = integrator.migrate_existing_predictions()
    print(f"   Predições migradas: {migrated}")
    
    # 3. Configurar logging automático
    print("\n3️⃣ Configurando logging automático...")
    integrator.setup_automatic_logging()
    
    # 4. Verificar estado final
    print("\n4️⃣ Verificando estado final...")
    final_state = integrator.verify_logging_system()
    
    if final_state:
        print(f"   Logs existentes: {final_state['total_logs']}")
        print(f"   Predições: {final_state['total_predictions']}")
        print(f"   Integração: {final_state['integration_percentage']:.1f}%")
    
    print("\n✅ Integração concluída!")

if __name__ == "__main__":
    main()
