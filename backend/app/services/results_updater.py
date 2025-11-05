#!/usr/bin/env python3
"""
🔄 SERVIÇO DE ATUALIZAÇÃO AUTOMÁTICA DE RESULTADOS

Fluxo contínuo:
1. Busca jogos finalizados na API
2. Atualiza resultados reais no banco
3. Calcula GREEN/RED das predictions
4. 🆕 Alimenta sistema de ML com feedback loop
5. Remove jogos passados das Predictions
"""
import requests
import asyncio
import os
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from typing import List, Dict
from app.models import Match, Prediction
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# API-Sports PRO
API_KEY = settings.API_SPORTS_KEY
if not API_KEY:
    raise ValueError("API_SPORTS_KEY não configurada. Configure no arquivo .env")
BASE_URL = 'https://v3.football.api-sports.io'
HEADERS = {'x-apisports-key': API_KEY}


class ResultsUpdater:
    """Atualiza resultados e calcula GREEN/RED automaticamente"""

    def __init__(self, db: Session):
        self.db = db

    def update_all_results(self) -> Dict:
        """
        Executa o fluxo completo de atualização

        Returns:
            Dict com estatísticas da atualização
        """
        stats = {
            'total_matches_checked': 0,
            'results_updated': 0,
            'predictions_evaluated': 0,
            'greens': 0,
            'reds': 0,
            'errors': []
        }

        # Buscar todos os jogos finalizados que ainda não têm score
        finished_matches = self.db.query(Match).filter(
            Match.status.in_(['FT', 'AET', 'PEN']),
            Match.home_score.is_(None)  # Ainda sem resultado
        ).all()

        logger.info(f"🔍 Encontrados {len(finished_matches)} jogos finalizados sem resultado")
        stats['total_matches_checked'] = len(finished_matches)

        for match in finished_matches:
            try:
                if not match.external_id or not match.external_id.isdigit():
                    continue

                # Buscar resultado na API
                result = self._fetch_match_result(match.external_id)

                if result:
                    # Atualizar match com resultado real
                    match.home_score = result['home_score']
                    match.away_score = result['away_score']
                    match.status = result['status']

                    stats['results_updated'] += 1

                    # Calcular GREEN/RED para todas as predictions deste jogo
                    predictions = self.db.query(Prediction).filter(
                        Prediction.match_id == match.id
                    ).all()

                    green_red_stats = self._calculate_green_red(match, predictions)
                    stats['predictions_evaluated'] += green_red_stats['total']
                    stats['greens'] += green_red_stats['greens']
                    stats['reds'] += green_red_stats['reds']

                    # 🆕 FEEDBACK LOOP: Salvar dados para retreino de ML
                    if predictions:
                        try:
                            match_data = self._prepare_match_data_for_ml(match, predictions)
                            self._save_for_ml_retraining(match_data)
                            logger.debug(f"💾 Dados salvos para ML retraining: Match {match.id}")
                        except Exception as ml_error:
                            logger.warning(f"⚠️ Erro ao salvar dados ML: {ml_error}")

                    logger.info(f"✅ {match.home_team} {result['home_score']}-{result['away_score']} {match.away_team}")

            except Exception as e:
                error_msg = f"Erro ao atualizar {match.id}: {str(e)}"
                logger.error(error_msg)
                stats['errors'].append(error_msg)

        # Commit todas as alterações
        self.db.commit()

        logger.info(f"""
        📊 ATUALIZAÇÃO CONCLUÍDA:
        - Jogos verificados: {stats['total_matches_checked']}
        - Resultados atualizados: {stats['results_updated']}
        - Predictions avaliadas: {stats['predictions_evaluated']}
        - 🟢 GREENS: {stats['greens']}
        - 🔴 REDS: {stats['reds']}
        """)

        return stats

    def _fetch_match_result(self, fixture_id: str) -> Dict:
        """
        Busca resultado do jogo na API

        Args:
            fixture_id: ID do jogo na API-Sports

        Returns:
            Dict com home_score, away_score, status
        """
        try:
            url = f"{BASE_URL}/fixtures"
            params = {'id': fixture_id}

            response = requests.get(url, headers=HEADERS, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data['response']:
                fixture = data['response'][0]

                return {
                    'home_score': fixture['goals']['home'],
                    'away_score': fixture['goals']['away'],
                    'status': fixture['fixture']['status']['short']
                }

        except Exception as e:
            logger.error(f"Erro ao buscar resultado fixture {fixture_id}: {e}")

        return None

    def _calculate_green_red(self, match: Match, predictions: List[Prediction]) -> Dict:
        """
        Calcula GREEN/RED para todas as predictions do jogo

        Args:
            match: Match com resultado real
            predictions: Lista de predictions do jogo

        Returns:
            Dict com estatísticas de greens/reds
        """
        stats = {'total': 0, 'greens': 0, 'reds': 0}

        # Determinar resultado real
        if match.home_score > match.away_score:
            actual_outcome = '1'  # Casa ganhou
        elif match.home_score < match.away_score:
            actual_outcome = '2'  # Fora ganhou
        else:
            actual_outcome = 'X'  # Empate

        # Calcular BTTS (Both Teams To Score)
        actual_btts = match.home_score > 0 and match.away_score > 0

        # Calcular Over/Under 2.5
        total_goals = match.home_score + match.away_score
        actual_over_2_5 = total_goals > 2.5

        for pred in predictions:
            stats['total'] += 1

            # Determinar se acertou baseado no tipo de mercado
            is_correct = False

            # O market_type pode ser '1X2' ou o outcome direto ('HOME_WIN', 'DRAW', 'AWAY_WIN')
            if pred.market_type == '1X2' or pred.market_type in ['HOME_WIN', 'DRAW', 'AWAY_WIN']:
                pred.actual_outcome = actual_outcome

                # Se predicted_outcome é HOME_WIN/DRAW/AWAY_WIN, mapear para 1/X/2
                pred_outcome_mapped = pred.predicted_outcome
                if pred.predicted_outcome == 'HOME_WIN':
                    pred_outcome_mapped = '1'
                elif pred.predicted_outcome == 'DRAW':
                    pred_outcome_mapped = 'X'
                elif pred.predicted_outcome == 'AWAY_WIN':
                    pred_outcome_mapped = '2'

                is_correct = pred_outcome_mapped == actual_outcome

            # BTTS pode vir como market_type='BTTS' ou market_type='BTTS_YES'/'BTTS_NO'
            elif pred.market_type == 'BTTS' or pred.market_type in ['BTTS_YES', 'BTTS_NO']:
                pred.actual_outcome = 'BTTS_YES' if actual_btts else 'BTTS_NO'
                # Suportar ambos formatos: 'BTTS_YES'/'BTTS_NO' e 'Yes'/'No'
                predicted_btts = pred.predicted_outcome in ['BTTS_YES', 'Yes'] or pred.market_type == 'BTTS_YES'
                is_correct = predicted_btts == actual_btts

            # Over/Under pode vir como 'Over/Under 2.5' ou 'OVER_2_5'/'UNDER_2_5'
            elif pred.market_type in ['Over/Under 2.5', 'Goals O/U', 'OVER_2_5', 'UNDER_2_5']:
                pred.actual_outcome = 'OVER_2_5' if actual_over_2_5 else 'UNDER_2_5'
                # Suportar ambos formatos: 'OVER_2_5'/'UNDER_2_5' e 'Over'/'Under'
                predicted_over = (pred.predicted_outcome in ['OVER_2_5', 'Over'] or
                                 pred.market_type == 'OVER_2_5')
                is_correct = predicted_over == actual_over_2_5

            else:
                # Fallback para outros mercados
                pred.actual_outcome = actual_outcome
                is_correct = pred.predicted_outcome == actual_outcome

            # Atualizar GREEN (acertou) ou RED (errou)
            if is_correct:
                pred.is_winner = True
                stats['greens'] += 1

                # Calcular profit (se tiver odd)
                if pred.actual_odds:
                    stake = 10.0  # Stake padrão
                    pred.profit_loss = (pred.actual_odds - 1) * stake
                else:
                    pred.profit_loss = 0.0
            else:
                pred.is_winner = False
                stats['reds'] += 1
                pred.profit_loss = -10.0  # Perda do stake

            pred.is_validated = True

        return stats

    def _prepare_match_data_for_ml(self, match: Match, predictions: List[Prediction]) -> Dict:
        """
        Prepara dados do jogo para alimentar sistema de ML retraining

        Args:
            match: Match com resultado
            predictions: Predictions do jogo

        Returns:
            Dict com dados formatados para ML
        """
        # Calcular resultados reais
        if match.home_score > match.away_score:
            match_result = 'home'
        elif match.home_score < match.away_score:
            match_result = 'away'
        else:
            match_result = 'draw'

        total_goals = match.home_score + match.away_score
        both_teams_scored = match.home_score > 0 and match.away_score > 0

        # Organizar predictions por mercado
        predictions_made = {}
        for pred in predictions:
            if pred.market_type not in predictions_made:
                predictions_made[pred.market_type] = []

            predictions_made[pred.market_type].append({
                'predicted_outcome': pred.predicted_outcome,
                'actual_outcome': pred.actual_outcome,
                'is_correct': pred.is_winner,
                'confidence': getattr(pred, 'confidence', 0.5),  # Default 0.5 se não tiver
                'odds': pred.actual_odds,
                'source': getattr(pred, 'source', 'ML')  # Default 'ML' se não tiver
            })

        match_data = {
            'match_id': match.id,
            'external_id': match.external_id,
            'match_info': {
                'home_team': match.home_team if isinstance(match.home_team, str) else (match.home_team.name if hasattr(match.home_team, 'name') else str(match.home_team)),
                'away_team': match.away_team if isinstance(match.away_team, str) else (match.away_team.name if hasattr(match.away_team, 'name') else str(match.away_team)),
                'league': match.league,
                'match_date': match.match_date.isoformat() if match.match_date else None,
            },
            'actual_results': {
                'match_result': match_result,
                'home_score': match.home_score,
                'away_score': match.away_score,
                'total_goals': total_goals,
                'btts': both_teams_scored,
                'over_2_5': total_goals > 2.5,
            },
            'predictions_made': predictions_made,
            'features_for_ml': {
                'home_strength': 0.5,  # TODO: Calcular real
                'away_strength': 0.5,  # TODO: Calcular real
                'expected_goals_home': match.home_score,
                'expected_goals_away': match.away_score,
                'h2h_advantage': 0,
                'form_home': 1.5,
                'form_away': 1.5,
                'venue_advantage': 0.05,
                'league_tier': 1
            },
            'timestamp': datetime.now().isoformat()
        }

        return match_data

    def _save_for_ml_retraining(self, match_data: Dict):
        """
        Salva dados do jogo para retreino de ML
        Compatível com sistema automated_retraining.py

        Args:
            match_data: Dados formatados do jogo
        """
        import json

        # Criar diretório se não existir
        data_directory = 'retraining_data'
        os.makedirs(data_directory, exist_ok=True)

        # Salvar arquivo JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        match_id = match_data.get('match_id', 'unknown')
        filename = f"{data_directory}/match_result_{match_id}_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(match_data, f, indent=2, ensure_ascii=False)

        logger.info(f"💾 Dados salvos para ML: {filename}")


    def validate_historical_predictions(self) -> Dict:
        """
        🆕 Valida predictions que já têm jogos finalizados
        Usado para processar backlog de predictions não validadas

        Returns:
            Dict com estatísticas da validação
        """
        stats = {
            'predictions_validated': 0,
            'greens': 0,
            'reds': 0,
            'matches_processed': 0,
            'errors': []
        }

        # Buscar predictions não validadas com jogo já finalizado
        unvalidated_predictions = self.db.query(Prediction).join(Match).filter(
            Prediction.is_validated == False,
            Match.status == 'FT',
            Match.home_score.isnot(None),
            Match.away_score.isnot(None)
        ).all()

        logger.info(f"🔍 Encontradas {len(unvalidated_predictions)} predictions para validar")

        # Agrupar por match_id
        predictions_by_match = {}
        for pred in unvalidated_predictions:
            if pred.match_id not in predictions_by_match:
                predictions_by_match[pred.match_id] = []
            predictions_by_match[pred.match_id].append(pred)

        # Processar cada match
        for match_id, predictions in predictions_by_match.items():
            try:
                match = self.db.query(Match).filter(Match.id == match_id).first()
                if not match:
                    continue

                # Calcular GREEN/RED
                green_red_stats = self._calculate_green_red(match, predictions)
                stats['predictions_validated'] += green_red_stats['total']
                stats['greens'] += green_red_stats['greens']
                stats['reds'] += green_red_stats['reds']
                stats['matches_processed'] += 1

                # 🆕 FEEDBACK LOOP: Salvar dados para ML
                try:
                    match_data = self._prepare_match_data_for_ml(match, predictions)
                    self._save_for_ml_retraining(match_data)
                except Exception as ml_error:
                    logger.warning(f"⚠️ Erro ao salvar dados ML (match {match_id}): {ml_error}")

                logger.info(f"✅ Match {match_id}: {green_red_stats['greens']} greens, {green_red_stats['reds']} reds")

            except Exception as e:
                error_msg = f"Erro ao validar match {match_id}: {str(e)}"
                logger.error(error_msg)
                stats['errors'].append(error_msg)

        # Commit todas as alterações
        self.db.commit()

        logger.info(f"""
        📊 VALIDAÇÃO HISTÓRICA CONCLUÍDA:
        - Matches processados: {stats['matches_processed']}
        - Predictions validadas: {stats['predictions_validated']}
        - 🟢 GREENS: {stats['greens']}
        - 🔴 REDS: {stats['reds']}
        """)

        return stats


def run_results_update(db: Session):
    """
    Função helper para rodar atualização

    Args:
        db: Session do SQLAlchemy
    """
    updater = ResultsUpdater(db)
    return updater.update_all_results()


def run_historical_validation(db: Session):
    """
    🆕 Função helper para validar predictions históricas

    Args:
        db: Session do SQLAlchemy
    """
    updater = ResultsUpdater(db)
    return updater.validate_historical_predictions()
