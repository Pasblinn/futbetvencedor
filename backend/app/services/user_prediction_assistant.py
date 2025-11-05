"""
🎯 USER PREDICTION ASSISTANT
Assistente AI para predictions criadas pelo usuário

Fluxo:
1. Usuário escolhe jogo + mercados
2. ML calcula probabilidades
3. AI Agent analisa contexto
4. Usuário vê análise completa antes de confirmar
5. Pode aceitar, modificar ou rejeitar
"""
import logging
from typing import Dict, List
from sqlalchemy.orm import Session

from app.models import Match
from app.services.prediction_service import PredictionService
from app.services.ai_agent_service import AIAgentService
from app.services.context_analyzer import get_context_analyzer
from app.services.few_shot_memory import get_few_shot_memory

logger = logging.getLogger(__name__)


class UserPredictionAssistant:
    """
    Assistente inteligente para predictions do usuário
    Combina ML + AI Agent para análise completa
    """

    def __init__(self, db: Session):
        self.db = db
        self.prediction_service = PredictionService(db)
        self.ai_agent = AIAgentService()
        self.context_analyzer = get_context_analyzer(db)
        self.memory = get_few_shot_memory(db)

    async def analyze_user_selection(
        self,
        match_id: int,
        markets: List[str] = None,
        user_context: Dict = None
    ) -> Dict:
        """
        Analisa seleção do usuário com AI Agent

        Args:
            match_id: ID do jogo escolhido
            markets: Mercados selecionados (ex: ['1X2', 'OVER_UNDER'])
            user_context: Contexto adicional fornecido pelo usuário

        Returns:
            Análise completa com recomendação do AI
        """
        logger.info(f"🎯 Assistindo usuário na prediction para match {match_id}")

        # 1. Buscar dados do jogo
        match = self.db.query(Match).filter(Match.id == match_id).first()

        if not match:
            return {
                'error': 'Match not found',
                'match_id': match_id
            }

        # 2. Gerar prediction ML
        logger.info("📊 Calculando probabilidades com ML...")
        ml_prediction = await self.prediction_service.generate_match_prediction(match_id)

        if not ml_prediction:
            return {
                'error': 'Failed to generate ML prediction',
                'match_id': match_id
            }

        # 3. Analisar contexto externo
        logger.info("🌍 Buscando contexto externo...")
        context_data = self.context_analyzer.analyze_match_context(match)

        # 4. Obter exemplos de aprendizado
        logger.info("📚 Carregando exemplos de aprendizado...")
        few_shot_examples = self.memory.get_learning_examples(limit=10)

        # 5. Análise do AI Agent
        if self.ai_agent.is_available():
            logger.info("🧠 Analisando com AI Agent...")

            # Preparar dados do jogo
            match_data = {
                'match_id': match.id,
                'home_team': match.home_team.name if match.home_team else 'Unknown',
                'away_team': match.away_team.name if match.away_team else 'Unknown',
                'league': match.league,
                'match_date': match.match_date.isoformat() if match.match_date else None,
            }

            # Preparar prediction ML
            outcome = ml_prediction.get('match_outcome', {})
            ml_pred = {
                'predicted_outcome': outcome.get('predicted_outcome'),
                'confidence': outcome.get('confidence', 0.5),
                'probability_home': outcome.get('home_win_probability'),
                'probability_draw': outcome.get('draw_probability'),
                'probability_away': outcome.get('away_win_probability'),
                'markets': markets or ['1X2']
            }

            # Executar análise AI
            ai_analysis = self.ai_agent.analyze_prediction(
                match_data=match_data,
                ml_prediction=ml_pred,
                context_data=context_data,
                few_shot_examples=few_shot_examples
            )

        else:
            logger.warning("⚠️ AI Agent não disponível, usando apenas ML")
            ai_analysis = {
                'context_analysis': 'AI Agent não disponível',
                'key_factors': [],
                'adjusted_confidence': outcome.get('confidence', 0.5),
                'recommendation': 'MONITOR',
                'risk_level': 'MEDIUM',
                'explanation': 'Análise disponível apenas com ML. Ative Ollama para análise completa.',
                'ai_available': False
            }

        # 6. Montar resposta completa
        response = {
            'match': {
                'id': match.id,
                'home_team': match.home_team.name if match.home_team else 'Unknown',
                'away_team': match.away_team.name if match.away_team else 'Unknown',
                'league': match.league,
                'date': match.match_date.isoformat() if match.match_date else None,
            },
            'ml_analysis': {
                'probabilities': {
                    'home': outcome.get('home_win_probability'),
                    'draw': outcome.get('draw_probability'),
                    'away': outcome.get('away_win_probability'),
                },
                'confidence': outcome.get('confidence'),
                'suggested_outcome': outcome.get('predicted_outcome'),
                'odds': {
                    'home': outcome.get('home_win_odds'),
                    'draw': outcome.get('draw_odds'),
                    'away': outcome.get('away_win_odds'),
                }
            },
            'context': context_data,
            'ai_analysis': ai_analysis,
            'final_recommendation': {
                'outcome': ai_analysis.get('adjusted_confidence', 0) > 0.65,
                'confidence': ai_analysis.get('adjusted_confidence'),
                'recommendation': ai_analysis.get('recommendation'),
                'risk_level': ai_analysis.get('risk_level'),
                'should_bet': ai_analysis.get('recommendation') == 'BET',
            },
            'learning_insights': {
                'success_rate': self.memory.get_success_rate(market_type='1X2'),
                'similar_patterns': len(few_shot_examples),
            }
        }

        logger.info(f"✅ Análise completa - Recomendação: {ai_analysis.get('recommendation')}")

        return response

    async def create_assisted_prediction(
        self,
        match_id: int,
        markets: List[str],
        user_override: Dict = None
    ) -> Dict:
        """
        Cria prediction com assistência do AI

        Args:
            match_id: ID do jogo
            markets: Mercados escolhidos
            user_override: Valores que usuário quer sobrescrever

        Returns:
            Prediction criada com análise AI anexada
        """
        # Primeiro, fazer análise completa
        analysis = await self.analyze_user_selection(match_id, markets)

        if 'error' in analysis:
            return analysis

        # Criar prediction baseada na análise
        from app.models import Prediction

        # Usar valores do AI ou do usuário (se override)
        confidence = user_override.get('confidence') if user_override else \
                     analysis['ai_analysis'].get('adjusted_confidence')

        outcome = user_override.get('outcome') if user_override else \
                  analysis['ml_analysis']['suggested_outcome']

        # Criar prediction
        prediction = Prediction(
            match_id=match_id,
            prediction_type='SINGLE',  # Pode expandir para múltiplas
            market_type=markets[0] if markets else '1X2',
            predicted_outcome=outcome,
            confidence_score=confidence,
            probability_home=analysis['ml_analysis']['probabilities']['home'],
            probability_draw=analysis['ml_analysis']['probabilities']['draw'],
            probability_away=analysis['ml_analysis']['probabilities']['away'],
            model_version='ai_assisted_v1',
            analysis_summary=analysis['ai_analysis'].get('explanation'),
            key_factors=analysis['ai_analysis'].get('key_factors', [])
        )

        self.db.add(prediction)
        self.db.commit()

        logger.info(f"✅ Prediction assistida criada: ID {prediction.id}")

        return {
            'prediction_id': prediction.id,
            'analysis': analysis,
            'created': True
        }

    def compare_with_community(self, match_id: int) -> Dict:
        """
        Compara análise com predictions da comunidade

        Args:
            match_id: ID do jogo

        Returns:
            Comparação com consensus da comunidade
        """
        from app.models import Prediction

        # Buscar predictions da comunidade para este jogo
        community_predictions = self.db.query(Prediction).filter(
            Prediction.match_id == match_id
        ).all()

        if not community_predictions:
            return {
                'community_size': 0,
                'message': 'Nenhuma prediction da comunidade ainda'
            }

        # Calcular consensus
        outcomes = {}
        total_confidence = 0

        for pred in community_predictions:
            outcome = pred.predicted_outcome
            outcomes[outcome] = outcomes.get(outcome, 0) + 1
            total_confidence += pred.confidence_score

        consensus = max(outcomes.items(), key=lambda x: x[1])

        return {
            'community_size': len(community_predictions),
            'consensus_outcome': consensus[0],
            'consensus_percentage': (consensus[1] / len(community_predictions)) * 100,
            'average_confidence': total_confidence / len(community_predictions),
            'distribution': outcomes
        }
