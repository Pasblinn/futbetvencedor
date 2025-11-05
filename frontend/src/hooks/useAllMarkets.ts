import { useQuery, useQueryClient, UseQueryResult } from '@tanstack/react-query';
import { apiClient, endpoints } from '../utils/apiClient';
import { logger } from '../utils/logger';

interface AllMarketsData {
  match_info: {
    match_id: number;
    home_team: string;
    away_team: string;
    league: string;
    match_date: string;
  };
  probabilities: Record<string, number>;
  fair_odds: Record<string, number>;
  market_odds?: Record<string, number>; // Odds reais de mercado (quando disponíveis)
  value_bets?: Array<{
    market: string;
    edge: number;
    fair_odds: number;
    market_odds?: number;
  }>;
  team_stats: {
    home: {
      goals_scored_avg: number;
      goals_conceded_avg: number;
      clean_sheets_percentage: number;
    };
    away: {
      goals_scored_avg: number;
      goals_conceded_avg: number;
      clean_sheets_percentage: number;
    };
  };
  poisson_params: {
    lambda_home: number;
    lambda_away: number;
  };
  total_markets: number;
}

interface UseAllMarketsOptions {
  matchId: number | null | undefined;
  lastNGames?: number;
  enabled?: boolean;
}

/**
 * Hook customizado para buscar todos os mercados de uma partida
 * com cache inteligente usando React Query
 *
 * @example
 * const { data, isLoading, error } = useAllMarkets({
 *   matchId: 123,
 *   lastNGames: 10
 * });
 */
export const useAllMarkets = ({
  matchId,
  lastNGames = 10,
  enabled = true,
}: UseAllMarketsOptions): UseQueryResult<AllMarketsData, Error> => {
  return useQuery({
    // Query key única por match e parâmetros
    queryKey: ['all-markets', matchId, lastNGames],

    // Função que busca os dados
    queryFn: async () => {
      if (!matchId) {
        throw new Error('Match ID is required');
      }

      logger.info('useAllMarkets', `Fetching markets for match ${matchId}`);
      logger.time(`useAllMarkets-${matchId}`);

      try {
        const data = await apiClient.get<AllMarketsData>(
          endpoints.predictions.allMarkets(matchId),
          { params: { last_n_games: lastNGames } }
        );

        logger.timeEnd(`useAllMarkets-${matchId}`);
        logger.success('useAllMarkets', `Loaded ${data.total_markets} markets`);

        return data;
      } catch (error) {
        logger.timeEnd(`useAllMarkets-${matchId}`);
        logger.error('useAllMarkets', 'Failed to fetch markets', error);
        throw error;
      }
    },

    // Configurações de cache
    enabled: enabled && !!matchId, // Só busca se habilitado e matchId existe
    staleTime: 5 * 60 * 1000, // 5 minutos - dados considerados frescos
    gcTime: 30 * 60 * 1000, // 30 minutos - garbage collection (cache time)
    retry: 2, // Tenta 2 vezes em caso de erro
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000), // Exponential backoff

    // Meta para debug
    meta: {
      errorMessage: 'Erro ao carregar mercados da partida',
    },
  });
};

/**
 * Hook para pre-carregar mercados (útil para hover ou preview)
 *
 * @example
 * const prefetchMarkets = usePrefetchAllMarkets();
 *
 * <button onMouseEnter={() => prefetchMarkets(123)}>
 *   Ver Mercados
 * </button>
 */
export const usePrefetchAllMarkets = () => {
  const queryClient = useQueryClient();

  return async (matchId: number, lastNGames = 10) => {
    await queryClient.prefetchQuery({
      queryKey: ['all-markets', matchId, lastNGames],
      queryFn: async () => {
        logger.info('prefetchAllMarkets', `Prefetching for match ${matchId}`);
        const data = await apiClient.get<AllMarketsData>(
          endpoints.predictions.allMarkets(matchId),
          { params: { last_n_games: lastNGames } }
        );
        return data;
      },
      staleTime: 5 * 60 * 1000,
    });
  };
};
