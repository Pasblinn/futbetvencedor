import { useState, useEffect, useCallback } from 'react';
import { monitoringService, SystemMetrics, Alert } from '../services/monitoring';

export interface MonitoringHookReturn {
  metrics: SystemMetrics | null;
  metricsHistory: SystemMetrics[];
  alerts: Alert[];
  unreadAlerts: Alert[];
  connectionStatus: 'connected' | 'disconnected' | 'connecting' | 'error';
  isHealthy: boolean;
  stats: {
    [key: string]: any;
  };
  actions: {
    connect: () => Promise<void>;
    disconnect: () => void;
    resolveAlert: (alertId: string) => boolean;
    requestMetrics: () => void;
    getMetricsStats: (metric: string, timeRange?: number) => any;
  };
}

export const useMonitoring = (autoConnect = true): MonitoringHookReturn => {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [metricsHistory, setMetricsHistory] = useState<SystemMetrics[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'connecting' | 'error'>('disconnected');
  const [isHealthy, setIsHealthy] = useState(false);
  const [stats, setStats] = useState<{ [key: string]: any }>({});

  // Atualizar estado baseado nos eventos do serviço
  useEffect(() => {
    const handleMetrics = (newMetrics: SystemMetrics) => {
      setMetrics(newMetrics);
      setMetricsHistory(monitoringService.getMetricsHistory(100)); // Últimas 100 métricas

      // Calcular estatísticas principais
      const newStats = {
        responseTime: monitoringService.getMetricsStats('performance.responseTime'),
        errorRate: monitoringService.getMetricsStats('performance.errorRate'),
        successRate: monitoringService.getMetricsStats('performance.successRate'),
        cpuUsage: monitoringService.getMetricsStats('system.cpuUsage'),
        memoryUsage: monitoringService.getMetricsStats('system.memoryUsage'),
        liveMatches: monitoringService.getMetricsStats('realTime.liveMatches'),
        accuracyRate: monitoringService.getMetricsStats('predictions.accuracyRate')
      };
      setStats(newStats);
    };

    const handleAlert = (newAlert: Alert) => {
      setAlerts(monitoringService.getAlerts());
    };

    const handleConnected = () => {
      setConnectionStatus('connected');
      setIsHealthy(true);
    };

    const handleDisconnected = () => {
      setConnectionStatus('disconnected');
      setIsHealthy(false);
    };

    const handleError = () => {
      setConnectionStatus('error');
      setIsHealthy(false);
    };

    const handleReconnectFailed = () => {
      setConnectionStatus('error');
      setIsHealthy(false);
    };

    // Registrar listeners
    monitoringService.on('metrics', handleMetrics);
    monitoringService.on('alert', handleAlert);
    monitoringService.on('connected', handleConnected);
    monitoringService.on('disconnected', handleDisconnected);
    monitoringService.on('error', handleError);
    monitoringService.on('reconnectFailed', handleReconnectFailed);

    // Conectar automaticamente se solicitado
    if (autoConnect && !monitoringService.isConnectionHealthy()) {
      setConnectionStatus('connecting');
      monitoringService.connect().catch(() => {
        setConnectionStatus('error');
        setIsHealthy(false);
      });
    }

    // Estado inicial
    setMetrics(monitoringService.getLatestMetrics());
    setMetricsHistory(monitoringService.getMetricsHistory(100));
    setAlerts(monitoringService.getAlerts());
    setConnectionStatus(monitoringService.getConnectionStatus());
    setIsHealthy(monitoringService.isConnectionHealthy());

    // Cleanup
    return () => {
      monitoringService.off('metrics', handleMetrics);
      monitoringService.off('alert', handleAlert);
      monitoringService.off('connected', handleConnected);
      monitoringService.off('disconnected', handleDisconnected);
      monitoringService.off('error', handleError);
      monitoringService.off('reconnectFailed', handleReconnectFailed);
    };
  }, [autoConnect]);

  // Filtrar alertas não lidos
  const unreadAlerts = alerts.filter(alert => !alert.resolved);

  // Actions
  const connect = useCallback(async () => {
    setConnectionStatus('connecting');
    try {
      await monitoringService.connect();
    } catch (error) {
      setConnectionStatus('error');
      setIsHealthy(false);
      throw error;
    }
  }, []);

  const disconnect = useCallback(() => {
    monitoringService.disconnect();
    setConnectionStatus('disconnected');
    setIsHealthy(false);
  }, []);

  const resolveAlert = useCallback((alertId: string) => {
    const resolved = monitoringService.resolveAlert(alertId);
    if (resolved) {
      setAlerts(monitoringService.getAlerts());
    }
    return resolved;
  }, []);

  const requestMetrics = useCallback(() => {
    monitoringService.requestMetrics();
  }, []);

  const getMetricsStats = useCallback((metric: string, timeRange?: number) => {
    return monitoringService.getMetricsStats(metric, timeRange);
  }, []);

  return {
    metrics,
    metricsHistory,
    alerts,
    unreadAlerts,
    connectionStatus,
    isHealthy,
    stats,
    actions: {
      connect,
      disconnect,
      resolveAlert,
      requestMetrics,
      getMetricsStats
    }
  };
};

// Hook específico para alertas
export const useMonitoringAlerts = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    const handleAlert = () => {
      const allAlerts = monitoringService.getAlerts();
      setAlerts(allAlerts);
      setUnreadCount(allAlerts.filter(alert => !alert.resolved).length);
    };

    const handleAlertResolved = () => {
      const allAlerts = monitoringService.getAlerts();
      setAlerts(allAlerts);
      setUnreadCount(allAlerts.filter(alert => !alert.resolved).length);
    };

    monitoringService.on('alert', handleAlert);
    monitoringService.on('alertResolved', handleAlertResolved);

    // Estado inicial
    const initialAlerts = monitoringService.getAlerts();
    setAlerts(initialAlerts);
    setUnreadCount(initialAlerts.filter(alert => !alert.resolved).length);

    return () => {
      monitoringService.off('alert', handleAlert);
      monitoringService.off('alertResolved', handleAlertResolved);
    };
  }, []);

  const resolveAlert = useCallback((alertId: string) => {
    return monitoringService.resolveAlert(alertId);
  }, []);

  const resolveAllAlerts = useCallback(() => {
    alerts.forEach(alert => {
      if (!alert.resolved) {
        monitoringService.resolveAlert(alert.id);
      }
    });
  }, [alerts]);

  return {
    alerts,
    unreadCount,
    resolveAlert,
    resolveAllAlerts
  };
};

// Hook para métricas específicas
export const useMetricsStats = (metric: string, timeRange = 3600000) => {
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    const updateStats = () => {
      const newStats = monitoringService.getMetricsStats(metric, timeRange);
      setStats(newStats);
    };

    const handleMetrics = () => {
      updateStats();
    };

    monitoringService.on('metrics', handleMetrics);
    updateStats(); // Estado inicial

    return () => {
      monitoringService.off('metrics', handleMetrics);
    };
  }, [metric, timeRange]);

  return stats;
};

export default useMonitoring;