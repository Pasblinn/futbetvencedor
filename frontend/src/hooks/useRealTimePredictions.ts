import { useState, useEffect, useCallback, useRef } from 'react';
import { realTimePredictionService, RealTimePrediction } from '../services/realTimePredictionService';
import { liveDataService, LiveMatch } from '../services/liveDataService';
import { notificationService } from '../services/notifications';

interface UseRealTimePredictionsOptions {
  autoRefresh?: boolean;
  refreshInterval?: number; // em millisegundos
  enableNotifications?: boolean;
}

interface UseRealTimePredictionsReturn {
  predictions: RealTimePrediction[];
  matches: LiveMatch[];
  loading: boolean;
  refreshing: boolean;
  error: string | null;
  refreshAll: () => Promise<void>;
  refreshSpecific: (matchId: string) => Promise<void>;
  createPrediction: (match: LiveMatch) => Promise<void>;
  getPredictionHistory: (matchId: string) => Promise<RealTimePrediction[]>;
  stats: {
    total: number;
    live: number;
    highConfidence: number;
    valueAlerts: number;
  };
}

export const useRealTimePredictions = (
  options: UseRealTimePredictionsOptions = {}
): UseRealTimePredictionsReturn => {
  const {
    autoRefresh = true,
    refreshInterval = 120000, // 2 minutos
    enableNotifications = true
  } = options;

  const [predictions, setPredictions] = useState<RealTimePrediction[]>([]);
  const [matches, setMatches] = useState<LiveMatch[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const notificationsRef = useRef<Set<string>>(new Set());

  // Carregar dados iniciais
  const loadInitialData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      console.log('🔄 Carregando dados iniciais de predições...');

      // 1. Buscar jogos de hoje
      const todayMatches = await liveDataService.getLiveMatches();
      setMatches(todayMatches);

      // 2. Buscar predições existentes
      const existingPredictions = await realTimePredictionService.getAllActivePredictions();

      if (existingPredictions.length === 0 && todayMatches.length > 0) {
        // Criar novas predições se não existirem
        console.log('📊 Criando novas predições para jogos de hoje...');
        const newPredictions = await realTimePredictionService.createTodayPredictions();
        setPredictions(newPredictions);

        if (enableNotifications) {
          notificationService.addNotification({
            type: 'success',
            title: 'Predições Criadas',
            message: `${newPredictions.length} novas predições geradas`
          });
        }
      } else {
        setPredictions(existingPredictions);
      }

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erro desconhecido';
      console.error('Erro ao carregar dados iniciais:', err);
      setError(errorMessage);

      if (enableNotifications) {
        notificationService.addNotification({
          type: 'error',
          title: 'Erro ao Carregar',
          message: errorMessage
        });
      }
    } finally {
      setLoading(false);
    }
  }, [enableNotifications]);

  // Atualizar todas as predições
  const refreshAll = useCallback(async () => {
    if (predictions.length === 0) return;

    try {
      setRefreshing(true);
      setError(null);

      console.log('🔄 Atualizando todas as predições...');

      const updatedPredictions: RealTimePrediction[] = [];
      let updatedCount = 0;

      // Atualizar cada predição
      for (const prediction of predictions) {
        try {
          const updated = await realTimePredictionService.updateLivePrediction(prediction.matchId);
          if (updated) {
            updatedPredictions.push(updated);

            // Verificar mudanças significativas
            if (hasSignificantChange(prediction, updated)) {
              updatedCount++;

              if (enableNotifications && !notificationsRef.current.has(prediction.matchId)) {
                notificationService.addNotification({
                  type: 'prediction_ready',
                  title: 'Predição Atualizada',
                  message: `${updated.homeTeam} vs ${updated.awayTeam} - Probabilidades mudaram`,
                  metadata: { matchId: prediction.matchId }
                });
                notificationsRef.current.add(prediction.matchId);
              }
            }
          } else {
            updatedPredictions.push(prediction);
          }
        } catch (err) {
          console.error(`Erro ao atualizar predição ${prediction.matchId}:`, err);
          updatedPredictions.push(prediction);
        }
      }

      setPredictions(updatedPredictions);

      if (updatedCount > 0 && enableNotifications) {
        notificationService.addNotification({
          type: 'info',
          title: 'Predições Atualizadas',
          message: `${updatedCount} predições foram atualizadas`
        });
      }

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erro ao atualizar';
      console.error('Erro ao atualizar predições:', err);
      setError(errorMessage);
    } finally {
      setRefreshing(false);
    }
  }, [predictions, enableNotifications]);

  // Atualizar predição específica
  const refreshSpecific = useCallback(async (matchId: string) => {
    try {
      const updated = await realTimePredictionService.updateLivePrediction(matchId);
      if (updated) {
        setPredictions(prev =>
          prev.map(p => p.matchId === matchId ? updated : p)
        );

        if (enableNotifications) {
          notificationService.addNotification({
            type: 'success',
            title: 'Predição Atualizada',
            message: `${updated.homeTeam} vs ${updated.awayTeam}`
          });
        }
      }
    } catch (err) {
      console.error(`Erro ao atualizar predição ${matchId}:`, err);
      if (enableNotifications) {
        notificationService.addNotification({
          type: 'error',
          title: 'Erro na Atualização',
          message: 'Falha ao atualizar predição específica'
        });
      }
    }
  }, [enableNotifications]);

  // Criar nova predição para um jogo
  const createPrediction = useCallback(async (match: LiveMatch) => {
    try {
      console.log(`🆕 Criando nova predição para ${match.homeTeam.name} vs ${match.awayTeam.name}`);

      const newPrediction = await realTimePredictionService.createRealTimePrediction(match);

      setPredictions(prev => {
        const exists = prev.find(p => p.matchId === match.id);
        if (exists) {
          return prev.map(p => p.matchId === match.id ? newPrediction : p);
        }
        return [...prev, newPrediction];
      });

      if (enableNotifications) {
        notificationService.addNotification({
          type: 'success',
          title: 'Nova Predição',
          message: `Predição criada para ${match.homeTeam.name} vs ${match.awayTeam.name}`,
          metadata: { matchId: match.id }
        });
      }

    } catch (err) {
      console.error('Erro ao criar predição:', err);
      if (enableNotifications) {
        notificationService.addNotification({
          type: 'error',
          title: 'Erro ao Criar Predição',
          message: 'Falha ao gerar nova predição'
        });
      }
    }
  }, [enableNotifications]);

  // Buscar histórico de predição
  const getPredictionHistory = useCallback(async (matchId: string): Promise<RealTimePrediction[]> => {
    try {
      return await realTimePredictionService.getPredictionHistory(matchId);
    } catch (err) {
      console.error(`Erro ao buscar histórico de ${matchId}:`, err);
      return [];
    }
  }, []);

  // Verificar mudanças significativas
  const hasSignificantChange = (old: RealTimePrediction, updated: RealTimePrediction): boolean => {
    const oldProb = old.updatedProbabilities || old.prediction.probability;
    const newProb = updated.updatedProbabilities || updated.prediction.probability;

    const homeChange = Math.abs(newProb.homeWin - oldProb.homeWin);
    const awayChange = Math.abs(newProb.awayWin - oldProb.awayWin);

    return homeChange > 0.1 || awayChange > 0.1;
  };

  // Calcular estatísticas
  const stats = {
    total: predictions.length,
    live: predictions.filter(p => p.liveData?.isLive).length,
    highConfidence: predictions.filter(p => p.prediction.confidence >= 0.8).length,
    valueAlerts: predictions.reduce((acc, p) => acc + (p.alerts?.valueOdds?.length || 0), 0)
  };

  // Configurar auto-refresh
  useEffect(() => {
    if (autoRefresh && predictions.length > 0) {
      intervalRef.current = setInterval(() => {
        refreshAll();
      }, refreshInterval);

      return () => {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
        }
      };
    }
  }, [autoRefresh, refreshInterval, refreshAll, predictions.length]);

  // Carregar dados ao montar
  useEffect(() => {
    loadInitialData();

    // Cleanup ao desmontar
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      // Limpar cache de notificações antigas
      notificationsRef.current.clear();
    };
  }, [loadInitialData]);

  // Limpar notificações antigas periodicamente
  useEffect(() => {
    const cleanupInterval = setInterval(() => {
      notificationsRef.current.clear();
    }, 300000); // Limpar a cada 5 minutos

    return () => clearInterval(cleanupInterval);
  }, []);

  return {
    predictions,
    matches,
    loading,
    refreshing,
    error,
    refreshAll,
    refreshSpecific,
    createPrediction,
    getPredictionHistory,
    stats
  };
};

export default useRealTimePredictions;