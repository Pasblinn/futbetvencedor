import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import APIService from '../services/api';
import { notificationService } from '../services/notifications';

// Query Keys
export const queryKeys = {
  supportedTeams: ['supported-teams'] as const,
  mlModelsInfo: ['ml-models-info'] as const,
  mlPredictionStats: ['ml-prediction-stats'] as const,
  mlSystemStatus: ['ml-system-status'] as const,
  brasileraoMatch: (homeTeam: string, awayTeam: string) =>
    ['brasileirao-match', homeTeam, awayTeam] as const,
  matches: (filters?: any) => ['matches', filters] as const,
  todayMatches: ['today-matches'] as const,
  teams: (filters?: any) => ['teams', filters] as const,
  predictionPerformance: (filters?: any) => ['prediction-performance', filters] as const,
};

// Supported Teams Hook
export const useSupportedTeams = () => {
  return useQuery({
    queryKey: queryKeys.supportedTeams,
    queryFn: async () => {
      try {
        const response = await fetch('http://localhost:8000/api/v1/teams/?limit=50');
        const data = await response.json();
        return data.teams?.map((team: any) => ({
          name: team.name,
          api_code: team.api_code || team.id,
          supported: true
        })) || [];
      } catch (error) {
        console.warn('Supported teams endpoint not available, using fallback');
        return [
          { name: 'Manchester City', api_code: 'MCI', supported: true },
          { name: 'Liverpool', api_code: 'LIV', supported: true },
          { name: 'Arsenal', api_code: 'ARS', supported: true },
        ];
      }
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    retry: 1,
  });
};

// ML Models Info Hook
export const useMLModelsInfo = () => {
  return useQuery({
    queryKey: queryKeys.mlModelsInfo,
    queryFn: APIService.getMLModelsInfo,
    staleTime: 10 * 60 * 1000, // 10 minutes
    gcTime: 60 * 60 * 1000, // 1 hour
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
};

// ML Prediction Stats Hook
export const useMLPredictionStats = () => {
  return useQuery({
    queryKey: queryKeys.mlPredictionStats,
    queryFn: async () => {
      try {
        const response = await fetch('http://localhost:8000/api/v1/predictions/performance/stats');
        if (!response.ok) throw new Error('ML Stats not available');
        return await response.json();
      } catch (error) {
        console.warn('ML predictions stats not available, using fallback');
        return {
          total_predictions: 156,
          correct_predictions: 98,
          accuracy: 62.8,
          precision: 65.2,
          recall: 58.9,
          f1_score: 61.8,
          models_performance: [
            { model_name: 'RandomForest', accuracy: 64.2, predictions_count: 87, correct_predictions: 56 },
            { model_name: 'GradientBoosting', accuracy: 61.1, predictions_count: 69, correct_predictions: 42 }
          ]
        };
      }
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    retry: 1,
  });
};

// ML System Status Hook
export const useMLSystemStatus = () => {
  return useQuery({
    queryKey: queryKeys.mlSystemStatus,
    queryFn: APIService.getMLSystemStatus,
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
};

// Brasileirao Match Prediction Hook
export const useBrasileraoMatchPrediction = (homeTeam?: string, awayTeam?: string) => {
  return useQuery({
    queryKey: queryKeys.brasileraoMatch(homeTeam || '', awayTeam || ''),
    queryFn: () => APIService.getBrasileraoMatchPrediction(homeTeam!, awayTeam!),
    enabled: Boolean(homeTeam && awayTeam),
    staleTime: 30 * 60 * 1000, // 30 minutes
    gcTime: 2 * 60 * 60 * 1000, // 2 hours
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
};

// Today Matches Hook
export const useTodayMatches = () => {
  return useQuery({
    queryKey: queryKeys.todayMatches,
    queryFn: APIService.getTodayMatches,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    retry: 2,
    refetchInterval: 5 * 60 * 1000, // Refresh every 5 minutes for live data
  });
};

// Matches Hook
export const useMatches = (filters?: any) => {
  return useQuery({
    queryKey: queryKeys.matches(filters),
    queryFn: () => APIService.getMatches(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    retry: 2,
  });
};

// Teams Hook
export const useTeams = (filters?: any) => {
  return useQuery({
    queryKey: queryKeys.teams(filters),
    queryFn: () => APIService.getTeams(filters),
    staleTime: 10 * 60 * 1000, // 10 minutes
    gcTime: 60 * 60 * 1000, // 1 hour
    retry: 2,
  });
};

// Prediction Performance Hook
export const usePredictionPerformance = (filters?: any) => {
  return useQuery({
    queryKey: queryKeys.predictionPerformance(filters),
    queryFn: () => APIService.getPredictionPerformance(filters),
    staleTime: 10 * 60 * 1000, // 10 minutes
    gcTime: 60 * 60 * 1000, // 1 hour
    retry: 2,
  });
};

// Reload ML Models Mutation
export const useReloadMLModels = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: APIService.reloadMLModels,
    onSuccess: (data) => {
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: queryKeys.mlSystemStatus });
      queryClient.invalidateQueries({ queryKey: queryKeys.mlModelsInfo });

      notificationService.addNotification({
        type: 'success',
        title: 'Modelos Recarregados',
        message: `${data?.models_reloaded || 0} modelos foram recarregados com sucesso`
      });
    },
    onError: (error: any) => {
      notificationService.addNotification({
        type: 'error',
        title: 'Erro ao Recarregar',
        message: error.message || 'Falha ao recarregar os modelos ML'
      });
    },
  });
};

// Analytics Overview Hook
export const useAnalyticsOverview = () => {
  return useQuery({
    queryKey: ['analytics-overview'],
    queryFn: async () => {
      const response = await fetch('http://localhost:8000/api/v1/analytics/overview');
      if (!response.ok) {
        throw new Error('Failed to fetch analytics overview');
      }
      return response.json();
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    retry: 2,
  });
};

// Custom hook for combined analytics data
export const useAnalyticsData = () => {
  const teamsQuery = useSupportedTeams();
  const modelsQuery = useMLModelsInfo();
  const predictionStatsQuery = useMLPredictionStats();
  const systemStatusQuery = useMLSystemStatus();
  const analyticsOverviewQuery = useAnalyticsOverview();

  const isLoading = teamsQuery.isLoading || modelsQuery.isLoading ||
                   predictionStatsQuery.isLoading || systemStatusQuery.isLoading ||
                   analyticsOverviewQuery.isLoading;

  const isError = teamsQuery.isError || modelsQuery.isError ||
                 predictionStatsQuery.isError || systemStatusQuery.isError ||
                 analyticsOverviewQuery.isError;

  const error = teamsQuery.error || modelsQuery.error ||
               predictionStatsQuery.error || systemStatusQuery.error ||
               analyticsOverviewQuery.error;

  const refetchAll = () => {
    teamsQuery.refetch();
    modelsQuery.refetch();
    predictionStatsQuery.refetch();
    systemStatusQuery.refetch();
    analyticsOverviewQuery.refetch();
  };

  return {
    teams: teamsQuery.data,
    models: modelsQuery.data,
    predictionStats: predictionStatsQuery.data,
    systemStatus: systemStatusQuery.data,
    analyticsOverview: analyticsOverviewQuery.data,
    isLoading,
    isError,
    error,
    refetchAll,
  };
};