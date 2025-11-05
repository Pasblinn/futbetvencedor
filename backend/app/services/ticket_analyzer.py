"""
🎫 TICKET ANALYZER SERVICE
Analisa bilhetes de usuários automaticamente quando jogos terminam
Atualiza bankroll e cria transações
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.user_ticket import (
    UserTicket,
    TicketSelection,
    TicketStatus,
    SelectionStatus
)
from app.models.match import Match
from app.models.user_bankroll import (
    UserBankroll,
    BankrollHistory,
    TransactionType
)

logger = logging.getLogger(__name__)


class TicketAnalyzer:
    """Analisa tickets e atualiza resultados automaticamente"""

    def __init__(self, db: Session):
        self.db = db

    def analyze_pending_tickets(self) -> Dict:
        """
        Analisa todos os tickets pendentes com jogos finalizados

        Returns:
            Estatísticas da análise
        """
        logger.info("🎯 Iniciando análise de tickets pendentes...")

        stats = {
            'analyzed': 0,
            'won': 0,
            'lost': 0,
            'still_pending': 0,
            'total_profit': 0.0,
            'total_loss': 0.0
        }

        # Buscar tickets pendentes
        pending_tickets = self.db.query(UserTicket).filter(
            UserTicket.status == TicketStatus.PENDING
        ).all()

        logger.info(f"📊 {len(pending_tickets)} tickets pendentes encontrados")

        for ticket in pending_tickets:
            try:
                result = self._analyze_ticket(ticket)
                if result:
                    stats['analyzed'] += 1
                    if result['status'] == TicketStatus.WON:
                        stats['won'] += 1
                        stats['total_profit'] += result['profit_loss']
                    elif result['status'] == TicketStatus.LOST:
                        stats['lost'] += 1
                        stats['total_loss'] += abs(result['profit_loss'])
                    else:
                        stats['still_pending'] += 1

            except Exception as e:
                logger.error(f"❌ Erro ao analisar ticket {ticket.id}: {e}")
                continue

        self.db.commit()

        # Log estatísticas
        if stats['analyzed'] > 0:
            logger.info(f"✅ Análise concluída:")
            logger.info(f"   🟢 Ganhos: {stats['won']} (R$ {stats['total_profit']:.2f})")
            logger.info(f"   🔴 Perdas: {stats['lost']} (R$ {stats['total_loss']:.2f})")
            logger.info(f"   ⏳ Ainda pendentes: {stats['still_pending']}")
        else:
            logger.info("ℹ️  Nenhum ticket novo para analisar")

        return stats

    def _analyze_ticket(self, ticket: UserTicket) -> Optional[Dict]:
        """
        Analisa um ticket específico

        Returns:
            Dict com status e resultado, ou None se ainda pendente
        """
        # Buscar todas as seleções do ticket
        selections = ticket.selections

        if not selections:
            logger.warning(f"⚠️  Ticket {ticket.id} sem seleções")
            return None

        # Verificar status de cada seleção
        all_finished = True
        all_won = True
        any_lost = False

        for selection in selections:
            # Buscar o jogo
            match = self.db.query(Match).filter(
                Match.id == selection.match_id
            ).first()

            if not match:
                logger.warning(f"⚠️  Match {selection.match_id} não encontrado")
                all_finished = False
                continue

            # Verificar se jogo terminou
            if match.status not in ['FT', 'FINISHED'] or match.home_score is None:
                all_finished = False
                continue

            # Analisar resultado da seleção
            selection_result = self._check_selection_result(
                selection,
                match.home_score,
                match.away_score
            )

            # Atualizar seleção
            selection.status = selection_result['status']
            selection.actual_outcome = selection_result['actual_outcome']
            selection.settled_at = datetime.utcnow()

            if selection_result['status'] == SelectionStatus.LOST:
                any_lost = True
                all_won = False
            elif selection_result['status'] != SelectionStatus.WON:
                all_won = False

        # Se nem todos os jogos terminaram, retornar None
        if not all_finished:
            return None

        # Determinar status do ticket
        if any_lost:
            # Se qualquer seleção perdeu, o ticket inteiro perde
            ticket_status = TicketStatus.LOST
            actual_return = 0.0
            profit_loss = -ticket.stake
        elif all_won:
            # Se todas ganharam, o ticket ganhou
            ticket_status = TicketStatus.WON
            actual_return = ticket.potential_return
            profit_loss = ticket.potential_return - ticket.stake
        else:
            # Ainda tem seleções pendentes (empates, jogos adiados, etc)
            return None

        # Atualizar ticket
        ticket.status = ticket_status
        ticket.actual_return = actual_return
        ticket.profit_loss = profit_loss
        ticket.settled_at = datetime.utcnow()

        # Atualizar bankroll do usuário
        self._update_user_bankroll(ticket)

        logger.info(
            f"{'🟢 GREEN' if ticket_status == TicketStatus.WON else '🔴 RED'} | "
            f"Ticket #{ticket.id} | "
            f"Stake: R$ {ticket.stake:.2f} | "
            f"{'Retorno' if ticket_status == TicketStatus.WON else 'Perda'}: R$ {abs(profit_loss):.2f}"
        )

        return {
            'status': ticket_status,
            'actual_return': actual_return,
            'profit_loss': profit_loss
        }

    def _check_selection_result(
        self,
        selection: TicketSelection,
        home_score: int,
        away_score: int
    ) -> Dict:
        """
        Verifica se uma seleção ganhou ou perdeu
        Suporta TODOS os 41 mercados do sistema

        Returns:
            Dict com status e outcome real
        """
        market = selection.market.upper()
        outcome = selection.outcome.upper()
        total_goals = home_score + away_score

        # === RESULTADO FINAL (HOME_WIN, DRAW, AWAY_WIN) ===
        if market in ['HOME_WIN', 'AWAY_WIN', 'DRAW']:
            if home_score > away_score:
                actual = 'HOME_WIN'
            elif home_score < away_score:
                actual = 'AWAY_WIN'
            else:
                actual = 'DRAW'

            # Mapear outcome para formato padronizado
            outcome_map = {
                'HOME': 'HOME_WIN', 'HOME_WIN': 'HOME_WIN', '1': 'HOME_WIN',
                'AWAY': 'AWAY_WIN', 'AWAY_WIN': 'AWAY_WIN', '2': 'AWAY_WIN',
                'DRAW': 'DRAW', 'X': 'DRAW',
                'YES': market  # Se market=DRAW e outcome=YES, quer empate
            }
            normalized_outcome = outcome_map.get(outcome, market)
            won = (normalized_outcome == actual)

            return {
                'status': SelectionStatus.WON if won else SelectionStatus.LOST,
                'actual_outcome': actual
            }

        # === 1X2 ===
        elif market == '1X2':
            if home_score > away_score:
                actual = '1'
            elif home_score < away_score:
                actual = '2'
            else:
                actual = 'X'

            outcome_map = {
                'HOME': '1', '1': '1',
                'AWAY': '2', '2': '2',
                'DRAW': 'X', 'X': 'X'
            }
            normalized_outcome = outcome_map.get(outcome, outcome)
            won = (normalized_outcome == actual)

            return {
                'status': SelectionStatus.WON if won else SelectionStatus.LOST,
                'actual_outcome': actual
            }

        # === DUPLA CHANCE (1X, 12, X2) ===
        elif market in ['1X', '12', 'X2']:
            home_win = home_score > away_score
            draw = home_score == away_score
            away_win = home_score < away_score

            won = False
            if market == '1X':
                won = home_win or draw
            elif market == '12':
                won = home_win or away_win
            elif market == 'X2':
                won = draw or away_win

            return {
                'status': SelectionStatus.WON if won else SelectionStatus.LOST,
                'actual_outcome': f"{'1' if home_win else ('X' if draw else '2')}"
            }

        # === BTTS (BOTH TEAMS TO SCORE) ===
        elif 'BTTS' in market:
            both_scored = (home_score > 0 and away_score > 0)
            actual = 'YES' if both_scored else 'NO'

            # BUG FIX (2025-10-29): Normalizar outcome para compatibilidade
            # Aceita tanto 'BTTS_YES'/'BTTS_NO' (antigo) quanto 'YES'/'NO' (novo)
            normalized_outcome = outcome.replace('BTTS_', '') if 'BTTS_' in outcome else outcome
            won = (normalized_outcome == actual)

            return {
                'status': SelectionStatus.WON if won else SelectionStatus.LOST,
                'actual_outcome': actual
            }

        # === OVER/UNDER ===
        elif 'OVER' in market or 'UNDER' in market:
            # Extrair threshold
            threshold = 2.5  # Default
            if '0.5' in market or '0_5' in market:
                threshold = 0.5
            elif '1.5' in market or '1_5' in market:
                threshold = 1.5
            elif '2.5' in market or '2_5' in market:
                threshold = 2.5
            elif '3.5' in market or '3_5' in market:
                threshold = 3.5
            elif '4.5' in market or '4_5' in market:
                threshold = 4.5

            actual = 'OVER' if total_goals > threshold else 'UNDER'

            # BUG FIX (2025-10-29): Normalizar outcome para compatibilidade
            # Aceita tanto 'OVER_2_5' (antigo) quanto 'OVER' (novo)
            normalized_outcome = outcome
            if 'OVER_' in outcome:
                normalized_outcome = 'OVER'
            elif 'UNDER_' in outcome:
                normalized_outcome = 'UNDER'
            won = (normalized_outcome == actual or outcome in market)

            return {
                'status': SelectionStatus.WON if won else SelectionStatus.LOST,
                'actual_outcome': f"{total_goals} goals"
            }

        # === EXACTLY X GOALS ===
        elif 'EXACTLY' in market:
            if '0' in market:
                won = total_goals == 0
            elif '1' in market:
                won = total_goals == 1
            elif '2' in market:
                won = total_goals == 2
            elif '3' in market:
                won = total_goals == 3
            else:
                won = False

            return {
                'status': SelectionStatus.WON if won else SelectionStatus.LOST,
                'actual_outcome': f"{total_goals} goals"
            }

        # === 4+ GOALS ===
        elif '4_OR_MORE' in market or '4+' in market:
            won = total_goals >= 4
            return {
                'status': SelectionStatus.WON if won else SelectionStatus.LOST,
                'actual_outcome': f"{total_goals} goals"
            }

        # === ODD/EVEN GOALS ===
        elif 'ODD' in market or 'EVEN' in market:
            is_odd = (total_goals % 2 == 1)
            actual = 'ODD' if is_odd else 'EVEN'

            # BUG FIX (2025-10-29): Normalizar outcome para compatibilidade
            # Aceita tanto 'ODD_GOALS' (antigo) quanto 'ODD' (novo)
            normalized_outcome = outcome.replace('_GOALS', '') if '_GOALS' in outcome else outcome
            won = (normalized_outcome == actual or outcome in market)

            return {
                'status': SelectionStatus.WON if won else SelectionStatus.LOST,
                'actual_outcome': actual
            }

        # === FIRST GOAL (NO_GOAL, HOME, AWAY) ===
        elif 'FIRST_GOAL' in market or 'NO_GOAL' in market:
            if total_goals == 0:
                actual = 'NO_GOAL'
            elif home_score > 0 and away_score == 0:
                actual = 'FIRST_GOAL_HOME'
            elif away_score > 0 and home_score == 0:
                actual = 'FIRST_GOAL_AWAY'
            else:
                # Ambos marcaram, não temos info de quem marcou primeiro
                # Considerar empate técnico ou void
                actual = 'UNKNOWN'

            won = (outcome in actual or actual in outcome)
            return {
                'status': SelectionStatus.WON if won else SelectionStatus.VOID,
                'actual_outcome': actual
            }

        # === CLEAN SHEET (HOME/AWAY) ===
        elif 'CLEAN_SHEET' in market:
            if 'HOME' in market:
                actual_won = away_score == 0
                actual = 'YES' if away_score == 0 else 'NO'
            elif 'AWAY' in market:
                actual_won = home_score == 0
                actual = 'YES' if home_score == 0 else 'NO'
            else:
                actual_won = False
                actual = 'UNKNOWN'

            # BUG FIX (2025-10-29): Normalizar outcome para compatibilidade
            # Aceita tanto 'HOME_CLEAN_SHEET' ou 'AWAY_CLEAN_SHEET' (market) quanto 'YES' (outcome)
            # Se outcome é o próprio market, assume que prevê YES
            if outcome == market:
                normalized_outcome = 'YES'
            else:
                normalized_outcome = outcome

            won = (normalized_outcome == actual or actual_won)

            return {
                'status': SelectionStatus.WON if won else SelectionStatus.LOST,
                'actual_outcome': actual
            }

        # === SCORE EXATO (0_0, 1_0, 0_1, 1_1, 2_0, etc) ===
        elif 'SCORE_' in market:
            # Extrair placar do market (ex: SCORE_2_1 -> 2x1)
            parts = market.replace('SCORE_', '').split('_')
            if len(parts) == 2:
                try:
                    expected_home = int(parts[0])
                    expected_away = int(parts[1])
                    won = (home_score == expected_home and away_score == expected_away)

                    return {
                        'status': SelectionStatus.WON if won else SelectionStatus.LOST,
                        'actual_outcome': f"{home_score}x{away_score}"
                    }
                except ValueError:
                    pass

        # === DEFAULT: MERCADO NÃO RECONHECIDO ===
        logger.warning(f"⚠️  Mercado não implementado: {market}")
        return {
            'status': SelectionStatus.VOID,
            'actual_outcome': f'Market not supported: {market}'
        }

    def _update_user_bankroll(self, ticket: UserTicket):
        """
        Atualiza bankroll do usuário após resultado do ticket
        """
        # Buscar bankroll do usuário
        bankroll = self.db.query(UserBankroll).filter(
            UserBankroll.user_id == ticket.user_id
        ).first()

        if not bankroll:
            logger.error(f"❌ Bankroll não encontrado para usuário {ticket.user_id}")
            return

        # Atualizar saldo
        old_balance = bankroll.current_bankroll

        # Se ganhou, adicionar RETORNO TOTAL (stake já foi debitado quando apostou)
        # Se perdeu, não adicionar nada (stake já foi debitado)
        if ticket.status == TicketStatus.WON:
            bankroll.current_bankroll += ticket.actual_return
        # Se perdeu, profit_loss já é negativo e stake já foi debitado, então não mexe no saldo

        # Atualizar estatísticas
        bankroll.total_bets += 1
        bankroll.total_staked += ticket.stake
        bankroll.total_return += ticket.actual_return

        if ticket.status == TicketStatus.WON:
            bankroll.greens += 1
            bankroll.total_profit += ticket.profit_loss
        else:
            bankroll.reds += 1
            bankroll.total_profit += ticket.profit_loss  # profit_loss é negativo em perdas

        # Atualizar ROI
        if bankroll.total_staked > 0:
            bankroll.roi = (bankroll.total_profit / bankroll.total_staked) * 100

        # Atualizar win_rate
        total_settled = bankroll.greens + bankroll.reds
        if total_settled > 0:
            bankroll.win_rate = (bankroll.greens / total_settled) * 100

        # Criar transação
        # amount deve ser o RETORNO se ganhou (não o lucro), pois stake já foi debitado
        transaction_amount = ticket.actual_return if ticket.status == TicketStatus.WON else 0

        transaction = BankrollHistory(
            user_id=ticket.user_id,
            transaction_type=(
                TransactionType.WIN if ticket.status == TicketStatus.WON
                else TransactionType.LOSS
            ),
            amount=transaction_amount,
            balance_before=old_balance,
            balance_after=bankroll.current_bankroll,
            description=(
                f"🟢 Ticket #{ticket.id} ganho (stake R$ {ticket.stake:.2f} × {ticket.total_odds:.2f})"
                if ticket.status == TicketStatus.WON
                else f"🔴 Ticket #{ticket.id} perdido (stake R$ {ticket.stake:.2f})"
            ),
            metadata={
                'ticket_id': ticket.id,
                'stake': float(ticket.stake),
                'odds': float(ticket.total_odds),
                'potential_return': float(ticket.potential_return),
                'actual_return': float(ticket.actual_return)
            }
        )

        self.db.add(transaction)

        logger.info(
            f"💰 Bankroll atualizado | Usuário {ticket.user_id} | "
            f"Saldo: R$ {old_balance:.2f} → R$ {bankroll.current_bankroll:.2f}"
        )


def analyze_all_tickets(db: Session) -> Dict:
    """
    Função helper para analisar todos os tickets
    Pode ser chamada por schedulers ou endpoints
    """
    analyzer = TicketAnalyzer(db)
    return analyzer.analyze_pending_tickets()
