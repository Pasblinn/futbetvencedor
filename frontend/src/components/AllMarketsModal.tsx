import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, TrendingUp, DollarSign, BarChart3, Activity, Target } from 'lucide-react';
import { useAllMarkets } from '../hooks/useAllMarkets';

interface AllMarketsModalProps {
  isOpen: boolean;
  onClose: () => void;
  matchId: number;
  matchInfo?: {
    homeTeam: string;
    awayTeam: string;
    league: string;
    matchDate: string;
  };
}

export const AllMarketsModal: React.FC<AllMarketsModalProps> = ({
  isOpen,
  onClose,
  matchId,
  matchInfo,
}) => {
  // React Query hook com cache inteligente
  const { data, isLoading, isError, error, refetch } = useAllMarkets({
    matchId: matchId || null,
    lastNGames: 10,
    enabled: isOpen && !!matchId, // Só busca quando modal está aberto
  });

  if (!isOpen) return null;

  // ✅ Helper function para formatar valores numéricos com segurança
  const safeToFixed = (value: any, decimals: number = 2, fallback: string = '0.00'): string => {
    if (value === null || value === undefined || isNaN(Number(value))) {
      return fallback;
    }
    const numValue = Number(value);
    if (!isFinite(numValue) || numValue === 0) {
      return fallback;
    }
    return numValue.toFixed(decimals);
  };

  const renderMarketCard = (
    label: string,
    probability: number,
    fairOdds: number,
    marketOdds: number | undefined,
    isValueBet: boolean = false
  ) => {
    const probPercentage = safeToFixed(probability * 100, 1, '0.0');
    const hasMarketOdds = marketOdds !== undefined && marketOdds > 0;

    // Calcular edge se ambas odds disponíveis
    let edge = null;
    if (hasMarketOdds && fairOdds > 0) {
      edge = ((marketOdds / fairOdds - 1) * 100);
    }

    return (
      <div
        className={`
          relative p-4 rounded-lg transition-all
          ${isValueBet
            ? 'bg-gradient-to-br from-green-500/20 to-green-600/20 border-2 border-green-500 shadow-lg shadow-green-500/20'
            : 'bg-gray-800/50 border border-gray-700 hover:bg-gray-800/70'
          }
        `}
      >
        {isValueBet && (
          <div className="absolute -top-2 -right-2 bg-green-500 text-white text-xs font-bold px-2 py-1 rounded-full flex items-center gap-1">
            <TrendingUp size={12} />
            VALUE
          </div>
        )}

        <div className="flex justify-between items-start mb-2">
          <span className="text-sm text-gray-300 font-medium">{label}</span>
          <span className="text-xs text-gray-500">{probPercentage}%</span>
        </div>

        <div className="flex items-end justify-between">
          <div className="flex-1">
            <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${
                  isValueBet ? 'bg-green-500' : 'bg-blue-500'
                }`}
                style={{ width: `${probPercentage}%` }}
              />
            </div>
          </div>

          <div className="ml-3 text-right space-y-1">
            {/* ODD REAL (Principal) */}
            {hasMarketOdds && (
              <div>
                <div className={`text-xl font-bold ${isValueBet ? 'text-green-400' : 'text-blue-400'}`}>
                  {safeToFixed(marketOdds, 2, '-.--')}
                </div>
                <div className="text-xs text-gray-400">Odd Real</div>
              </div>
            )}

            {/* ODD JUSTA (Secundária) */}
            <div>
              <div className={`${hasMarketOdds ? 'text-sm' : 'text-lg font-bold'} ${hasMarketOdds ? 'text-gray-400' : isValueBet ? 'text-green-400' : 'text-blue-400'}`}>
                {safeToFixed(fairOdds, 2, '-.--')}
              </div>
              <div className="text-xs text-gray-500">Odd Justa</div>
            </div>

            {/* EDGE (se disponível) */}
            {edge !== null && (
              <div className={`text-xs font-semibold ${edge > 0 ? 'text-green-400' : 'text-red-400'}`}>
                {edge > 0 ? '+' : ''}{safeToFixed(edge, 1)}% edge
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  const renderCategory = (title: string, icon: React.ReactNode, markets: Array<{label: string, key: string}>) => {
    if (!data) return null;

    // ✅ Filter markets that have BOTH probability AND fair_odds
    const categoryMarkets = markets.filter(m =>
      data.probabilities[m.key] !== undefined &&
      data.fair_odds[m.key] !== undefined
    );
    if (categoryMarkets.length === 0) return null;

    const valueMarkets = new Set(data.value_bets?.map(vb => vb.market) || []);

    return (
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-4">
          <div className="text-blue-400">{icon}</div>
          <h3 className="text-lg font-bold text-white">{title}</h3>
          <span className="text-xs text-gray-500">({categoryMarkets.length} mercados)</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {categoryMarkets.map(market => {
            const prob = data.probabilities[market.key];
            const fairOdds = data.fair_odds[market.key];
            const marketOdds = data.market_odds?.[market.key] || undefined;
            const isValue = valueMarkets.has(market.key);

            return (
              <div key={market.key}>
                {renderMarketCard(market.label, prob, fairOdds, marketOdds, isValue)}
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50"
          />

          {/* Modal */}
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl shadow-2xl max-w-7xl w-full max-h-[90vh] overflow-hidden pointer-events-auto border border-gray-700"
            >
              {/* Header */}
              <div className="bg-gradient-to-r from-blue-600 to-purple-600 px-6 py-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <BarChart3 className="text-white" size={24} />
                  <div>
                    <h2 className="text-xl font-bold text-white">
                      {data ? data.match_info.home_team : matchInfo?.homeTeam || 'Carregando...'} vs{' '}
                      {data ? data.match_info.away_team : matchInfo?.awayTeam || '...'}
                    </h2>
                    <p className="text-sm text-blue-100">
                      {data ? `${data.total_markets} mercados disponíveis` : 'Carregando mercados...'}
                    </p>
                  </div>
                </div>

                <button
                  onClick={onClose}
                  className="text-white hover:bg-white/20 p-2 rounded-lg transition-colors"
                >
                  <X size={24} />
                </button>
              </div>

              {/* Content */}
              <div className="p-6 overflow-y-auto max-h-[calc(90vh-80px)] custom-scrollbar">
                {isLoading && (
                  <div className="flex flex-col items-center justify-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mb-4"></div>
                    <p className="text-gray-400">Carregando mercados...</p>
                  </div>
                )}

                {isError && (
                  <div className="bg-red-500/10 border border-red-500 rounded-lg p-4 text-center">
                    <p className="text-red-400 font-medium">Erro ao carregar mercados</p>
                    <p className="text-gray-400 text-sm mt-1">{error?.message || 'Erro desconhecido'}</p>
                    <button
                      onClick={() => refetch()}
                      className="mt-3 px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors"
                    >
                      Tentar Novamente
                    </button>
                  </div>
                )}

                {data && !isLoading && !isError && (
                  <>
                    {/* Stats Summary */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6 p-4 bg-gray-800/50 rounded-lg border border-gray-700">
                      <div>
                        <div className="text-xs text-gray-500 mb-1">Gols Médios (Casa)</div>
                        <div className="text-lg font-bold text-blue-400">
                          {safeToFixed(data.team_stats.home.goals_scored_avg, 2)}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-gray-500 mb-1">Gols Médios (Fora)</div>
                        <div className="text-lg font-bold text-purple-400">
                          {safeToFixed(data.team_stats.away.goals_scored_avg, 2)}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-gray-500 mb-1">Parâmetros Poisson</div>
                        <div className="text-sm text-gray-300">
                          λ<sub>casa</sub>: {safeToFixed(data.poisson_params.lambda_home, 2)} |{' '}
                          λ<sub>fora</sub>: {safeToFixed(data.poisson_params.lambda_away, 2)}
                        </div>
                      </div>
                    </div>

                    {/* Value Bets Alert */}
                    {data.value_bets && data.value_bets.length > 0 && (
                      <div className="bg-gradient-to-r from-green-500/20 to-emerald-500/20 border border-green-500 rounded-lg p-4 mb-6">
                        <div className="flex items-center gap-2 mb-2">
                          <DollarSign className="text-green-400" size={20} />
                          <span className="font-bold text-green-400">
                            {data.value_bets.length} Value Bet{data.value_bets.length > 1 ? 's' : ''} Identificada{data.value_bets.length > 1 ? 's' : ''}!
                          </span>
                        </div>
                        <p className="text-sm text-gray-300">
                          Mercados destacados em verde possuem vantagem matemática
                        </p>
                      </div>
                    )}

                    {/* Markets by Category */}
                    {renderCategory('Resultado Final', <Target size={20} />, [
                      { label: 'Vitória Casa', key: 'HOME_WIN' },
                      { label: 'Empate', key: 'DRAW' },
                      { label: 'Vitória Fora', key: 'AWAY_WIN' },
                    ])}

                    {renderCategory('Dupla Chance', <Activity size={20} />, [
                      { label: '1X (Casa ou Empate)', key: 'DOUBLE_CHANCE_1X' },
                      { label: '12 (Casa ou Fora)', key: 'DOUBLE_CHANCE_12' },
                      { label: 'X2 (Empate ou Fora)', key: 'DOUBLE_CHANCE_X2' },
                    ])}

                    {renderCategory('Ambas Marcam (BTTS)', <Target size={20} />, [
                      { label: 'Sim', key: 'BTTS_YES' },
                      { label: 'Não', key: 'BTTS_NO' },
                    ])}

                    {renderCategory('Total de Gols - Over', <TrendingUp size={20} />, [
                      { label: 'Over 0.5', key: 'OVER_0_5' },
                      { label: 'Over 1.5', key: 'OVER_1_5' },
                      { label: 'Over 2.5', key: 'OVER_2_5' },
                      { label: 'Over 3.5', key: 'OVER_3_5' },
                      { label: 'Over 4.5', key: 'OVER_4_5' },
                      { label: 'Over 5.5', key: 'OVER_5_5' },
                    ])}

                    {renderCategory('Total de Gols - Under', <TrendingUp size={20} />, [
                      { label: 'Under 0.5', key: 'UNDER_0_5' },
                      { label: 'Under 1.5', key: 'UNDER_1_5' },
                      { label: 'Under 2.5', key: 'UNDER_2_5' },
                      { label: 'Under 3.5', key: 'UNDER_3_5' },
                      { label: 'Under 4.5', key: 'UNDER_4_5' },
                      { label: 'Under 5.5', key: 'UNDER_5_5' },
                    ])}

                    {renderCategory('Gols Exatos', <BarChart3 size={20} />, [
                      { label: '0 Gols', key: 'EXACT_GOALS_0' },
                      { label: '1 Gol', key: 'EXACT_GOALS_1' },
                      { label: '2 Gols', key: 'EXACT_GOALS_2' },
                      { label: '3 Gols', key: 'EXACT_GOALS_3' },
                      { label: '4+ Gols', key: 'EXACT_GOALS_4_PLUS' },
                    ])}

                    {renderCategory('Par/Ímpar', <Activity size={20} />, [
                      { label: 'Par', key: 'ODD_EVEN_EVEN' },
                      { label: 'Ímpar', key: 'ODD_EVEN_ODD' },
                    ])}

                    {renderCategory('Primeiro Gol', <Target size={20} />, [
                      { label: 'Casa', key: 'FIRST_GOAL_HOME' },
                      { label: 'Fora', key: 'FIRST_GOAL_AWAY' },
                      { label: 'Nenhum', key: 'FIRST_GOAL_NONE' },
                    ])}

                    {renderCategory('Clean Sheet', <Activity size={20} />, [
                      { label: 'Casa', key: 'CLEAN_SHEET_HOME' },
                      { label: 'Fora', key: 'CLEAN_SHEET_AWAY' },
                    ])}

                    {renderCategory('Placares Exatos', <BarChart3 size={20} />, [
                      { label: '0-0', key: 'CORRECT_SCORE_0_0' },
                      { label: '1-0', key: 'CORRECT_SCORE_1_0' },
                      { label: '2-0', key: 'CORRECT_SCORE_2_0' },
                      { label: '2-1', key: 'CORRECT_SCORE_2_1' },
                      { label: '3-0', key: 'CORRECT_SCORE_3_0' },
                      { label: '3-1', key: 'CORRECT_SCORE_3_1' },
                      { label: '0-1', key: 'CORRECT_SCORE_0_1' },
                      { label: '0-2', key: 'CORRECT_SCORE_0_2' },
                      { label: '1-2', key: 'CORRECT_SCORE_1_2' },
                      { label: '0-3', key: 'CORRECT_SCORE_0_3' },
                      { label: '1-3', key: 'CORRECT_SCORE_1_3' },
                      { label: '1-1', key: 'CORRECT_SCORE_1_1' },
                      { label: '2-2', key: 'CORRECT_SCORE_2_2' },
                    ])}
                  </>
                )}
              </div>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  );
};
