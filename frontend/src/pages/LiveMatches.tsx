import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Radio,
  Clock,
  Target,
  Zap,
  RefreshCw,
  Filter,
  Search,
  TrendingUp,
  Award,
  DollarSign
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from '../contexts/I18nContext';

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

// 💎 VALUE BET TYPES
interface ValueBet {
  match_id: number;
  match_name: string;
  market_type: string;
  market_name: string;
  selection: string;
  market_odds: number;
  fair_odds: number;
  our_probability: number;
  implied_probability: number;
  edge: number;
  kelly_stake: number;
  value_rating: 'LOW' | 'MEDIUM' | 'HIGH' | 'PREMIUM';
  confidence: number;
  bookmaker: string;
  created_at: string;
}

interface ValueBetsScanResponse {
  total_matches_analyzed: number;
  total_value_bets_found: number;
  value_bets: ValueBet[];
  generated_at: string;
}

interface LiveMatch {
  match_id: number;
  status: string;
  minute: number | null;
  home_team: { id: number; name: string };
  away_team: { id: number; name: string };
  score: {
    home: number | null;
    away: number | null;
  };
  league: string;
  venue: string;
  match_date: string;
  markets: {
    '1X2'?: Market;
    'Over/Under 2.5'?: Market;
    'BTTS'?: Market;
    'Asian Handicap'?: Market;
    'Corners 9.5'?: Market;
  };
  prediction?: {
    predicted_outcome: string;
    confidence_score: number;
    probabilities: {
      home: number;
      draw: number;
      away: number;
    };
    recommendation: string;
  };
}

interface LiveMatchesResponse {
  success: boolean;
  live_matches: LiveMatch[];
  total: number;
  timestamp: string;
}


const fetchLiveMatches = async (): Promise<LiveMatchesResponse> => {
  const response = await fetch('http://localhost:8000/api/v1/predictions/live?limit=50');
  if (!response.ok) throw new Error('Failed to fetch live matches');
  return await response.json();
};

// 💎 Fetch value bets
const fetchValueBets = async (): Promise<ValueBetsScanResponse> => {
  const response = await fetch('http://localhost:8000/api/v1/markets/value-bets/scan?min_edge=10&limit=10');
  if (!response.ok) throw new Error('Failed to fetch value bets');
  return await response.json();
};

const LiveMatches: React.FC = () => {
  const { t } = useTranslation();
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<'all' | 'live' | 'pre-match'>('live');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [expandedMatchId, setExpandedMatchId] = useState<number | null>(null);

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['live-matches', filterStatus],
    queryFn: fetchLiveMatches,
    refetchInterval: autoRefresh ? 5000 : false, // 5 seconds - TEMPO REAL
    staleTime: 0, // Dados sempre frescos
    gcTime: 0, // Sem cache
  });

  // 💎 Query para Value Bets
  const { data: valueBetsData } = useQuery({
    queryKey: ['value-bets-scan'],
    queryFn: fetchValueBets,
    refetchInterval: 60000, // 1 minuto
    staleTime: 30000, // 30 segundos
  });


  // Auto-refresh em tempo real a cada 5s
  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        refetch();
      }, 5000); // 5 segundos - TEMPO REAL
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refetch]);

  const getScoreColor = (homeScore: number | null, awayScore: number | null, isHome: boolean) => {
    if (homeScore === null || awayScore === null) return 'text-slate-700';
    if (isHome) {
      return homeScore > awayScore ? 'text-green-600 font-bold' : homeScore < awayScore ? 'text-red-600' : 'text-yellow-600';
    } else {
      return awayScore > homeScore ? 'text-green-600 font-bold' : awayScore < homeScore ? 'text-red-600' : 'text-yellow-600';
    }
  };

  const filteredMatches = data?.live_matches.filter(match => {
    const matchText = `${match.home_team.name} ${match.away_team.name}`.toLowerCase();
    return matchText.includes(searchTerm.toLowerCase());
  }) || [];

  const getStatusBadge = (status: string, minute: number | null) => {
    const statusMap: { [key: string]: { label: string; color: string } } = {
      'LIVE': { label: 'LIVE', color: 'bg-red-500 animate-pulse' },
      '1H': { label: '1° Tempo', color: 'bg-red-500' },
      '2H': { label: '2° Tempo', color: 'bg-red-500' },
      'HT': { label: 'Intervalo', color: 'bg-yellow-500' },
      'NS': { label: 'Aguardando', color: 'bg-blue-500' },
      'FT': { label: 'Finalizado', color: 'bg-gray-500' },
    };

    const { label, color } = statusMap[status] || { label: status, color: 'bg-gray-500' };

    return (
      <div className="flex items-center space-x-2">
        <span className={`px-3 py-1 rounded-full text-white text-xs font-bold ${color} flex items-center space-x-1`}>
          {status === 'LIVE' || status === '1H' || status === '2H' ? (
            <div className="w-2 h-2 bg-white rounded-full animate-pulse mr-1"></div>
          ) : null}
          <span>{label}</span>
        </span>
        {minute && (
          <span className="text-sm font-bold text-slate-700">{minute}'</span>
        )}
      </div>
    );
  };

  // 💎 Helper para cores/badges de value bets
  const getValueBetBadge = (rating: string, edge: number) => {
    const ratingMap: { [key: string]: { bg: string; text: string; icon: string } } = {
      'PREMIUM': { bg: 'bg-purple-600', text: 'text-white', icon: '💎' },
      'HIGH': { bg: 'bg-green-600', text: 'text-white', icon: '🟢' },
      'MEDIUM': { bg: 'bg-orange-500', text: 'text-white', icon: '🟠' },
      'LOW': { bg: 'bg-yellow-500', text: 'text-white', icon: '🟡' },
    };

    const { bg, text, icon } = ratingMap[rating] || { bg: 'bg-gray-500', text: 'text-white', icon: '💰' };

    return (
      <div className={`${bg} ${text} px-3 py-1 rounded-full text-xs font-bold flex items-center space-x-1 shadow-lg animate-pulse`}>
        <span>{icon}</span>
        <span>{rating}</span>
        <span className="text-[10px]">+{edge.toFixed(1)}%</span>
      </div>
    );
  };

  // 💎 Buscar value bets de um jogo específico
  const getMatchValueBets = (matchId: number): ValueBet[] => {
    if (!valueBetsData?.value_bets) return [];
    return valueBetsData.value_bets.filter(vb => vb.match_id === matchId);
  };


  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center space-x-3 mb-8">
            <Radio className="w-10 h-10 text-red-600 animate-pulse" />
            <h1 className="text-4xl font-bold text-slate-900">{t('live.loading')}</h1>
          </div>
          <div className="grid grid-cols-1 gap-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="bg-white rounded-xl shadow-lg p-6 animate-pulse">
                <div className="h-24 bg-slate-200 rounded"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-50 border-2 border-red-200 rounded-xl p-8 text-center">
            <Radio className="w-16 h-16 text-red-600 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-red-900 mb-2">{t('live.error_title')}</h2>
            <p className="text-red-700 mb-4">{t('live.error_desc')}</p>
            <button
              onClick={() => refetch()}
              className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium"
            >
              {t('live.retry')}
            </button>
          </div>
        </div>
      </div>
    );
  }

  const displayMatches = filteredMatches;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-4">
              <div className="bg-red-600 p-3 rounded-xl">
                <Radio className="w-10 h-10 text-white" />
              </div>
              <div>
                <h1 className="text-4xl font-bold text-slate-900">{t('live.title')}</h1>
                <p className="text-slate-600 mt-1">{t('live.subtitle')}</p>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              <div className="bg-white px-4 py-2 rounded-lg shadow-sm border border-slate-200">
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
                  <span className="text-lg font-bold text-red-600">{data?.total || 0}</span>
                  <span className="text-slate-600 text-sm">{t('live.live_now')}</span>
                </div>
              </div>

              <button
                onClick={() => setAutoRefresh(!autoRefresh)}
                className={`p-3 rounded-lg transition-all ${
                  autoRefresh
                    ? 'bg-green-600 text-white'
                    : 'bg-white text-slate-600 border border-slate-200'
                }`}
                title={autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
              >
                <RefreshCw className={`w-5 h-5 ${autoRefresh ? 'animate-spin-slow' : ''}`} />
              </button>

              <button
                onClick={() => refetch()}
                className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium shadow-lg hover:shadow-xl"
              >
                {t('live.update_now')}
              </button>
            </div>
          </div>

          {/* Filters */}
          <div className="flex items-center space-x-4 bg-white rounded-xl p-4 shadow-sm border border-slate-200">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
              <input
                type="text"
                placeholder={t('live.search_placeholder')}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>

            <div className="flex items-center space-x-2">
              <Filter className="w-5 h-5 text-slate-600" />
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value as any)}
                className="px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              >
                <option value="all">{t('live.filter_all')}</option>
                <option value="live">{t('live.filter_live')}</option>
                <option value="pre-match">{t('live.filter_prematch')}</option>
              </select>
            </div>
          </div>
        </motion.div>

        {/* 💎 VALUE BETS SUMMARY - TOP 3 */}
        {valueBetsData && valueBetsData.value_bets && valueBetsData.value_bets.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 bg-gradient-to-br from-purple-50 via-pink-50 to-yellow-50 rounded-xl shadow-xl border-2 border-purple-200 p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className="bg-purple-600 p-2 rounded-lg">
                  <TrendingUp className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-slate-900">💎 Top Value Bets</h3>
                  <p className="text-sm text-slate-600">
                    {valueBetsData.total_value_bets_found} oportunidades encontradas
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-2 bg-purple-100 px-4 py-2 rounded-lg">
                <Award className="w-5 h-5 text-purple-600" />
                <span className="text-sm font-bold text-purple-900">
                  Edge Mínimo: 10%
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {valueBetsData.value_bets.slice(0, 3).map((vb, idx) => (
                <div
                  key={idx}
                  className="bg-white p-4 rounded-lg shadow-md border-2 border-purple-200 hover:shadow-xl transition-all cursor-pointer hover:scale-105"
                >
                  <div className="flex items-center justify-between mb-3">
                    {getValueBetBadge(vb.value_rating, vb.edge)}
                    <div className="flex items-center space-x-1 text-green-600">
                      <DollarSign className="w-4 h-4" />
                      <span className="text-xs font-bold">Kelly: {vb.kelly_stake.toFixed(1)}%</span>
                    </div>
                  </div>

                  <div className="mb-2">
                    <div className="text-xs text-slate-500 mb-1">{vb.match_name}</div>
                    <div className="text-sm font-bold text-slate-900">{vb.market_name}</div>
                    <div className="text-xs text-purple-600 font-medium">{vb.selection}</div>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="bg-slate-50 p-2 rounded">
                      <div className="text-slate-500">Market Odds</div>
                      <div className="font-bold text-slate-900">{vb.market_odds.toFixed(2)}</div>
                    </div>
                    <div className="bg-green-50 p-2 rounded">
                      <div className="text-green-600">Fair Odds</div>
                      <div className="font-bold text-green-900">{vb.fair_odds.toFixed(2)}</div>
                    </div>
                  </div>

                  <div className="mt-3 pt-3 border-t border-slate-200">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-500">Nossa Prob:</span>
                      <span className="font-bold text-blue-600">{(vb.our_probability * 100).toFixed(1)}%</span>
                    </div>
                    <div className="flex items-center justify-between text-xs mt-1">
                      <span className="text-slate-500">Confiança:</span>
                      <span className="font-bold text-purple-600">{(vb.confidence * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Live Matches Grid */}
        <AnimatePresence mode="popLayout">
          <div className="space-y-4">
            {displayMatches.map((match, index) => (
              <motion.div
                key={match.match_id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ delay: index * 0.05 }}
                className="bg-white rounded-xl shadow-lg hover:shadow-2xl transition-all border border-slate-200 overflow-hidden"
              >
                <div className="p-6">
                  {/* Status Bar */}
                  <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center space-x-3">
                      {getStatusBadge(match.status, match.minute)}

                      {/* 💎 Value Bet Badge para este jogo */}
                      {(() => {
                        const matchVBs = getMatchValueBets(match.match_id);
                        if (matchVBs.length > 0) {
                          const bestVB = matchVBs[0]; // Melhor value bet
                          return (
                            <div className="relative">
                              {getValueBetBadge(bestVB.value_rating, bestVB.edge)}
                              {matchVBs.length > 1 && (
                                <div className="absolute -top-1 -right-1 bg-red-600 text-white text-[10px] font-bold w-5 h-5 rounded-full flex items-center justify-center">
                                  {matchVBs.length}
                                </div>
                              )}
                            </div>
                          );
                        }
                        return null;
                      })()}
                    </div>

                    {match.prediction && (
                      <div className="flex items-center space-x-2 px-3 py-1 bg-blue-50 rounded-lg">
                        <Target className="w-4 h-4 text-blue-600" />
                        <span className="text-sm font-medium text-blue-700">
                          Prediction: {match.prediction.predicted_outcome}
                        </span>
                        <span className="text-xs text-blue-600">
                          ({(match.prediction.confidence_score * 100).toFixed(0)}%)
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Match Info */}
                  <div className="grid grid-cols-7 gap-4 items-center mb-6">
                    {/* Home Team */}
                    <div className="col-span-3 text-right">
                      <h3 className="text-xl font-bold text-slate-900">{match.home_team.name}</h3>
                    </div>

                    {/* Score */}
                    <div className="col-span-1 flex items-center justify-center">
                      <div className="bg-slate-100 px-6 py-3 rounded-xl">
                        <div className="flex items-center space-x-3 text-3xl font-bold">
                          <span className={getScoreColor(match.score.home, match.score.away, true)}>
                            {match.score.home ?? '-'}
                          </span>
                          <span className="text-slate-400">:</span>
                          <span className={getScoreColor(match.score.home, match.score.away, false)}>
                            {match.score.away ?? '-'}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Away Team */}
                    <div className="col-span-3">
                      <h3 className="text-xl font-bold text-slate-900">{match.away_team.name}</h3>
                    </div>
                  </div>

                  {/* Odds Section - 1X2 */}
                  {match.markets['1X2'] && (
                    <div className="mb-4">
                      <div className="text-sm font-medium text-slate-600 mb-2">Resultado Final (1X2)</div>
                      <div className="grid grid-cols-3 gap-3">
                        <div className="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-lg text-center border-2 border-green-200 hover:border-green-400 transition-all cursor-pointer">
                          <div className="text-xs text-green-700 font-medium mb-1">CASA</div>
                          <div className="text-2xl font-bold text-green-900">
                            {match.markets['1X2'].home?.toFixed(2) || '-'}
                          </div>
                        </div>

                        <div className="bg-gradient-to-br from-yellow-50 to-yellow-100 p-4 rounded-lg text-center border-2 border-yellow-200 hover:border-yellow-400 transition-all cursor-pointer">
                          <div className="text-xs text-yellow-700 font-medium mb-1">EMPATE</div>
                          <div className="text-2xl font-bold text-yellow-900">
                            {match.markets['1X2'].draw?.toFixed(2) || '-'}
                          </div>
                        </div>

                        <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-lg text-center border-2 border-blue-200 hover:border-blue-400 transition-all cursor-pointer">
                          <div className="text-xs text-blue-700 font-medium mb-1">FORA</div>
                          <div className="text-2xl font-bold text-blue-900">
                            {match.markets['1X2'].away?.toFixed(2) || '-'}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Additional Markets */}
                  <div className="grid grid-cols-2 gap-3">
                    {/* Over/Under 2.5 */}
                    {match.markets['Over/Under 2.5'] && (
                      <div className="bg-purple-50 p-3 rounded-lg border border-purple-200">
                        <div className="text-xs text-purple-700 font-medium mb-2">⚽ Over/Under 2.5 Gols</div>
                        <div className="flex justify-between">
                          <div className="text-center">
                            <div className="text-xs text-purple-600">Over</div>
                            <div className="text-lg font-bold text-purple-900">
                              {match.markets['Over/Under 2.5'].over?.toFixed(2) || '-'}
                            </div>
                          </div>
                          <div className="text-center">
                            <div className="text-xs text-purple-600">Under</div>
                            <div className="text-lg font-bold text-purple-900">
                              {match.markets['Over/Under 2.5'].under?.toFixed(2) || '-'}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* BTTS */}
                    {match.markets['BTTS'] && (
                      <div className="bg-orange-50 p-3 rounded-lg border border-orange-200">
                        <div className="text-xs text-orange-700 font-medium mb-2">Ambos Marcam (BTTS)</div>
                        <div className="flex justify-between">
                          <div className="text-center">
                            <div className="text-xs text-orange-600">Sim</div>
                            <div className="text-lg font-bold text-orange-900">
                              {match.markets['BTTS'].yes?.toFixed(2) || '-'}
                            </div>
                          </div>
                          <div className="text-center">
                            <div className="text-xs text-orange-600">Não</div>
                            <div className="text-lg font-bold text-orange-900">
                              {match.markets['BTTS'].no?.toFixed(2) || '-'}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Corners */}
                    {match.markets['Corners 9.5'] && (
                      <div className="bg-cyan-50 p-3 rounded-lg border border-cyan-200">
                        <div className="text-xs text-cyan-700 font-medium mb-2">🚩 Over/Under 9.5 Escanteios</div>
                        <div className="flex justify-between">
                          <div className="text-center">
                            <div className="text-xs text-cyan-600">+9.5</div>
                            <div className="text-lg font-bold text-cyan-900">
                              {match.markets['Corners 9.5'].over?.toFixed(2) || '-'}
                            </div>
                          </div>
                          <div className="text-center">
                            <div className="text-xs text-cyan-600">-9.5</div>
                            <div className="text-lg font-bold text-cyan-900">
                              {match.markets['Corners 9.5'].under?.toFixed(2) || '-'}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Asian Handicap */}
                    {match.markets['Asian Handicap'] && (
                      <div className="bg-indigo-50 p-3 rounded-lg border border-indigo-200">
                        <div className="text-xs text-indigo-700 font-medium mb-2">
                          Handicap Asiático ({match.markets['Asian Handicap'].line})
                        </div>
                        <div className="flex justify-between">
                          <div className="text-center">
                            <div className="text-xs text-indigo-600">Casa</div>
                            <div className="text-lg font-bold text-indigo-900">
                              {match.markets['Asian Handicap'].home?.toFixed(2) || '-'}
                            </div>
                          </div>
                          <div className="text-center">
                            <div className="text-xs text-indigo-600">Fora</div>
                            <div className="text-lg font-bold text-indigo-900">
                              {match.markets['Asian Handicap'].away?.toFixed(2) || '-'}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Botão Ver Todos os Mercados */}
                  <div className="mt-4 flex items-center justify-end">
                    <button
                      onClick={() => setExpandedMatchId(expandedMatchId === match.match_id ? null : match.match_id)}
                      className="px-4 py-2 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg hover:from-blue-700 hover:to-blue-800 transition-all text-sm font-medium flex items-center space-x-2 shadow-md"
                    >
                      <Target className="w-4 h-4" />
                      <span>{expandedMatchId === match.match_id ? 'Ocultar Mercados' : 'Ver Todos os Mercados'}</span>
                      <svg
                        className={`w-4 h-4 transition-transform ${expandedMatchId === match.match_id ? 'rotate-180' : ''}`}
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>
                  </div>

                  {/* Seção Expandida de Todos os Mercados - Estilo Bet365 */}
                  <AnimatePresence>
                    {expandedMatchId === match.match_id && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.3 }}
                        className="mt-4 pt-4 border-t-2 border-slate-200"
                      >
                        <div className="bg-gradient-to-br from-slate-50 to-blue-50 p-6 rounded-xl border border-slate-200">
                          <h4 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
                            <Target className="w-5 h-5 text-blue-600" />
                            <span>Todos os Mercados Disponíveis</span>
                            {match.markets['1X2'] && (
                              <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full ml-2">
                                {match.markets['1X2'].bookmaker}
                              </span>
                            )}
                          </h4>

                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {/* 1X2 - Resultado Final */}
                            {match.markets['1X2'] && (
                              <div className="bg-white p-4 rounded-lg border-2 border-green-200 shadow-sm">
                                <div className="text-sm font-bold text-green-700 mb-3 flex items-center gap-2">
                                  <span className="bg-green-100 px-2 py-1 rounded">⚽ RESULTADO FINAL</span>
                                </div>
                                <div className="grid grid-cols-3 gap-2">
                                  <div className="bg-gradient-to-br from-green-50 to-green-100 p-3 rounded-lg text-center border border-green-200 hover:shadow-md transition-shadow cursor-pointer">
                                    <div className="text-xs text-green-700 font-medium mb-1">Casa</div>
                                    <div className="text-xl font-bold text-green-900">
                                      {match.markets['1X2'].home?.toFixed(2)}
                                    </div>
                                  </div>
                                  <div className="bg-gradient-to-br from-yellow-50 to-yellow-100 p-3 rounded-lg text-center border border-yellow-200 hover:shadow-md transition-shadow cursor-pointer">
                                    <div className="text-xs text-yellow-700 font-medium mb-1">Empate</div>
                                    <div className="text-xl font-bold text-yellow-900">
                                      {match.markets['1X2'].draw?.toFixed(2)}
                                    </div>
                                  </div>
                                  <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-3 rounded-lg text-center border border-blue-200 hover:shadow-md transition-shadow cursor-pointer">
                                    <div className="text-xs text-blue-700 font-medium mb-1">Fora</div>
                                    <div className="text-xl font-bold text-blue-900">
                                      {match.markets['1X2'].away?.toFixed(2)}
                                    </div>
                                  </div>
                                </div>
                              </div>
                            )}

                            {/* Over/Under 2.5 Gols */}
                            {match.markets['Over/Under 2.5'] && (
                              <div className="bg-white p-4 rounded-lg border-2 border-purple-200 shadow-sm">
                                <div className="text-sm font-bold text-purple-700 mb-3 flex items-center gap-2">
                                  <span className="bg-purple-100 px-2 py-1 rounded">⚽ OVER/UNDER 2.5 GOLS</span>
                                </div>
                                <div className="grid grid-cols-2 gap-2">
                                  <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-3 rounded-lg text-center border border-purple-200 hover:shadow-md transition-shadow cursor-pointer">
                                    <div className="text-xs text-purple-700 font-medium mb-1">Over 2.5</div>
                                    <div className="text-xl font-bold text-purple-900">
                                      {match.markets['Over/Under 2.5'].over?.toFixed(2)}
                                    </div>
                                  </div>
                                  <div className="bg-gradient-to-br from-indigo-50 to-indigo-100 p-3 rounded-lg text-center border border-indigo-200 hover:shadow-md transition-shadow cursor-pointer">
                                    <div className="text-xs text-indigo-700 font-medium mb-1">Under 2.5</div>
                                    <div className="text-xl font-bold text-indigo-900">
                                      {match.markets['Over/Under 2.5'].under?.toFixed(2)}
                                    </div>
                                  </div>
                                </div>
                              </div>
                            )}

                            {/* BTTS - Ambos Marcam */}
                            {match.markets['BTTS'] && (
                              <div className="bg-white p-4 rounded-lg border-2 border-orange-200 shadow-sm">
                                <div className="text-sm font-bold text-orange-700 mb-3 flex items-center gap-2">
                                  <span className="bg-orange-100 px-2 py-1 rounded">🎯 AMBOS MARCAM</span>
                                </div>
                                <div className="grid grid-cols-2 gap-2">
                                  <div className="bg-gradient-to-br from-orange-50 to-orange-100 p-3 rounded-lg text-center border border-orange-200 hover:shadow-md transition-shadow cursor-pointer">
                                    <div className="text-xs text-orange-700 font-medium mb-1">Sim</div>
                                    <div className="text-xl font-bold text-orange-900">
                                      {match.markets['BTTS'].yes?.toFixed(2)}
                                    </div>
                                  </div>
                                  <div className="bg-gradient-to-br from-red-50 to-red-100 p-3 rounded-lg text-center border border-red-200 hover:shadow-md transition-shadow cursor-pointer">
                                    <div className="text-xs text-red-700 font-medium mb-1">Não</div>
                                    <div className="text-xl font-bold text-red-900">
                                      {match.markets['BTTS'].no?.toFixed(2)}
                                    </div>
                                  </div>
                                </div>
                              </div>
                            )}

                            {/* Escanteios 9.5 */}
                            {match.markets['Corners 9.5'] && (
                              <div className="bg-white p-4 rounded-lg border-2 border-cyan-200 shadow-sm">
                                <div className="text-sm font-bold text-cyan-700 mb-3 flex items-center gap-2">
                                  <span className="bg-cyan-100 px-2 py-1 rounded">🚩 OVER/UNDER 9.5 ESCANTEIOS</span>
                                </div>
                                <div className="grid grid-cols-2 gap-2">
                                  <div className="bg-gradient-to-br from-cyan-50 to-cyan-100 p-3 rounded-lg text-center border border-cyan-200 hover:shadow-md transition-shadow cursor-pointer">
                                    <div className="text-xs text-cyan-700 font-medium mb-1">Over 9.5</div>
                                    <div className="text-xl font-bold text-cyan-900">
                                      {match.markets['Corners 9.5'].over?.toFixed(2)}
                                    </div>
                                  </div>
                                  <div className="bg-gradient-to-br from-teal-50 to-teal-100 p-3 rounded-lg text-center border border-teal-200 hover:shadow-md transition-shadow cursor-pointer">
                                    <div className="text-xs text-teal-700 font-medium mb-1">Under 9.5</div>
                                    <div className="text-xl font-bold text-teal-900">
                                      {match.markets['Corners 9.5'].under?.toFixed(2)}
                                    </div>
                                  </div>
                                </div>
                              </div>
                            )}

                            {/* Asian Handicap */}
                            {match.markets['Asian Handicap'] && (
                              <div className="bg-white p-4 rounded-lg border-2 border-pink-200 shadow-sm md:col-span-2">
                                <div className="text-sm font-bold text-pink-700 mb-3 flex items-center gap-2">
                                  <span className="bg-pink-100 px-2 py-1 rounded">⚖️ HANDICAP ASIÁTICO ({match.markets['Asian Handicap'].line})</span>
                                </div>
                                <div className="grid grid-cols-2 gap-2 max-w-2xl mx-auto">
                                  <div className="bg-gradient-to-br from-pink-50 to-pink-100 p-3 rounded-lg text-center border border-pink-200 hover:shadow-md transition-shadow cursor-pointer">
                                    <div className="text-xs text-pink-700 font-medium mb-1">{match.home_team.name}</div>
                                    <div className="text-xl font-bold text-pink-900">
                                      {match.markets['Asian Handicap'].home?.toFixed(2)}
                                    </div>
                                  </div>
                                  <div className="bg-gradient-to-br from-rose-50 to-rose-100 p-3 rounded-lg text-center border border-rose-200 hover:shadow-md transition-shadow cursor-pointer">
                                    <div className="text-xs text-rose-700 font-medium mb-1">{match.away_team.name}</div>
                                    <div className="text-xl font-bold text-rose-900">
                                      {match.markets['Asian Handicap'].away?.toFixed(2)}
                                    </div>
                                  </div>
                                </div>
                              </div>
                            )}
                          </div>

                          {/* Predição da IA */}
                          {match.prediction && (
                            <div className="mt-4 bg-gradient-to-r from-blue-50 to-purple-50 p-4 rounded-lg border-2 border-blue-200">
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                  <div className="bg-blue-600 p-2 rounded-lg">
                                    <Zap className="w-5 h-5 text-white" />
                                  </div>
                                  <div>
                                    <div className="text-sm font-bold text-slate-900">Predição da IA</div>
                                    <div className="text-xs text-slate-600">Baseado em análise de machine learning</div>
                                  </div>
                                </div>
                                <div className="flex items-center gap-4">
                                  <div className="text-center">
                                    <div className="text-xs text-slate-600">Resultado</div>
                                    <div className="text-lg font-bold text-blue-900">
                                      {match.prediction.predicted_outcome === '1' ? 'Casa' :
                                       match.prediction.predicted_outcome === 'X' ? 'Empate' : 'Fora'}
                                    </div>
                                  </div>
                                  <div className="text-center">
                                    <div className="text-xs text-slate-600">Confiança</div>
                                    <div className="text-lg font-bold text-green-600">
                                      {(match.prediction.confidence_score * 100).toFixed(0)}%
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </div>
                          )}

                          {/* 💎 Value Bets deste jogo */}
                          {(() => {
                            const matchVBs = getMatchValueBets(match.match_id);
                            if (matchVBs.length > 0) {
                              return (
                                <div className="mt-4 bg-gradient-to-br from-purple-50 via-pink-50 to-yellow-50 p-4 rounded-lg border-2 border-purple-300">
                                  <div className="flex items-center gap-3 mb-3">
                                    <div className="bg-purple-600 p-2 rounded-lg">
                                      <TrendingUp className="w-5 h-5 text-white" />
                                    </div>
                                    <div>
                                      <div className="text-sm font-bold text-slate-900">💎 Value Bets Identificados</div>
                                      <div className="text-xs text-slate-600">{matchVBs.length} oportunidade(s) com edge positivo</div>
                                    </div>
                                  </div>

                                  <div className="space-y-2">
                                    {matchVBs.map((vb, vbIdx) => (
                                      <div key={vbIdx} className="bg-white p-3 rounded-lg border border-purple-200">
                                        <div className="flex items-center justify-between mb-2">
                                          <div className="flex items-center space-x-2">
                                            {getValueBetBadge(vb.value_rating, vb.edge)}
                                            <span className="text-xs font-bold text-slate-900">{vb.market_name}</span>
                                          </div>
                                          <div className="flex items-center space-x-1 text-green-600">
                                            <DollarSign className="w-3 h-3" />
                                            <span className="text-xs font-bold">Kelly: {vb.kelly_stake.toFixed(1)}%</span>
                                          </div>
                                        </div>

                                        <div className="text-xs text-purple-600 font-medium mb-2">{vb.selection}</div>

                                        <div className="grid grid-cols-3 gap-2 text-xs">
                                          <div className="bg-slate-50 p-1.5 rounded text-center">
                                            <div className="text-slate-500">Market</div>
                                            <div className="font-bold text-slate-900">{vb.market_odds.toFixed(2)}</div>
                                          </div>
                                          <div className="bg-green-50 p-1.5 rounded text-center">
                                            <div className="text-green-600">Fair</div>
                                            <div className="font-bold text-green-900">{vb.fair_odds.toFixed(2)}</div>
                                          </div>
                                          <div className="bg-purple-50 p-1.5 rounded text-center">
                                            <div className="text-purple-600">Prob</div>
                                            <div className="font-bold text-purple-900">{(vb.our_probability * 100).toFixed(0)}%</div>
                                          </div>
                                        </div>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              );
                            }
                            return null;
                          })()}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </motion.div>
            ))}
          </div>
        </AnimatePresence>

        {/* Empty State */}
        {displayMatches.length === 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-16 bg-white rounded-xl shadow-sm"
          >
            <Radio className="w-20 h-20 text-slate-300 mx-auto mb-4" />
            <h3 className="text-2xl font-bold text-slate-700 mb-2">{t('live.no_matches')}</h3>
            <p className="text-slate-500">{t('live.wait_matches')}</p>
          </motion.div>
        )}

        {/* Live Stats Footer */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="mt-8 grid grid-cols-1 md:grid-cols-4 gap-4"
        >
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600 mb-1">{t('live.total_matches')}</p>
                <p className="text-3xl font-bold text-slate-900">{data?.total || 0}</p>
              </div>
              <Clock className="w-10 h-10 text-blue-600" />
            </div>
          </div>

          <div className="bg-gradient-to-br from-red-500 to-red-600 p-6 rounded-xl shadow-lg text-white">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-red-100 mb-1">{t('live.live_now_stat')}</p>
                <p className="text-3xl font-bold">{data?.total || 0}</p>
              </div>
              <Radio className="w-10 h-10 animate-pulse" />
            </div>
          </div>

          <div className="bg-gradient-to-br from-purple-500 to-purple-600 p-6 rounded-xl shadow-lg text-white">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-purple-100 mb-1">{t('live.value_bets_stat')}</p>
                <p className="text-3xl font-bold">{valueBetsData?.total_value_bets_found || 0}</p>
              </div>
              <TrendingUp className="w-10 h-10 animate-pulse" />
            </div>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600 mb-1">{t('live.next_update')}</p>
                <p className="text-3xl font-bold text-slate-900">30s</p>
              </div>
              <RefreshCw className={`w-10 h-10 text-green-600 ${autoRefresh ? 'animate-spin-slow' : ''}`} />
            </div>
          </div>
        </motion.div>
      </div>

      <style>{`
        @keyframes spin-slow {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .animate-spin-slow {
          animation: spin-slow 3s linear infinite;
        }
      `}</style>
    </div>
  );
};

export default LiveMatches;
