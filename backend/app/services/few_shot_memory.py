"""
📚 FEW-SHOT MEMORY - Aprendizado com Exemplos
Sistema de memória para aprendizado rápido do AI Agent

Armazena:
- Predictions GREEN (acertou)
- Predictions RED (errou)
- Contexto de cada prediction
- Padrões identificados

Usa: SQLite local (grátis, rápido)
"""
import logging
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from app.models import Prediction, BetCombination, Match

logger = logging.getLogger(__name__)


class FewShotMemory:
    """
    Sistema de memória para few-shot learning
    Aprende com exemplos GREEN/RED
    """

    def __init__(self, db: Session):
        self.db = db

    def get_learning_examples(
        self,
        limit: int = 10,
        match_context: Dict = None
    ) -> List[Dict]:
        """
        Obtém exemplos de aprendizado (GREEN/RED)

        Args:
            limit: Número máximo de exemplos
            match_context: Contexto do jogo atual (para filtrar exemplos relevantes)

        Returns:
            Lista de exemplos formatados para o LLM
        """
        examples = []

        # Buscar predictions resolvidas (com resultado real)
        resolved_predictions = self.db.query(Prediction).filter(
            and_(
                Prediction.actual_outcome.isnot(None),
                Prediction.is_winner.isnot(None)
            )
        ).order_by(desc(Prediction.created_at)).limit(limit * 2).all()

        # Balancear GREEN e RED
        greens = [p for p in resolved_predictions if p.is_winner]
        reds = [p for p in resolved_predictions if not p.is_winner]

        # Pegar metade de cada
        half = limit // 2
        selected = greens[:half] + reds[:half]

        # Formatar para few-shot learning
        for pred in selected:
            example = self._format_example(pred)
            if example:
                examples.append(example)

        logger.info(f"📚 {len(examples)} exemplos de aprendizado carregados ({len([e for e in examples if e['label'] == 'GREEN'])} GREEN, {len([e for e in examples if e['label'] == 'RED'])} RED)")

        return examples

    def _format_example(self, prediction: Prediction) -> Optional[Dict]:
        """Formata prediction como exemplo de aprendizado"""
        try:
            match = prediction.match

            if not match or not match.home_team or not match.away_team:
                return None

            # Extrair contexto
            context_factors = []

            if prediction.analysis_summary:
                context_factors.append(prediction.analysis_summary)

            # Criar descrição do exemplo
            description = f"{match.home_team.name} vs {match.away_team.name}"
            description += f"\nPrediction: {prediction.predicted_outcome} ({prediction.market_type})"
            description += f"\nConfidence: {prediction.confidence_score:.1%}"

            if prediction.probability_home:
                description += f"\nProbs: H:{prediction.probability_home:.1%} D:{prediction.probability_draw:.1%} A:{prediction.probability_away:.1%}"

            if context_factors:
                description += f"\nContexto: {', '.join(context_factors[:3])}"

            return {
                'description': description,
                'predicted': prediction.predicted_outcome,
                'actual': prediction.actual_outcome,
                'outcome': f"{prediction.predicted_outcome} (real: {prediction.actual_outcome})",
                'label': 'GREEN' if prediction.is_winner else 'RED',
                'confidence': prediction.confidence_score,
                'market': prediction.market_type,
                'league': match.league,
                'date': match.match_date.isoformat() if match.match_date else None
            }

        except Exception as e:
            logger.error(f"Erro ao formatar exemplo: {e}")
            return None

    def add_feedback(
        self,
        prediction_id: int,
        actual_outcome: str,
        user_notes: str = None
    ) -> bool:
        """
        Adiciona feedback de resultado real

        Args:
            prediction_id: ID da prediction
            actual_outcome: Resultado real (1, X, 2, etc.)
            user_notes: Notas do usuário sobre o que aconteceu

        Returns:
            True se feedback foi adicionado
        """
        try:
            prediction = self.db.query(Prediction).filter(
                Prediction.id == prediction_id
            ).first()

            if not prediction:
                logger.error(f"Prediction {prediction_id} não encontrada")
                return False

            # Atualizar resultado
            prediction.actual_outcome = actual_outcome
            prediction.is_winner = (prediction.predicted_outcome == actual_outcome)

            # Adicionar notas do usuário
            if user_notes:
                if prediction.analysis_summary:
                    prediction.analysis_summary += f"\n\nFeedback usuário: {user_notes}"
                else:
                    prediction.analysis_summary = f"Feedback usuário: {user_notes}"

            self.db.commit()

            label = 'GREEN ✅' if prediction.is_winner else 'RED ❌'
            logger.info(f"{label} Feedback adicionado para prediction {prediction_id}")

            return True

        except Exception as e:
            logger.error(f"Erro ao adicionar feedback: {e}")
            self.db.rollback()
            return False

    def get_success_rate(
        self,
        market_type: str = None,
        last_n_days: int = 30
    ) -> Dict:
        """
        Calcula taxa de sucesso (GREEN/RED)

        Args:
            market_type: Filtrar por mercado específico
            last_n_days: Últimos N dias

        Returns:
            Estatísticas de sucesso
        """
        cutoff_date = datetime.now() - timedelta(days=last_n_days)

        query = self.db.query(Prediction).filter(
            and_(
                Prediction.actual_outcome.isnot(None),
                Prediction.created_at >= cutoff_date
            )
        )

        if market_type:
            query = query.filter(Prediction.market_type == market_type)

        predictions = query.all()

        if not predictions:
            return {
                'total': 0,
                'green': 0,
                'red': 0,
                'success_rate': 0.0
            }

        green = sum(1 for p in predictions if p.is_winner)
        red = len(predictions) - green

        return {
            'total': len(predictions),
            'green': green,
            'red': red,
            'success_rate': green / len(predictions) if predictions else 0.0,
            'market_type': market_type or 'ALL',
            'period_days': last_n_days
        }

    def get_best_patterns(self, limit: int = 5) -> List[Dict]:
        """
        Identifica padrões com maior taxa de sucesso

        Returns:
            Lista de padrões vencedores
        """
        # Buscar predictions GREEN
        green_predictions = self.db.query(Prediction).filter(
            and_(
                Prediction.is_winner == True,
                Prediction.confidence_score >= 0.70  # Alta confidence
            )
        ).limit(limit).all()

        patterns = []

        for pred in green_predictions:
            if pred.key_factors:
                patterns.append({
                    'factors': pred.key_factors,
                    'confidence': pred.confidence_score,
                    'market': pred.market_type,
                    'outcome': pred.predicted_outcome
                })

        return patterns

    def save_ai_analysis(
        self,
        prediction_id: int,
        ai_analysis: Dict
    ) -> bool:
        """
        Salva análise do AI Agent na prediction

        Args:
            prediction_id: ID da prediction
            ai_analysis: Análise do AI Agent

        Returns:
            True se salvou
        """
        try:
            prediction = self.db.query(Prediction).filter(
                Prediction.id == prediction_id
            ).first()

            if not prediction:
                return False

            # Atualizar com dados do AI
            prediction.confidence_score = ai_analysis.get('adjusted_confidence', prediction.confidence_score)
            prediction.analysis_summary = ai_analysis.get('explanation', prediction.analysis_summary)
            prediction.key_factors = ai_analysis.get('key_factors', [])

            # Adicionar metadados do AI
            if not hasattr(prediction, 'ai_metadata'):
                prediction.ai_metadata = {}

            prediction.ai_metadata = {
                'context_analysis': ai_analysis.get('context_analysis'),
                'adjustment_reasoning': ai_analysis.get('adjustment_reasoning'),
                'ml_confidence': ai_analysis.get('ml_confidence'),
                'confidence_delta': ai_analysis.get('confidence_delta'),
                'analyzed_at': datetime.now().isoformat()
            }

            self.db.commit()
            return True

        except Exception as e:
            logger.error(f"Erro ao salvar análise AI: {e}")
            self.db.rollback()
            return False


# Singleton
_few_shot_memory = None


def get_few_shot_memory(db: Session) -> FewShotMemory:
    """Obtém instância global"""
    global _few_shot_memory

    if _few_shot_memory is None or _few_shot_memory.db != db:
        _few_shot_memory = FewShotMemory(db)

    return _few_shot_memory
