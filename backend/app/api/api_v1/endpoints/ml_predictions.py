"""
🤖 ML PREDICTIONS API - Endpoints para Machine Learning
Integra sistema de ML avançado com predições ensemble
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.services.ml_manager import ml_manager
from app.services.ml_training_service import MLTrainingService
from app.services.ml_trainer_real_data import universal_ml_trainer
from app.core.config import settings

router = APIRouter()

# Modelos Pydantic para requests/responses
class PredictionRequest(BaseModel):
    home_team_id: str
    away_team_id: str
    match_date: Optional[str] = None

class TrainingRequest(BaseModel):
    training_type: str = "full"  # "full" ou "quick"
    leagues: Optional[List[str]] = None

@router.post("/enhanced-prediction/{home_team_id}/{away_team_id}")
async def get_enhanced_prediction(
    home_team_id: str,
    away_team_id: str,
    match_date: Optional[str] = None
) -> Dict:
    """
    🔮 Predição avançada combinando ML + Análise Matemática

    - **home_team_id**: ID do time mandante
    - **away_team_id**: ID do time visitante
    - **match_date**: Data do jogo (opcional, padrão: hoje)

    Retorna predições ensemble com alta precisão
    """
    try:
        # Converter data se fornecida
        if match_date:
            match_datetime = datetime.fromisoformat(match_date.replace('Z', '+00:00'))
        else:
            match_datetime = datetime.now()

        # Gerar predição avançada
        result = await ml_manager.generate_enhanced_prediction(
            home_team_id,
            away_team_id,
            match_datetime
        )

        return {
            "status": "success",
            "data": result,
            "engine": "ML_Enhanced_v2.0"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro na predição ML: {str(e)}"
        )

@router.get("/system/status")
async def get_ml_system_status() -> Dict:
    """
    📊 Status do sistema de Machine Learning

    Retorna informações sobre modelos, treinamento e configurações
    """
    try:
        return {
            "status": "success",
            "data": {
                "system_status": ml_manager.system_status,
                "configuration": ml_manager.config,
                "retrain_needed": await ml_manager.check_retrain_needed(),
                "last_check": datetime.now().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao verificar status: {str(e)}"
        )

@router.post("/system/initialize")
async def initialize_ml_system(background_tasks: BackgroundTasks) -> Dict:
    """
    🚀 Inicializar sistema de Machine Learning

    Executa setup completo: verifica modelos, treina se necessário, testa sistema
    """
    try:
        # Executar inicialização em background para não bloquear
        background_tasks.add_task(ml_manager.initialize_ml_system)

        return {
            "status": "success",
            "message": "Inicialização do sistema ML iniciada em background",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro na inicialização: {str(e)}"
        )

@router.post("/training/start")
async def start_training(
    training_request: TrainingRequest,
    background_tasks: BackgroundTasks
) -> Dict:
    """
    🎓 Iniciar treinamento de modelos ML

    - **training_type**: "full" para treinamento completo, "quick" para retreino rápido
    - **leagues**: Lista de ligas específicas (opcional)
    """
    try:
        training_service = MLTrainingService()

        if training_request.training_type == "full":
            # Treinamento completo em background
            background_tasks.add_task(training_service.run_full_training_pipeline)
            message = "Treinamento completo iniciado em background"
        else:
            # Retreinamento rápido
            background_tasks.add_task(training_service.quick_retrain)
            message = "Retreinamento rápido iniciado em background"

        return {
            "status": "success",
            "message": message,
            "training_type": training_request.training_type,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro no treinamento: {str(e)}"
        )

@router.post("/training/auto-retrain")
async def auto_retrain(background_tasks: BackgroundTasks) -> Dict:
    """
    🔄 Retreinamento automático baseado em configurações

    Verifica se retreinamento é necessário e executa se for o caso
    """
    try:
        background_tasks.add_task(ml_manager.auto_retrain_if_needed)

        return {
            "status": "success",
            "message": "Verificação de retreinamento automático iniciada",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro no retreinamento automático: {str(e)}"
        )

@router.get("/models/info")
async def get_models_info() -> Dict:
    """
    📋 Informações detalhadas sobre modelos treinados

    Retorna metadados, performance e estatísticas dos modelos
    """
    try:
        models_data = await ml_manager.ml_engine._load_models()

        if not models_data:
            return {
                "status": "success",
                "data": {
                    "models_available": False,
                    "message": "Nenhum modelo treinado encontrado"
                }
            }

        # Extrair informações dos modelos
        model_info = {
            "models_available": True,
            "training_date": models_data.get('training_date'),
            "training_samples": models_data.get('training_samples'),
            "feature_count": len(models_data.get('feature_columns', [])),
            "result_models": {},
            "goals_models": {}
        }

        # Informações dos modelos de resultado
        for name, model_data in models_data.get('result_models', {}).items():
            model_info['result_models'][name] = {
                'cv_mean': model_data.get('cv_mean'),
                'cv_std': model_data.get('cv_std'),
                'model_type': 'classification'
            }

        # Informações dos modelos de gols
        for name, model_data in models_data.get('goals_models', {}).items():
            model_info['goals_models'][name] = {
                'cv_mean': model_data.get('cv_mean'),
                'cv_std': model_data.get('cv_std'),
                'model_type': 'regression' if name != 'gradient_boosting' else 'classification'
            }

        return {
            "status": "success",
            "data": model_info
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter informações dos modelos: {str(e)}"
        )

@router.post("/prediction/compare/{home_team_id}/{away_team_id}")
async def compare_prediction_methods(
    home_team_id: str,
    away_team_id: str,
    match_date: Optional[str] = None
) -> Dict:
    """
    ⚖️ Comparar métodos de predição (ML vs Matemático)

    Retorna predições de ambos os métodos para comparação
    """
    try:
        # Converter data se fornecida
        if match_date:
            match_datetime = datetime.fromisoformat(match_date.replace('Z', '+00:00'))
        else:
            match_datetime = datetime.now()

        # Predição ML
        ml_prediction = await ml_manager.ml_engine.predict_with_ml(
            home_team_id, away_team_id, match_datetime
        )

        # Predição Matemática
        math_prediction = await ml_manager.real_engine.generate_real_prediction(
            f"{home_team_id}_vs_{away_team_id}",
            home_team_id,
            away_team_id,
            match_datetime
        )

        # Comparação
        comparison = {
            "match_info": {
                "home_team_id": home_team_id,
                "away_team_id": away_team_id,
                "match_date": match_datetime.isoformat()
            },
            "ml_prediction": ml_prediction,
            "mathematical_prediction": math_prediction,
            "comparison_analysis": {
                "ml_available": 'error' not in ml_prediction,
                "math_confidence": math_prediction.get('confidence_system', {}).get('overall_confidence', 0),
                "methods_agreement": "Both methods available" if 'error' not in ml_prediction else "Only mathematical available"
            }
        }

        return {
            "status": "success",
            "data": comparison
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro na comparação: {str(e)}"
        )

@router.get("/training/reports")
async def get_training_reports() -> Dict:
    """
    📋 Relatórios de treinamento disponíveis

    Lista relatórios de treinamentos anteriores
    """
    try:
        from pathlib import Path
        import json

        reports_dir = Path("app/ml/reports")

        if not reports_dir.exists():
            return {
                "status": "success",
                "data": {
                    "reports_available": False,
                    "reports": []
                }
            }

        reports = []
        for report_file in reports_dir.glob("training_report_*.json"):
            try:
                with open(report_file, 'r') as f:
                    report_data = json.load(f)

                reports.append({
                    "filename": report_file.name,
                    "creation_date": report_file.stat().st_mtime,
                    "summary": report_data.get('training_summary', {}),
                    "file_path": str(report_file)
                })
            except:
                continue

        # Ordenar por data mais recente
        reports.sort(key=lambda x: x['creation_date'], reverse=True)

        return {
            "status": "success",
            "data": {
                "reports_available": len(reports) > 0,
                "total_reports": len(reports),
                "reports": reports[:10]  # Últimos 10 relatórios
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao listar relatórios: {str(e)}"
        )

@router.post("/test/ml-engine/{home_team_id}/{away_team_id}")
async def test_ml_engine(
    home_team_id: str,
    away_team_id: str
) -> Dict:
    """
    🧪 Testar motor de ML com times específicos

    Endpoint para debugging e testes do sistema ML
    """
    try:
        # Teste básico do sistema
        test_result = {
            "system_check": {
                "models_loaded": ml_manager.system_status['models_trained'],
                "models_available": ml_manager.system_status['models_available']
            },
            "test_timestamp": datetime.now().isoformat()
        }

        # Tentar predição de teste
        if ml_manager.system_status['models_trained']:
            try:
                prediction = await ml_manager.ml_engine.predict_with_ml(
                    home_team_id, away_team_id, datetime.now()
                )
                test_result["prediction_test"] = {
                    "success": 'error' not in prediction,
                    "prediction_summary": prediction if 'error' not in prediction else prediction.get('error')
                }
            except Exception as e:
                test_result["prediction_test"] = {
                    "success": False,
                    "error": str(e)
                }
        else:
            test_result["prediction_test"] = {
                "success": False,
                "error": "Models not loaded"
            }

        return {
            "status": "success",
            "data": test_result
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro no teste: {str(e)}"
        )

@router.post("/training/universal")
async def train_universal_model(background_tasks: BackgroundTasks) -> Dict:
    """
    🌍 Treinar modelo universal com TODAS as ligas

    Treina um modelo que suporta:
    - La Liga, Premier League, Bundesliga, Serie A, Brasileirão, Champions League
    - Arquitetura ensemble robusta (RandomForest + GradientBoosting + LogisticRegression)
    - Feature engineering matemático avançado
    """
    try:
        # Verificar quantos dados temos
        from app.core.database import get_db_session
        from app.models.match import Match

        with get_db_session() as session:
            total_matches = session.query(Match).filter(
                Match.home_score.isnot(None),
                Match.away_score.isnot(None),
                Match.status == 'FINISHED'
            ).count()

            leagues_data = session.query(Match.league, session.query(Match).filter(
                Match.home_score.isnot(None),
                Match.away_score.isnot(None),
                Match.status == 'FINISHED',
                Match.league == Match.league
            ).count()).group_by(Match.league).all()

        training_info = {
            "status": "INICIADO",
            "total_finished_matches": total_matches,
            "leagues_breakdown": dict(leagues_data) if leagues_data else {},
            "trainer_type": "universal",
            "models_to_train": ["random_forest", "gradient_boosting", "logistic_regression"],
            "start_time": datetime.now().isoformat()
        }

        if total_matches < 50:
            return {
                "status": "insufficient_data",
                "message": f"Apenas {total_matches} partidas finalizadas. Mínimo recomendado: 50",
                "data": training_info
            }

        # Iniciar treinamento em background
        background_tasks.add_task(
            _train_universal_background,
            training_info
        )

        return {
            "status": "training_started",
            "message": "🌍 Treinamento universal iniciado em background",
            "data": training_info
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao iniciar treinamento universal: {str(e)}"
        )

async def _train_universal_background(training_info: Dict):
    """Função background para treinar modelo universal"""
    try:
        print("🌍 INICIANDO TREINAMENTO UNIVERSAL ML")
        print("=" * 60)

        # Treinar com todas as ligas
        result = await universal_ml_trainer.train_models_with_real_data()

        print(f"✅ TREINAMENTO CONCLUÍDO: {result.get('success', False)}")

        if result.get('success'):
            print(f"📊 Total de jogos: {result['data_stats']['total_matches']}")
            print(f"🏆 Ligas processadas: {list(result['data_stats']['leagues'].keys())}")

            for model_name, metrics in result['models_trained'].items():
                print(f"🤖 {model_name}: {metrics['test_accuracy']:.3f} accuracy")

        return result

    except Exception as e:
        print(f"❌ ERRO no treinamento universal: {e}")
        return {"success": False, "error": str(e)}

@router.get("/universal/status")
async def get_universal_model_status() -> Dict:
    """
    🌍 Status do modelo universal ML

    Retorna informações sobre modelos universais treinados
    """
    try:
        import os
        from pathlib import Path

        models_dir = Path(universal_ml_trainer.models_dir)

        status = {
            "models_dir": str(models_dir),
            "models_exist": models_dir.exists(),
            "trained_models": [],
            "metadata_available": False,
            "supported_leagues": [],
            "total_teams": 0
        }

        if models_dir.exists():
            # Verificar modelos treinados
            model_files = [f for f in os.listdir(models_dir) if f.endswith('_real_data.joblib')]
            status["trained_models"] = [f.replace('_real_data.joblib', '') for f in model_files]

            # Verificar metadata
            metadata_file = models_dir / "training_metadata.joblib"
            status["metadata_available"] = metadata_file.exists()

            if metadata_file.exists():
                import joblib
                metadata = joblib.load(metadata_file)
                status["training_date"] = metadata.get('training_date', 'Unknown')
                status["total_samples"] = metadata.get('total_samples', 0)
                status["feature_names"] = metadata.get('feature_names', [])

        # Verificar dados disponíveis por liga
        from app.core.database import get_db_session
        from app.models.match import Match

        with get_db_session() as session:
            leagues_count = session.query(
                Match.league,
                session.query(Match).filter(
                    Match.league == Match.league,
                    Match.home_score.isnot(None),
                    Match.away_score.isnot(None),
                    Match.status == 'FINISHED'
                ).count()
            ).group_by(Match.league).all()

            status["supported_leagues"] = [{"league": league, "finished_matches": count} for league, count in leagues_count]
            status["total_finished_matches"] = sum([count for _, count in leagues_count])

        return {
            "status": "success",
            "data": status
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao verificar status universal: {str(e)}"
        )

@router.post("/universal/predict/{home_team}/{away_team}")
async def predict_universal_match(
    home_team: str,
    away_team: str,
    league: Optional[str] = None
) -> Dict:
    """
    🌍 Predição universal para qualquer liga

    Usa o modelo universal treinado com todas as ligas
    """
    try:
        # Fazer predição usando o modelo universal
        prediction_result = await universal_ml_trainer.predict_match_outcome(
            home_team=home_team,
            away_team=away_team,
            league=league or "Unknown"
        )

        if 'error' in prediction_result:
            return {
                "status": "error",
                "message": prediction_result['error'],
                "data": {
                    "home_team": home_team,
                    "away_team": away_team,
                    "league": league
                }
            }

        return {
            "status": "success",
            "message": "Predição universal gerada com sucesso",
            "data": {
                "match_info": {
                    "home_team": home_team,
                    "away_team": away_team,
                    "league": league or "Unknown"
                },
                "prediction": prediction_result,
                "model_type": "universal_ensemble"
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro na predição universal: {str(e)}"
        )