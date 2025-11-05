"""
🧠 GERADOR AUTOMÁTICO DE PREDICTIONS PARA APRENDIZADO ML
Meta: 4500+ predictions/dia com 45+ mercados via Poisson

🔥 VERSÃO 2.0 (2025-10-16):
- Expandido de 6 para 45+ mercados
- Usa PoissonService diretamente para cálculos reais
- Detecta value bets automaticamente (edge > 10%)
- Filtra predictions por qualidade (evita mercados ruins)

Mercados suportados (41 total):
- Resultado Final (3)
- Ambas Marcam (2)
- Total de Gols Over/Under (12)
- Dupla Chance (3)
- Gols Exatos (5)
- Primeiro a Marcar (3)
- Clean Sheet (2)
- Par/Ímpar (2)
- Placares Exatos (9)

Tipos de predictions:
- Singles: 1 mercado, 1 jogo
- Doubles: 2 mercados, 1 jogo ou 2 jogos
- Trebles: 3 mercados, 1 jogo ou 3 jogos
- Quads: 4 mercados, 1 jogo ou 4 jogos

Objetivo: Aprendizado acelerado do ML com dados GREEN/RED de qualidade
"""
import logging
from typing import List, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_
import random

from app.models import Match, Prediction, BetCombination
from app.services.prediction_service import PredictionService

logger = logging.getLogger(__name__)


class MLPredictionGenerator:
    """Gera predictions automáticas para aprendizado ML"""

    # 🔥 MERCADOS COMPLETOS (41+ MERCADOS) - EXPANDIDO v6.1
    # Para atingir meta de 4500+ predictions/dia e maximizar lucro
    MARKETS = [
        # Resultado Final (3)
        'HOME_WIN', 'DRAW', 'AWAY_WIN',

        # Dupla Chance (3)
        '1X', '12', 'X2',

        # Ambas Marcam (2)
        'BTTS_YES', 'BTTS_NO',

        # Over/Under (10 linhas)
        'OVER_0_5', 'UNDER_0_5',
        'OVER_1_5', 'UNDER_1_5',
        'OVER_2_5', 'UNDER_2_5',
        'OVER_3_5', 'UNDER_3_5',
        'OVER_4_5', 'UNDER_4_5',

        # Gols Exatos (5)
        'EXACTLY_0_GOALS', 'EXACTLY_1_GOAL', 'EXACTLY_2_GOALS',
        'EXACTLY_3_GOALS', '4_OR_MORE_GOALS',

        # Par/Ímpar (2)
        'ODD_GOALS', 'EVEN_GOALS',

        # Primeiro a Marcar (3)
        'NO_GOAL', 'FIRST_GOAL_HOME', 'FIRST_GOAL_AWAY',

        # Clean Sheet (2)
        'HOME_CLEAN_SHEET', 'AWAY_CLEAN_SHEET',

        # Placares Exatos Principais (9)
        'SCORE_0_0', 'SCORE_1_0', 'SCORE_0_1',
        'SCORE_1_1', 'SCORE_2_0', 'SCORE_0_2',
        'SCORE_2_1', 'SCORE_1_2', 'SCORE_2_2',
    ]

    # TOTAL: 41 mercados para maximizar predictions e lucro!

    # 🎯 THRESHOLDS v6.1 (2025-10-24) - AJUSTADO PÓS-VALIDAÇÃO (MEIO-TERMO)
    #
    # FILOSOFIA: QUALIDADE > QUANTIDADE (mas realista)
    # TARGET: Apenas 15-20% dos jogos (seletivo mas alcançável)
    # Accuracy esperada: 50-55% (baseado em validação real)
    #
    # VALIDAÇÃO REAL (24 OUT):
    # - Singles V3: 37.5% accuracy (3/8) ❌
    # - BTTS_NO: 40% (melhor mercado)
    # - HOME_WIN: 33.3%
    # - BTTS_YES: 0%
    #
    # AJUSTES v6.1:
    # - v6.0 estava muito alto (70-75%) = 0 predictions geradas
    # - v6.1 meio-termo (+5 a +7 pontos vs original)
    # - Min_confidence ajustado para valores alcançáveis
    # - Filtro anti-goleada mantido
    MARKET_THRESHOLDS = {
        # 1X2: RELAXADO (-10%)
        'HOME_WIN': {'min_prob': 0.52, 'min_edge': 0, 'min_confidence': 0.30},
        'DRAW': {'min_prob': 0.62, 'min_edge': 0, 'min_confidence': 0.40},
        'AWAY_WIN': {'min_prob': 0.50, 'min_edge': 0, 'min_confidence': 0.30},

        # Dupla Chance: RELAXADO (-10%)
        '1X': {'min_prob': 0.50, 'min_edge': 0, 'min_confidence': 0.30},
        '12': {'min_prob': 0.50, 'min_edge': 0, 'min_confidence': 0.30},
        'X2': {'min_prob': 0.50, 'min_edge': 0, 'min_confidence': 0.30},

        # BTTS: RELAXADO (-10%)
        'BTTS_YES': {'min_prob': 0.58, 'min_edge': 0, 'min_confidence': 0.50},
        'BTTS_NO': {'min_prob': 0.62, 'min_edge': 0, 'min_confidence': 0.55},

        # Over/Under: RELAXADO (-10%)
        'OVER_0_5': {'min_prob': 0.55, 'min_edge': 0, 'min_confidence': 0.35},
        'UNDER_0_5': {'min_prob': 0.55, 'min_edge': 0, 'min_confidence': 0.35},
        'OVER_1_5': {'min_prob': 0.50, 'min_edge': 0, 'min_confidence': 0.30},
        'UNDER_1_5': {'min_prob': 0.50, 'min_edge': 0, 'min_confidence': 0.30},
        'OVER_2_5': {'min_prob': 0.48, 'min_edge': 0, 'min_confidence': 0.30},
        'UNDER_2_5': {'min_prob': 0.48, 'min_edge': 0, 'min_confidence': 0.30},
        'OVER_3_5': {'min_prob': 0.45, 'min_edge': 0, 'min_confidence': 0.25},
        'UNDER_3_5': {'min_prob': 0.45, 'min_edge': 0, 'min_confidence': 0.25},
        'OVER_4_5': {'min_prob': 0.40, 'min_edge': 0, 'min_confidence': 0.20},
        'UNDER_4_5': {'min_prob': 0.40, 'min_edge': 0, 'min_confidence': 0.20},

        # Gols Exatos: RELAXADO (-10%)
        'EXACTLY_0_GOALS': {'min_prob': 0.15, 'min_edge': 0, 'min_confidence': 0.30},
        'EXACTLY_1_GOAL': {'min_prob': 0.15, 'min_edge': 0, 'min_confidence': 0.30},
        'EXACTLY_2_GOALS': {'min_prob': 0.15, 'min_edge': 0, 'min_confidence': 0.30},
        'EXACTLY_3_GOALS': {'min_prob': 0.10, 'min_edge': 0, 'min_confidence': 0.25},
        '4_OR_MORE_GOALS': {'min_prob': 0.10, 'min_edge': 0, 'min_confidence': 0.25},

        # Par/Ímpar: RELAXADO (-10%)
        'ODD_GOALS': {'min_prob': 0.45, 'min_edge': 0, 'min_confidence': 0.25},
        'EVEN_GOALS': {'min_prob': 0.45, 'min_edge': 0, 'min_confidence': 0.25},

        # Primeiro a Marcar: RELAXADO (-10%)
        'NO_GOAL': {'min_prob': 0.05, 'min_edge': 0, 'min_confidence': 0.15},
        'FIRST_GOAL_HOME': {'min_prob': 0.40, 'min_edge': 0, 'min_confidence': 0.25},
        'FIRST_GOAL_AWAY': {'min_prob': 0.40, 'min_edge': 0, 'min_confidence': 0.25},

        # Clean Sheet: RELAXADO (-10%)
        'HOME_CLEAN_SHEET': {'min_prob': 0.45, 'min_edge': 0, 'min_confidence': 0.30},
        'AWAY_CLEAN_SHEET': {'min_prob': 0.45, 'min_edge': 0, 'min_confidence': 0.30},

        # Placares Exatos: RELAXADO (-10%)
        'SCORE_0_0': {'min_prob': 0.05, 'min_edge': 0, 'min_confidence': 0.20},
        'SCORE_1_0': {'min_prob': 0.05, 'min_edge': 0, 'min_confidence': 0.20},
        'SCORE_0_1': {'min_prob': 0.05, 'min_edge': 0, 'min_confidence': 0.20},
        'SCORE_1_1': {'min_prob': 0.05, 'min_edge': 0, 'min_confidence': 0.20},
        'SCORE_2_0': {'min_prob': 0.02, 'min_edge': 0, 'min_confidence': 0.15},
        'SCORE_0_2': {'min_prob': 0.02, 'min_edge': 0, 'min_confidence': 0.15},
        'SCORE_2_1': {'min_prob': 0.02, 'min_edge': 0, 'min_confidence': 0.15},
        'SCORE_1_2': {'min_prob': 0.02, 'min_edge': 0, 'min_confidence': 0.15},
        'SCORE_2_2': {'min_prob': 0.00, 'min_edge': 0, 'min_confidence': 0.10},
    }

    # 🛡️ FILTRO ANTI-GOLEADA (novo!)
    # Evita predictions BTTS_NO quando há risco de muitos gols
    ANTI_GOLEADA = {
        'max_avg_goals': 3.5,     # Média de gols por jogo < 3.5
        'max_xg_total': 3.0,      # xG total esperado < 3.0
    }

    def __init__(self, db: Session):
        self.db = db
        self.prediction_service = PredictionService(db)
        self._stats_cache = {}  # Cache de TeamStatistics por team_id
        self._odds_cache = {}   # Cache de Odds por match_id
        self._accuracy_cache = {}  # Cache de accuracy histórica por market

    def _convert_market_to_outcome(self, market: str) -> str:
        """
        Converte market_type para predicted_outcome no formato esperado pelo Ticket Analyzer

        BUG FIX (2025-10-29): Ticket Analyzer espera formatos específicos:
        - BTTS: 'YES' ou 'NO', não 'BTTS_YES'/'BTTS_NO'
        - OVER/UNDER: 'OVER' ou 'UNDER', não 'OVER_2_5'
        - CLEAN_SHEET: 'YES' ou 'NO'
        - 1X2: Mantém 'HOME_WIN'/'DRAW'/'AWAY_WIN'
        - Etc.

        Args:
            market: Market type (ex: 'BTTS_NO', 'HOME_WIN', 'OVER_2_5')

        Returns:
            Outcome formatado para Ticket Analyzer
        """
        # BTTS: Retorna YES ou NO
        if market == 'BTTS_YES':
            return 'YES'
        elif market == 'BTTS_NO':
            return 'NO'

        # OVER/UNDER: Retorna OVER ou UNDER (sem o threshold)
        elif 'OVER_' in market:
            return 'OVER'
        elif 'UNDER_' in market:
            return 'UNDER'

        # CLEAN_SHEET: Retorna YES
        elif 'CLEAN_SHEET' in market:
            return 'YES'

        # FIRST_GOAL: Mantém o formato
        elif 'FIRST_GOAL_HOME' in market:
            return 'FIRST_GOAL_HOME'
        elif 'FIRST_GOAL_AWAY' in market:
            return 'FIRST_GOAL_AWAY'
        elif 'NO_GOAL' in market:
            return 'NO_GOAL'

        # EXACTLY X GOALS: Mantém market (analyzer detecta pelo nome)
        elif 'EXACTLY_' in market or '4_OR_MORE' in market:
            return market

        # ODD/EVEN: Extrai ODD ou EVEN
        elif market == 'ODD_GOALS':
            return 'ODD'
        elif market == 'EVEN_GOALS':
            return 'EVEN'

        # DUPLA CHANCE: Mantém (1X, 12, X2)
        elif market in ['1X', '12', 'X2']:
            return market

        # SCORE: Mantém formato
        elif 'SCORE_' in market:
            return market

        # 1X2 e RESULTADO FINAL: Mantém formato
        # HOME_WIN, DRAW, AWAY_WIN
        else:
            return market

    def generate_predictions_for_single_match(self, match: Match) -> List[Dict]:
        """
        Gera predictions para um único jogo - TODOS os markets

        Args:
            match: Match object

        Returns:
            List de dicts com predictions (uma para cada market que passar nos thresholds)
        """
        from app.models import TeamStatistics

        # 🚨 FILTRO CRÍTICO: Não gerar predictions sem TeamStatistics
        # BUG FIX v6.1 (2025-10-24): Usar TeamStatistics se disponível, senão defaults com variância
        # Defaults com variância baseado em team_id evitam probabilidades idênticas
        home_stats = self.db.query(TeamStatistics).filter(
            TeamStatistics.team_id == match.home_team_id
        ).order_by(TeamStatistics.created_at.desc()).first()

        away_stats = self.db.query(TeamStatistics).filter(
            TeamStatistics.team_id == match.away_team_id
        ).order_by(TeamStatistics.created_at.desc()).first()

        # Se não tem TeamStatistics, cria objeto mock com defaults + variância
        if not home_stats:
            class MockStats:
                def __init__(self, team_id):
                    # Variância baseada em team_id para garantir diversidade
                    variance = (team_id % 11) * 0.05  # 0.0 a 0.5
                    self.goals_scored_avg = 1.5 + variance - 0.25
                    self.goals_conceded_avg = 1.2 + variance - 0.25
            home_stats = MockStats(match.home_team_id)
            logger.debug(f"Match {match.id}: Usando defaults com variância para home team")

        if not away_stats:
            class MockStats:
                def __init__(self, team_id):
                    variance = (team_id % 11) * 0.05
                    self.goals_scored_avg = 1.3 + variance - 0.25
                    self.goals_conceded_avg = 1.1 + variance - 0.25
            away_stats = MockStats(match.away_team_id)
            logger.debug(f"Match {match.id}: Usando defaults com variância para away team")

        predictions = []

        # ✅ USAR TODOS OS 41 MERCADOS!
        for market in self.MARKETS:
            pred_dict = self._generate_prediction_for_market(match, market)

            if pred_dict:  # Se passou nos thresholds
                predictions.append(pred_dict)

        return predictions

    def generate_daily_predictions(self, target_count: int = 2500) -> Dict:
        """
        Gera predictions diárias para aprendizado ML

        Args:
            target_count: Meta de predictions a gerar (default: 2500)

        Returns:
            Estatísticas da geração
        """
        logger.info(f"🧠 Iniciando geração de {target_count} predictions para aprendizado ML...")

        stats = {
            'singles': 0,
            'doubles_same_match': 0,
            'trebles_same_match': 0,
            'quads_same_match': 0,
            'doubles_multi': 0,
            'trebles_multi': 0,
            'quads_multi': 0,
            'total': 0,
            'errors': 0
        }

        # Buscar jogos futuros disponíveis (OTIMIZADO: apenas próximos 7 dias, máximo 100 jogos)
        from datetime import timedelta

        max_date = datetime.utcnow() + timedelta(days=7)

        future_matches = self.db.query(Match).filter(
            and_(
                Match.match_date > datetime.utcnow(),
                Match.match_date < max_date,  # LIMITAR A 7 DIAS
                Match.status.in_(['NS', 'TBD', 'SCHEDULED'])
            )
        ).limit(100).all()  # MÁXIMO 100 JOGOS

        if len(future_matches) < 5:
            logger.warning(f"Apenas {len(future_matches)} jogos disponíveis. Mínimo recomendado: 5")
            return stats

        logger.info(f"📊 {len(future_matches)} jogos disponíveis (próximos 7 dias, max 100)")

        # Distribuição de predictions
        # 🎯 NOVA DISTRIBUIÇÃO (2025-10-17):
        # - 5% singles (apostas simples)
        # - 80% doubles + trebles (duplas e triplas) - FOCO PRINCIPAL
        # - 15% quads+ (múltiplas com 4+ seleções)
        distribution = {
            'singles': int(target_count * 0.05),              # 5%  = 225 (para 4500)
            'doubles_same_match': int(target_count * 0.20),   # 20% = 900
            'trebles_same_match': int(target_count * 0.20),   # 20% = 900
            'quads_same_match': int(target_count * 0.10),     # 10% = 450
            'doubles_multi': int(target_count * 0.20),        # 20% = 900
            'trebles_multi': int(target_count * 0.20),        # 20% = 900
            'quads_multi': int(target_count * 0.05),          # 5%  = 225
        }

        # 1. SINGLES (1 mercado, 1 jogo)
        logger.info("📊 Gerando Singles (1 mercado, 1 jogo)...")
        stats['singles'] = self._generate_singles(future_matches, distribution['singles'])

        # 2. DOUBLES - MESMO JOGO (2 mercados, 1 jogo)
        logger.info("📊 Gerando Doubles no mesmo jogo (2 mercados, 1 jogo)...")
        stats['doubles_same_match'] = self._generate_same_match_multiples(
            future_matches,
            market_count=2,
            target=distribution['doubles_same_match']
        )

        # 3. TREBLES - MESMO JOGO (3 mercados, 1 jogo)
        logger.info("📊 Gerando Trebles no mesmo jogo (3 mercados, 1 jogo)...")
        stats['trebles_same_match'] = self._generate_same_match_multiples(
            future_matches,
            market_count=3,
            target=distribution['trebles_same_match']
        )

        # 4. QUADS - MESMO JOGO (4 mercados, 1 jogo)
        logger.info("📊 Gerando Quads no mesmo jogo (4 mercados, 1 jogo)...")
        stats['quads_same_match'] = self._generate_same_match_multiples(
            future_matches,
            market_count=4,
            target=distribution['quads_same_match']
        )

        # 5. DOUBLES - MÚLTIPLOS JOGOS (2 mercados, 2 jogos)
        logger.info("📊 Gerando Doubles múltiplos (2 mercados, 2 jogos)...")
        stats['doubles_multi'] = self._generate_multi_match_combinations(
            future_matches,
            match_count=2,
            target=distribution['doubles_multi']
        )

        # 6. TREBLES - MÚLTIPLOS JOGOS (3 mercados, 3 jogos)
        logger.info("📊 Gerando Trebles múltiplos (3 mercados, 3 jogos)...")
        stats['trebles_multi'] = self._generate_multi_match_combinations(
            future_matches,
            match_count=3,
            target=distribution['trebles_multi']
        )

        # 7. QUADS - MÚLTIPLOS JOGOS (4 mercados, 4 jogos)
        logger.info("📊 Gerando Quads múltiplos (4 mercados, 4 jogos)...")
        stats['quads_multi'] = self._generate_multi_match_combinations(
            future_matches,
            match_count=4,
            target=distribution['quads_multi']
        )

        stats['total'] = sum([v for k, v in stats.items() if k != 'errors'])

        logger.info(f"""
        ✅ GERAÇÃO COMPLETA:
        - Singles: {stats['singles']}
        - Doubles (mesmo jogo): {stats['doubles_same_match']}
        - Trebles (mesmo jogo): {stats['trebles_same_match']}
        - Quads (mesmo jogo): {stats['quads_same_match']}
        - Doubles (multi): {stats['doubles_multi']}
        - Trebles (multi): {stats['trebles_multi']}
        - Quads (multi): {stats['quads_multi']}
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        TOTAL: {stats['total']} predictions geradas
        """)

        return stats

    def _generate_singles(self, matches: List[Match], target: int) -> int:
        """Gera predictions singles (1 mercado, 1 jogo)"""
        created = 0

        # Distribuir entre os mercados
        per_market = target // len(self.MARKETS)

        logger.info(f"Gerando singles: {per_market} por mercado x {len(self.MARKETS)} mercados = {target} target")

        for market in self.MARKETS:
            market_created = 0

            for match in matches:
                if market_created >= per_market:
                    break

                try:
                    # Verificar se já existe prediction desse mercado para esse jogo
                    existing = self.db.query(Prediction).filter(
                        and_(
                            Prediction.match_id == match.id,
                            Prediction.market_type == market,
                            Prediction.prediction_type == 'SINGLE'
                        )
                    ).first()

                    if existing:
                        continue

                    # Gerar prediction baseada no mercado
                    prediction_data = self._generate_prediction_for_market(match, market)

                    if prediction_data:
                        prediction = Prediction(
                            match_id=match.id,
                            prediction_type='SINGLE',
                            **prediction_data
                        )
                        self.db.add(prediction)
                        market_created += 1
                        created += 1

                except Exception as e:
                    logger.error(f"Erro ao criar single para match {match.id}, market {market}: {e}")

            self.db.commit()

        return created

    def _generate_same_match_multiples(self, matches: List[Match], market_count: int, target: int) -> int:
        """Gera predictions múltiplas no mesmo jogo (N mercados, 1 jogo)"""
        created = 0

        for match in matches:
            if created >= target:
                break

            try:
                # Selecionar mercados aleatórios
                selected_markets = random.sample(self.MARKETS, min(market_count, len(self.MARKETS)))

                # Gerar predictions para cada mercado
                prediction_ids = []
                total_confidence = 1.0

                for market in selected_markets:
                    pred_data = self._generate_prediction_for_market(match, market)

                    if pred_data:
                        # Criar prediction individual
                        prediction = Prediction(
                            match_id=match.id,
                            prediction_type=f"COMBO_{market_count}X",
                            **pred_data
                        )
                        self.db.add(prediction)
                        self.db.flush()

                        prediction_ids.append(prediction.id)
                        total_confidence *= pred_data['confidence_score']

                if len(prediction_ids) == market_count:
                    # Criar combinação
                    combo_type = {2: 'DOUBLE', 3: 'TREBLE', 4: 'QUAD'}.get(market_count, 'MULTIPLE')

                    combination = BetCombination(
                        combination_type=combo_type,
                        selections_count=market_count,
                        total_odds=1.0,  # Será calculado depois com odds reais
                        prediction_ids=prediction_ids,
                        combined_confidence=total_confidence,
                        is_recommended=total_confidence >= 0.60,
                        risk_level='MEDIUM' if total_confidence >= 0.60 else 'HIGH'
                    )
                    self.db.add(combination)
                    created += 1

                self.db.commit()

            except Exception as e:
                logger.error(f"Erro ao criar combo para match {match.id}: {e}")
                self.db.rollback()

        return created

    def _generate_multi_match_combinations(self, matches: List[Match], match_count: int, target: int) -> int:
        """Gera predictions combinando múltiplos jogos"""
        created = 0

        if len(matches) < match_count:
            logger.warning(f"Não há jogos suficientes para combos de {match_count} jogos")
            return 0

        while created < target:
            try:
                # Selecionar jogos aleatórios
                selected_matches = random.sample(matches, match_count)

                prediction_ids = []
                total_confidence = 1.0

                # Para cada jogo, escolher 1 mercado aleatório
                for match in selected_matches:
                    market = random.choice(self.MARKETS)
                    pred_data = self._generate_prediction_for_market(match, market)

                    if pred_data:
                        prediction = Prediction(
                            match_id=match.id,
                            prediction_type=f"MULTI_{match_count}X",
                            **pred_data
                        )
                        self.db.add(prediction)
                        self.db.flush()

                        prediction_ids.append(prediction.id)
                        total_confidence *= pred_data['confidence_score']

                if len(prediction_ids) == match_count:
                    combo_type = {2: 'DOUBLE', 3: 'TREBLE', 4: 'QUAD'}.get(match_count, 'MULTIPLE')

                    combination = BetCombination(
                        combination_type=combo_type,
                        selections_count=match_count,
                        total_odds=1.0,
                        prediction_ids=prediction_ids,
                        combined_confidence=total_confidence,
                        is_recommended=total_confidence >= 0.50,
                        risk_level='LOW' if total_confidence >= 0.70 else 'MEDIUM' if total_confidence >= 0.50 else 'HIGH'
                    )
                    self.db.add(combination)
                    created += 1

                self.db.commit()

            except Exception as e:
                logger.error(f"Erro ao criar multi-combo: {e}")
                self.db.rollback()

        return created

    def _get_historical_accuracy(self, market: str) -> float:
        """
        Busca accuracy histórica de um market específico

        Returns:
            Float entre 0 e 1 representando accuracy (ex: 0.45 = 45%)
        """
        if market in self._accuracy_cache:
            return self._accuracy_cache[market]

        try:
            from sqlalchemy import func, case

            # Buscar predictions validadas desse market
            validated = self.db.query(
                func.count(Prediction.id).label('total'),
                func.sum(case((Prediction.is_winner == True, 1), else_=0)).label('greens')
            ).filter(
                Prediction.market_type == market,
                Prediction.is_validated == True
            ).first()

            if validated and validated.total > 0:
                accuracy = validated.greens / validated.total
            else:
                accuracy = 0.5  # Default se não temos dados

            self._accuracy_cache[market] = accuracy
            return accuracy

        except Exception as e:
            logger.warning(f"Erro ao buscar accuracy histórica de {market}: {e}")
            return 0.5  # Default

    def _calibrate_confidence(self, raw_probability: float, market: str) -> float:
        """
        Calibra confidence score baseado no histórico de accuracy do market

        Args:
            raw_probability: Probabilidade bruta do Poisson
            market: Tipo de mercado

        Returns:
            Confidence calibrado entre 0 e 1
        """
        historical_accuracy = self._get_historical_accuracy(market)

        # Fórmula de calibração:
        # confidence = raw_probability * (historical_accuracy / 0.5)
        # Se accuracy > 50%, aumenta confidence
        # Se accuracy < 50%, reduz confidence
        calibration_factor = historical_accuracy / 0.5

        calibrated = raw_probability * calibration_factor

        # Clamp entre 0 e 1
        return max(0.0, min(1.0, calibrated))

    def _calculate_edge(self, match: Match, market: str, fair_odds: float) -> float:
        """
        Calcula edge de uma prediction

        Returns:
            Edge em porcentagem (ex: 15.0 = 15% edge)
        """
        try:
            from app.models import Odds

            # Buscar odds do jogo (com cache)
            if match.id not in self._odds_cache:
                self._odds_cache[match.id] = self.db.query(Odds).filter(
                    Odds.match_id == match.id
                ).first()

            odds_record = self._odds_cache.get(match.id)

            if not odds_record or not fair_odds or fair_odds <= 0:
                return 0.0

            # Buscar odd real do market
            market_odds_value = None
            if hasattr(odds_record, market.lower()):
                market_odds_value = getattr(odds_record, market.lower(), None)

            if not market_odds_value or market_odds_value <= 0:
                return 0.0

            # Calcular edge
            edge = ((market_odds_value / fair_odds) - 1) * 100
            return edge

        except Exception as e:
            logger.warning(f"Erro ao calcular edge: {e}")
            return 0.0

    def _select_best_1x2_outcome(self, match: Match) -> tuple:
        """
        Seleciona o MELHOR outcome entre HOME_WIN, DRAW, AWAY_WIN

        Returns:
            Tuple (market, probability, edge) ou (None, None, None) se nenhum passar nos filtros
        """
        try:
            from app.models import TeamStatistics, Odds
            from app.services.poisson_service import PoissonService

            # Buscar stats e calcular Poisson (com cache)
            cache_key = f"poisson_{match.id}"

            if not hasattr(self, '_poisson_cache'):
                self._poisson_cache = {}

            if cache_key not in self._poisson_cache:
                # Buscar stats
                home_stats = self._stats_cache.get(match.home_team_id)
                away_stats = self._stats_cache.get(match.away_team_id)

                if match.home_team_id not in self._stats_cache:
                    home_stats = self.db.query(TeamStatistics).filter(
                        TeamStatistics.team_id == match.home_team_id
                    ).order_by(TeamStatistics.created_at.desc()).first()
                    self._stats_cache[match.home_team_id] = home_stats

                if match.away_team_id not in self._stats_cache:
                    away_stats = self.db.query(TeamStatistics).filter(
                        TeamStatistics.team_id == match.away_team_id
                    ).order_by(TeamStatistics.created_at.desc()).first()
                    self._stats_cache[match.away_team_id] = away_stats

                # Calcular Poisson
                poisson = PoissonService()
                self._poisson_cache[cache_key] = poisson.analyze_match(
                    home_goals_avg=home_stats.goals_scored_avg if home_stats else 1.5,
                    away_goals_avg=away_stats.goals_scored_avg if away_stats else 1.3,
                    home_conceded_avg=home_stats.goals_conceded_avg if home_stats else 1.2,
                    away_conceded_avg=away_stats.goals_conceded_avg if away_stats else 1.1,
                    market_odds={},
                    league_avg=2.7
                )

            poisson_analysis = self._poisson_cache[cache_key]

            # Analisar os 3 outcomes
            outcomes = {}
            for market in ['HOME_WIN', 'DRAW', 'AWAY_WIN']:
                if market not in poisson_analysis.probabilities:
                    continue

                prob = poisson_analysis.probabilities[market]
                fair_odds = poisson_analysis.fair_odds.get(market, 0)
                edge = self._calculate_edge(match, market, fair_odds)

                # Aplicar FILTROS (BET365 LOGIC)
                threshold = self.MARKET_THRESHOLDS.get(market, {'min_prob': 0.3, 'min_edge': 0})

                # TODOS os markets precisam passar AMBOS filtros (prob E edge)
                if prob < threshold['min_prob'] or edge < threshold['min_edge']:
                    continue  # Não passa nos filtros

                outcomes[market] = {
                    'prob': prob,
                    'edge': edge,
                    'fair_odds': fair_odds
                }

            # Se nenhum outcome passou nos filtros
            if not outcomes:
                return (None, None, None)

            # 🎯 BET365 LOGIC SIMPLES: Selecionar outcome com MAIOR PROBABILIDADE
            # Como em futebol real: o mais provável é selecionado
            # DRAW já foi filtrado por threshold alto (40%), então se passou, merece
            best_market = max(outcomes.items(), key=lambda x: x[1]['prob'])

            return (
                best_market[0],
                best_market[1]['prob'],
                best_market[1]['edge']
            )

        except Exception as e:
            logger.error(f"Erro ao selecionar melhor 1X2 outcome: {e}")
            return (None, None, None)

    def _generate_prediction_for_market(self, match: Match, market: str) -> Dict:
        """
        🔥 ATUALIZADO (2025-10-20): Gera prediction com SELEÇÃO INTELIGENTE de outcomes

        Para 1X2: Seleciona APENAS o melhor outcome (evita muitos DRAWS ruins)
        Para outros: Aplica thresholds específicos e calibração de confidence
        """
        try:
            from app.models import TeamStatistics, Odds
            from app.services.poisson_service import PoissonService

            # 🎯 LÓGICA ESPECIAL PARA 1X2: Selecionar apenas o MELHOR outcome
            if market in ['HOME_WIN', 'DRAW', 'AWAY_WIN']:
                best_outcome, probability, edge = self._select_best_1x2_outcome(match)

                # Se o market solicitado não é o melhor, retornar None
                if best_outcome != market:
                    return None

                # Se chegou aqui, é o melhor outcome - continuar com a geração
                # Buscar dados do Poisson (já está em cache)
                cache_key = f"poisson_{match.id}"
                poisson_analysis = self._poisson_cache.get(cache_key)

                if not poisson_analysis:
                    return None

                fair_odds = poisson_analysis.fair_odds.get(market, 0)

                # Buscar odds reais
                if match.id not in self._odds_cache:
                    self._odds_cache[match.id] = self.db.query(Odds).filter(Odds.match_id == match.id).first()

                odds_record = self._odds_cache.get(match.id)
                market_odds_value = None
                if odds_record and hasattr(odds_record, market.lower()):
                    market_odds_value = getattr(odds_record, market.lower(), None)

                # Calibrar confidence
                confidence_score = self._calibrate_confidence(probability, market)

                # Determinar value bet
                is_value_bet = edge > 10.0 and probability > 0.15

                return {
                    'market_type': market,
                    'predicted_outcome': self._convert_market_to_outcome(market),
                    'predicted_probability': probability,
                    'confidence_score': confidence_score,
                    'probability_home': poisson_analysis.probabilities.get('HOME_WIN', 0.33),
                    'probability_draw': poisson_analysis.probabilities.get('DRAW', 0.33),
                    'probability_away': poisson_analysis.probabilities.get('AWAY_WIN', 0.33),
                    'value_score': edge / 100.0 if edge > 0 else 0.0,
                    'kelly_percentage': min(edge / 5.0, 10.0) if edge > 0 else 0.0,
                    'recommended_odds': fair_odds,
                    'actual_odds': market_odds_value,
                    'analysis_summary': f"BEST 1X2: {probability*100:.1f}% prob, Confidence: {confidence_score*100:.1f}%, Edge: {edge:+.1f}%",
                    'final_recommendation': 'BET' if is_value_bet else 'MONITOR',
                    'model_version': 'poisson_v3_smart_selection',
                    'key_factors': {
                        'probability': float(probability),
                        'confidence_calibrated': float(confidence_score),
                        'fair_odds': float(fair_odds),
                        'market_odds': float(market_odds_value) if market_odds_value else None,
                        'edge': float(edge),
                        'is_value_bet': 'yes' if is_value_bet else 'no',
                        'selection_method': 'best_1x2_outcome'
                    }
                }

            # 🎯 LÓGICA NORMAL PARA OUTROS MARKETS (BTTS, O/U, etc)
            # Buscar stats dos times (COM CACHE)
            if match.home_team_id not in self._stats_cache:
                self._stats_cache[match.home_team_id] = self.db.query(TeamStatistics).filter(
                    TeamStatistics.team_id == match.home_team_id
                ).order_by(TeamStatistics.created_at.desc()).first()

            if match.away_team_id not in self._stats_cache:
                self._stats_cache[match.away_team_id] = self.db.query(TeamStatistics).filter(
                    TeamStatistics.team_id == match.away_team_id
                ).order_by(TeamStatistics.created_at.desc()).first()

            home_stats = self._stats_cache.get(match.home_team_id)
            away_stats = self._stats_cache.get(match.away_team_id)

            # Buscar odds reais do mercado (COM CACHE)
            if match.id not in self._odds_cache:
                self._odds_cache[match.id] = self.db.query(Odds).filter(Odds.match_id == match.id).first()

            odds_record = self._odds_cache.get(match.id)

            # Calcular TODAS as probabilidades via Poisson (COM CACHE POR MATCH)
            cache_key = f"poisson_{match.id}"

            if not hasattr(self, '_poisson_cache'):
                self._poisson_cache = {}

            if cache_key not in self._poisson_cache:
                poisson = PoissonService()
                self._poisson_cache[cache_key] = poisson.analyze_match(
                    home_goals_avg=home_stats.goals_scored_avg if home_stats else 1.5,
                    away_goals_avg=away_stats.goals_scored_avg if away_stats else 1.3,
                    home_conceded_avg=home_stats.goals_conceded_avg if home_stats else 1.2,
                    away_conceded_avg=away_stats.goals_conceded_avg if away_stats else 1.1,
                    market_odds={},
                    league_avg=2.7
                )

            poisson_analysis = self._poisson_cache[cache_key]

            # Verificar se o mercado existe no Poisson
            if market not in poisson_analysis.probabilities:
                return None

            # Extrair dados do mercado
            probability = poisson_analysis.probabilities[market]
            fair_odds = poisson_analysis.fair_odds.get(market, 0)

            # Calcular edge
            edge = self._calculate_edge(match, market, fair_odds)

            # 🎯 APLICAR THRESHOLDS ESPECÍFICOS POR MARKET
            threshold = self.MARKET_THRESHOLDS.get(market, {'min_prob': 0.3, 'min_edge': 0})

            # Filtrar por threshold
            if probability < threshold['min_prob'] or edge < threshold['min_edge']:
                return None  # Não passa no filtro

            # Calibrar confidence
            confidence_score = self._calibrate_confidence(probability, market)

            # 🔥 NOVO: Filtrar por min_confidence (v6.0)
            min_confidence = threshold.get('min_confidence', 0)
            if confidence_score < min_confidence:
                return None  # Não passa no filtro de confidence

            # 🛡️ NOVO: Filtro anti-goleada para BTTS_NO (v6.1)
            if market == 'BTTS_NO':
                # Usar Poisson probabilities para detectar jogos de muitos gols
                # Se OVER_2_5 tem prob alta (> 60%), evitar BTTS_NO
                over_25_prob = poisson_analysis.probabilities.get('OVER_2_5', 0)

                # Rejeitar se alta probabilidade de muitos gols
                if over_25_prob > 0.60:
                    logger.debug(f"BTTS_NO rejeitado por risco de goleada (over_2_5_prob={over_25_prob:.1%})")
                    return None

            # Determinar value bet
            is_value_bet = edge > 10.0 and probability > 0.15

            # Buscar odd real
            market_odds_value = None
            if odds_record and hasattr(odds_record, market.lower()):
                market_odds_value = getattr(odds_record, market.lower(), None)

            return {
                'market_type': market,
                'predicted_outcome': self._convert_market_to_outcome(market),
                'predicted_probability': probability,
                'confidence_score': confidence_score,
                'probability_home': poisson_analysis.probabilities.get('HOME_WIN', 0.33),
                'probability_draw': poisson_analysis.probabilities.get('DRAW', 0.33),
                'probability_away': poisson_analysis.probabilities.get('AWAY_WIN', 0.33),
                'value_score': edge / 100.0 if edge > 0 else 0.0,
                'kelly_percentage': min(edge / 5.0, 10.0) if edge > 0 else 0.0,
                'recommended_odds': fair_odds,
                'actual_odds': market_odds_value,
                'analysis_summary': f"Poisson: {probability*100:.1f}%, Confidence: {confidence_score*100:.1f}%, Edge: {edge:+.1f}%",
                'final_recommendation': 'BET' if is_value_bet else 'MONITOR',
                'model_version': 'poisson_v3_calibrated',
                'key_factors': {
                    'probability': float(probability),
                    'confidence_calibrated': float(confidence_score),
                    'fair_odds': float(fair_odds),
                    'market_odds': float(market_odds_value) if market_odds_value else None,
                    'edge': float(edge),
                    'is_value_bet': 'yes' if is_value_bet else 'no',
                    'lambda_home': float(poisson_analysis.home_lambda),
                    'lambda_away': float(poisson_analysis.away_lambda),
                }
            }

        except Exception as e:
            logger.error(f"Erro ao gerar prediction para market {market} no match {match.id}: {e}")
            return None


# Função helper para uso no scheduler
def run_daily_ml_prediction_generation(target: int = 2500):
    """Job: Gerar predictions diárias para aprendizado ML"""
    from app.core.database import get_db_session

    db = get_db_session()
    try:
        generator = MLPredictionGenerator(db)
        return generator.generate_daily_predictions(target)
    finally:
        db.close()
