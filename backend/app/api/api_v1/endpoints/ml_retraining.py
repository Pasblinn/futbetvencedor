"""
🤖 API ENDPOINTS - RETREINO AUTOMÁTICO DE ML
Endpoints para gerenciar o sistema de retreino automático dos modelos
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List, Optional
from datetime import datetime
from app.services.automated_ml_retraining import automated_ml_retraining

router = APIRouter()

@router.get("/status")
async def get_retraining_status():
    """
    📊 Status do Sistema de Retreino Automático

    Retorna informações completas sobre:
    - Performance atual de cada modelo
    - Triggers pendentes para retreino
    - Configurações do sistema
    - Próximos agendamentos
    """
    try:
        status = await automated_ml_retraining.get_retraining_status()
        return {
            "success": True,
            "retraining_system": status,
            "message": "Status do sistema de retreino automático"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter status: {str(e)}")

@router.get("/triggers")
async def evaluate_retraining_triggers():
    """
    🔍 Avaliar Triggers de Retreino

    Verifica quais modelos precisam ser retreinados baseado em:
    - Performance degradada
    - Volume de novos dados
    - Agendamento automático
    """
    try:
        triggers = await automated_ml_retraining.evaluate_retraining_triggers()

        return {
            "success": True,
            "triggers_found": len(triggers),
            "triggers": [
                {
                    "type": trigger.trigger_type,
                    "threshold": trigger.threshold_value,
                    "current_value": trigger.current_value,
                    "reason": trigger.reason,
                    "triggered_at": trigger.triggered_at.isoformat()
                }
                for trigger in triggers
            ],
            "recommendations": {
                "immediate_action_needed": len(triggers) > 0,
                "critical_triggers": len([t for t in triggers if t.trigger_type == "performance"]),
                "data_triggers": len([t for t in triggers if t.trigger_type == "data_volume"])
            },
            "message": f"Encontrados {len(triggers)} triggers para retreino"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao avaliar triggers: {str(e)}")

@router.post("/retrain/{model_name}")
async def retrain_specific_model(model_name: str, background_tasks: BackgroundTasks):
    """
    🔄 Retreinar Modelo Específico

    Força o retreino de um modelo específico, independente dos triggers automáticos.
    """
    try:
        # Verificar se o modelo é suportado
        if model_name not in automated_ml_retraining.supported_models:
            available_models = list(automated_ml_retraining.supported_models.keys())
            raise HTTPException(
                status_code=400,
                detail=f"Modelo '{model_name}' não suportado. Modelos disponíveis: {available_models}"
            )

        # Criar trigger manual
        from app.services.automated_ml_retraining import RetrainingTrigger
        manual_trigger = RetrainingTrigger(
            trigger_type="manual",
            threshold_value=0,
            current_value=1,
            triggered_at=datetime.now(),
            reason=f"Retreino manual solicitado para {model_name}"
        )

        # Executar retreino em background
        background_tasks.add_task(
            _execute_model_retraining,
            model_name,
            manual_trigger
        )

        return {
            "success": True,
            "message": f"Retreino do modelo '{model_name}' iniciado em background",
            "model_name": model_name,
            "trigger_type": "manual",
            "estimated_duration": "2-5 minutos",
            "status_endpoint": f"/api/v1/ml-retraining/status"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao iniciar retreino: {str(e)}")

@router.post("/retrain-all")
async def retrain_all_models(background_tasks: BackgroundTasks):
    """
    🚀 Retreino em Massa

    Executa retreino para todos os modelos que precisam baseado nos triggers.
    """
    try:
        # Avaliar triggers
        triggers = await automated_ml_retraining.evaluate_retraining_triggers()

        if not triggers:
            return {
                "success": True,
                "message": "Nenhum modelo precisa de retreino no momento",
                "models_evaluated": len(automated_ml_retraining.supported_models),
                "triggers_found": 0
            }

        # Executar retreino em massa em background
        background_tasks.add_task(_execute_bulk_retraining)

        return {
            "success": True,
            "message": "Retreino em massa iniciado em background",
            "triggers_found": len(triggers),
            "models_to_retrain": list(automated_ml_retraining.supported_models.keys()),
            "estimated_duration": "5-15 minutos",
            "status_endpoint": "/api/v1/ml-retraining/status"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao iniciar retreino em massa: {str(e)}")

@router.get("/performance-history/{model_name}")
async def get_model_performance_history(model_name: str, days: int = 30):
    """
    📈 Histórico de Performance

    Retorna o histórico de performance de um modelo específico.
    """
    try:
        if model_name not in automated_ml_retraining.supported_models:
            available_models = list(automated_ml_retraining.supported_models.keys())
            raise HTTPException(
                status_code=400,
                detail=f"Modelo '{model_name}' não encontrado. Modelos disponíveis: {available_models}"
            )

        # Carregar histórico de performance
        import json
        from pathlib import Path

        history_file = Path("logs") / f"{model_name}_performance_history.json"

        if not history_file.exists():
            return {
                "success": True,
                "model_name": model_name,
                "history": [],
                "message": "Nenhum histórico encontrado para este modelo"
            }

        with open(history_file, 'r') as f:
            history = json.load(f)

        # Filtrar por dias
        from datetime import datetime, timedelta
        cutoff_date = datetime.now() - timedelta(days=days)

        filtered_history = [
            entry for entry in history
            if datetime.fromisoformat(entry['timestamp']) >= cutoff_date
        ]

        # Calcular estatísticas
        if filtered_history:
            accuracies = [entry['accuracy'] for entry in filtered_history]
            stats = {
                "current_accuracy": accuracies[-1] if accuracies else 0,
                "avg_accuracy": sum(accuracies) / len(accuracies),
                "max_accuracy": max(accuracies),
                "min_accuracy": min(accuracies),
                "trend": "improving" if len(accuracies) >= 2 and accuracies[-1] > accuracies[0] else "stable"
            }
        else:
            stats = {
                "current_accuracy": 0,
                "avg_accuracy": 0,
                "max_accuracy": 0,
                "min_accuracy": 0,
                "trend": "no_data"
            }

        return {
            "success": True,
            "model_name": model_name,
            "period_days": days,
            "history": filtered_history,
            "statistics": stats,
            "total_evaluations": len(filtered_history),
            "message": f"Histórico de {len(filtered_history)} avaliações nos últimos {days} dias"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter histórico: {str(e)}")

@router.put("/config", response_model=None)
async def update_retraining_config(config: dict):
    """
    ⚙️ Atualizar Configurações

    Atualiza as configurações do sistema de retreino automático.
    """
    try:
        # Validar configurações
        valid_keys = [
            "min_accuracy_threshold",
            "min_data_samples",
            "performance_window_days",
            "auto_retrain_schedule",
            "max_retrain_frequency",
            "validation_split",
            "backup_models"
        ]

        invalid_keys = [key for key in config.keys() if key not in valid_keys]
        if invalid_keys:
            raise HTTPException(
                status_code=400,
                detail=f"Configurações inválidas: {invalid_keys}. Válidas: {valid_keys}"
            )

        # Atualizar configurações
        old_config = automated_ml_retraining.config.copy()
        automated_ml_retraining.config.update(config)

        return {
            "success": True,
            "message": "Configurações atualizadas com sucesso",
            "old_config": old_config,
            "new_config": automated_ml_retraining.config,
            "changes": {
                key: {"old": old_config.get(key), "new": value}
                for key, value in config.items()
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar configurações: {str(e)}")

@router.get("/models")
async def get_supported_models():
    """
    📋 Modelos Suportados

    Lista todos os modelos suportados pelo sistema de retreino automático.
    """
    try:
        models_info = {}

        for model_name, model_config in automated_ml_retraining.supported_models.items():
            # Obter performance atual
            performance = await automated_ml_retraining._evaluate_model_performance(model_name)

            models_info[model_name] = {
                "target_column": model_config["target_column"],
                "features": model_config["features"],
                "model_type": model_config["model_class"].__name__,
                "current_performance": {
                    "accuracy": performance.accuracy if performance else 0,
                    "samples_count": performance.samples_count if performance else 0,
                    "last_evaluation": performance.last_evaluation.isoformat() if performance else None,
                    "trend": performance.trend if performance else "unknown"
                },
                "model_file_exists": (automated_ml_retraining.models_dir / f"{model_name}.joblib").exists()
            }

        return {
            "success": True,
            "supported_models": models_info,
            "total_models": len(models_info),
            "models_dir": str(automated_ml_retraining.models_dir),
            "message": f"{len(models_info)} modelos suportados pelo sistema"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar modelos: {str(e)}")

@router.delete("/model/{model_name}")
async def delete_model(model_name: str):
    """
    🗑️ Remover Modelo

    Remove um modelo específico e seu histórico.
    """
    try:
        if model_name not in automated_ml_retraining.supported_models:
            raise HTTPException(status_code=404, detail=f"Modelo '{model_name}' não encontrado")

        removed_files = []

        # Remover arquivo do modelo
        model_file = automated_ml_retraining.models_dir / f"{model_name}.joblib"
        if model_file.exists():
            model_file.unlink()
            removed_files.append(str(model_file))

        # Remover histórico de performance
        history_file = automated_ml_retraining.performance_log_dir / f"{model_name}_performance_history.json"
        if history_file.exists():
            history_file.unlink()
            removed_files.append(str(history_file))

        # Remover log de retreino
        retrain_file = automated_ml_retraining.retraining_data_dir / f"{model_name}_last_retrain.json"
        if retrain_file.exists():
            retrain_file.unlink()
            removed_files.append(str(retrain_file))

        return {
            "success": True,
            "message": f"Modelo '{model_name}' removido com sucesso",
            "removed_files": removed_files,
            "model_name": model_name
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao remover modelo: {str(e)}")

# Funções auxiliares para background tasks
async def _execute_model_retraining(model_name: str, trigger):
    """Executa retreino de um modelo específico em background"""
    try:
        result = await automated_ml_retraining.retrain_model(model_name, trigger)
        print(f"Retreino do modelo {model_name} concluído: {'Sucesso' if result.success else 'Falha'}")
    except Exception as e:
        print(f"Erro no retreino do modelo {model_name}: {str(e)}")

async def _execute_bulk_retraining():
    """Executa retreino em massa em background"""
    try:
        results = await automated_ml_retraining.run_bulk_retraining()
        successful = len([r for r in results if r.success])
        print(f"Retreino em massa concluído: {successful}/{len(results)} modelos atualizados")
    except Exception as e:
        print(f"Erro no retreino em massa: {str(e)}")