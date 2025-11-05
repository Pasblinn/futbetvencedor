import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Target,
  TrendingUp,
  BarChart3,
  RefreshCw,
  PlusCircle,
  Trophy,
  Activity,
  Filter,
  ChevronDown,
  X,
} from "lucide-react";
import { StatCard } from "../components/UI/StatCard";
import { LiveBadge } from "../components/UI/LiveBadge";
import { LoadingState, EmptyState } from "../components/UI/LoadingStates";
import { notificationService } from "../services/notifications";
import { PredictionModesHeader } from "../components/Predictions/PredictionModesHeader";
import { AutomaticModeModal } from "../components/Predictions/AutomaticModeModal";
import { AssistedModeModal } from "../components/Predictions/AssistedModeModal";
import { ManualModeModal } from "../components/Predictions/ManualModeModal";
import { AllMarketsModal } from "../components/AllMarketsModal";
import { BettingCart } from "../components/Betting/BettingCart";
import { formatMatchTime, formatMatchDateShort } from "../utils/dateUtils";
import { APIService } from "../services/api";
import { useAuth } from "../contexts/AuthContext";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "../contexts/I18nContext";

// 🎨 FUNÇÕES HELPER PARA LIGAS
const normalizeLeagueName = (league: string): string => {
  if (!league) return 'Outras Ligas';

  const leagueMap: { [key: string]: string } = {
    // Brasil - TODAS AS VARIAÇÕES (com/sem acento, com/sem til)
    'Brasileirão Série A': 'Brasileirão Série A',
    'Brasileirão Serie A': 'Brasileirão Série A',  // sem acento
    'Brasileirao Série A': 'Brasileirão Série A',  // sem til
    'Brasileirao Serie A': 'Brasileirão Série A',  // sem acento e til
    'Brasileirão Série B': 'Brasileirão Série B',
    'Brasileirão Serie B': 'Brasileirão Série B',
    'Brasileirao Série B': 'Brasileirão Série B',
    'Brasileirao Serie B': 'Brasileirão Série B',
    'Campeonato Brasileiro Serie A': 'Brasileirão Série A',
    'Campeonato Brasileiro Série A': 'Brasileirão Série A',
    'Serie A': 'Brasileirão Série A',  // Assume Brasil se não especificar

    // Itália
    'Italy Serie A': 'Itália - Serie A',
    'Italian Serie A': 'Itália - Serie A',
    'Serie A - Italy': 'Itália - Serie A',
    'Serie B - Italy': 'Itália - Serie B',

    // Argentina
    'Liga Profesional Argentina': 'Argentina - Liga Profesional',
    'Liga Profesional': 'Argentina - Liga Profesional',

    // Chile
    'Primera División': 'Chile - Primera División',
    'Primera Division': 'Chile - Primera División',

    // Colômbia
    'Primera A': 'Colômbia - Primera A',

    // Espanha
    'La Liga': 'Espanha - La Liga',
    'LaLiga': 'Espanha - La Liga',
    'La Liga 2': 'Espanha - La Liga 2',
    'LaLiga2': 'Espanha - La Liga 2',

    // Inglaterra
    'Premier League': 'Inglaterra - Premier League',
    'English Premier League': 'Inglaterra - Premier League',
    'Championship': 'Inglaterra - Championship',

    // Alemanha
    'Bundesliga': 'Alemanha - Bundesliga',
    'German Bundesliga': 'Alemanha - Bundesliga',
    'Bundesliga 2': 'Alemanha - 2. Bundesliga',
    '2. Bundesliga': 'Alemanha - 2. Bundesliga',

    // França
    'Ligue 1': 'França - Ligue 1',
    'French Ligue 1': 'França - Ligue 1',
    'Ligue 2': 'França - Ligue 2',

    // Portugal
    'Primeira Liga': 'Portugal - Primeira Liga',
    'Portuguese Primeira Liga': 'Portugal - Primeira Liga',

    // Copas
    'Copa Libertadores': 'Copa Libertadores',
    'CONMEBOL Libertadores': 'Copa Libertadores',
    'Copa Sudamericana': 'Copa Sul-Americana',
    'CONMEBOL Sudamericana': 'Copa Sul-Americana',
    'Copa do Brasil': 'Copa do Brasil',
    'Champions League': 'UEFA Champions League',
    'UEFA Champions League': 'UEFA Champions League',
    'Europa League': 'UEFA Europa League',
    'UEFA Europa League': 'UEFA Europa League',
  };

  // Normalizar removendo espaços extras e convertendo para comparação
  const cleanLeague = league.trim();

  // Tentar match exato primeiro
  if (leagueMap[cleanLeague]) {
    return leagueMap[cleanLeague];
  }

  // Caso especial: se já está no formato "País - Liga", retornar como está
  if (cleanLeague.includes(' - ')) {
    return cleanLeague;
  }

  // Se não encontrou no mapa e não tem formato padrão, retornar original
  return cleanLeague;
};

const getLeagueColors = (league: string): { bg: string; text: string; border: string } => {
  const leagueNormalized = league.toLowerCase();

  // Brasil - Verde e Amarelo (menos saturado)
  if (leagueNormalized.includes('brasil') || leagueNormalized.includes('serie a') || leagueNormalized.includes('serie b')) {
    return {
      bg: 'bg-gradient-to-r from-green-700/80 to-yellow-600/80',
      text: 'text-white',
      border: 'border-green-700'
    };
  }

  // Argentina - Azul claro (menos saturado)
  if (leagueNormalized.includes('argentina')) {
    return {
      bg: 'bg-gradient-to-r from-sky-600/80 to-blue-700/80',
      text: 'text-white',
      border: 'border-sky-700'
    };
  }

  // Chile - Vermelho e azul (menos saturado)
  if (leagueNormalized.includes('chile')) {
    return {
      bg: 'bg-gradient-to-r from-red-700/80 to-blue-800/80',
      text: 'text-white',
      border: 'border-red-700'
    };
  }

  // Colômbia - Amarelo e azul (menos saturado)
  if (leagueNormalized.includes('colômbia') || leagueNormalized.includes('colombia')) {
    return {
      bg: 'bg-gradient-to-r from-yellow-600/80 to-blue-700/80',
      text: 'text-white',
      border: 'border-yellow-700'
    };
  }

  // Itália - Verde, branco e vermelho (menos saturado)
  if (leagueNormalized.includes('itália') || leagueNormalized.includes('italy') || (leagueNormalized.includes('serie') && !leagueNormalized.includes('brasil'))) {
    return {
      bg: 'bg-gradient-to-r from-green-700/70 via-gray-100/90 to-red-700/70',
      text: 'text-gray-800',
      border: 'border-green-800'
    };
  }

  // Espanha - Vermelho e amarelo (menos saturado)
  if (leagueNormalized.includes('espanha') || leagueNormalized.includes('spain') || leagueNormalized.includes('la liga')) {
    return {
      bg: 'bg-gradient-to-r from-red-700/80 to-yellow-600/80',
      text: 'text-white',
      border: 'border-red-800'
    };
  }

  // Inglaterra - Roxo e rosa (menos saturado)
  if (leagueNormalized.includes('inglaterra') || leagueNormalized.includes('england') || leagueNormalized.includes('premier')) {
    return {
      bg: 'bg-gradient-to-r from-purple-800/80 to-pink-700/80',
      text: 'text-white',
      border: 'border-purple-900'
    };
  }

  // Alemanha - Preto, vermelho e amarelo (menos saturado)
  if (leagueNormalized.includes('alemanha') || leagueNormalized.includes('germany') || leagueNormalized.includes('bundesliga')) {
    return {
      bg: 'bg-gradient-to-r from-gray-900/80 via-red-700/80 to-yellow-600/80',
      text: 'text-white',
      border: 'border-gray-900'
    };
  }

  // França - Azul e vermelho (menos saturado)
  if (leagueNormalized.includes('frança') || leagueNormalized.includes('france') || leagueNormalized.includes('ligue')) {
    return {
      bg: 'bg-gradient-to-r from-blue-800/80 to-red-700/80',
      text: 'text-white',
      border: 'border-blue-900'
    };
  }

  // Portugal - Verde e vermelho (menos saturado)
  if (leagueNormalized.includes('portugal') || leagueNormalized.includes('primeira liga')) {
    return {
      bg: 'bg-gradient-to-r from-green-800/80 to-red-800/80',
      text: 'text-white',
      border: 'border-green-900'
    };
  }

  // Padrão - Cinza
  return {
    bg: 'bg-gradient-to-r from-gray-600/80 to-gray-700/80',
    text: 'text-white',
    border: 'border-gray-700'
  };
};

interface Match {
  id: string;
  homeTeam: string;
  awayTeam: string;
  league: string;
  date: string;
  time: string;
  odds: {
    home: number;
    draw: number;
    away: number;
  };
  confidence: number;
  value: number;
  recommendation: "home" | "draw" | "away";
  prediction?: {
    ensemble_prediction: string;
    confidence: number;
    individual_predictions: any;
  };
}

interface TicketItem {
  match: Match;
  selection: "home" | "draw" | "away";  // Mantém para compatibilidade com 1X2
  marketId?: string;  // ID do mercado (OVER_2_5, BTTS_YES, etc)
  marketName?: string;  // Nome traduzido do mercado
  odds?: number;  // Odd específica do mercado
  stake: number;
  kellyPercentage: number;
  market: string; // ID único para identificar diferentes mercados do mesmo match
}

const Predictions: React.FC = () => {
  const { token } = useAuth();
  const { t } = useTranslation();
  const [availableMatches, setAvailableMatches] = useState<Match[]>([]);
  const [selectedMatches, setSelectedMatches] = useState<TicketItem[]>([]);
  const [loading, setLoading] = useState(false);

  // 🎯 Estados para os 3 modos de predictions
  const [predictionMode, setPredictionMode] = useState<'automatic' | 'assisted' | 'manual'>('automatic');
  const [isAutomaticModalOpen, setIsAutomaticModalOpen] = useState(false);
  const [isAssistedModalOpen, setIsAssistedModalOpen] = useState(false);
  const [isManualModalOpen, setIsManualModalOpen] = useState(false);

  // 📊 Estado para All Markets Modal
  const [isAllMarketsModalOpen, setIsAllMarketsModalOpen] = useState(false);
  const [selectedMatchForMarkets, setSelectedMatchForMarkets] = useState<Match | null>(null);

  // 🔍 NOVO: Estados para filtros
  const [selectedLeague, setSelectedLeague] = useState<string>('all');
  const [minConfidence, setMinConfidence] = useState<number>(0);
  const [minValue, setMinValue] = useState<number>(0);
  const [showFilters, setShowFilters] = useState(false);

  // Buscar banca do usuário
  const { data: userBankroll } = useQuery({
    queryKey: ['bankroll'],
    queryFn: async () => {
      const response = await fetch('http://localhost:8000/api/v1/user/bankroll', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      if (!response.ok) throw new Error('Failed to fetch bankroll');
      return response.json();
    },
    enabled: !!token,
  });

  const bankroll = userBankroll?.current_bankroll || 1000;

  useEffect(() => {
    loadAvailableMatches();
  }, []);

  const loadAvailableMatches = async () => {
    setLoading(true);

    try {
      // Load real upcoming matches from API using the new endpoint
      const upcomingData = await APIService.getUpcomingPredictions(7, 50);

      if (!upcomingData || !upcomingData.matches) {
        throw new Error("No upcoming matches found");
      }

      console.log(
        "🏆 Loaded upcoming matches:",
        upcomingData.matches.length,
      );

      const matches: Match[] = [];

      // Process real upcoming matches from the API
      for (const apiMatch of upcomingData.matches) {
        try {
          // FILTRAR JOGOS FINALIZADOS
          if (apiMatch.status && ['FT', 'AET', 'PEN', 'FINISHED'].includes(apiMatch.status)) {
            continue; // Pular jogos já finalizados
          }

          // Skip matches without predictions
          if (!apiMatch.prediction) {
            continue;
          }

          // Extract date and time from API response
          // ⚠️ VALIDAR match_date antes de usar
          if (!apiMatch.match_date) {
            console.error(`❌ ERRO: Match ${apiMatch.match_id} SEM DATA!`);
            continue; // Pular jogos sem data
          }

          // 🎯 USAR APENAS ODDS REAIS DA API - SEM FALLBACK!
          const apiOdds = (apiMatch.prediction as any).odds; // Forçar acesso às odds

          // ⚠️ SE NÃO HOUVER ODDS REAIS, MOSTRAR ERRO ÓBVIO
          const odds = apiOdds && apiOdds.home && apiOdds.draw && apiOdds.away ? {
            home: parseFloat(apiOdds.home.toFixed(2)),
            draw: parseFloat(apiOdds.draw.toFixed(2)),
            away: parseFloat(apiOdds.away.toFixed(2)),
          } : {
            // ❌ ERRO: Odds não disponíveis - valores óbvios de erro
            home: 999.99,
            draw: 999.99,
            away: 999.99,
          };

          // Pular matches sem odds reais
          if (odds.home === 999.99) {
            console.error(`❌ ERRO: Match ${apiMatch.match_id} (${apiMatch.home_team.name} vs ${apiMatch.away_team.name}) SEM ODDS REAIS!`);
            continue; // Não mostrar jogos sem odds reais
          }

          // Use confidence from API
          const confidence = apiMatch.prediction.confidence_score;
          const value = confidence > 0.4 ? (confidence - 0.4) * 0.5 : 0;

          // Use prediction from API
          const recommendation =
            apiMatch.prediction.predicted_outcome === "1"
              ? "home"
              : apiMatch.prediction.predicted_outcome === "2"
                ? "away"
                : "draw";

          const match: Match = {
            id: apiMatch.match_id.toString(),
            homeTeam: apiMatch.home_team.name,
            awayTeam: apiMatch.away_team.name,
            league: normalizeLeagueName(apiMatch.league.name), // 🌍 Normalizar nome da liga com país
            date: apiMatch.match_date, // ✅ ARMAZENAR DATA RAW
            time: formatMatchTime(apiMatch.match_date), // ✅ Formatar apenas o horário
            odds: odds,
            confidence: confidence,
            value: value,
            recommendation: recommendation,
            prediction: {
              ensemble_prediction: apiMatch.prediction.predicted_outcome,
              confidence: confidence,
              individual_predictions: {
                home_prob: odds.home > 0 ? 1 / odds.home : 0.33,
                draw_prob: odds.draw > 0 ? 1 / odds.draw : 0.33,
                away_prob: odds.away > 0 ? 1 / odds.away : 0.33,
              },
            },
          };

          matches.push(match);
        } catch (error) {
          console.error(`Error processing match ${apiMatch.match_id}:`, error);
        }
      }

      // Sort matches by date
      matches.sort(
        (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime(),
      );
      setAvailableMatches(matches);
    } catch (error) {
      console.error("Error loading matches:", error);
      notificationService.addNotification({
        type: "error",
        title: t('predictions.error_loading'),
        message: t('predictions.error_loading_message'),
      });
    } finally {
      setLoading(false);
    }
  };


  // 🔥 Adiciona qualquer mercado ao bilhete (via 3 modos ou AllMarketsModal)
  const addMarketToTicket = (
    match: Match,
    marketId: string,
    marketName: string,
    odds: number,
    skipCheckboxValidation: boolean = false
  ) => {
    // Create unique market identifier
    const uniqueMarketId = `${match.id}-${marketId}`;

    // Check if this specific market is already selected
    const isMarketAlreadySelected = selectedMatches.some(
      (item) => item.market === uniqueMarketId,
    );

    if (isMarketAlreadySelected) {
      notificationService.addNotification({
        type: "warning",
        title: t('predictions.market_already_selected'),
        message: `${match.homeTeam} vs ${match.awayTeam} - ${marketName} ${t('predictions.already_in_ticket')}`,
      });
      return;
    }

    // Limite máximo de 10 mercados no bilhete
    if (selectedMatches.length >= 10) {
      notificationService.addNotification({
        type: "warning",
        title: t('predictions.limit_reached'),
        message: t('predictions.max_markets_message'),
      });
      return;
    }

    const newItem: TicketItem = {
      match,
      selection: "home", // Fallback para compatibilidade
      marketId: marketId,
      marketName: marketName,
      odds: odds,
      stake: 0, // Será definido pelo usuário no BettingCart
      kellyPercentage: 0,
      market: uniqueMarketId,
    };

    setSelectedMatches((prev) => [...prev, newItem]);

    notificationService.addNotification({
      type: "success",
      title: t('predictions.market_added'),
      message: `${match.homeTeam} vs ${match.awayTeam} - ${marketName} @ ${odds.toFixed(2)}`,
    });
  };

  // Função legada para 1X2 (mantém compatibilidade)
  const addToTicket = (match: Match, selection: "home" | "draw" | "away", skipCheckboxValidation: boolean = false) => {
    // Map selection to marketId
    const marketIdMap: Record<string, string> = {
      'home': 'HOME_WIN',
      'draw': 'DRAW',
      'away': 'AWAY_WIN',
    };
    const marketNameMap: Record<string, string> = {
      'home': t('predictions.home_win'),
      'draw': t('predictions.draw'),
      'away': t('predictions.away_win'),
    };

    const marketId = marketIdMap[selection];
    const marketName = marketNameMap[selection];
    const odds = match.odds[selection];

    // Use the new function
    addMarketToTicket(match, marketId, marketName, odds, skipCheckboxValidation);
  };

  const removeFromTicket = (index: number) => {
    setSelectedMatches((prev) => prev.filter((_, i) => i !== index));
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return "text-primary-400";
    if (confidence >= 0.7) return "text-accent-400";
    return "text-text-tertiary";
  };

  const getValueColor = (value: number) => {
    if (value >= 0.15) return "text-primary-400";
    if (value >= 0.1) return "text-accent-400";
    return "text-text-tertiary";
  };

  // 🎯 Handler para mudar modo e abrir modal
  const handleModeChange = (mode: 'automatic' | 'assisted' | 'manual') => {
    setPredictionMode(mode);
    if (mode === 'automatic') {
      setIsAutomaticModalOpen(true);
    } else if (mode === 'assisted') {
      setIsAssistedModalOpen(true);
    } else if (mode === 'manual') {
      setIsManualModalOpen(true);
    }
  };

  // 🔍 Filtrar matches baseado nos filtros ativos
  const filteredMatches = availableMatches.filter(match => {
    // Filtro de liga
    if (selectedLeague !== 'all' && match.league !== selectedLeague) {
      return false;
    }

    // Filtro de confiança mínima
    if (match.confidence < minConfidence / 100) {
      return false;
    }

    // Filtro de value mínimo
    if (match.value < minValue / 100) {
      return false;
    }

    return true;
  });

  // Obter lista única de ligas
  const uniqueLeagues = Array.from(new Set(availableMatches.map(m => m.league))).sort();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-bg-card rounded-lg border border-border-subtle p-4 md:p-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 md:gap-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-primary-600/20 rounded-lg flex items-center justify-center flex-shrink-0">
              <Target className="w-5 h-5 text-primary-400" />
            </div>
            <div className="min-w-0">
              <h2 className="text-base md:text-lg font-semibold text-text-primary">
                {t('predictions.bet_generator')}
              </h2>
              <p className="text-xs md:text-sm text-text-secondary truncate">
                {t('predictions.kelly_ai_desc')}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 md:gap-3">
            <button
              onClick={() => {
                setSelectedMatches([]);
              }}
              className="bg-accent-600 text-white px-3 md:px-4 py-2 rounded-lg hover:bg-accent-700 transition-all flex items-center gap-2 text-sm md:text-base whitespace-nowrap"
            >
              <RefreshCw className="w-4 h-4 flex-shrink-0" />
              <span className="hidden sm:inline">{t('predictions.clear_ticket')}</span>
              <span className="sm:hidden">{t('predictions.clear')}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
        <StatCard
          title={t('predictions.available_matches')}
          value={filteredMatches.length !== availableMatches.length
            ? `${filteredMatches.length}/${availableMatches.length}`
            : availableMatches.length}
          icon={<Target className="w-5 h-5 text-primary-400" />}
          color={filteredMatches.length < availableMatches.length ? "accent" : "primary"}
        />
        <StatCard
          title={t('predictions.markets_in_ticket')}
          value={selectedMatches.length}
          icon={<PlusCircle className="w-5 h-5 text-accent-400" />}
          color={selectedMatches.length > 0 ? "success" : "accent"}
        />
        <StatCard
          title={t('predictions.bankroll')}
          value={`R$ ${bankroll.toLocaleString()}`}
          icon={<TrendingUp className="w-5 h-5 text-primary-400" />}
          color="success"
        />
      </div>

      {/* 🎯 Header dos 3 Modos de Predictions */}
      <PredictionModesHeader
        activeMode={predictionMode}
        onModeChange={handleModeChange}
      />

      {/* 🔍 NOVO: Filtros */}
      <div className="bg-bg-card rounded-lg border border-border-subtle overflow-hidden">
        {/* Header de Filtros */}
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="w-full p-4 flex items-center justify-between hover:bg-bg-secondary transition-colors"
        >
          <div className="flex items-center gap-2">
            <Filter className="w-5 h-5 text-primary-400" />
            <h3 className="text-base md:text-lg font-semibold text-text-primary">
              {t('predictions.filters')}
            </h3>
            {(selectedLeague !== 'all' || minConfidence > 0 || minValue > 0) && (
              <span className="px-2 py-1 bg-primary-600/20 text-primary-400 rounded text-xs font-medium">
                {t('predictions.active')}
              </span>
            )}
          </div>
          <ChevronDown className={`w-5 h-5 text-text-tertiary transition-transform ${showFilters ? 'rotate-180' : ''}`} />
        </button>

        {/* Painel de Filtros */}
        {showFilters && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t border-border-subtle p-4 bg-bg-elevated"
          >
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Filtro de Liga */}
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  {t('predictions.league')}
                </label>
                <select
                  value={selectedLeague}
                  onChange={(e) => setSelectedLeague(e.target.value)}
                  className="w-full bg-bg-card border border-border-primary rounded-lg px-3 py-2 text-text-primary focus:outline-none focus:ring-2 focus:ring-primary-400"
                >
                  <option value="all">{t('predictions.all_leagues')} ({availableMatches.length})</option>
                  {uniqueLeagues.map(league => (
                    <option key={league} value={league}>
                      {league} ({availableMatches.filter(m => m.league === league).length})
                    </option>
                  ))}
                </select>
              </div>

              {/* Filtro de Confiança */}
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  {t('predictions.min_confidence')}: {minConfidence}%
                </label>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={minConfidence}
                  onChange={(e) => setMinConfidence(parseInt(e.target.value))}
                  className="w-full h-2 bg-bg-secondary rounded-lg appearance-none cursor-pointer accent-primary-400"
                />
                <div className="flex justify-between text-xs text-text-tertiary mt-1">
                  <span>0%</span>
                  <span>50%</span>
                  <span>100%</span>
                </div>
              </div>

              {/* Filtro de Value */}
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  {t('predictions.min_value')}: {minValue}%
                </label>
                <input
                  type="range"
                  min="0"
                  max="50"
                  value={minValue}
                  onChange={(e) => setMinValue(parseInt(e.target.value))}
                  className="w-full h-2 bg-bg-secondary rounded-lg appearance-none cursor-pointer accent-accent-400"
                />
                <div className="flex justify-between text-xs text-text-tertiary mt-1">
                  <span>0%</span>
                  <span>25%</span>
                  <span>50%</span>
                </div>
              </div>
            </div>

            {/* Botão Limpar Filtros */}
            {(selectedLeague !== 'all' || minConfidence > 0 || minValue > 0) && (
              <div className="mt-4 flex justify-end">
                <button
                  onClick={() => {
                    setSelectedLeague('all');
                    setMinConfidence(0);
                    setMinValue(0);
                  }}
                  className="px-4 py-2 bg-bg-secondary hover:bg-bg-tertiary text-text-primary rounded-lg transition-colors flex items-center gap-2 text-sm"
                >
                  <X className="w-4 h-4" />
                  {t('predictions.clear_filters')}
                </button>
              </div>
            )}
          </motion.div>
        )}
      </div>

      {/* 🎯 Modais dos 3 Modos */}
      <AutomaticModeModal
        isOpen={isAutomaticModalOpen}
        onClose={() => setIsAutomaticModalOpen(false)}
        onAddToTicket={(pred) => {
          // Convert AutomaticPrediction to Match format
          const match: Match = {
            id: pred.match_id.toString(),
            homeTeam: pred.match_info.home_team,
            awayTeam: pred.match_info.away_team,
            league: pred.match_info.league,
            date: pred.match_info.match_date,
            time: new Date(pred.match_info.match_date).toLocaleTimeString('pt-BR', {
              hour: '2-digit',
              minute: '2-digit'
            }),
            odds: {
              home: pred.prediction.market_type === '1X2' && pred.prediction.outcome === '1' ? pred.prediction.odds : 2.0,
              draw: pred.prediction.market_type === '1X2' && pred.prediction.outcome === 'X' ? pred.prediction.odds : 3.0,
              away: pred.prediction.market_type === '1X2' && pred.prediction.outcome === '2' ? pred.prediction.odds : 2.5,
            },
            confidence: pred.ai_validation.ai_confidence,
            value: pred.ai_validation.edge_percentage / 100,
            recommendation: pred.prediction.outcome === '1' ? 'home' : pred.prediction.outcome === 'X' ? 'draw' : 'away',
          };

          // Determine selection based on outcome
          const selection: "home" | "draw" | "away" =
            pred.prediction.outcome === '1' ? 'home' :
            pred.prediction.outcome === 'X' ? 'draw' : 'away';

          // Add to ticket using existing function (skip checkbox validation for automatic mode)
          addToTicket(match, selection, true);
        }}
      />

      <AssistedModeModal
        isOpen={isAssistedModalOpen}
        onClose={() => setIsAssistedModalOpen(false)}
        availableMatches={availableMatches}
      />

      <ManualModeModal
        isOpen={isManualModalOpen}
        onClose={() => setIsManualModalOpen(false)}
        availableMatches={availableMatches}
      />

      {/* 📊 NOVO: Modal All Markets */}
      <AllMarketsModal
        isOpen={isAllMarketsModalOpen}
        onClose={() => {
          setIsAllMarketsModalOpen(false);
          setSelectedMatchForMarkets(null);
        }}
        matchId={selectedMatchForMarkets?.id ? parseInt(selectedMatchForMarkets.id) : 0}
        matchInfo={
          selectedMatchForMarkets
            ? {
                homeTeam: selectedMatchForMarkets.homeTeam,
                awayTeam: selectedMatchForMarkets.awayTeam,
                league: selectedMatchForMarkets.league,
                matchDate: selectedMatchForMarkets.date,
              }
            : undefined
        }
      />

      {/* 🛒 Betting Cart */}
      <BettingCart
        selectedBets={selectedMatches}
        onRemoveBet={removeFromTicket}
        onPlaceBet={(stake) => {
          notificationService.addNotification({
            type: 'success',
            title: t('predictions.bet_created'),
            message: t('predictions.ticket_created').replace('{amount}', stake.toFixed(2)),
          });
          // TODO: Implement actual bet placement
        }}
        onClearAll={() => {
          setSelectedMatches([]);
          notificationService.addNotification({
            type: 'info',
            title: t('predictions.ticket_cleared'),
            message: t('predictions.all_bets_removed'),
          });
        }}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Available Matches */}
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-bg-card rounded-lg border border-border-subtle p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-semibold text-text-primary">
                  {t('predictions.available_matches')}
                </h3>
                <p className="text-sm text-text-secondary">
                  {t('predictions.use_modes_instruction')}
                </p>
              </div>
              <button
                onClick={loadAvailableMatches}
                disabled={loading}
                className="p-2 hover:bg-bg-secondary rounded-lg transition-all"
              >
                <RefreshCw
                  className={`w-4 h-4 text-text-secondary ${loading ? "animate-spin" : ""}`}
                />
              </button>
            </div>

            {loading ? (
              <LoadingState
                type="skeleton"
                message={t('predictions.loading_matches')}
              />
            ) : filteredMatches.length === 0 ? (
              <EmptyState
                icon={<Target className="w-8 h-8 text-text-tertiary" />}
                title={availableMatches.length > 0 ? t('predictions.no_matches_found') : t('predictions.no_matches_available')}
                description={availableMatches.length > 0 ? t('predictions.no_matches_filters') : t('predictions.no_matches_scheduled')}
                action={{
                  label: availableMatches.length > 0 ? t('predictions.clear_filters') : t('predictions.reload'),
                  onClick: availableMatches.length > 0 ? () => {
                    setSelectedLeague('all');
                    setMinConfidence(0);
                    setMinValue(0);
                  } : loadAvailableMatches,
                  loading: loading,
                }}
              />
            ) : (
              <div className="space-y-6">
                {/* Organizar por liga e data */}
                {Object.entries(
                  filteredMatches
                    // Agrupar por liga primeiro
                    .reduce((acc, match) => {
                      const league = match.league === 'Outras Ligas' ? t('predictions.other_leagues') : (match.league || t('predictions.other_leagues'));
                      if (!acc[league]) acc[league] = [];
                      acc[league].push(match);
                      return acc;
                    }, {} as Record<string, Match[]>)
                )
                  // Ordenar ligas alfabeticamente
                  .sort(([leagueA], [leagueB]) => leagueA.localeCompare(leagueB))
                  .map(([league, matches]) => {
                    const colors = getLeagueColors(league);
                    return (
                      <div key={league} className="space-y-4 mb-8">
                      {/* Cabeçalho da Liga - Com Cores do País */}
                      <motion.div
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="sticky top-0 z-20 mb-4"
                      >
                        <div className={`${colors.bg} border-l-4 ${colors.border} rounded-r-lg p-3 md:p-4 backdrop-blur-md shadow-lg`}>
                          <div className="flex items-center justify-between gap-2">
                            <div className="flex items-center gap-2 md:gap-4 min-w-0 flex-1">
                              <div className="bg-white/20 p-2 md:p-3 rounded-lg backdrop-blur-sm flex-shrink-0">
                                <Trophy className={`w-5 h-5 md:w-6 md:h-6 ${colors.text}`} />
                              </div>
                              <div className="min-w-0 flex-1">
                                <h3 className={`text-base md:text-xl font-bold ${colors.text} tracking-wide truncate`}>
                                  {league}
                                </h3>
                                <div className="flex flex-wrap items-center gap-2 md:gap-3 mt-1">
                                  <span className={`text-xs md:text-sm ${colors.text} opacity-90 flex items-center gap-1`}>
                                    <Target className="w-3 h-3 md:w-4 md:h-4 flex-shrink-0" />
                                    <span className="whitespace-nowrap">{matches.length} {matches.length === 1 ? t('predictions.match_single') : t('predictions.match_plural')}</span>
                                  </span>
                                  <span className="px-2 py-0.5 bg-white/30 text-white rounded-full text-xs font-medium backdrop-blur-sm whitespace-nowrap">
                                    {t('predictions.status_active')}
                                  </span>
                                </div>
                              </div>
                            </div>
                            <div className={`hidden md:flex items-center gap-2 text-sm ${colors.text} opacity-90 flex-shrink-0`}>
                              <Activity className="w-4 h-4" />
                              <span className="whitespace-nowrap">{t('predictions.real_odds')}</span>
                            </div>
                          </div>
                        </div>
                      </motion.div>

                      {/* Jogos da Liga - Ordenados por data (mais próximos primeiro) */}
                      {matches
                        .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
                        .map((match) => (
                        <motion.div
                          key={match.id}
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          className="bg-bg-secondary rounded-lg p-3 md:p-4 hover:bg-bg-tertiary transition-all"
                        >
                          <div className="flex items-start justify-between mb-3 gap-2">
                            <div className="flex-1 min-w-0">
                              <h4 className="font-medium text-text-primary truncate">
                                {match.homeTeam} <span className="text-text-tertiary">{t('predictions.vs')}</span> {match.awayTeam}
                              </h4>
                              <p className="text-xs md:text-sm text-text-secondary">
                                📅 {formatMatchDateShort(match.date)} • ⏰ {match.time}
                              </p>
                            </div>
                            <LiveBadge status="upcoming" />
                          </div>

                          <div className="bg-gradient-to-r from-primary-600/10 to-accent-600/10 p-3 rounded-lg mb-3">
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-xs font-medium text-text-secondary">{t('predictions.ai_prediction')}</span>
                              <span className="px-2 py-1 bg-primary-600/20 text-primary-400 rounded text-xs font-bold">
                                {match.recommendation.toUpperCase()}
                              </span>
                            </div>
                            <div className="grid grid-cols-3 gap-2">
                              <div className={`text-center p-2 rounded ${match.recommendation === 'home' ? 'bg-primary-600/20' : 'bg-bg-secondary/50'}`}>
                                <div className="text-xs text-text-tertiary">{t('predictions.home')}</div>
                                <div className="font-mono font-bold text-text-primary text-sm">
                                  {match.odds.home.toFixed(2)}
                                </div>
                              </div>
                              <div className={`text-center p-2 rounded ${match.recommendation === 'draw' ? 'bg-primary-600/20' : 'bg-bg-secondary/50'}`}>
                                <div className="text-xs text-text-tertiary">{t('predictions.draw')}</div>
                                <div className="font-mono font-bold text-text-primary text-sm">
                                  {match.odds.draw.toFixed(2)}
                                </div>
                              </div>
                              <div className={`text-center p-2 rounded ${match.recommendation === 'away' ? 'bg-primary-600/20' : 'bg-bg-secondary/50'}`}>
                                <div className="text-xs text-text-tertiary">{t('predictions.away')}</div>
                                <div className="font-mono font-bold text-text-primary text-sm">
                                  {match.odds.away.toFixed(2)}
                                </div>
                              </div>
                            </div>
                          </div>

                          <div className="flex flex-wrap items-center justify-between gap-2 text-sm mb-3">
                            <div className="flex flex-wrap items-center gap-2 md:gap-4">
                              <span className="flex items-center gap-1 text-xs md:text-sm">
                                <div className="w-2 h-2 bg-primary-400 rounded-full flex-shrink-0"></div>
                                <span
                                  className={getConfidenceColor(match.confidence)}
                                >
                                  {(match.confidence * 100).toFixed(0)}% conf.
                                </span>
                              </span>
                              <span className="flex items-center gap-1 text-xs md:text-sm">
                                <div className="w-2 h-2 bg-accent-400 rounded-full flex-shrink-0"></div>
                                <span className={getValueColor(match.value)}>
                                  {(match.value * 100).toFixed(0)}% value
                                </span>
                              </span>
                            </div>
                            <span className="px-2 py-1 bg-primary-600/20 text-primary-400 rounded text-xs font-medium whitespace-nowrap">
                              {match.recommendation.toUpperCase()}
                            </span>
                          </div>

                          {/* Botão Ver Todos os Mercados */}
                          <button
                            onClick={() => {
                              setSelectedMatchForMarkets(match);
                              setIsAllMarketsModalOpen(true);
                            }}
                            className="w-full py-2 px-3 md:px-4 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-lg transition-all flex items-center justify-center gap-2 font-medium text-xs md:text-sm"
                          >
                            <BarChart3 size={16} className="flex-shrink-0" />
                            <span className="hidden sm:inline">{t('predictions.view_all_markets')}</span>
                            <span className="sm:hidden">{t('predictions.all_markets')}</span>
                          </button>
                        </motion.div>
                      ))}
                    </div>
                    );
                  })}
              </div>
            )}
          </div>
        </div>

        {/* Coluna lateral - Escondida em mobile */}
        <div className="space-y-4 lg:block hidden">
          <div className="bg-bg-card rounded-lg border border-border-subtle p-6 sticky top-4">
            <h3 className="text-lg font-semibold text-text-primary mb-4">
              💡 {t('predictions.tip')}
            </h3>
            <p className="text-sm text-text-secondary leading-relaxed">
              {t('predictions.tip_description')}
            </p>
            <ul className="mt-3 space-y-2 text-sm text-text-secondary">
              <li>{t('predictions.automatic_mode')}</li>
              <li>{t('predictions.assisted_mode')}</li>
              <li>{t('predictions.manual_mode')}</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Educational Footer */}
      <div className="bg-bg-card rounded-lg border border-border-subtle p-4 md:p-6">
        <div className="text-center">
          <h4 className="text-base md:text-lg font-semibold text-text-primary mb-2">
            🎯 {t('predictions.kelly_title')}
          </h4>
          <p className="text-xs md:text-sm text-text-secondary leading-relaxed">
            {t('predictions.kelly_description')}
            <strong className="text-text-primary">
              {" "}
              {t('predictions.educational_project')}
            </strong>{" "}
            {t('predictions.educational_desc')}
          </p>
          <div className="mt-3 md:mt-4 flex flex-wrap items-center justify-center gap-3 md:gap-6 text-xs text-text-tertiary">
            <span className="whitespace-nowrap">🧮 {t('predictions.kelly_formula')}</span>
            <span className="whitespace-nowrap">📊 {t('predictions.risk_management')}</span>
            <span className="whitespace-nowrap">🎯 {t('predictions.educational')}</span>
            <span className="whitespace-nowrap">⚡ {t('predictions.ai_math')}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Predictions;
