import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Newspaper,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  User,
  Heart,
  Bell,
  Search,
  Activity,
  Target,
  X,
  RefreshCw,
  ExternalLink,
  Clock
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';

import { StatCard, LiveBadge } from '../components/UI';
import { formatMatchDateTime } from '../utils/dateUtils';
import APIService from '../services/api';

// Real news from external APIs
interface NewsItem {
  id: string;
  title: string;
  description: string;
  url: string;
  source: {
    id: string;
    name: string;
  };
  author?: string;
  publishedAt: string;
  urlToImage?: string;
  category: string;
  language: string;
}

// RSS Feed Item structure
interface RSSItem {
  title: string;
  description: string;
  link: string;
  pubDate: string;
  source: string;
  category: string;
}

// Real leagues and competitions
interface League {
  id: string;
  name: string;
  country: string;
  season: string;
  rssUrl?: string;
  keywords: string[];
}

// Search filters for real news
interface NewsFilters {
  league: string;
  category: string;
  language: string;
  sortBy: string;
  timeRange: string;
}

// Real leagues configuration
const LEAGUES: League[] = [
  {
    id: 'brasileirao',
    name: 'Brasileirão Série A',
    country: 'Brazil',
    season: '2024',
    keywords: ['brasileirão', 'serie a', 'campeonato brasileiro', 'flamengo', 'palmeiras', 'santos', 'corinthians', 'são paulo', 'vasco', 'botafogo', 'grêmio', 'internacional']
  },
  {
    id: 'libertadores',
    name: 'Copa Libertadores',
    country: 'South America',
    season: '2024',
    keywords: ['libertadores', 'conmebol', 'copa libertadores', 'final', 'semifinal', 'oitavas', 'fase de grupos']
  },
  {
    id: 'sudamericana',
    name: 'Copa Sul-Americana',
    country: 'South America',
    season: '2024',
    keywords: ['sul-americana', 'sudamericana', 'conmebol sudamericana', 'copa sul-americana']
  },
  {
    id: 'premier-league',
    name: 'Premier League',
    country: 'England',
    season: '2024-25',
    keywords: ['premier league', 'manchester', 'liverpool', 'chelsea', 'arsenal', 'tottenham', 'manchester city', 'manchester united']
  },
  {
    id: 'la-liga',
    name: 'La Liga',
    country: 'Spain',
    season: '2024-25',
    keywords: ['la liga', 'real madrid', 'barcelona', 'atletico madrid', 'valencia', 'sevilla', 'el clasico']
  }
];

// Mapeamento de ligas para IDs usados pela API
const LEAGUE_ID_MAP: Record<string, string> = {
  'brasileirao': 'brasileirao',
  'libertadores': 'libertadores',
  'sudamericana': 'sudamericana',
  'premier-league': 'premier-league',
  'la-liga': 'la-liga',
  'all': 'all'
};

const NewsInjuries: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'news' | 'injuries' | 'alerts'>('news');
  const [filters, setFilters] = useState<NewsFilters>({
    league: 'brasileirao',
    category: 'all',
    language: 'pt',
    sortBy: 'publishedAt',
    timeRange: '24h'
  });
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedNews, setSelectedNews] = useState<NewsItem | null>(null);

  // Real API queries para notícias
  const { data: newsResponse, isLoading: newsLoading, refetch: refetchNews } = useQuery({
    queryKey: ['football-news', filters.league, filters.timeRange],
    queryFn: async () => {
      const leagueId = LEAGUE_ID_MAP[filters.league] || 'all';
      const response = await APIService.getNewsFromRSS(leagueId, 50);
      return response;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 10 * 60 * 1000, // 10 minutes
  });

  const news = newsResponse?.items || [];

  // Real API queries para lesões
  const { data: injuriesResponse, isLoading: injuriesLoading } = useQuery({
    queryKey: ['football-injuries', filters.league],
    queryFn: async () => {
      const response = await APIService.getInjuries({
        league: filters.league !== 'all' ? filters.league : undefined
      });
      return response;
    },
    staleTime: 30 * 60 * 1000, // 30 minutes
  });

  const injuries = injuriesResponse?.injuries || [];
  const alerts: any[] = []; // Alerts ainda não implementado no backend

  // Handlers
  const handleRefresh = () => {
    refetchNews();
  };

  const handleFilterChange = (key: keyof NewsFilters, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'text-red-400 bg-red-900/20 border-red-500/30';
      case 'high':
        return 'text-orange-400 bg-orange-900/20 border-orange-500/30';
      case 'medium':
        return 'text-yellow-400 bg-yellow-900/20 border-yellow-500/30';
      case 'low':
        return 'text-green-400 bg-green-900/20 border-green-500/30';
      default:
        return 'text-gray-400 bg-gray-900/20 border-gray-500/30';
    }
  };

  const getImpactIcon = (impact: number) => {
    if (impact > 0) return <TrendingUp className="w-4 h-4 text-green-400" />;
    if (impact < 0) return <TrendingDown className="w-4 h-4 text-red-400" />;
    return <Activity className="w-4 h-4 text-gray-400" />;
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'injury': return <Heart className="w-4 h-4" />;
      case 'transfer': return <User className="w-4 h-4" />;
      case 'match': return <Target className="w-4 h-4" />;
      default: return <Newspaper className="w-4 h-4" />;
    }
  };

  const filteredNews = news.filter(item => {
    const matchesFilter = filters.category === 'all' || item.category === filters.category;
    const matchesSearch = !searchTerm ||
      item.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.source.name.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const filteredInjuries = injuries.filter(injury => {
    const matchesFilter = filters.category === 'all' || injury.status === filters.category;
    const matchesSearch = !searchTerm ||
      injury.player_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      injury.team_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      injury.injury_type?.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  if (newsLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-purple-500"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-gradient-to-br from-purple-500 to-pink-600 rounded-2xl">
                <Newspaper className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-white">Notícias & Lesões</h1>
                <p className="text-slate-400">
                  Acompanhe as últimas notícias e relatórios de lesões
                </p>
              </div>
            </div>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <StatCard
              title="Notícias Recentes"
              value={filteredNews.length}
              subtitle={`${news.length} total de ${newsResponse?.sources.length || 0} fontes`}
              icon={<Newspaper className="w-6 h-6" />}
              color="primary"
            />
            <StatCard
              title="Lesões Reportadas"
              value={filteredInjuries.filter(i => i.status === 'injured').length}
              subtitle={`${filteredInjuries.filter(i => i.status === 'recovering').length} em recuperação`}
              icon={<AlertTriangle className="w-6 h-6" />}
              color="warning"
            />
            <StatCard
              title="Fontes Ativas"
              value={newsResponse?.sources.length || 0}
              subtitle={`Atualizando a cada 10min`}
              icon={<Bell className="w-6 h-6" />}
              color="accent"
            />
          </div>
        </div>

        {/* Tabs */}
        <div className="flex space-x-1 mb-8 bg-slate-800/30 p-1 rounded-2xl">
          {(['news', 'injuries', 'alerts'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex-1 py-3 px-4 rounded-xl text-sm font-medium transition-all duration-300 ${
                activeTab === tab
                  ? 'bg-gradient-to-r from-purple-500 to-pink-600 text-white shadow-lg'
                  : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
              }`}
            >
              {tab === 'news' ? 'Notícias' : tab === 'injuries' ? 'Lesões' : 'Alertas'}
            </button>
          ))}
        </div>

        {/* Filters */}
        <div className="bg-white/5 backdrop-blur-xl rounded-3xl p-6 mb-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center space-x-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-5 h-5" />
                <input
                  type="text"
                  placeholder="Buscar..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-4 py-2 bg-slate-800/50 border border-slate-700 rounded-xl text-white placeholder-slate-400 focus:border-purple-500 transition-colors"
                />
              </div>

              <select
                value={filters.category}
                onChange={(e) => handleFilterChange('category', e.target.value)}
                className="px-4 py-2 bg-slate-800/50 border border-slate-700 rounded-xl text-white focus:border-purple-500 transition-colors"
              >
                <option value="all">Todos</option>
                {activeTab === 'news' && (
                  <>
                    <option value="injury">Lesões</option>
                    <option value="transfer">Transferências</option>
                    <option value="match">Partidas</option>
                    <option value="general">Geral</option>
                  </>
                )}
                {activeTab === 'injuries' && (
                  <>
                    <option value="injured">Lesionados</option>
                    <option value="recovering">Em Recuperação</option>
                    <option value="fit">Aptos</option>
                  </>
                )}
              </select>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="bg-white/5 backdrop-blur-xl rounded-3xl overflow-hidden">
          {activeTab === 'news' && (
            <div className="divide-y divide-slate-700/50">
              {filteredNews.map((item) => (
                <motion.div
                  key={item.id}
                  className="p-6 hover:bg-white/5 transition-colors cursor-pointer"
                  onClick={() => setSelectedNews(item)}
                  whileHover={{ scale: 1.01 }}
                  whileTap={{ scale: 0.99 }}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-4 flex-1">
                      <div className={`p-2 rounded-xl border ${getSeverityColor('medium')}`}>
                        {getCategoryIcon(item.category)}
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex-1">
                            <div className="flex items-center space-x-2 mb-1">
                              <h3 className="text-lg font-semibold text-white line-clamp-2">
                                {item.title}
                              </h3>
                            </div>
                            <p className="text-slate-400 text-sm mb-3 line-clamp-2">
                              {item.description}
                            </p>
                          </div>
                        </div>

                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-4 text-xs text-slate-500">
                            <span>{item.source.name}</span>
                            <span>{formatMatchDateTime(item.publishedAt)}</span>
                          </div>

                          {item.author && (
                            <span className="text-xs text-slate-500">
                              {item.author}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}

              {filteredNews.length === 0 && (
                <div className="p-12 text-center">
                  <Newspaper className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-slate-400 mb-2">Nenhuma notícia encontrada</h3>
                  <p className="text-slate-500">Tente ajustar seus filtros de busca</p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'injuries' && (
            <div className="divide-y divide-slate-700/50">
              {filteredInjuries.map((injury) => (
                <motion.div
                  key={injury.id}
                  className="p-6 hover:bg-white/5 transition-colors"
                  whileHover={{ scale: 1.01 }}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-4 flex-1">
                      <div className={`p-2 rounded-xl border ${getSeverityColor(injury.severity)}`}>
                        <Heart className="w-4 h-4" />
                      </div>

                      <div className="flex-1">
                        <div className="flex items-start justify-between mb-2">
                          <div>
                            <h3 className="text-lg font-semibold text-white">
                              {injury.player_name} - {injury.team_name}
                            </h3>
                            <p className="text-slate-400 text-sm">
                              {injury.position} • {injury.injury_type}
                            </p>
                          </div>

                          <div className={`px-3 py-1 rounded-full text-xs font-medium ${
                            injury.status === 'injured' ? 'bg-red-900/20 text-red-300' :
                            injury.status === 'recovering' ? 'bg-yellow-900/20 text-yellow-300' :
                            'bg-green-900/20 text-green-300'
                          }`}>
                            {injury.status === 'injured' ? 'Lesionado' :
                             injury.status === 'recovering' ? 'Recuperando' : 'Apto'}
                          </div>
                        </div>

                        <p className="text-slate-400 text-sm mb-3">
                          {injury.description}
                        </p>

                        <div className="flex items-center justify-between text-xs text-slate-500">
                          <span>Retorno previsto: {injury.expected_return ? formatMatchDateTime(injury.expected_return) : 'A definir'}</span>
                          <span>Reportado: {formatMatchDateTime(injury.reported_at)}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}

              {filteredInjuries.length === 0 && (
                <div className="p-12 text-center">
                  <Heart className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-slate-400 mb-2">Nenhuma lesão encontrada</h3>
                  <p className="text-slate-500">Tente ajustar seus filtros de busca</p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'alerts' && (
            <div className="divide-y divide-slate-700/50">
              {alerts.map((alert) => (
                <motion.div
                  key={alert.id}
                  className="p-6 hover:bg-white/5 transition-colors"
                  whileHover={{ scale: 1.01 }}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className={`p-2 rounded-xl border ${alert.enabled ? 'bg-green-900/20 border-green-500/30' : 'bg-gray-900/20 border-gray-500/30'}`}>
                        <Bell className={`w-4 h-4 ${alert.enabled ? 'text-green-400' : 'text-gray-400'}`} />
                      </div>

                      <div>
                        <h3 className="text-lg font-semibold text-white">
                          {alert.type.charAt(0).toUpperCase() + alert.type.slice(1)}: {alert.value}
                        </h3>
                        <p className="text-slate-400 text-sm">
                          Severidades: {alert.severity.join(', ')}
                        </p>
                      </div>
                    </div>

                    <div className={`px-3 py-1 rounded-full text-xs font-medium ${
                      alert.enabled ? 'bg-green-900/20 text-green-300' : 'bg-gray-900/20 text-gray-300'
                    }`}>
                      {alert.enabled ? 'Ativo' : 'Inativo'}
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>

        {/* News Detail Modal */}
        <AnimatePresence>
          {selectedNews && (
            <motion.div
              className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setSelectedNews(null)}
            >
              <motion.div
                className="bg-slate-900 rounded-3xl p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto"
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                onClick={(e) => e.stopPropagation()}
              >
                <div className="flex items-start justify-between mb-6">
                  <div className="flex-1">
                    <h2 className="text-2xl font-bold text-white mb-2">
                      {selectedNews.title}
                    </h2>
                    <p className="text-slate-400">
                      {selectedNews.description}
                    </p>
                  </div>
                  <button
                    onClick={() => setSelectedNews(null)}
                    className="p-2 hover:bg-slate-800 rounded-xl transition-colors"
                  >
                    <X className="w-5 h-5 text-slate-400" />
                  </button>
                </div>

                <div className="space-y-6">
                  {selectedNews.urlToImage && (
                    <img
                      src={selectedNews.urlToImage}
                      alt={selectedNews.title}
                      className="w-full h-64 object-cover rounded-xl"
                    />
                  )}

                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-slate-800/50 rounded-xl p-4">
                      <h3 className="text-sm font-medium text-slate-400 mb-2">Fonte</h3>
                      <p className="text-white">{selectedNews.source.name}</p>
                      {selectedNews.author && (
                        <p className="text-slate-400 text-sm">{selectedNews.author}</p>
                      )}
                    </div>
                    <div className="bg-slate-800/50 rounded-xl p-4">
                      <h3 className="text-sm font-medium text-slate-400 mb-2">Link Original</h3>
                      <a
                        href={selectedNews.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-purple-400 hover:text-purple-300 text-sm flex items-center gap-1"
                      >
                        Ler mais <ExternalLink className="w-3 h-3" />
                      </a>
                    </div>
                  </div>

                  <div className="text-xs text-slate-500 text-center pt-4 border-t border-slate-700">
                    Publicado em {formatMatchDateTime(selectedNews.publishedAt)}
                  </div>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default NewsInjuries;