"""
📊 SERVIÇO DE DISTRIBUIÇÃO DE POISSON PARA ANÁLISE DE ODDS
Calcula probabilidades reais usando Poisson e identifica value bets

A distribuição de Poisson é ideal para modelar eventos raros como gols em futebol.
Fórmula: P(X = k) = (λ^k * e^(-λ)) / k!

Onde:
- λ (lambda) = média de gols esperados
- k = número de gols
- e = 2.71828... (constante de Euler)
"""

import numpy as np
import math
from scipy import stats
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class PoissonPrediction:
    """Resultado de predição usando Poisson"""
    home_lambda: float  # Média de gols esperados casa
    away_lambda: float  # Média de gols esperados visitante
    probabilities: Dict[str, float]  # Probabilidades por mercado
    fair_odds: Dict[str, float]  # Odds justas calculadas
    value_bets: List[Dict]  # Value bets identificados


class PoissonService:
    """Serviço de análise de Poisson para futebol"""

    def __init__(self):
        self.max_goals = 10  # Máximo de gols para calcular
        self.value_threshold = 0.05  # 5% de edge mínimo para value bet

    def poisson_probability(self, lambda_param: float, k: int) -> float:
        """
        Calcula probabilidade de Poisson para k eventos
        P(X = k) = (λ^k * e^(-λ)) / k!
        """
        try:
            return (lambda_param ** k * math.exp(-lambda_param)) / math.factorial(k)
        except (ValueError, OverflowError):
            return 0.0

    def calculate_lambdas(
        self,
        home_attack: float,
        home_defense: float,
        away_attack: float,
        away_defense: float,
        league_avg_goals: float = 2.7
    ) -> Tuple[float, float]:
        """
        Calcula lambda (média de gols esperados) para cada time

        Args:
            home_attack: Força de ataque do time casa (gols marcados/jogo)
            home_defense: Força de defesa do time casa (gols sofridos/jogo)
            away_attack: Força de ataque do visitante
            away_defense: Força de defesa do visitante
            league_avg_goals: Média de gols por jogo na liga

        Returns:
            (lambda_home, lambda_away)
        """
        # Fator casa: times geralmente marcam 1.3x mais em casa
        home_advantage = 1.3

        # Lambda casa = ataque casa * defesa visitante * vantagem casa / média liga
        lambda_home = (home_attack * away_defense * home_advantage) / league_avg_goals

        # Lambda visitante = ataque visitante * defesa casa / média liga
        lambda_away = (away_attack * home_defense) / league_avg_goals

        return lambda_home, lambda_away

    def calculate_match_probabilities(
        self,
        lambda_home: float,
        lambda_away: float
    ) -> Dict[str, float]:
        """
        Calcula probabilidades de todos os resultados possíveis

        Returns:
            Dict com probabilidades para cada resultado
        """
        probabilities = {}

        # Matriz de probabilidades para cada placar
        score_matrix = np.zeros((self.max_goals + 1, self.max_goals + 1))

        for home_goals in range(self.max_goals + 1):
            for away_goals in range(self.max_goals + 1):
                prob_home = self.poisson_probability(lambda_home, home_goals)
                prob_away = self.poisson_probability(lambda_away, away_goals)
                score_matrix[home_goals, away_goals] = prob_home * prob_away

        # ========== MERCADOS PRINCIPAIS ==========

        # 1X2 - Resultado Final
        probabilities['HOME_WIN'] = np.sum(np.tril(score_matrix, -1))  # Casa ganha
        probabilities['DRAW'] = np.trace(score_matrix)  # Empate
        probabilities['AWAY_WIN'] = np.sum(np.triu(score_matrix, 1))  # Visitante ganha

        # Dupla Hipótese
        probabilities['1X'] = probabilities['HOME_WIN'] + probabilities['DRAW']
        probabilities['12'] = probabilities['HOME_WIN'] + probabilities['AWAY_WIN']
        probabilities['X2'] = probabilities['DRAW'] + probabilities['AWAY_WIN']

        # BTTS - Ambas Marcam
        probabilities['BTTS_YES'] = 1 - score_matrix[0, :].sum() - score_matrix[:, 0].sum() + score_matrix[0, 0]
        probabilities['BTTS_NO'] = 1 - probabilities['BTTS_YES']

        # Over/Under Gols
        for line in [0.5, 1.5, 2.5, 3.5, 4.5, 5.5]:
            over_prob = 0
            for i in range(self.max_goals + 1):
                for j in range(self.max_goals + 1):
                    if i + j > line:
                        over_prob += score_matrix[i, j]

            probabilities[f'OVER_{line}'] = over_prob
            probabilities[f'UNDER_{line}'] = 1 - over_prob

        # ========== GOLS EXATOS ==========
        probabilities['EXACTLY_0_GOALS'] = score_matrix[0, 0]
        probabilities['EXACTLY_1_GOAL'] = score_matrix[0, 1] + score_matrix[1, 0]
        probabilities['EXACTLY_2_GOALS'] = score_matrix[0, 2] + score_matrix[1, 1] + score_matrix[2, 0]
        probabilities['EXACTLY_3_GOALS'] = (
            score_matrix[0, 3] + score_matrix[1, 2] +
            score_matrix[2, 1] + score_matrix[3, 0]
        )
        probabilities['4_OR_MORE_GOALS'] = 1 - sum([
            probabilities['EXACTLY_0_GOALS'],
            probabilities['EXACTLY_1_GOAL'],
            probabilities['EXACTLY_2_GOALS'],
            probabilities['EXACTLY_3_GOALS']
        ])

        # ========== PAR/ÍMPAR ==========
        odd_prob = sum(
            score_matrix[i, j]
            for i in range(self.max_goals + 1)
            for j in range(self.max_goals + 1)
            if (i + j) % 2 == 1
        )
        probabilities['ODD_GOALS'] = odd_prob
        probabilities['EVEN_GOALS'] = 1 - odd_prob

        # ========== PRIMEIRO GOL ==========
        # Baseado em estatísticas: ~10% sem gols, 45% casa, 45% visitante
        prob_no_goals = score_matrix[0, 0]
        probabilities['NO_GOAL'] = prob_no_goals
        probabilities['FIRST_GOAL_HOME'] = (1 - prob_no_goals) * (lambda_home / (lambda_home + lambda_away))
        probabilities['FIRST_GOAL_AWAY'] = (1 - prob_no_goals) * (lambda_away / (lambda_home + lambda_away))

        # ========== CLEAN SHEET ==========
        probabilities['HOME_CLEAN_SHEET'] = score_matrix[:, 0].sum()
        probabilities['AWAY_CLEAN_SHEET'] = score_matrix[0, :].sum()

        # ========== PLACARES EXATOS MAIS COMUNS ==========
        common_scores = [
            (0, 0), (1, 0), (0, 1), (1, 1), (2, 0), (0, 2),
            (2, 1), (1, 2), (2, 2), (3, 0), (0, 3), (3, 1), (1, 3)
        ]
        for home_score, away_score in common_scores:
            probabilities[f'SCORE_{home_score}_{away_score}'] = score_matrix[home_score, away_score]

        return probabilities

    def calculate_fair_odds(self, probabilities: Dict[str, float]) -> Dict[str, float]:
        """
        Converte probabilidades em odds justas (fair odds)
        Fair Odds = 1 / Probabilidade
        """
        fair_odds = {}
        for market, prob in probabilities.items():
            if prob > 0:
                fair_odds[market] = 1 / prob
            else:
                fair_odds[market] = 999.99  # Probabilidade zero

        return fair_odds

    def identify_value_bets(
        self,
        fair_odds: Dict[str, float],
        market_odds: Dict[str, float],
        min_edge: float = None
    ) -> List[Dict]:
        """
        Identifica value bets comparando odds do mercado com odds justas

        Value bet = quando odds do mercado > odds justas (bookmaker subavaliou)
        Edge = (market_odds / fair_odds) - 1

        Args:
            fair_odds: Odds calculadas por Poisson
            market_odds: Odds do bookmaker
            min_edge: Edge mínimo para considerar value (default: 5%)

        Returns:
            Lista de value bets com edge > threshold
        """
        if min_edge is None:
            min_edge = self.value_threshold

        value_bets = []

        for market, fair_odd in fair_odds.items():
            if market in market_odds:
                market_odd = market_odds[market]

                # Edge = quanto % a mais o bookmaker está pagando
                edge = (market_odd / fair_odd) - 1

                if edge > min_edge:
                    # Probabilidade implícita do bookmaker
                    implied_prob = 1 / market_odd if market_odd > 0 else 0

                    # Nossa probabilidade (Poisson)
                    our_prob = 1 / fair_odd if fair_odd > 0 else 0

                    value_bets.append({
                        'market': market,
                        'market_odds': round(market_odd, 2),
                        'fair_odds': round(fair_odd, 2),
                        'edge': round(edge * 100, 2),  # Em %
                        'implied_prob': round(implied_prob * 100, 2),
                        'our_prob': round(our_prob * 100, 2),
                        'kelly_stake': self._calculate_kelly(our_prob, market_odd)
                    })

        # Ordenar por edge (maior primeiro)
        value_bets.sort(key=lambda x: x['edge'], reverse=True)

        return value_bets

    def _calculate_kelly(self, probability: float, odds: float, fraction: float = 0.25) -> float:
        """
        Calcula Kelly Criterion para sizing ideal da aposta

        Kelly = (p * (odds - 1) - (1 - p)) / (odds - 1)

        Usamos fractional Kelly (25%) para ser mais conservador

        Args:
            probability: Nossa probabilidade estimada
            odds: Odds do mercado (decimal)
            fraction: Fração do Kelly a usar (0.25 = 25%)

        Returns:
            % da banca a apostar (0-1)
        """
        if odds <= 1 or probability <= 0:
            return 0.0

        # Kelly completo
        kelly = (probability * (odds - 1) - (1 - probability)) / (odds - 1)

        # Fractional Kelly (mais seguro)
        kelly_fraction = max(0, kelly * fraction)

        return round(min(kelly_fraction, 0.05), 4)  # Máximo 5% da banca

    def analyze_match(
        self,
        home_goals_avg: float,
        away_goals_avg: float,
        home_conceded_avg: float,
        away_conceded_avg: float,
        market_odds: Dict[str, float] = None,
        league_avg: float = 2.7
    ) -> PoissonPrediction:
        """
        Análise completa de uma partida usando Poisson

        Args:
            home_goals_avg: Média de gols marcados casa
            away_goals_avg: Média de gols marcados visitante
            home_conceded_avg: Média de gols sofridos casa
            away_conceded_avg: Média de gols sofridos visitante
            market_odds: Odds do mercado (opcional)
            league_avg: Média de gols da liga

        Returns:
            PoissonPrediction com probabilidades, odds justas e value bets
        """
        # Calcular lambdas
        lambda_home, lambda_away = self.calculate_lambdas(
            home_attack=home_goals_avg,
            home_defense=home_conceded_avg,
            away_attack=away_goals_avg,
            away_defense=away_conceded_avg,
            league_avg_goals=league_avg
        )

        # Log removido para performance (era chamado 1000s de vezes)

        # Calcular probabilidades
        probabilities = self.calculate_match_probabilities(lambda_home, lambda_away)

        # Calcular odds justas
        fair_odds = self.calculate_fair_odds(probabilities)

        # Identificar value bets (se odds de mercado fornecidas)
        value_bets = []
        if market_odds:
            value_bets = self.identify_value_bets(fair_odds, market_odds)

        return PoissonPrediction(
            home_lambda=lambda_home,
            away_lambda=lambda_away,
            probabilities=probabilities,
            fair_odds=fair_odds,
            value_bets=value_bets
        )

    def get_recommended_bets(
        self,
        prediction: PoissonPrediction,
        min_edge: float = 0.05,
        max_bets: int = 3
    ) -> List[Dict]:
        """
        Retorna as melhores apostas recomendadas

        Args:
            prediction: Predição Poisson
            min_edge: Edge mínimo (default 5%)
            max_bets: Máximo de apostas a retornar

        Returns:
            Lista das melhores value bets
        """
        return [
            bet for bet in prediction.value_bets
            if bet['edge'] >= min_edge * 100
        ][:max_bets]


# Instância global do serviço
poisson_service = PoissonService()
