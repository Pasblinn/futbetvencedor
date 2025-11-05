"""
🧠 AI AGENT BATCH SERVICE - Processamento em Lote
Analisa predictions pendentes usando AI Agent (Ollama local)

Características:
- Processa predictions com ai_analyzed = False
- Batch processing (100 por vez)
- Atualiza banco com análises contextuais
- Zero custo (100% local via Ollama)
- Integrado ao scheduler (roda a cada 2h)
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.prediction import Prediction
from app.models.match import Match
from app.services.ai_agent_service import AIAgentService

logger = logging.getLogger(__name__)


class AIAgentBatchService:
    """Serviço de processamento em lote do AI Agent"""

    def __init__(self, db: Session = None):
        """
        Inicializa batch service

        Args:
            db: Sessão do banco de dados (opcional, cria uma se não fornecida)
        """
        self.db = db or SessionLocal()
        self.ai_agent = AIAgentService(model="llama3.1:8b")
        self.stats = {
            'processed': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0
        }

    def process_unanalyzed_predictions(
        self,
        limit: int = 100,
        min_confidence: float = 0.0
    ) -> Dict:
        """
        Processa predictions pendentes de análise AI

        Args:
            limit: Máximo de predictions a processar por batch
            min_confidence: Confidence mínima para processar (filtro)

        Returns:
            Estatísticas do processamento
        """
        if not self.ai_agent.is_available():
            logger.error("❌ AI Agent não disponível (Ollama não conectado)")
            logger.error("🔧 Inicie Ollama: ollama serve")
            return {
                'success': False,
                'error': 'AI Agent não disponível',
                'stats': self.stats
            }

        logger.info(f"🧠 Iniciando batch analysis (limit={limit}, min_confidence={min_confidence})")

        try:
            # Buscar predictions não analisadas
            pending_predictions = self._get_pending_predictions(limit, min_confidence)

            if not pending_predictions:
                logger.info("ℹ️ Nenhuma prediction pendente para análise")
                return {
                    'success': True,
                    'message': 'Nenhuma prediction pendente',
                    'stats': self.stats
                }

            logger.info(f"📊 {len(pending_predictions)} predictions pendentes encontradas")

            # Processar cada prediction
            for prediction in pending_predictions:
                try:
                    self._analyze_single_prediction(prediction)
                    self.stats['success'] += 1

                except Exception as e:
                    logger.error(f"❌ Erro ao analisar prediction {prediction.id}: {e}")
                    self.stats['failed'] += 1

                self.stats['processed'] += 1

                # Commit a cada 10 predictions
                if self.stats['processed'] % 10 == 0:
                    self.db.commit()
                    logger.info(f"✅ {self.stats['processed']}/{len(pending_predictions)} processadas")

            # Commit final
            self.db.commit()

            logger.info(f"🎉 Batch analysis concluída: {self.stats}")

            return {
                'success': True,
                'stats': self.stats
            }

        except Exception as e:
            logger.error(f"❌ Erro crítico no batch processing: {e}")
            self.db.rollback()
            return {
                'success': False,
                'error': str(e),
                'stats': self.stats
            }

    def _get_pending_predictions(
        self,
        limit: int,
        min_confidence: float
    ) -> List[Prediction]:
        """
        Busca predictions pendentes de análise

        Args:
            limit: Máximo de predictions a retornar
            min_confidence: Confidence mínima

        Returns:
            Lista de predictions pendentes
        """
        query = self.db.query(Prediction).filter(
            Prediction.ai_analyzed == False,
            Prediction.confidence_score >= min_confidence
        )

        # Priorizar predictions mais recentes
        query = query.order_by(Prediction.created_at.desc())

        return query.limit(limit).all()

    def _analyze_single_prediction(self, prediction: Prediction):
        """
        Analisa uma única prediction com AI Agent

        Args:
            prediction: Objeto Prediction do banco
        """
        # Buscar dados do match
        match = self.db.query(Match).filter(
            Match.id == prediction.match_id
        ).first()

        if not match:
            logger.warning(f"⚠️ Match {prediction.match_id} não encontrado para prediction {prediction.id}")
            prediction.ai_analyzed = True
            prediction.ai_analyzed_at = datetime.utcnow()
            prediction.ai_recommendation = "SKIP"
            prediction.ai_analysis = "Match não encontrado"
            self.stats['skipped'] += 1
            return

        # Preparar dados para análise
        match_data = self._build_match_data(match, prediction)
        ml_prediction = self._build_ml_prediction(prediction)
        context_data = self._build_context_data(match, prediction)

        # Executar análise AI
        analysis = self.ai_agent.analyze_prediction(
            match_data=match_data,
            ml_prediction=ml_prediction,
            context_data=context_data
        )

        # Atualizar prediction com resultado da análise
        self._update_prediction_with_analysis(prediction, analysis)

        logger.debug(f"✅ Prediction {prediction.id} analisada: {analysis['recommendation']} (confidence: {analysis['adjusted_confidence']:.2%})")

    def _build_match_data(self, match: Match, prediction: Prediction) -> Dict:
        """Constrói dicionário de dados do match"""
        return {
            'home_team': match.home_team.name if match.home_team else 'Unknown',
            'away_team': match.away_team.name if match.away_team else 'Unknown',
            'league': match.league,
            'match_date': match.match_date.isoformat() if match.match_date else None
        }

    def _build_ml_prediction(self, prediction: Prediction) -> Dict:
        """Constrói dicionário de dados da prediction ML"""
        return {
            'predicted_outcome': prediction.predicted_outcome,
            'probability': prediction.predicted_probability,
            'confidence': prediction.confidence_score,
            'market': prediction.market_type,
            'markets': [prediction.market_type]
        }

    def _build_context_data(self, match: Match, prediction: Prediction) -> Dict:
        """
        Constrói dados de contexto para análise

        Usa key_factors da prediction se disponível
        """
        context = {
            'rivalry_level': 'baixa',
            'motivation_home': 'normal',
            'motivation_away': 'normal',
            'weather': 'bom',
            'key_injuries': [],
            'recent_news': []
        }

        # Se key_factors existe, usar dados de lá
        if prediction.key_factors:
            try:
                import json
                factors = json.loads(prediction.key_factors) if isinstance(prediction.key_factors, str) else prediction.key_factors

                # Extrair informações disponíveis
                if 'home_form' in factors:
                    context['home_form'] = factors['home_form']
                if 'away_form' in factors:
                    context['away_form'] = factors['away_form']
                if 'head_to_head' in factors:
                    context['head_to_head'] = factors['head_to_head']

            except Exception as e:
                logger.debug(f"Erro ao parsear key_factors: {e}")

        return context

    def _update_prediction_with_analysis(self, prediction: Prediction, analysis: Dict):
        """
        Atualiza prediction com resultado da análise AI

        Args:
            prediction: Objeto Prediction
            analysis: Resultado da análise AI
        """
        prediction.ai_analyzed = True
        prediction.ai_analyzed_at = datetime.utcnow()
        prediction.ai_recommendation = analysis.get('recommendation', 'MONITOR')
        prediction.ai_analysis = analysis.get('explanation', '')

        # Calcular ajuste de confidence
        ml_confidence = prediction.confidence_score or 0.5
        adjusted_confidence = analysis.get('adjusted_confidence', ml_confidence)
        prediction.ai_confidence_delta = adjusted_confidence - ml_confidence


# Função standalone para usar no scheduler
async def analyze_unanalyzed_predictions(limit: int = 100) -> Dict:
    """
    Função standalone para processar predictions pendentes
    Usada pelo scheduler

    Args:
        limit: Máximo de predictions a processar

    Returns:
        Estatísticas do processamento
    """
    logger.info("🧠 [SCHEDULER] Iniciando AI Agent batch processing")

    batch_service = AIAgentBatchService()
    result = batch_service.process_unanalyzed_predictions(limit=limit)

    if result.get('success'):
        stats = result.get('stats', {})
        logger.info(f"✅ [SCHEDULER] Batch concluído: {stats['success']}/{stats['processed']} analisadas")
    else:
        logger.error(f"❌ [SCHEDULER] Batch falhou: {result.get('error')}")

    return result
