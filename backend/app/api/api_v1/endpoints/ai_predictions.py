"""
🤖 AI-POWERED PREDICTIONS ENDPOINTS
Endpoints para predictions assistidas por AI Agent
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.services.user_prediction_assistant import UserPredictionAssistant

router = APIRouter()


# Schemas
class AnalysisRequest(BaseModel):
    match_id: int
    markets: List[str] = ['1X2']
    user_context: Optional[dict] = None


class PredictionCreateRequest(BaseModel):
    match_id: int
    markets: List[str]
    user_override: Optional[dict] = None


# Endpoints
@router.post("/analyze-with-ai")
async def analyze_prediction_with_ai(
    request: AnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    🧠 Analisa prediction com AI Agent

    **Fluxo:**
    1. ML calcula probabilidades matemáticas
    2. Context Analyzer busca notícias, clima, rivalidade
    3. AI Agent (Ollama) analisa contexto profundo
    4. Retorna recomendação completa

    **Returns:**
    - **ml_analysis**: Probabilidades e confidence do ML
    - **context**: Notícias, rivalidade, motivação, clima
    - **ai_analysis**: Análise contextual do LLM
    - **final_recommendation**: Recomendação final (BET/SKIP/MONITOR)
    """
    assistant = UserPredictionAssistant(db)

    try:
        analysis = await assistant.analyze_user_selection(
            match_id=request.match_id,
            markets=request.markets,
            user_context=request.user_context
        )

        if 'error' in analysis:
            raise HTTPException(status_code=404, detail=analysis['error'])

        return analysis

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-assisted")
async def create_assisted_prediction(
    request: PredictionCreateRequest,
    db: Session = Depends(get_db)
):
    """
    ✅ Cria prediction com assistência do AI

    Usuário pode:
    - Aceitar recomendação do AI
    - Modificar valores (override)
    - Ver análise completa antes de confirmar

    **Returns:**
    - prediction_id: ID da prediction criada
    - analysis: Análise completa que gerou a prediction
    """
    assistant = UserPredictionAssistant(db)

    try:
        result = await assistant.create_assisted_prediction(
            match_id=request.match_id,
            markets=request.markets,
            user_override=request.user_override
        )

        if 'error' in result:
            raise HTTPException(status_code=404, detail=result['error'])

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/community-consensus/{match_id}")
async def get_community_consensus(
    match_id: int,
    db: Session = Depends(get_db)
):
    """
    👥 Obtém consensus da comunidade

    Compara prediction do usuário com o que a comunidade está apostando

    **Returns:**
    - consensus_outcome: Outcome mais escolhido
    - consensus_percentage: % da comunidade que escolheu
    - distribution: Distribuição completa de predictions
    """
    assistant = UserPredictionAssistant(db)

    try:
        consensus = assistant.compare_with_community(match_id)
        return consensus

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ai-status")
async def check_ai_status(db: Session = Depends(get_db)):
    """
    🔍 Verifica status do AI Agent

    Retorna se Ollama está rodando e qual modelo está ativo

    **Returns:**
    - available: True se AI Agent está funcionando
    - model: Modelo Ollama em uso
    - features: Lista de features disponíveis
    """
    from app.services.ai_agent_service import AIAgentService

    ai_agent = AIAgentService()

    return {
        'available': ai_agent.is_available(),
        'model': ai_agent.model if ai_agent.is_available() else None,
        'features': {
            'context_analysis': True,
            'news_integration': True,
            'few_shot_learning': True,
            'real_time_adaptation': ai_agent.is_available()
        },
        'message': 'AI Agent ativo' if ai_agent.is_available() else 'Ollama não encontrado. Instale: ollama pull llama3.1:8b'
    }


@router.get("/learning-stats")
async def get_learning_statistics(
    market_type: Optional[str] = None,
    last_n_days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    📊 Estatísticas de aprendizado do AI

    Mostra taxa de sucesso (GREEN/RED) e padrões identificados

    **Returns:**
    - success_rate: Taxa de acerto geral
    - total_predictions: Total de predictions analisadas
    - best_patterns: Padrões com maior taxa de sucesso
    """
    from app.services.few_shot_memory import get_few_shot_memory

    memory = get_few_shot_memory(db)

    stats = memory.get_success_rate(
        market_type=market_type,
        last_n_days=last_n_days
    )

    patterns = memory.get_best_patterns(limit=5)

    return {
        'statistics': stats,
        'best_patterns': patterns,
        'learning_active': True
    }
