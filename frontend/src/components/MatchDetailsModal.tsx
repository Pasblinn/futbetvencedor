import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Target, TrendingUp, Plus, Trash2, Check } from 'lucide-react';

interface Market {
  bookmaker: string;
  home?: number;
  draw?: number;
  away?: number;
  over?: number;
  under?: number;
  yes?: number;
  no?: number;
  line?: number;
  timestamp?: string;
}

interface MatchData {
  match_id: number;
  home_team: { name: string };
  away_team: { name: string };
  status: string;
  league: string;
  time: string;
  confidence: number;
  odds: {
    home: number;
    draw: number;
    away: number;
  };
  prediction: string;
}

interface SelectedBet {
  market: string;
  selection: string;
  odd: number;
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  match: MatchData | null;
}

const MatchDetailsModal: React.FC<Props> = ({ isOpen, onClose, match }) => {
  const [selectedBets, setSelectedBets] = useState<SelectedBet[]>([]);
  const [stake, setStake] = useState<number>(10);

  if (!match) return null;

  const addBet = (market: string, selection: string, odd: number) => {
    const existingBet = selectedBets.find(b => b.market === market);
    if (existingBet) {
      // Atualizar seleção no mesmo mercado
      setSelectedBets(selectedBets.map(b =>
        b.market === market ? { market, selection, odd } : b
      ));
    } else {
      setSelectedBets([...selectedBets, { market, selection, odd }]);
    }
  };

  const removeBet = (market: string) => {
    setSelectedBets(selectedBets.filter(b => b.market !== market));
  };

  const totalOdds = selectedBets.reduce((acc, bet) => acc * bet.odd, 1);
  const potentialWin = stake * totalOdds;

  const createTicket = () => {
    // TODO: Enviar bilhete para backend
    console.log('Bilhete criado:', {
      match_id: match.match_id,
      bets: selectedBets,
      stake,
      total_odds: totalOdds,
      potential_win: potentialWin
    });
    alert('Bilhete criado com sucesso! (será salvo no BD)');
    onClose();
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Overlay */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/50 z-40"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
          >
            <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
              {/* Header */}
              <div className="bg-gradient-to-r from-primary-600 to-primary-700 p-6 text-white">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-2xl font-bold mb-2">
                      {match.home_team.name} vs {match.away_team.name}
                    </h2>
                    <div className="flex items-center gap-4 text-sm text-primary-100">
                      <span>{match.league}</span>
                      <span>•</span>
                      <span>{new Date(match.time).toLocaleString()}</span>
                      <span>•</span>
                      <span className="flex items-center gap-1">
                        <Target className="w-4 h-4" />
                        Confidence: {match.confidence}%
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={onClose}
                    className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                  >
                    <X className="w-6 h-6" />
                  </button>
                </div>
              </div>

              {/* Content */}
              <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
                <div className="grid grid-cols-2 gap-6">
                  {/* Left Column - Mercados Disponíveis */}
                  <div>
                    <h3 className="text-lg font-semibold text-slate-900 mb-4">Mercados Disponíveis</h3>

                    {/* 1X2 */}
                    <div className="mb-4">
                      <h4 className="text-sm font-medium text-slate-700 mb-2">Resultado Final (1X2)</h4>
                      <div className="grid grid-cols-3 gap-2">
                        <button
                          onClick={() => addBet('1X2', 'Casa', match.odds.home)}
                          className={`p-3 rounded-lg border-2 transition-all ${
                            selectedBets.find(b => b.market === '1X2' && b.selection === 'Casa')
                              ? 'border-primary-600 bg-primary-50'
                              : 'border-slate-200 hover:border-primary-300'
                          }`}
                        >
                          <div className="text-xs text-slate-600">Casa</div>
                          <div className="text-lg font-bold text-slate-900">{match.odds.home.toFixed(2)}</div>
                        </button>
                        <button
                          onClick={() => addBet('1X2', 'Empate', match.odds.draw)}
                          className={`p-3 rounded-lg border-2 transition-all ${
                            selectedBets.find(b => b.market === '1X2' && b.selection === 'Empate')
                              ? 'border-primary-600 bg-primary-50'
                              : 'border-slate-200 hover:border-primary-300'
                          }`}
                        >
                          <div className="text-xs text-slate-600">Empate</div>
                          <div className="text-lg font-bold text-slate-900">{match.odds.draw.toFixed(2)}</div>
                        </button>
                        <button
                          onClick={() => addBet('1X2', 'Fora', match.odds.away)}
                          className={`p-3 rounded-lg border-2 transition-all ${
                            selectedBets.find(b => b.market === '1X2' && b.selection === 'Fora')
                              ? 'border-primary-600 bg-primary-50'
                              : 'border-slate-200 hover:border-primary-300'
                          }`}
                        >
                          <div className="text-xs text-slate-600">Fora</div>
                          <div className="text-lg font-bold text-slate-900">{match.odds.away.toFixed(2)}</div>
                        </button>
                      </div>
                    </div>

                    {/* Placeholder para outros mercados */}
                    <div className="bg-slate-50 rounded-lg p-4 text-center text-slate-600">
                      <p className="text-sm">Outros mercados serão carregados da API</p>
                      <p className="text-xs text-slate-500 mt-1">(Over/Under, BTTS, Corners, etc.)</p>
                    </div>
                  </div>

                  {/* Right Column - Bilhete */}
                  <div>
                    <h3 className="text-lg font-semibold text-slate-900 mb-4">Seu Bilhete</h3>

                    <div className="bg-gradient-to-br from-primary-50 to-blue-50 rounded-xl p-4 border-2 border-primary-200">
                      {selectedBets.length === 0 ? (
                        <div className="text-center text-slate-500 py-8">
                          <Plus className="w-12 h-12 mx-auto mb-2 text-slate-400" />
                          <p className="text-sm">Selecione mercados para criar seu bilhete</p>
                        </div>
                      ) : (
                        <div className="space-y-3">
                          {selectedBets.map((bet, index) => (
                            <div key={index} className="bg-white rounded-lg p-3 flex items-center justify-between">
                              <div className="flex-1">
                                <div className="text-xs text-slate-600">{bet.market}</div>
                                <div className="text-sm font-semibold text-slate-900">{bet.selection}</div>
                              </div>
                              <div className="flex items-center gap-2">
                                <span className="text-lg font-bold text-primary-600">{bet.odd.toFixed(2)}</span>
                                <button
                                  onClick={() => removeBet(bet.market)}
                                  className="p-1 hover:bg-red-50 rounded transition-colors"
                                >
                                  <Trash2 className="w-4 h-4 text-red-600" />
                                </button>
                              </div>
                            </div>
                          ))}

                          <div className="border-t-2 border-primary-200 pt-3 mt-3">
                            <div className="mb-3">
                              <label className="text-sm text-slate-700 font-medium mb-1 block">Valor da Aposta</label>
                              <input
                                type="number"
                                value={stake}
                                onChange={(e) => setStake(Number(e.target.value))}
                                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                                min="1"
                              />
                            </div>

                            <div className="space-y-2 text-sm">
                              <div className="flex justify-between">
                                <span className="text-slate-600">Odd Total:</span>
                                <span className="font-bold text-primary-600">{totalOdds.toFixed(2)}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-slate-600">Aposta:</span>
                                <span className="font-semibold">R$ {stake.toFixed(2)}</span>
                              </div>
                              <div className="flex justify-between text-lg border-t border-primary-200 pt-2">
                                <span className="text-slate-900 font-bold">Retorno Potencial:</span>
                                <span className="font-bold text-green-600">R$ {potentialWin.toFixed(2)}</span>
                              </div>
                            </div>

                            <button
                              onClick={createTicket}
                              className="w-full mt-4 px-4 py-3 bg-gradient-to-r from-green-600 to-green-700 text-white rounded-lg hover:from-green-700 hover:to-green-800 transition-all font-semibold flex items-center justify-center gap-2 shadow-lg"
                            >
                              <Check className="w-5 h-5" />
                              Criar Bilhete Manual
                            </button>
                          </div>
                        </div>
                      )}
                    </div>

                    <div className="mt-4 bg-blue-50 rounded-lg p-3 border border-blue-200">
                      <div className="flex items-start gap-2">
                        <TrendingUp className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                        <div className="text-xs text-blue-900">
                          <p className="font-semibold mb-1">Bilhetes Manuais para ML</p>
                          <p className="text-blue-700">
                            Seus bilhetes manuais serão salvos no banco de dados e utilizados para treinar a ML,
                            ajudando a identificar padrões de sucesso!
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default MatchDetailsModal;
