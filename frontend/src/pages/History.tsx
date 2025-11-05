import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search,
  TrendingUp,
  TrendingDown,
  Minus,
  Trophy,
  Target,
  Home,
  Plane,
  Calendar,
  X,
  Loader
} from 'lucide-react';
import { useTranslation } from '../contexts/I18nContext';

interface Team {
  id: number;
  name: string;
  logo_url?: string;
  total_matches?: number;
}

interface TeamMatch {
  id: number;
  match_date: string;
  home_team: {
    id: number;
    name: string;
    logo: string | null;
  };
  away_team: {
    id: number;
    name: string;
    logo: string | null;
  };
  home_score: number;
  away_score: number;
  venue: 'home' | 'away';
  result: 'W' | 'D' | 'L';
  league: {
    id: number | null;
    name: string;
  };
}

interface TeamStats {
  general: {
    played: number;
    wins: number;
    draws: number;
    losses: number;
    win_rate: number;
    goals_scored: number;
    goals_conceded: number;
    goal_difference: number;
    avg_goals_scored: number;
    avg_goals_conceded: number;
  };
  home: {
    played: number;
    wins: number;
    draws: number;
    losses: number;
    goals_scored: number;
    goals_conceded: number;
  };
  away: {
    played: number;
    wins: number;
    draws: number;
    losses: number;
    goals_scored: number;
    goals_conceded: number;
  };
  form: {
    recent_5: string[];
    current_streak: {
      type: string;
      count: number;
    };
  };
}

const History: React.FC = () => {
  const { t } = useTranslation();
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState<Team[]>([]);
  const [selectedTeam, setSelectedTeam] = useState<Team | null>(null);
  const [teamMatches, setTeamMatches] = useState<TeamMatch[]>([]);
  const [teamStats, setTeamStats] = useState<TeamStats | null>(null);
  const [venueFilter, setVenueFilter] = useState<'all' | 'home' | 'away'>('all');
  const [matchLimit, setMatchLimit] = useState(10);
  const [searching, setSearching] = useState(false);
  const [loading, setLoading] = useState(false);

  // Buscar times
  const handleSearch = async (query: string) => {
    if (query.length < 2) {
      setSearchResults([]);
      return;
    }

    setSearching(true);
    try {
      const response = await fetch(`http://localhost:8000/api/v1/teams/search?q=${encodeURIComponent(query)}&limit=10`);
      const data = await response.json();

      if (data.success) {
        setSearchResults(data.teams);
      }
    } catch (error) {
      console.error('Erro ao buscar times:', error);
    } finally {
      setSearching(false);
    }
  };

  // Selecionar time e carregar dados
  const handleSelectTeam = async (team: Team) => {
    setSelectedTeam(team);
    setSearchResults([]);
    setSearchTerm('');
    setLoading(true);

    try {
      // Carregar histórico e estatísticas em paralelo
      const [historyRes, statsRes] = await Promise.all([
        fetch(`http://localhost:8000/api/v1/teams/${team.id}/history?venue=${venueFilter}&limit=${matchLimit}`),
        fetch(`http://localhost:8000/api/v1/teams/${team.id}/stats?last_n_games=${matchLimit}`)
      ]);

      const historyData = await historyRes.json();
      const statsData = await statsRes.json();

      if (historyData.success) {
        setTeamMatches(historyData.matches);
      }

      if (statsData.success && statsData.stats) {
        setTeamStats(statsData.stats);
      }
    } catch (error) {
      console.error('Erro ao carregar dados do time:', error);
    } finally {
      setLoading(false);
    }
  };

  // Recarregar quando mudar filtros
  const handleFilterChange = async (newVenue?: 'all' | 'home' | 'away', newLimit?: number) => {
    if (!selectedTeam) return;

    const venue = newVenue || venueFilter;
    const limit = newLimit || matchLimit;

    if (newVenue) setVenueFilter(newVenue);
    if (newLimit) setMatchLimit(newLimit);

    setLoading(true);
    try {
      const [historyRes, statsRes] = await Promise.all([
        fetch(`http://localhost:8000/api/v1/teams/${selectedTeam.id}/history?venue=${venue}&limit=${limit}`),
        fetch(`http://localhost:8000/api/v1/teams/${selectedTeam.id}/stats?last_n_games=${limit}`)
      ]);

      const historyData = await historyRes.json();
      const statsData = await statsRes.json();

      if (historyData.success) {
        setTeamMatches(historyData.matches);
      }

      if (statsData.success && statsData.stats) {
        setTeamStats(statsData.stats);
      }
    } catch (error) {
      console.error('Erro ao recarregar dados:', error);
    } finally {
      setLoading(false);
    }
  };

  // Componente de resultado W/D/L
  const ResultBadge = ({ result }: { result: 'W' | 'D' | 'L' }) => {
    const config = {
      W: { bg: 'bg-green-600', text: 'text-white', label: 'V' },
      D: { bg: 'bg-yellow-600', text: 'text-white', label: 'E' },
      L: { bg: 'bg-red-600', text: 'text-white', label: 'D' }
    };

    const { bg, text, label } = config[result];

    return (
      <div className={`${bg} ${text} w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm`}>
        {label}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-4 mb-6">
            <div className="p-3 bg-gradient-to-br from-purple-500 to-pink-600 rounded-2xl">
              <Trophy className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white">{t('history.title')}</h1>
              <p className="text-slate-400">
                {t('history.subtitle')}
              </p>
            </div>
          </div>

          {/* Barra de Busca */}
          <div className="relative">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-slate-400 w-5 h-5" />
              <input
                type="text"
                placeholder={t('history.search_placeholder')}
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value);
                  handleSearch(e.target.value);
                }}
                className="w-full pl-12 pr-12 py-4 bg-white/10 backdrop-blur-xl border border-slate-700 rounded-2xl text-white placeholder-slate-400 focus:border-purple-500 transition-colors text-lg"
              />
              {searching && (
                <Loader className="absolute right-4 top-1/2 transform -translate-y-1/2 text-purple-400 w-5 h-5 animate-spin" />
              )}
            </div>

            {/* Resultados da Busca */}
            <AnimatePresence>
              {searchResults.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="absolute z-50 w-full mt-2 bg-slate-800 border border-slate-700 rounded-2xl shadow-2xl overflow-hidden"
                >
                  {searchResults.map((team) => (
                    <button
                      key={team.id}
                      onClick={() => handleSelectTeam(team)}
                      className="w-full flex items-center gap-4 p-4 hover:bg-slate-700 transition-colors text-left"
                    >
                      {team.logo_url ? (
                        <img src={team.logo_url} alt={team.name} className="w-10 h-10 object-contain" />
                      ) : (
                        <div className="w-10 h-10 rounded-full bg-slate-600 flex items-center justify-center">
                          <Trophy className="w-5 h-5 text-slate-400" />
                        </div>
                      )}
                      <div className="flex-1">
                        <h4 className="text-white font-semibold">{team.name}</h4>
                        <p className="text-xs text-slate-400">
                          {team.total_matches || 0} {t('history.matches_in_history')}
                        </p>
                      </div>
                    </button>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Time Selecionado */}
        {selectedTeam && (
          <div className="space-y-6">
            {/* Header do Time */}
            <div className="bg-white/5 backdrop-blur-xl rounded-3xl p-6 border border-slate-700">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  {selectedTeam.logo_url ? (
                    <img src={selectedTeam.logo_url} alt={selectedTeam.name} className="w-16 h-16 object-contain" />
                  ) : (
                    <div className="w-16 h-16 rounded-full bg-slate-700 flex items-center justify-center">
                      <Trophy className="w-8 h-8 text-slate-400" />
                    </div>
                  )}
                  <div>
                    <h2 className="text-2xl font-bold text-white">{selectedTeam.name}</h2>
                    <p className="text-slate-400">{t('history.performance_analysis')}</p>
                  </div>
                </div>

                <button
                  onClick={() => {
                    setSelectedTeam(null);
                    setTeamMatches([]);
                    setTeamStats(null);
                  }}
                  className="p-2 hover:bg-slate-700 rounded-xl transition-colors"
                >
                  <X className="w-5 h-5 text-slate-400" />
                </button>
              </div>
            </div>

            {/* Filtros */}
            <div className="bg-white/5 backdrop-blur-xl rounded-3xl p-6 border border-slate-700">
              <div className="flex flex-wrap gap-4 items-center">
                <div>
                  <label className="text-sm text-slate-400 mb-2 block">{t('history.venue_label')}</label>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleFilterChange('all')}
                      className={`px-4 py-2 rounded-xl font-medium transition-colors ${
                        venueFilter === 'all'
                          ? 'bg-purple-600 text-white'
                          : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                      }`}
                    >
                      {t('history.all')}
                    </button>
                    <button
                      onClick={() => handleFilterChange('home')}
                      className={`px-4 py-2 rounded-xl font-medium transition-colors flex items-center gap-2 ${
                        venueFilter === 'home'
                          ? 'bg-green-600 text-white'
                          : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                      }`}
                    >
                      <Home className="w-4 h-4" />
                      {t('history.home')}
                    </button>
                    <button
                      onClick={() => handleFilterChange('away')}
                      className={`px-4 py-2 rounded-xl font-medium transition-colors flex items-center gap-2 ${
                        venueFilter === 'away'
                          ? 'bg-blue-600 text-white'
                          : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                      }`}
                    >
                      <Plane className="w-4 h-4" />
                      {t('history.away')}
                    </button>
                  </div>
                </div>

                <div>
                  <label className="text-sm text-slate-400 mb-2 block">{t('history.matches_label')}</label>
                  <select
                    value={matchLimit}
                    onChange={(e) => handleFilterChange(undefined, Number(e.target.value))}
                    className="px-4 py-2 bg-slate-700 text-white rounded-xl border border-slate-600 focus:border-purple-500 transition-colors"
                  >
                    <option value={5}>{t('history.last_5')}</option>
                    <option value={10}>{t('history.last_10')}</option>
                    <option value={15}>{t('history.last_15')}</option>
                    <option value={20}>{t('history.last_20')}</option>
                  </select>
                </div>
              </div>
            </div>

            {loading ? (
              <div className="flex items-center justify-center p-12">
                <Loader className="w-12 h-12 text-purple-500 animate-spin" />
              </div>
            ) : (
              <>
                {/* Estatísticas */}
                {teamStats && (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Estatísticas Gerais */}
                    <div className="bg-white/5 backdrop-blur-xl rounded-3xl p-6 border border-slate-700">
                      <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                        <Target className="w-5 h-5 text-purple-400" />
                        {t('history.general')} ({venueFilter === 'all' ? t('history.all') : venueFilter === 'home' ? t('history.home') : t('history.away')})
                      </h3>
                      <div className="space-y-3">
                        <div className="flex justify-between">
                          <span className="text-slate-400">{t('history.matches')}:</span>
                          <span className="text-white font-bold">{teamStats.general.played}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-green-400">{t('history.wins')}:</span>
                          <span className="text-white font-bold">{teamStats.general.wins}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-yellow-400">{t('history.draws')}:</span>
                          <span className="text-white font-bold">{teamStats.general.draws}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-red-400">{t('history.losses')}:</span>
                          <span className="text-white font-bold">{teamStats.general.losses}</span>
                        </div>
                        <div className="border-t border-slate-700 pt-3 mt-3">
                          <div className="flex justify-between">
                            <span className="text-slate-400">{t('history.win_rate')}:</span>
                            <span className="text-purple-400 font-bold">{teamStats.general.win_rate}%</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Gols */}
                    <div className="bg-white/5 backdrop-blur-xl rounded-3xl p-6 border border-slate-700">
                      <h3 className="text-lg font-bold text-white mb-4">{t('history.goals')}</h3>
                      <div className="space-y-3">
                        <div className="flex justify-between">
                          <span className="text-slate-400">{t('history.goals_scored')}:</span>
                          <span className="text-green-400 font-bold">{teamStats.general.goals_scored}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">{t('history.goals_conceded')}:</span>
                          <span className="text-red-400 font-bold">{teamStats.general.goals_conceded}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">{t('history.goal_balance')}:</span>
                          <span className={`font-bold ${teamStats.general.goal_difference >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                            {teamStats.general.goal_difference > 0 ? '+' : ''}{teamStats.general.goal_difference}
                          </span>
                        </div>
                        <div className="border-t border-slate-700 pt-3 mt-3">
                          <div className="flex justify-between">
                            <span className="text-slate-400">{t('history.avg_per_match')}:</span>
                            <span className="text-white font-bold">{teamStats.general.avg_goals_scored.toFixed(2)}</span>
                          </div>
                          <div className="flex justify-between mt-2">
                            <span className="text-slate-400">{t('history.concedes_per_match')}:</span>
                            <span className="text-white font-bold">{teamStats.general.avg_goals_conceded.toFixed(2)}</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Forma Recente */}
                    <div className="bg-white/5 backdrop-blur-xl rounded-3xl p-6 border border-slate-700">
                      <h3 className="text-lg font-bold text-white mb-4">{t('history.recent_form')}</h3>
                      <div className="flex gap-2 mb-4">
                        {teamStats.form.recent_5.map((result, idx) => (
                          <ResultBadge key={idx} result={result as 'W' | 'D' | 'L'} />
                        ))}
                      </div>
                      <div className="space-y-3 mt-4">
                        <div className="flex justify-between items-center">
                          <span className="text-slate-400">{t('history.current_streak')}:</span>
                          <div className="flex items-center gap-2">
                            <ResultBadge result={teamStats.form.current_streak.type as 'W' | 'D' | 'L'} />
                            <span className="text-white font-bold">×{teamStats.form.current_streak.count}</span>
                          </div>
                        </div>
                      </div>

                      {/* Casa vs Fora */}
                      <div className="mt-6 pt-4 border-t border-slate-700">
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <div className="flex items-center gap-1 text-green-400 mb-2">
                              <Home className="w-4 h-4" />
                              <span className="font-semibold">{t('history.home')}</span>
                            </div>
                            <div className="text-slate-400 text-xs">
                              {teamStats.home.wins}V / {teamStats.home.draws}E / {teamStats.home.losses}D
                            </div>
                          </div>
                          <div>
                            <div className="flex items-center gap-1 text-blue-400 mb-2">
                              <Plane className="w-4 h-4" />
                              <span className="font-semibold">{t('history.away')}</span>
                            </div>
                            <div className="text-slate-400 text-xs">
                              {teamStats.away.wins}V / {teamStats.away.draws}E / {teamStats.away.losses}D
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Lista de Jogos */}
                {teamMatches.length > 0 && (
                  <div className="bg-white/5 backdrop-blur-xl rounded-3xl border border-slate-700 overflow-hidden">
                    <div className="p-6 border-b border-slate-700">
                      <h3 className="text-xl font-bold text-white flex items-center gap-2">
                        <Calendar className="w-5 h-5 text-purple-400" />
                        {t('history.match_history')} ({teamMatches.length})
                      </h3>
                    </div>

                    <div className="divide-y divide-slate-700">
                      {teamMatches.map((match) => (
                        <div key={match.id} className="p-6 hover:bg-white/5 transition-colors">
                          <div className="flex items-center justify-between gap-4">
                            {/* Data e Liga */}
                            <div className="min-w-[120px]">
                              <div className="text-sm text-slate-400">
                                {new Date(match.match_date).toLocaleDateString('pt-BR', {
                                  day: '2-digit',
                                  month: '2-digit',
                                  year: '2-digit'
                                })}
                              </div>
                              <div className="text-xs text-slate-500">{match.league.name}</div>
                            </div>

                            {/* Times e Placar */}
                            <div className="flex-1 flex items-center justify-between gap-4">
                              {/* Time Casa */}
                              <div className={`flex items-center gap-2 ${match.home_team.id === selectedTeam.id ? 'font-bold' : ''}`}>
                                {match.home_team.logo ? (
                                  <img src={match.home_team.logo} alt={match.home_team.name} className="w-8 h-8 object-contain" />
                                ) : (
                                  <div className="w-8 h-8 rounded-full bg-slate-700" />
                                )}
                                <span className={match.home_team.id === selectedTeam.id ? 'text-white' : 'text-slate-300'}>
                                  {match.home_team.name}
                                </span>
                              </div>

                              {/* Placar */}
                              <div className="flex items-center gap-3 px-6 py-2 bg-slate-800 rounded-xl">
                                <span className="text-white font-bold text-lg">{match.home_score}</span>
                                <span className="text-slate-500">-</span>
                                <span className="text-white font-bold text-lg">{match.away_score}</span>
                              </div>

                              {/* Time Fora */}
                              <div className={`flex items-center gap-2 ${match.away_team.id === selectedTeam.id ? 'font-bold' : ''}`}>
                                <span className={match.away_team.id === selectedTeam.id ? 'text-white' : 'text-slate-300'}>
                                  {match.away_team.name}
                                </span>
                                {match.away_team.logo ? (
                                  <img src={match.away_team.logo} alt={match.away_team.name} className="w-8 h-8 object-contain" />
                                ) : (
                                  <div className="w-8 h-8 rounded-full bg-slate-700" />
                                )}
                              </div>
                            </div>

                            {/* Resultado */}
                            <div className="flex items-center gap-3 min-w-[100px] justify-end">
                              <div className="flex items-center gap-2">
                                {match.venue === 'home' ? (
                                  <Home className="w-4 h-4 text-green-400" />
                                ) : (
                                  <Plane className="w-4 h-4 text-blue-400" />
                                )}
                                <span className="text-xs text-slate-400">
                                  {match.venue === 'home' ? t('history.home') : t('history.away')}
                                </span>
                              </div>
                              <ResultBadge result={match.result} />
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {teamMatches.length === 0 && !loading && (
                  <div className="bg-white/5 backdrop-blur-xl rounded-3xl p-12 text-center border border-slate-700">
                    <Trophy className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                    <p className="text-slate-400">
                      {t('history.no_matches')}
                    </p>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* Empty State */}
        {!selectedTeam && (
          <div className="bg-white/5 backdrop-blur-xl rounded-3xl p-12 text-center border border-slate-700">
            <Search className="w-16 h-16 text-slate-600 mx-auto mb-4" />
            <h3 className="text-xl font-bold text-white mb-2">
              {t('history.search_to_start')}
            </h3>
            <p className="text-slate-400 max-w-md mx-auto">
              {t('history.search_description')}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default History;
