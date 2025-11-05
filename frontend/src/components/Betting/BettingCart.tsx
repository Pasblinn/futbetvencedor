import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ShoppingCart, X, TrendingUp, DollarSign, Trash2, CheckCircle, Loader2 } from 'lucide-react';
import { formatMarketForTicket, getMarketCategory } from '../../utils/marketTranslations';
import { useAuth } from '../../contexts/AuthContext';
import { notificationService } from '../../services/notifications';
import { useNavigate } from 'react-router-dom';

interface Match {
  id: string;
  homeTeam: string;
  awayTeam: string;
  league: string;
  date: string;
  time: string;
  odds: { home: number; draw: number; away: number };
  confidence: number;
  value: number;
  recommendation: "home" | "draw" | "away";
}

interface TicketItem {
  match: Match;
  selection: "home" | "draw" | "away";
  stake: number;
  kellyPercentage: number;
  market: string; // Unique ID (ex: "2827-HOME_WIN")
  marketId?: string; // 🔥 NOVO: ID do mercado (ex: "HOME_WIN", "OVER_2_5")
}

interface BettingCartProps {
  selectedBets: TicketItem[];
  onRemoveBet: (index: number) => void;
  onPlaceBet: (stake: number) => void;
  onClearAll: () => void;
}

export const BettingCart: React.FC<BettingCartProps> = ({
  selectedBets,
  onRemoveBet,
  onPlaceBet,
  onClearAll,
}) => {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [stake, setStake] = useState<number>(10);
  const [isExpanded, setIsExpanded] = useState(true);
  const [isPlacingBet, setIsPlacingBet] = useState(false);

  // Calculate total odds (multiply all odds together for accumulator)
  const totalOdds = selectedBets.reduce((acc, bet) => acc * bet.match.odds[bet.selection], 1);

  // Calculate potential return
  const potentialReturn = stake * totalOdds;

  // Calculate potential profit
  const potentialProfit = potentialReturn - stake;

  const handlePlaceBet = async () => {
    if (selectedBets.length === 0) {
      notificationService.addNotification({
        type: 'warning',
        title: 'Bilhete Vazio',
        message: 'Adicione pelo menos uma aposta ao bilhete',
      });
      return;
    }
    if (stake <= 0) {
      notificationService.addNotification({
        type: 'warning',
        title: 'Valor Inválido',
        message: 'Digite um valor de aposta válido',
      });
      return;
    }
    if (!token) {
      notificationService.addNotification({
        type: 'error',
        title: 'Autenticação Necessária',
        message: 'Faça login para criar apostas',
      });
      return;
    }

    setIsPlacingBet(true);

    try {
      // Preparar seleções para o backend
      const selections = selectedBets.map(bet => ({
        match_id: parseInt(bet.match.id),
        market: bet.marketId || bet.market.split('-')[1] || 'HOME_WIN',
        outcome: bet.selection.toUpperCase(),
        odd: bet.match.odds[bet.selection]
      }));

      // Criar bilhete via API
      const response = await fetch('http://localhost:8000/api/v1/user/tickets', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          selections: selections,
          stake: stake,
          notes: `Bilhete com ${selectedBets.length} seleção(ões)`,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Erro ao criar aposta');
      }

      const data = await response.json();

      notificationService.addNotification({
        type: 'success',
        title: 'Aposta Criada! 🎯',
        message: `Bilhete #${data.id} criado com sucesso! Valor: R$ ${stake.toFixed(2)}`,
      });

      // Limpar bilhete após sucesso
      onClearAll();

      // Redirecionar para página de bilhetes
      setTimeout(() => {
        navigate('/tickets');
      }, 1500);
    } catch (error: any) {
      console.error('Erro ao criar aposta:', error);
      notificationService.addNotification({
        type: 'error',
        title: 'Erro ao Criar Aposta',
        message: error.message || 'Erro ao criar aposta. Verifique sua banca e tente novamente.',
      });
    } finally {
      setIsPlacingBet(false);
    }
  };

  return (
    <div className="fixed right-4 top-20 w-80 z-40">
      <motion.div
        initial={{ x: 100, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl shadow-2xl border border-slate-700 overflow-hidden"
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-green-600 to-emerald-600 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShoppingCart className="w-5 h-5 text-white" />
              <h3 className="text-white font-bold">Bilhete</h3>
              <span className="bg-white/20 text-white text-xs font-bold px-2 py-0.5 rounded-full">
                {selectedBets.length}
              </span>
            </div>
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-white hover:bg-white/10 p-1 rounded transition-colors"
            >
              <TrendingUp className={`w-4 h-4 transition-transform ${!isExpanded ? 'rotate-180' : ''}`} />
            </button>
          </div>
        </div>

        <AnimatePresence>
          {isExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden"
            >
              {/* Bets List */}
              <div className="p-4 space-y-3 max-h-96 overflow-y-auto custom-scrollbar">
                {selectedBets.length === 0 ? (
                  <div className="text-center py-8 text-slate-400">
                    <ShoppingCart className="w-12 h-12 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">Seu bilhete está vazio</p>
                    <p className="text-xs mt-1">Adicione apostas para começar</p>
                  </div>
                ) : (
                  <>
                    {selectedBets.map((bet, index) => {
                      const selectedOdds = bet.match.odds[bet.selection];

                      // 🔥 NOVO: Determinar o marketId baseado na seleção
                      let marketId = bet.marketId;
                      if (!marketId) {
                        // Fallback: mapear selection antiga para marketId
                        if (bet.selection === 'home') marketId = 'HOME_WIN';
                        else if (bet.selection === 'draw') marketId = 'DRAW';
                        else if (bet.selection === 'away') marketId = 'AWAY_WIN';
                      }

                      // 🔥 Traduzir o mercado para português estilo bet365
                      const marketName = marketId
                        ? formatMarketForTicket(marketId, bet.match.homeTeam, bet.match.awayTeam)
                        : 'Resultado Final';

                      const marketCategory = marketId ? getMarketCategory(marketId) : 'Resultado Final (1X2)';

                      return (
                        <motion.div
                          key={bet.market}
                          initial={{ opacity: 0, y: -10 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, x: 20 }}
                          className="bg-slate-800/50 rounded-lg p-3 border border-slate-700"
                        >
                          <div className="flex items-start justify-between mb-2">
                            <div className="flex-1 min-w-0">
                              <div className="text-white text-sm font-semibold truncate">
                                {bet.match.homeTeam} vs {bet.match.awayTeam}
                              </div>
                              <div className="text-xs text-slate-400 truncate">
                                {bet.match.league}
                              </div>
                            </div>
                            <button
                              onClick={() => onRemoveBet(index)}
                              className="text-red-400 hover:text-red-300 hover:bg-red-500/10 p-1 rounded transition-colors ml-2"
                            >
                              <X className="w-4 h-4" />
                            </button>
                          </div>

                          <div className="flex items-center justify-between">
                            <div className="flex-1 min-w-0">
                              <div className="text-xs text-slate-500 truncate">{marketCategory}</div>
                              <div className="text-sm text-blue-400 font-semibold truncate">{marketName}</div>
                            </div>
                            <div className="bg-green-500/20 text-green-400 px-2 py-1 rounded font-bold text-sm ml-2">
                              {selectedOdds.toFixed(2)}
                            </div>
                          </div>
                        </motion.div>
                      );
                    })}

                    {/* Clear All Button */}
                    {selectedBets.length > 0 && (
                      <button
                        onClick={onClearAll}
                        className="w-full text-red-400 hover:text-red-300 text-xs py-2 hover:bg-red-500/10 rounded transition-colors flex items-center justify-center gap-1"
                      >
                        <Trash2 className="w-3 h-3" />
                        Limpar Bilhete
                      </button>
                    )}
                  </>
                )}
              </div>

              {/* Stake Input & Summary */}
              {selectedBets.length > 0 && (
                <>
                  <div className="border-t border-slate-700 p-4 space-y-3">
                    {/* Stake Input */}
                    <div>
                      <label className="block text-slate-300 text-xs font-semibold mb-2">
                        Valor da Aposta (R$)
                      </label>
                      <div className="relative">
                        <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                        <input
                          type="number"
                          min="1"
                          step="1"
                          value={stake}
                          onChange={(e) => setStake(Number(e.target.value))}
                          className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-10 pr-4 py-2 text-white focus:ring-2 focus:ring-green-500 focus:border-green-500"
                          placeholder="10.00"
                        />
                      </div>
                    </div>

                    {/* Quick Stake Buttons */}
                    <div className="flex gap-2">
                      {[10, 20, 50, 100].map((amount) => (
                        <button
                          key={amount}
                          onClick={() => setStake(amount)}
                          className="flex-1 bg-slate-700 hover:bg-slate-600 text-white text-xs py-1.5 rounded transition-colors"
                        >
                          R$ {amount}
                        </button>
                      ))}
                    </div>

                    {/* Summary */}
                    <div className="bg-slate-800/50 rounded-lg p-3 space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-400">Total de Apostas:</span>
                        <span className="text-white font-semibold">{selectedBets.length}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-400">Odd Total:</span>
                        <span className="text-blue-400 font-bold">{totalOdds.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-400">Valor Apostado:</span>
                        <span className="text-white font-semibold">R$ {stake.toFixed(2)}</span>
                      </div>
                      <div className="border-t border-slate-700 pt-2 mt-2">
                        <div className="flex justify-between">
                          <span className="text-slate-300 font-semibold">Retorno Potencial:</span>
                          <span className="text-green-400 font-bold text-lg">
                            R$ {potentialReturn.toFixed(2)}
                          </span>
                        </div>
                        <div className="flex justify-between text-xs mt-1">
                          <span className="text-slate-400">Lucro:</span>
                          <span className="text-green-400">+R$ {potentialProfit.toFixed(2)}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Place Bet Button */}
                  <div className="p-4 pt-0">
                    <button
                      onClick={handlePlaceBet}
                      disabled={isPlacingBet}
                      className="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 disabled:from-gray-600 disabled:to-gray-700 disabled:cursor-not-allowed text-white font-bold py-3 rounded-lg transition-all shadow-lg hover:shadow-green-500/20 flex items-center justify-center gap-2"
                    >
                      {isPlacingBet ? (
                        <>
                          <Loader2 className="w-5 h-5 animate-spin" />
                          Criando Aposta...
                        </>
                      ) : (
                        <>
                          <CheckCircle className="w-5 h-5" />
                          Fazer Aposta
                        </>
                      )}
                    </button>
                  </div>
                </>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
};
