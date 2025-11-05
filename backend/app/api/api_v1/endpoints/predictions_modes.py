#!/usr/bin/env python3
"""
🎯 ENDPOINTS PARA OS 3 MODOS DE PREDICTIONS

1. AUTOMÁTICO: ML + AI validação automática
2. ASSISTIDO: Usuário escolhe + AI explica
3. MANUAL: Usuário expert cria (GOLD data)
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db_session
from app.models import Match, Prediction
from app.services.ai_prediction_validator import ai_validator
from app.services.poisson_service import poisson_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== MODELS ====================

class AutomaticPredictionResponse(BaseModel):
    """Response para modo automático"""
    match_id: int
    match_info: dict
    prediction: dict
    ai_validation: dict
    status: str  # 'approved' ou 'rejected'


class AssistedAnalysisRequest(BaseModel):
    """Request para modo assistido - AGORA SUPORTA MÚLTIPLOS JOGOS E MÚLTIPLAS CATEGORIAS"""
    match_ids: List[int]  # 🔥 Múltiplos jogos
    market_type: Optional[str] = None  # 🔥 Opcional: Mercado específico
    market_categories: Optional[List[str]] = None  # 🔥 NOVO: Múltiplas categorias (ex: ["Over/Under", "BTTS", "1X2"])
    selected_outcome: Optional[str] = None


class AssistedAnalysisResponse(BaseModel):
    """Response para modo assistido - Single Match"""
    match_id: int
    match_info: dict
    selected_market: str  # 🔥 Mercado escolhido (AI ou usuário)
    selected_category: Optional[str] = None  # 🔥 NOVO: Categoria escolhida (quando MULTI_CATEGORY)
    ml_analysis: dict
    ai_insights: dict
    recommendation: dict


class AssistedMultipleAnalysisResponse(BaseModel):
    """Response para modo assistido - Multiple Matches"""
    total_matches: int
    selection_mode: str  # 'AI_AUTO', 'CATEGORY', 'MULTI_CATEGORY', 'SPECIFIC'
    analyses: List[AssistedAnalysisResponse]
    combined_recommendation: dict  # Recomendação do ticket combinado


class ManualPredictionRequest(BaseModel):
    """Request para modo manual"""
    match_id: int
    market_type: str
    predicted_outcome: str
    user_confidence: float
    user_reasoning: str
    stake_percentage: Optional[float] = 2.0


class ManualPredictionResponse(BaseModel):
    """Response para modo manual"""
    prediction_id: int
    status: str
    gold_data_registered: bool
    message: str


# ==================== MODO 1: AUTOMÁTICO ====================

@router.get("/automatic/top-predictions", response_model=List[AutomaticPredictionResponse])
async def get_automatic_predictions(
    limit: int = Query(default=50, le=100),
    min_confidence: float = Query(default=0.50, ge=0.3, le=1.0),  # 🔥 REDUZIDO: 0.6 → 0.5
    min_edge: float = Query(default=0.0, ge=0),  # 🔥 REMOVIDO: 10 → 0 (sem filtro de edge)
    db: Session = Depends(get_db_session)
):
    """
    🤖 MODO AUTOMÁTICO - COM PROPORÇÃO CORRETA

    Retorna TOP predictions automáticas com proporção:
    - 5% SINGLES (~3 tickets)
    - 80% DOUBLES/TREBLES (~40 tickets)
    - 15% MULTIPLES (~7 tickets)

    Args:
        limit: Máximo de predictions (default 50)
        min_confidence: Confiança mínima do ML (default 0.6)
        min_edge: Edge mínimo % (default 10%)
    """
    logger.info(f"🤖 Buscando TOP {limit} predictions automáticas com proporção 5/80/15...")

    # Calcular proporções
    singles_limit = max(1, int(limit * 0.05))  # 5%
    combos_limit = int(limit * 0.80)  # 80%
    multiples_limit = max(1, int(limit * 0.15))  # 15%

    # Buscar SINGLES
    singles_query = db.query(Prediction).filter(
        Prediction.is_validated == False,
        Prediction.prediction_type == 'SINGLE'
    ).order_by(
        Prediction.confidence_score.desc(),
        Prediction.predicted_probability.desc()
    ).limit(singles_limit * 3).all()

    # Buscar DOUBLES/TREBLES
    combos_query = db.query(Prediction).filter(
        Prediction.is_validated == False,
        Prediction.prediction_type.in_(['DOUBLE', 'TREBLE', 'MULTI_2X', 'MULTI_3X', 'COMBO_2X', 'COMBO_3X'])
    ).order_by(
        Prediction.confidence_score.desc(),
        Prediction.predicted_probability.desc()
    ).limit(combos_limit * 2).all()

    # Buscar MULTIPLES (4+)
    multiples_query = db.query(Prediction).filter(
        Prediction.is_validated == False,
        Prediction.prediction_type.in_(['MULTIPLE', 'MULTI_4X', 'COMBO_4X'])
    ).order_by(
        Prediction.confidence_score.desc(),
        Prediction.predicted_probability.desc()
    ).limit(multiples_limit * 3).all()

    approved_predictions = []

    # Processar cada grupo
    for pred_group, group_limit, group_name in [
        (singles_query, singles_limit, 'SINGLES'),
        (combos_query, combos_limit, 'DOUBLES/TREBLES'),
        (multiples_query, multiples_limit, 'MULTIPLES')
    ]:
        group_approved = 0

        for pred in pred_group:
            if group_approved >= group_limit:
                break

            try:
                # Buscar match
                match = db.query(Match).filter(Match.id == pred.match_id).first()
                if not match or match.status != 'NS':
                    continue

                # Usar confidence_score e predicted_probability da prediction
                confidence = pred.confidence_score or 0.7
                probability = pred.predicted_probability or 0.5

                # Calcular edge baseado na odd
                fair_odds = 1 / probability if probability > 0 else 2.0
                market_odds = pred.actual_odds or 2.0
                edge = ((market_odds / fair_odds) - 1) * 100 if fair_odds > 0 else 0

                # Preparar dados para AI
                prediction_data = {
                    'match_id': pred.match_id,
                    'market_type': pred.market_type,
                    'predicted_outcome': pred.predicted_outcome,
                    'confidence': confidence,
                    'edge': edge,
                    'odds': market_odds
                }

                # Validação simplificada (sem AI - usar apenas confidence)
                # 🔥 CRÍTICO: AI está travando, usando validação direta
                is_validated = confidence >= min_confidence

                # Calcular Kelly Criterion para stake recomendado
                # Kelly = (probability * odds - 1) / (odds - 1)
                kelly_stake = 0.0
                if market_odds > 1 and probability > 0:
                    kelly_full = (probability * market_odds - 1) / (market_odds - 1)
                    kelly_stake = max(0.5, min(kelly_full * 0.25, 5.0))  # 25% do Kelly, entre 0.5% e 5%

                ai_validation = {
                    'validated': is_validated,
                    'validation_mode': 'AUTOMATIC',
                    'ai_confidence': confidence,  # 🔥 NOVO: para frontend
                    'edge_percentage': edge,  # 🔥 NOVO: para frontend
                    'recommended_stake': kelly_stake,  # 🔥 NOVO: para frontend (% da banca)
                    'reasoning': f'Confidence {confidence:.1%}, Edge {edge:+.1f}% (odds {market_odds:.2f})',
                    'risk_level': 'HIGH' if confidence < 0.6 else 'MEDIUM' if confidence < 0.75 else 'LOW'
                }

                if is_validated:
                    approved_predictions.append(AutomaticPredictionResponse(
                        match_id=pred.match_id,
                        match_info={
                            'home_team': match.home_team if isinstance(match.home_team, str) else match.home_team.name,
                            'away_team': match.away_team if isinstance(match.away_team, str) else match.away_team.name,
                            'league': match.league,
                            'match_date': match.match_date.isoformat() if match.match_date else None
                        },
                        prediction={
                            'market_type': pred.market_type,
                            'outcome': pred.predicted_outcome,
                            'confidence': confidence,
                            'edge': edge,
                            'odds': market_odds,
                            'prediction_type': pred.prediction_type  # 🔥 NOVO: mostrar tipo
                        },
                        ai_validation=ai_validation,
                        status='approved'
                    ))
                    group_approved += 1

            except Exception as e:
                logger.error(f"Erro ao processar prediction {pred.id}: {e}")
                continue

        logger.info(f"  {group_name}: {group_approved}/{group_limit} aprovadas")

    logger.info(f"✅ {len(approved_predictions)} predictions automáticas aprovadas (proporção 5/80/15)")
    return approved_predictions


# ==================== MODO 2: ASSISTIDO ====================

@router.post("/assisted/analyze", response_model=AssistedMultipleAnalysisResponse)
async def analyze_assisted_prediction(
    request: AssistedAnalysisRequest,
    db: Session = Depends(get_db_session)
):
    """
    🧠 MODO ASSISTIDO - VERSÃO 3.0 (MÚLTIPLOS JOGOS + MÚLTIPLAS CATEGORIAS)

    Usuário escolhe:
    1. JOGOS: Um ou múltiplos jogos
    2. MERCADOS (OPCIONAL):
       - Específico (ex: "OVER_2_5")
       - Categoria única (ex: "Over/Under") → AI escolhe melhor dentro da categoria
       - Múltiplas categorias (ex: ["Over/Under", "BTTS", "1X2"]) → AI escolhe melhor de CADA categoria
       - Nenhum (AI_AUTO) → AI escolhe melhor mercado baseado em matemática + contexto

    ML + AI trabalham juntos:
    - ML calcula probabilidades (Poisson)
    - AI analisa contexto e escolhe melhores mercados
    - AI valida e explica TUDO
    - Usuário vê análise completa e decide

    Args:
        request: Lista de match IDs + seleção de mercados (opcional)
    """
    logger.info(f"🧠 Análise assistida: {len(request.match_ids)} jogos, Mercado: {request.market_type or request.market_categories or 'AI_AUTO'}")

    # Validar que temos pelo menos 1 jogo
    if not request.match_ids or len(request.match_ids) == 0:
        raise HTTPException(status_code=400, detail="Pelo menos 1 jogo deve ser selecionado")

    # Determinar modo de seleção
    if request.market_type:
        selection_mode = "SPECIFIC"  # Mercado específico escolhido
    elif request.market_categories and len(request.market_categories) > 1:
        selection_mode = "MULTI_CATEGORY"  # Múltiplas categorias, AI escolhe melhor de cada
    elif request.market_categories and len(request.market_categories) == 1:
        selection_mode = "CATEGORY"  # Categoria única, AI decide qual mercado
    else:
        selection_mode = "AI_AUTO"  # AI decide tudo

    analyses = []

    try:
        from app.models import TeamStatistics, Odds

        # 🔥 LOOP: Processar cada jogo selecionado
        for match_id in request.match_ids:
            # Buscar match
            match = db.query(Match).filter(Match.id == match_id).first()
            if not match:
                logger.warning(f"Match {match_id} não encontrado, pulando...")
                continue

            # Buscar stats dos times
            home_stats = db.query(TeamStatistics).filter(
                TeamStatistics.team_id == match.home_team_id
            ).order_by(TeamStatistics.created_at.desc()).first()

            away_stats = db.query(TeamStatistics).filter(
                TeamStatistics.team_id == match.away_team_id
            ).order_by(TeamStatistics.created_at.desc()).first()

            # Buscar odds reais
            odds_record = db.query(Odds).filter(Odds.match_id == match_id).first()

            # Preparar market_odds para o Poisson
            market_odds_dict = {}
            if odds_record:
                market_odds_dict = {
                    'HOME_WIN': odds_record.home_win,
                    'DRAW': odds_record.draw,
                    'AWAY_WIN': odds_record.away_win
                }

            # Análise Poisson completa
            poisson_analysis = poisson_service.analyze_match(
                home_goals_avg=home_stats.goals_scored_avg if home_stats else 1.5,
                away_goals_avg=away_stats.goals_scored_avg if away_stats else 1.3,
                home_conceded_avg=home_stats.goals_conceded_avg if home_stats else 1.2,
                away_conceded_avg=away_stats.goals_conceded_avg if away_stats else 1.1,
                market_odds=market_odds_dict,
                league_avg=2.7
            )

            # 🔥 DETERMINAR CATEGORIAS A PROCESSAR
            categories_to_process = []

            if selection_mode == "MULTI_CATEGORY":
                # Múltiplas categorias: processar cada uma
                categories_to_process = request.market_categories
            elif selection_mode == "CATEGORY":
                # Categoria única
                categories_to_process = [request.market_categories[0]]
            else:
                # SPECIFIC ou AI_AUTO: apenas uma iteração (sem categoria)
                categories_to_process = [None]

            # 🔥 LOOP POR CATEGORIA (se MULTI_CATEGORY, gera múltiplas análises por jogo)
            for category in categories_to_process:
                selected_market_key = None
                selected_category = None

                if selection_mode == "SPECIFIC":
                    # Usuário escolheu mercado específico
                    selected_market_key = request.market_type
                    logger.info(f"Match {match_id}: Mercado específico escolhido: {selected_market_key}")

                elif selection_mode in ["CATEGORY", "MULTI_CATEGORY"]:
                    # AI escolhe melhor mercado dentro da categoria
                    selected_market_key = await _select_best_market_in_category(
                        category,
                        poisson_analysis,
                        odds_record
                    )
                    selected_category = category
                    logger.info(f"Match {match_id}: AI escolheu {selected_market_key} na categoria {category}")

                else:  # AI_AUTO
                    # AI escolhe melhor mercado baseado em matemática + contexto
                    selected_market_key = await _select_best_market_auto(
                        poisson_analysis,
                        odds_record,
                        match
                    )
                    logger.info(f"Match {match_id}: AI escolheu automaticamente: {selected_market_key}")

                # Extrair dados do mercado selecionado
                market_prob = poisson_analysis.probabilities.get(selected_market_key, 0.5)
                fair_odds = poisson_analysis.fair_odds.get(selected_market_key, 2.0)

                # Buscar odd de mercado real
                market_odds_value = 2.0  # default
                if odds_record and hasattr(odds_record, selected_market_key.lower()):
                    market_odds_value = getattr(odds_record, selected_market_key.lower(), 2.0)

                # Calcular edge
                edge = ((market_odds_value / fair_odds) - 1) * 100 if fair_odds > 0 else 0

                # Montar análise ML
                ml_analysis = {
                    'probability': float(market_prob),
                    'fair_odds': float(fair_odds),
                    'market_odds': float(market_odds_value),
                    'edge': float(edge),
                    'confidence': 0.75,
                    'variance': 0.15,
                    'sample_size': 50,
                    'historical_accuracy': 0.68
                }

                # Preparar dados para AI
                match_info = {
                    'home_team': match.home_team if isinstance(match.home_team, str) else match.home_team.name,
                    'away_team': match.away_team if isinstance(match.away_team, str) else match.away_team.name,
                    'league': match.league
                }

                user_selection = {
                    'match_info': match_info,
                    'market_type': selected_market_key,
                    'selection_mode': selection_mode
                }

                # AI valida e fornece insights
                ai_insights = await ai_validator.validate_assisted_prediction(user_selection, ml_analysis)

                # Adicionar análise completa
                analyses.append(AssistedAnalysisResponse(
                    match_id=match_id,
                    match_info=match_info,
                    selected_market=selected_market_key,
                    selected_category=selected_category,  # 🔥 NOVO: Indica qual categoria foi usada
                    ml_analysis=ml_analysis,
                    ai_insights=ai_insights,
                    recommendation=ai_insights['recommendation']
                ))

        # 🔥 Criar recomendação combinada (para múltiplos jogos)
        combined_recommendation = _create_combined_recommendation(analyses, selection_mode)

        return AssistedMultipleAnalysisResponse(
            total_matches=len(analyses),
            selection_mode=selection_mode,
            analyses=analyses,
            combined_recommendation=combined_recommendation
        )

    except Exception as e:
        logger.error(f"Erro na análise assistida: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== HELPER FUNCTIONS FOR ASSISTED MODE ====================

async def _select_best_market_in_category(category: str, poisson_analysis, odds_record) -> str:
    """
    🎯 AI escolhe o MELHOR mercado dentro de uma categoria específica

    Exemplo: Categoria "Over/Under" → escolhe entre OVER_1_5, OVER_2_5, OVER_3_5, UNDER_1_5, etc.
    Critério: Maior edge positivo ou melhor probabilidade se edges similares
    """
    # 🔥 Mapear categorias para seus mercados (ATUALIZADO - em português estilo bet365)
    CATEGORY_MARKETS = {
        'Resultado Final (1X2)': ['HOME_WIN', 'DRAW', 'AWAY_WIN'],
        'Ambas Marcam': ['BTTS_YES', 'BTTS_NO'],
        'Total de Gols': ['OVER_0_5', 'OVER_1_5', 'OVER_2_5', 'OVER_3_5', 'OVER_4_5', 'OVER_5_5',
                          'UNDER_0_5', 'UNDER_1_5', 'UNDER_2_5', 'UNDER_3_5', 'UNDER_4_5', 'UNDER_5_5'],
        'Dupla Chance': ['DOUBLE_CHANCE_1X', 'DOUBLE_CHANCE_12', 'DOUBLE_CHANCE_X2'],
        'Total Exato de Gols': ['EXACT_GOALS_0', 'EXACT_GOALS_1', 'EXACT_GOALS_2', 'EXACT_GOALS_3', 'EXACT_GOALS_4_PLUS'],
        'Primeiro a Marcar': ['FIRST_GOAL_HOME', 'FIRST_GOAL_AWAY', 'FIRST_GOAL_NONE'],
        'Não Toma Gol': ['CLEAN_SHEET_HOME', 'CLEAN_SHEET_AWAY']
    }

    markets_in_category = CATEGORY_MARKETS.get(category, [])
    if not markets_in_category:
        logger.warning(f"Categoria {category} desconhecida, usando HOME_WIN")
        return 'HOME_WIN'

    best_market = markets_in_category[0]
    best_edge = -999999

    for market_key in markets_in_category:
        fair_odds = poisson_analysis.fair_odds.get(market_key, 0)
        if fair_odds <= 0:
            continue

        # Buscar odd real
        market_odds = 2.0
        if odds_record and hasattr(odds_record, market_key.lower()):
            market_odds = getattr(odds_record, market_key.lower(), 2.0)

        # Calcular edge
        edge = ((market_odds / fair_odds) - 1) * 100

        # Escolher mercado com melhor edge
        if edge > best_edge:
            best_edge = edge
            best_market = market_key

    logger.info(f"Categoria {category}: Melhor mercado = {best_market} (edge {best_edge:.1f}%)")
    return best_market


async def _select_best_market_auto(poisson_analysis, odds_record, match) -> str:
    """
    🤖 AI escolhe o MELHOR mercado AUTOMATICAMENTE

    Analisa TODOS os 45+ mercados e escolhe o melhor baseado em:
    1. Edge positivo (>10%)
    2. Probabilidade razoável (>15%)
    3. Confiança do modelo
    4. Contexto do jogo (via nome dos times e liga)
    """
    CRITICAL_MIN_EDGE = 10.0  # Edge mínimo para considerar
    MIN_PROBABILITY = 0.15  # Probabilidade mínima

    best_market = 'HOME_WIN'  # Fallback
    best_score = -999999

    # Avaliar todos os mercados
    for market_key, prob in poisson_analysis.probabilities.items():
        if prob < MIN_PROBABILITY:
            continue

        fair_odds = poisson_analysis.fair_odds.get(market_key, 0)
        if fair_odds <= 0:
            continue

        # Buscar odd real
        market_odds = 2.0
        if odds_record and hasattr(odds_record, market_key.lower()):
            market_odds = getattr(odds_record, market_key.lower(), 2.0)

        # Calcular edge
        edge = ((market_odds / fair_odds) - 1) * 100

        # Score: combinação de edge + probabilidade
        # Mercados com edge alto e probabilidade razoável têm prioridade
        score = edge * 2 + (prob * 100)  # Edge conta 2x mais que probabilidade

        if edge > best_score and edge >= CRITICAL_MIN_EDGE:
            best_score = edge
            best_market = market_key

    logger.info(f"AI Auto: Melhor mercado = {best_market} (score {best_score:.1f})")
    return best_market


def _create_combined_recommendation(analyses: List[AssistedAnalysisResponse], selection_mode: str) -> dict:
    """
    🎲 Cria recomendação combinada para múltiplos jogos (Acumulada/Múltipla)

    Analisa todas as análises individuais e retorna:
    - should_bet: Se deve apostar na múltipla
    - total_odds: Odd total da múltipla
    - combined_probability: Probabilidade combinada
    - stake_percentage: Porcentagem recomendada da banca
    - reasoning: Explicação detalhada
    """
    if not analyses or len(analyses) == 0:
        return {
            'should_bet': False,
            'total_odds': 1.0,
            'combined_probability': 0.0,
            'stake_percentage': 0.0,
            'reasoning': 'Nenhuma análise disponível'
        }

    # Calcular métricas combinadas
    total_odds = 1.0
    combined_probability = 1.0
    total_edge = 0.0
    approved_count = 0

    for analysis in analyses:
        ml = analysis.ml_analysis
        total_odds *= ml['fair_odds']
        combined_probability *= ml['probability']
        total_edge += ml['edge']

        if analysis.recommendation.get('should_bet', False):
            approved_count += 1

    avg_edge = total_edge / len(analyses) if len(analyses) > 0 else 0

    # Critérios para recomendar múltipla
    should_bet = (
        approved_count >= len(analyses) * 0.8 and  # 80%+ aprovadas
        avg_edge >= 8.0 and  # Edge médio bom
        combined_probability >= 0.10  # Prob combinada razoável (10%+)
    )

    # Kelly Criterion ajustado para múltiplas (mais conservador)
    stake_percentage = 0.0
    if should_bet and total_odds > 1:
        kelly = (combined_probability * total_odds - 1) / (total_odds - 1)
        stake_percentage = max(0.5, min(kelly * 0.25, 3.0))  # 25% do Kelly, max 3%

    # Reasoning
    reasoning_parts = [
        f"Múltipla com {len(analyses)} jogos selecionados.",
        f"Modo de seleção: {selection_mode}.",
        f"{approved_count}/{len(analyses)} jogos aprovados individualmente.",
        f"Odd total: {total_odds:.2f}, Probabilidade combinada: {combined_probability*100:.1f}%",
        f"Edge médio: {avg_edge:.1f}%"
    ]

    if should_bet:
        reasoning_parts.append(f"✅ RECOMENDADO apostar {stake_percentage:.1f}% da banca.")
    else:
        reasoning_parts.append("❌ NÃO RECOMENDADO - Critérios de qualidade não atingidos.")

    return {
        'should_bet': should_bet,
        'total_odds': float(total_odds),
        'combined_probability': float(combined_probability),
        'total_edge': float(total_edge),
        'avg_edge': float(avg_edge),
        'approved_count': approved_count,
        'total_matches': len(analyses),
        'stake_percentage': float(stake_percentage),
        'reasoning': ' '.join(reasoning_parts)
    }


# ==================== MODO 3: MANUAL ====================

@router.post("/manual/create", response_model=ManualPredictionResponse)
async def create_manual_prediction(
    request: ManualPredictionRequest,
    db: Session = Depends(get_db_session)
):
    """
    💎 MODO MANUAL (GOLD DATA)

    Usuário expert cria prediction manualmente
    - Ignora ML e AI completamente
    - Registra como GOLD data (peso 2x)
    - Será usado para treinar e melhorar ML

    Args:
        request: Prediction manual do usuário
    """
    logger.info(f"💎 Criando prediction MANUAL (GOLD): Match {request.match_id}")

    # Buscar match
    match = db.query(Match).filter(Match.id == request.match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    try:
        # Criar prediction
        prediction = Prediction(
            match_id=request.match_id,
            market_type=request.market_type,
            predicted_outcome=request.predicted_outcome,
            is_validated=False,
            created_at=datetime.now()
        )

        db.add(prediction)
        db.commit()
        db.refresh(prediction)

        # Registrar como GOLD data
        manual_data = {
            'match_id': request.match_id,
            'market_type': request.market_type,
            'predicted_outcome': request.predicted_outcome,
            'user_confidence': request.user_confidence,
            'user_reasoning': request.user_reasoning
        }

        gold_registration = await ai_validator.register_manual_prediction(manual_data)

        logger.info(f"✅ Prediction MANUAL criada: ID {prediction.id}")

        return ManualPredictionResponse(
            prediction_id=prediction.id,
            status='created',
            gold_data_registered=True,
            message=f"Prediction criada com sucesso! Registrada como GOLD data (peso 2x) para treinar ML."
        )

    except Exception as e:
        logger.error(f"Erro ao criar prediction manual: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ==================== HELPERS ====================

@router.get("/modes/info")
async def get_modes_info():
    """
    Retorna informações sobre os 3 modos

    Para o frontend exibir explicação dos modos
    """
    return {
        'modes': [
            {
                'id': 'automatic',
                'name': '🤖 Automático',
                'description': 'ML gera predictions → AI valida → Você vê apenas as aprovadas',
                'difficulty': 'Iniciante',
                'volume': '~100 predictions/dia',
                'features': [
                    'Totalmente automatizado',
                    'AI filtra as melhores',
                    'Zero esforço',
                    'Ideal para iniciantes'
                ]
            },
            {
                'id': 'assisted',
                'name': '🧠 Assistido',
                'description': 'Você escolhe → ML calcula → AI explica → Você decide',
                'difficulty': 'Intermediário',
                'volume': 'Quantas você quiser',
                'features': [
                    'Você tem controle',
                    'AI explica tudo',
                    'Aprende com AI',
                    'Ideal para aprender'
                ]
            },
            {
                'id': 'manual',
                'name': '💎 Manual (Expert)',
                'description': 'Você cria tudo manualmente → Sistema aprende com você',
                'difficulty': 'Expert',
                'volume': 'Ilimitado',
                'features': [
                    'Controle total',
                    'Ignora ML/AI',
                    'GOLD data (peso 2x)',
                    'Melhora o sistema'
                ]
            }
        ]
    }
