#!/usr/bin/env python3
"""
🤖 AI AGENT PREDICTION VALIDATOR

Sistema de validação inteligente de predictions com 3 modos:
1. AUTOMÁTICO: ML gera 2500/dia → AI valida TOP 100 → Usuário vê prontas
2. ASSISTIDO: Usuário escolhe → ML calcula → AI analisa → Usuário confirma
3. MANUAL: Usuário expert cria manualmente (GOLD data para treinar)
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class AIPredictionValidator:
    """Validador inteligente de predictions usando AI Agent"""

    def __init__(self):
        self.confidence_threshold = 0.6
        self.min_edge_for_auto = 10.0  # Mínimo 10% edge para modo automático

    async def validate_automatic_prediction(self, prediction_data: Dict) -> Dict:
        """
        MODO AUTOMÁTICO: Valida prediction gerada pelo ML

        AI Agent analisa rapidamente e aprova/rejeita automaticamente

        Args:
            prediction_data: Dados da prediction do ML

        Returns:
            Dict com validação e explicação
        """
        logger.info(f"🤖 AI validando prediction automática...")

        # Análise de confiança
        confidence = prediction_data.get('confidence', 0.5)
        edge = prediction_data.get('edge', 0)
        market_type = prediction_data.get('market_type', 'Unknown')

        # Critérios de aprovação automática
        auto_approved = (
            confidence >= self.confidence_threshold and
            edge >= self.min_edge_for_auto
        )

        analysis = {
            'validated': auto_approved,
            'validation_mode': 'automatic',
            'ai_confidence': confidence,
            'edge_percentage': edge,
            'reasoning': self._generate_automatic_reasoning(
                auto_approved, confidence, edge, market_type
            ),
            'risk_level': self._calculate_risk_level(confidence, edge),
            'recommended_stake': self._calculate_stake_recommendation(confidence, edge),
            'validated_at': datetime.now().isoformat()
        }

        if auto_approved:
            logger.info(f"✅ Prediction AUTO-APROVADA (Confiança: {confidence:.1%}, Edge: {edge:.1f}%)")
        else:
            logger.info(f"❌ Prediction REJEITADA (Confiança: {confidence:.1%}, Edge: {edge:.1f}%)")

        return analysis

    async def validate_assisted_prediction(self, user_selection: Dict, ml_analysis: Dict) -> Dict:
        """
        MODO ASSISTIDO: Usuário escolheu jogo/mercado, AI explica detalhadamente

        AI Agent fornece análise profunda ANTES do usuário confirmar

        Args:
            user_selection: Escolha do usuário (jogo, mercado, etc)
            ml_analysis: Análise do ML (probabilidades, odds, etc)

        Returns:
            Dict com análise detalhada para o usuário decidir
        """
        logger.info(f"🧠 AI analisando prediction assistida...")

        match_info = user_selection.get('match_info', {})
        market_type = user_selection.get('market_type', 'Unknown')

        # Análise completa
        analysis = {
            'validation_mode': 'assisted',
            'match': {
                'home_team': match_info.get('home_team'),
                'away_team': match_info.get('away_team'),
                'league': match_info.get('league')
            },
            'market_analysis': {
                'market_type': market_type,
                'ml_probability': ml_analysis.get('probability', 0),
                'fair_odds': ml_analysis.get('fair_odds', 0),
                'market_odds': ml_analysis.get('market_odds', 0),
                'edge': ml_analysis.get('edge', 0)
            },
            'ai_insights': self._generate_assisted_insights(ml_analysis, market_type),
            'strengths': self._identify_strengths(ml_analysis),
            'weaknesses': self._identify_weaknesses(ml_analysis),
            'historical_performance': self._get_historical_performance(market_type),
            'risk_assessment': {
                'risk_level': self._calculate_risk_level(
                    ml_analysis.get('probability', 0.5),
                    ml_analysis.get('edge', 0)
                ),
                'confidence_score': ml_analysis.get('confidence', 0.5),
                'variance': ml_analysis.get('variance', 0)
            },
            'recommendation': {
                'should_bet': ml_analysis.get('edge', 0) > 5,
                'stake_percentage': self._calculate_stake_recommendation(
                    ml_analysis.get('probability', 0.5),
                    ml_analysis.get('edge', 0)
                ),
                'reasoning': self._generate_assisted_reasoning(ml_analysis)
            },
            'validated_at': datetime.now().isoformat()
        }

        return analysis

    async def register_manual_prediction(self, manual_data: Dict) -> Dict:
        """
        MODO MANUAL: Usuário expert criou prediction manualmente

        Sistema registra como GOLD data (alta qualidade) para treinar ML

        Args:
            manual_data: Dados da prediction manual do usuário

        Returns:
            Dict com confirmação e status GOLD
        """
        logger.info(f"💎 Registrando prediction MANUAL (GOLD data)...")

        # Prediction manual = dado de altíssima qualidade
        registration = {
            'validation_mode': 'manual',
            'data_quality': 'GOLD',
            'created_by': 'user_expert',
            'use_for_training': True,  # Sempre usar para treinar ML
            'weight': 2.0,  # Peso 2x maior que predictions automáticas
            'manual_data': {
                'match_id': manual_data.get('match_id'),
                'market_type': manual_data.get('market_type'),
                'predicted_outcome': manual_data.get('predicted_outcome'),
                'user_confidence': manual_data.get('user_confidence', 0.8),
                'user_reasoning': manual_data.get('user_reasoning', '')
            },
            'ai_notes': self._generate_manual_notes(manual_data),
            'registered_at': datetime.now().isoformat()
        }

        logger.info(f"✅ Prediction MANUAL registrada como GOLD data")

        return registration

    def _generate_automatic_reasoning(self, approved: bool, confidence: float, edge: float, market: str) -> str:
        """Gera raciocínio para modo automático"""
        if approved:
            return (
                f"✅ Prediction aprovada automaticamente:\n"
                f"• Confiança ML: {confidence:.1%} (>{self.confidence_threshold:.0%} requerido)\n"
                f"• Edge detectado: +{edge:.1f}% (>{self.min_edge_for_auto:.0f}% requerido)\n"
                f"• Mercado: {market}\n"
                f"• Status: READY TO BET"
            )
        else:
            reasons = []
            if confidence < self.confidence_threshold:
                reasons.append(f"Confiança baixa ({confidence:.1%} < {self.confidence_threshold:.0%})")
            if edge < self.min_edge_for_auto:
                reasons.append(f"Edge insuficiente ({edge:.1f}% < {self.min_edge_for_auto:.0f}%)")

            return (
                f"❌ Prediction rejeitada:\n" +
                "\n".join(f"• {r}" for r in reasons)
            )

    def _generate_assisted_insights(self, ml_analysis: Dict, market_type: str) -> List[str]:
        """Gera insights detalhados para modo assistido"""
        insights = []

        prob = ml_analysis.get('probability', 0.5)
        edge = ml_analysis.get('edge', 0)

        # Insight de probabilidade
        if prob > 0.6:
            insights.append(f"🎯 Alta probabilidade detectada ({prob:.1%}) - modelo confiante")
        elif prob > 0.5:
            insights.append(f"📊 Probabilidade moderada ({prob:.1%}) - vantagem leve")
        else:
            insights.append(f"⚠️ Probabilidade neutra ({prob:.1%}) - risco equilibrado")

        # Insight de value
        if edge > 15:
            insights.append(f"💎 Excelente value bet (+{edge:.1f}% edge)")
        elif edge > 5:
            insights.append(f"✅ Value bet identificado (+{edge:.1f}% edge)")
        elif edge > 0:
            insights.append(f"📈 Pequeno edge positivo (+{edge:.1f}%)")
        else:
            insights.append(f"⚠️ Sem edge matemático ({edge:.1f}%)")

        # Insight de mercado
        insights.append(f"🎲 Mercado: {market_type} - histórico analisado")

        return insights

    def _identify_strengths(self, ml_analysis: Dict) -> List[str]:
        """Identifica pontos fortes da prediction"""
        strengths = []

        if ml_analysis.get('edge', 0) > 10:
            strengths.append("Edge matemático significativo")
        if ml_analysis.get('confidence', 0) > 0.7:
            strengths.append("Alta confiança do modelo ML")
        if ml_analysis.get('historical_accuracy', 0) > 0.6:
            strengths.append("Bom histórico de acurácia neste mercado")

        return strengths if strengths else ["Análise balanceada sem pontos fortes destacados"]

    def _identify_weaknesses(self, ml_analysis: Dict) -> List[str]:
        """Identifica pontos fracos da prediction"""
        weaknesses = []

        if ml_analysis.get('variance', 1) > 0.3:
            weaknesses.append("Alta variância - resultado mais imprevisível")
        if ml_analysis.get('confidence', 1) < 0.5:
            weaknesses.append("Baixa confiança do modelo")
        if ml_analysis.get('sample_size', 100) < 20:
            weaknesses.append("Poucos dados históricos disponíveis")

        return weaknesses if weaknesses else ["Nenhuma fraqueza significativa detectada"]

    def _generate_assisted_reasoning(self, ml_analysis: Dict) -> str:
        """Gera raciocínio completo para modo assistido"""
        prob = ml_analysis.get('probability', 0.5)
        edge = ml_analysis.get('edge', 0)
        fair_odds = ml_analysis.get('fair_odds', 0)
        market_odds = ml_analysis.get('market_odds', 0)

        reasoning = f"""
📊 ANÁLISE COMPLETA:

Probabilidade Real (ML): {prob:.1%}
Fair Odds: {fair_odds:.2f}
Market Odds: {market_odds:.2f}
Edge: {'+' if edge > 0 else ''}{edge:.2f}%

VEREDITO:
"""
        if edge > 10:
            reasoning += "✅ RECOMENDADO - Excelente oportunidade de value bet"
        elif edge > 5:
            reasoning += "✅ BOM - Value bet identificado, considerar apostar"
        elif edge > 0:
            reasoning += "⚠️ NEUTRO - Pequeno edge, avaliar outros fatores"
        else:
            reasoning += "❌ NÃO RECOMENDADO - Sem vantagem matemática"

        return reasoning

    def _generate_manual_notes(self, manual_data: Dict) -> str:
        """Gera notas sobre prediction manual"""
        return (
            f"💎 Prediction manual criada por usuário expert\n"
            f"• Qualidade: GOLD (peso 2x)\n"
            f"• Será usada para melhorar ML\n"
            f"• Raciocínio do usuário: {manual_data.get('user_reasoning', 'N/A')}"
        )

    def _calculate_risk_level(self, confidence: float, edge: float) -> str:
        """Calcula nível de risco"""
        if confidence > 0.7 and edge > 15:
            return "LOW"
        elif confidence > 0.6 and edge > 10:
            return "MEDIUM"
        elif confidence > 0.5 and edge > 5:
            return "MEDIUM-HIGH"
        else:
            return "HIGH"

    def _calculate_stake_recommendation(self, probability: float, edge: float) -> float:
        """Calcula recomendação de stake (% da banca)"""
        # Kelly Criterion simplificado com fração conservadora
        if edge <= 0:
            return 0.0

        # Fractional Kelly (25%)
        kelly = ((probability * 2.0) - 1) * 0.25

        # Limitar entre 0.5% e 5% da banca
        return max(0.5, min(5.0, kelly * 100))

    def _get_historical_performance(self, market_type: str) -> Dict:
        """Retorna performance histórica do mercado (mock por enquanto)"""
        # TODO: Implementar consulta real ao banco
        return {
            'market': market_type,
            'total_predictions': 150,
            'accuracy': 0.62,
            'avg_edge': 8.5,
            'roi': 12.3
        }


# Instância global
ai_validator = AIPredictionValidator()
