"""
💎 VALUE BET DETECTOR
Identifica oportunidades de value betting analisando odds de mercado vs probabilidades calculadas
"""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from app.services.poisson_service import poisson_service, PoissonPrediction
from app.core.markets_config import MARKET_NAMES, MARKET_CATEGORIES

logger = logging.getLogger(__name__)


@dataclass
class ValueBet:
    """Representa uma aposta de valor identificada"""
    match_id: int
    match_name: str
    market_type: str
    market_name: str
    selection: str  # Ex: "Home Win", "Over 2.5", etc
    market_odds: float
    fair_odds: float
    our_probability: float  # Nossa probabilidade calculada (0-1, ex: 0.4639 = 46.39%)
    implied_probability: float  # Probabilidade implícita do bookmaker (0-1, ex: 0.3333 = 33.33%)
    edge: float  # Edge em % (ex: 12.5)
    kelly_stake: float  # Fração da banca recomendada (0-1, ex: 0.025 = 2.5%)
    value_rating: str  # LOW, MEDIUM, HIGH, PREMIUM
    confidence: float  # Confiança na predição (0-1, ex: 0.7 = 70%)
    bookmaker: str
    created_at: datetime

    def to_dict(self) -> dict:
        """Converte para dict para JSON"""
        return asdict(self)


class ValueBetDetector:
    """Detector de apostas de valor"""

    def __init__(self):
        # Thresholds de edge para classificação
        self.edge_thresholds = {
            'LOW': 5.0,
            'MEDIUM': 10.0,
            'HIGH': 20.0,
            'PREMIUM': 30.0
        }

        # Edge mínimo para considerar value bet
        self.min_edge = 5.0

        # Confiança mínima
        self.min_confidence = 0.6

    def classify_value(self, edge: float) -> str:
        """Classifica o nível de value baseado no edge"""
        if edge >= self.edge_thresholds['PREMIUM']:
            return 'PREMIUM'
        elif edge >= self.edge_thresholds['HIGH']:
            return 'HIGH'
        elif edge >= self.edge_thresholds['MEDIUM']:
            return 'MEDIUM'
        elif edge >= self.edge_thresholds['LOW']:
            return 'LOW'
        else:
            return 'NONE'

    def get_value_badge_color(self, rating: str) -> str:
        """Retorna a cor do badge para o frontend"""
        colors = {
            'PREMIUM': '#9333EA',  # Purple
            'HIGH': '#22C55E',     # Green
            'MEDIUM': '#F59E0B',   # Orange
            'LOW': '#EAB308',      # Yellow
            'NONE': '#6B7280'      # Gray
        }
        return colors.get(rating, colors['NONE'])

    def detect_value_bets(
        self,
        match_id: int,
        match_name: str,
        poisson_prediction: PoissonPrediction,
        market_odds: Dict[str, Dict],  # {market_type: {selection: odds, bookmaker: name}}
        confidence: float = 0.8
    ) -> List[ValueBet]:
        """
        Detecta value bets comparando odds de mercado com probabilidades Poisson

        Args:
            match_id: ID da partida
            match_name: Nome da partida (ex: "San Antonio vs LDU")
            poisson_prediction: Predição Poisson
            market_odds: Odds do mercado
            confidence: Confiança na predição (0-1)

        Returns:
            Lista de ValueBets identificados
        """
        value_bets = []

        # Mapear probabilidades Poisson para formato de mercados
        prob_map = self._map_probabilities_to_markets(poisson_prediction.probabilities)

        for market_type, selections in market_odds.items():
            market_name = MARKET_NAMES.get(market_type, market_type)

            for selection, market_data in selections.items():
                # Odds do mercado
                odds = market_data.get('odds', 0)
                bookmaker = market_data.get('bookmaker', 'Unknown')

                # Nossa probabilidade
                prob_key = self._get_probability_key(market_type, selection)

                if prob_key in prob_map:
                    our_prob = prob_map[prob_key]

                    # Odds justa baseada na nossa probabilidade
                    fair_odd = 1 / our_prob if our_prob > 0 else 999.99

                    # Probabilidade implícita do bookmaker
                    implied_prob = 1 / odds if odds > 0 else 0

                    # Edge = quanto % a mais o bookmaker está pagando
                    edge = ((odds / fair_odd) - 1) * 100

                    # Filtros
                    if edge < self.min_edge:
                        continue

                    if confidence < self.min_confidence:
                        continue

                    # Kelly stake
                    kelly = poisson_service._calculate_kelly(our_prob, odds, fraction=0.25)

                    # Classificar value
                    value_rating = self.classify_value(edge)

                    value_bet = ValueBet(
                        match_id=match_id,
                        match_name=match_name,
                        market_type=market_type,
                        market_name=market_name,
                        selection=selection,
                        market_odds=round(odds, 2),
                        fair_odds=round(fair_odd, 2),
                        our_probability=round(our_prob, 4),  # 🔧 CORRIGIDO: mantém em 0-1 (ex: 0.4639)
                        implied_probability=round(implied_prob, 4),  # 🔧 CORRIGIDO: mantém em 0-1
                        edge=round(edge, 2),
                        kelly_stake=round(kelly, 4),  # 🔧 CORRIGIDO: mantém em 0-1 (ex: 0.025 = 2.5%)
                        value_rating=value_rating,
                        confidence=round(confidence, 2),
                        bookmaker=bookmaker,
                        created_at=datetime.now()
                    )

                    value_bets.append(value_bet)

        # Ordenar por edge (maior primeiro)
        value_bets.sort(key=lambda x: x.edge, reverse=True)

        logger.info(f"Detectados {len(value_bets)} value bets para {match_name}")

        return value_bets

    def _map_probabilities_to_markets(self, probabilities: Dict[str, float]) -> Dict[str, float]:
        """
        Mapeia probabilidades Poisson para keys de mercados

        Poisson retorna: {'HOME_WIN': 0.48, 'DRAW': 0.28, ...}
        Precisamos mapear para: {'1X2_HOME': 0.48, '1X2_DRAW': 0.28, ...}
        """
        mapping = {}

        # 1X2
        mapping['1X2_HOME'] = probabilities.get('HOME_WIN', 0)
        mapping['1X2_DRAW'] = probabilities.get('DRAW', 0)
        mapping['1X2_AWAY'] = probabilities.get('AWAY_WIN', 0)

        # Double Chance
        mapping['DOUBLE_CHANCE_1X'] = probabilities.get('1X', 0)
        mapping['DOUBLE_CHANCE_12'] = probabilities.get('12', 0)
        mapping['DOUBLE_CHANCE_X2'] = probabilities.get('X2', 0)

        # BTTS
        mapping['BTTS_YES'] = probabilities.get('BTTS_YES', 0)
        mapping['BTTS_NO'] = probabilities.get('BTTS_NO', 0)

        # Over/Under
        for line in [0.5, 1.5, 2.5, 3.5, 4.5, 5.5]:
            mapping[f'OVER_UNDER_{line}_OVER'] = probabilities.get(f'OVER_{line}', 0)
            mapping[f'OVER_UNDER_{line}_UNDER'] = probabilities.get(f'UNDER_{line}', 0)

        # Gols Exatos
        mapping['EXACT_GOALS_0'] = probabilities.get('EXACTLY_0_GOALS', 0)
        mapping['EXACT_GOALS_1'] = probabilities.get('EXACTLY_1_GOAL', 0)
        mapping['EXACT_GOALS_2'] = probabilities.get('EXACTLY_2_GOALS', 0)
        mapping['EXACT_GOALS_3'] = probabilities.get('EXACTLY_3_GOALS', 0)
        mapping['EXACT_GOALS_4+'] = probabilities.get('4_OR_MORE_GOALS', 0)

        # Par/Ímpar
        mapping['ODD_EVEN_ODD'] = probabilities.get('ODD_GOALS', 0)
        mapping['ODD_EVEN_EVEN'] = probabilities.get('EVEN_GOALS', 0)

        # Primeiro Gol
        mapping['FIRST_GOAL_HOME'] = probabilities.get('FIRST_GOAL_HOME', 0)
        mapping['FIRST_GOAL_AWAY'] = probabilities.get('FIRST_GOAL_AWAY', 0)
        mapping['FIRST_GOAL_NONE'] = probabilities.get('NO_GOAL', 0)

        # Clean Sheet
        mapping['CLEAN_SHEET_HOME'] = probabilities.get('HOME_CLEAN_SHEET', 0)
        mapping['CLEAN_SHEET_AWAY'] = probabilities.get('AWAY_CLEAN_SHEET', 0)

        # Placares Exatos
        common_scores = [
            (0, 0), (1, 0), (0, 1), (1, 1), (2, 0), (0, 2),
            (2, 1), (1, 2), (2, 2), (3, 0), (0, 3), (3, 1), (1, 3)
        ]
        for home, away in common_scores:
            mapping[f'CORRECT_SCORE_{home}_{away}'] = probabilities.get(f'SCORE_{home}_{away}', 0)

        return mapping

    def _get_probability_key(self, market_type: str, selection: str) -> str:
        """
        Gera a key de probabilidade baseada no mercado e seleção

        Ex: market_type='1X2', selection='Home' -> '1X2_HOME'
        """
        selection_upper = selection.upper().replace(' ', '_')
        return f"{market_type}_{selection_upper}"

    def get_top_value_bets(
        self,
        value_bets: List[ValueBet],
        limit: int = 5,
        min_rating: str = 'MEDIUM'
    ) -> List[ValueBet]:
        """
        Retorna os top N value bets filtrados por rating mínimo

        Args:
            value_bets: Lista de value bets
            limit: Número máximo de apostas a retornar
            min_rating: Rating mínimo (LOW, MEDIUM, HIGH, PREMIUM)

        Returns:
            Top value bets
        """
        rating_order = ['LOW', 'MEDIUM', 'HIGH', 'PREMIUM']
        min_idx = rating_order.index(min_rating)

        filtered = [
            vb for vb in value_bets
            if rating_order.index(vb.value_rating) >= min_idx
        ]

        return filtered[:limit]

    def calculate_expected_value(self, value_bet: ValueBet, stake: float = 100) -> Dict:
        """
        Calcula o valor esperado (EV) de uma aposta

        EV = (Probabilidade de Ganhar * Lucro) - (Probabilidade de Perder * Stake)

        Args:
            value_bet: Value bet
            stake: Valor apostado

        Returns:
            Dict com cálculos de EV
        """
        prob_win = value_bet.our_probability  # 🔧 CORRIGIDO: já vem em 0-1
        prob_lose = 1 - prob_win

        profit_if_win = stake * (value_bet.market_odds - 1)
        loss_if_lose = stake

        ev = (prob_win * profit_if_win) - (prob_lose * loss_if_lose)
        ev_percentage = (ev / stake) * 100

        return {
            'stake': stake,
            'expected_value': round(ev, 2),
            'ev_percentage': round(ev_percentage, 2),
            'profit_if_win': round(profit_if_win, 2),
            'loss_if_lose': round(loss_if_lose, 2),
            'roi': round(ev_percentage, 2)
        }


# Instância global
value_bet_detector = ValueBetDetector()
