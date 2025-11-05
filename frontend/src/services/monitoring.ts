import { EventEmitter } from 'events';

export interface SystemMetrics {
  timestamp: number;
  performance: {
    responseTime: number;
    apiLatency: number;
    errorRate: number;
    successRate: number;
    throughput: number;
  };
  realTime: {
    activeConnections: number;
    dataFreshness: number;
    updateFrequency: number;
    liveMatches: number;
  };
  predictions: {
    totalGenerated: number;
    successfulPredictions: number;
    accuracyRate: number;
    confidenceScore: number;
  };
  system: {
    cpuUsage: number;
    memoryUsage: number;
    networkLatency: number;
    uptime: number;
  };
}

export interface Alert {
  id: string;
  type: 'critical' | 'warning' | 'info';
  title: string;
  message: string;
  timestamp: number;
  source: string;
  resolved: boolean;
  metadata?: any;
}

export interface MonitoringThreshold {
  metric: keyof SystemMetrics | string;
  operator: 'gt' | 'lt' | 'eq' | 'gte' | 'lte';
  value: number;
  alertType: Alert['type'];
  message: string;
}

class MonitoringService extends EventEmitter {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectInterval = 5000;
  private metricsHistory: SystemMetrics[] = [];
  private maxHistorySize = 1000;
  private alerts: Alert[] = [];
  private thresholds: MonitoringThreshold[] = [];
  private isConnected = false;
  private pingInterval: NodeJS.Timeout | null = null;

  constructor() {
    super();
    this.setupDefaultThresholds();
  }

  // Configuração dos thresholds padrão
  private setupDefaultThresholds() {
    this.thresholds = [
      {
        metric: 'performance.responseTime',
        operator: 'gt',
        value: 2000,
        alertType: 'warning',
        message: 'Response time is above 2 seconds'
      },
      {
        metric: 'performance.responseTime',
        operator: 'gt',
        value: 5000,
        alertType: 'critical',
        message: 'Response time is critically high (>5s)'
      },
      {
        metric: 'performance.errorRate',
        operator: 'gt',
        value: 0.05,
        alertType: 'warning',
        message: 'Error rate is above 5%'
      },
      {
        metric: 'performance.errorRate',
        operator: 'gt',
        value: 0.1,
        alertType: 'critical',
        message: 'Error rate is critically high (>10%)'
      },
      {
        metric: 'realTime.dataFreshness',
        operator: 'gt',
        value: 300000,
        alertType: 'warning',
        message: 'Data is older than 5 minutes'
      },
      {
        metric: 'system.cpuUsage',
        operator: 'gt',
        value: 80,
        alertType: 'warning',
        message: 'CPU usage is above 80%'
      },
      {
        metric: 'system.memoryUsage',
        operator: 'gt',
        value: 90,
        alertType: 'critical',
        message: 'Memory usage is critically high (>90%)'
      }
    ];
  }

  // Conectar ao WebSocket de monitoramento
  connect(url?: string): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const wsUrl = url || `${process.env.REACT_APP_WS_URL || 'ws://localhost:3001'}/monitoring`;
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log('Monitoring WebSocket connected');
          this.isConnected = true;
          this.reconnectAttempts = 0;
          this.startPingInterval();
          this.emit('connected');
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
          } catch (error) {
            console.error('Error parsing monitoring message:', error);
          }
        };

        this.ws.onclose = () => {
          console.log('Monitoring WebSocket disconnected');
          this.isConnected = false;
          this.stopPingInterval();
          this.emit('disconnected');
          this.attemptReconnect();
        };

        this.ws.onerror = (error) => {
          console.error('Monitoring WebSocket error:', error);
          this.emit('error', error);
          reject(error);
        };

      } catch (error) {
        reject(error);
      }
    });
  }

  // Tentar reconectar
  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

      setTimeout(() => {
        this.connect().catch(() => {
          // Tentativa falhou, será tentada novamente
        });
      }, this.reconnectInterval * this.reconnectAttempts);
    } else {
      console.error('Max reconnection attempts reached');
      this.emit('reconnectFailed');
    }
  }

  // Gerenciar mensagens do WebSocket
  private handleMessage(data: any) {
    switch (data.type) {
      case 'metrics':
        this.processMetrics(data.payload);
        break;
      case 'alert':
        this.processAlert(data.payload);
        break;
      case 'threshold_updated':
        this.emit('thresholdUpdated', data.payload);
        break;
      case 'pong':
        // Resposta ao ping
        break;
      default:
        console.warn('Unknown monitoring message type:', data.type);
    }
  }

  // Processar métricas recebidas
  private processMetrics(metrics: SystemMetrics) {
    // Adicionar timestamp se não existir
    if (!metrics.timestamp) {
      metrics.timestamp = Date.now();
    }

    // Adicionar ao histórico
    this.metricsHistory.push(metrics);
    if (this.metricsHistory.length > this.maxHistorySize) {
      this.metricsHistory.shift();
    }

    // Verificar thresholds
    this.checkThresholds(metrics);

    // Emitir evento
    this.emit('metrics', metrics);
  }

  // Verificar se métricas violam thresholds
  private checkThresholds(metrics: SystemMetrics) {
    this.thresholds.forEach(threshold => {
      const value = this.getNestedValue(metrics, threshold.metric);
      if (value !== undefined && this.compareValues(value, threshold.operator, threshold.value)) {
        this.createAlert({
          type: threshold.alertType,
          title: `Threshold Violation: ${threshold.metric}`,
          message: threshold.message,
          source: 'threshold_monitor',
          resolved: false,
          metadata: {
            metric: threshold.metric,
            value,
            threshold: threshold.value,
            operator: threshold.operator
          }
        });
      }
    });
  }

  // Obter valor aninhado de objeto
  private getNestedValue(obj: any, path: string): any {
    return path.split('.').reduce((current, key) => current?.[key], obj);
  }

  // Comparar valores com operador
  private compareValues(value: number, operator: string, threshold: number): boolean {
    switch (operator) {
      case 'gt': return value > threshold;
      case 'lt': return value < threshold;
      case 'eq': return value === threshold;
      case 'gte': return value >= threshold;
      case 'lte': return value <= threshold;
      default: return false;
    }
  }

  // Processar alerta recebido
  private processAlert(alert: Omit<Alert, 'id' | 'timestamp'>) {
    this.createAlert(alert);
  }

  // Criar novo alerta
  private createAlert(alertData: Omit<Alert, 'id' | 'timestamp'>) {
    const alert: Alert = {
      id: `alert_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`,
      timestamp: Date.now(),
      ...alertData
    };

    this.alerts.unshift(alert);
    this.emit('alert', alert);

    // Limitar número de alertas armazenados
    if (this.alerts.length > 100) {
      this.alerts = this.alerts.slice(0, 100);
    }
  }

  // Gerenciar ping/pong para manter conexão viva
  private startPingInterval() {
    this.pingInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000); // Ping a cada 30 segundos
  }

  private stopPingInterval() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  // Métodos públicos
  getLatestMetrics(): SystemMetrics | null {
    return this.metricsHistory.length > 0
      ? this.metricsHistory[this.metricsHistory.length - 1]
      : null;
  }

  getMetricsHistory(limit?: number): SystemMetrics[] {
    return limit
      ? this.metricsHistory.slice(-limit)
      : [...this.metricsHistory];
  }

  getAlerts(unreadOnly = false): Alert[] {
    return unreadOnly
      ? this.alerts.filter(alert => !alert.resolved)
      : [...this.alerts];
  }

  resolveAlert(alertId: string): boolean {
    const alert = this.alerts.find(a => a.id === alertId);
    if (alert) {
      alert.resolved = true;
      this.emit('alertResolved', alert);
      return true;
    }
    return false;
  }

  addThreshold(threshold: MonitoringThreshold) {
    this.thresholds.push(threshold);
    this.emit('thresholdAdded', threshold);
  }

  removeThreshold(index: number) {
    if (index >= 0 && index < this.thresholds.length) {
      const removed = this.thresholds.splice(index, 1)[0];
      this.emit('thresholdRemoved', removed);
      return removed;
    }
    return null;
  }

  getThresholds(): MonitoringThreshold[] {
    return [...this.thresholds];
  }

  isConnectionHealthy(): boolean {
    return this.isConnected && this.ws?.readyState === WebSocket.OPEN;
  }

  getConnectionStatus(): 'connected' | 'disconnected' | 'connecting' | 'error' {
    if (!this.ws) return 'disconnected';

    switch (this.ws.readyState) {
      case WebSocket.CONNECTING: return 'connecting';
      case WebSocket.OPEN: return 'connected';
      case WebSocket.CLOSING:
      case WebSocket.CLOSED: return 'disconnected';
      default: return 'error';
    }
  }

  // Calcular estatísticas das métricas
  getMetricsStats(metric: string, timeRange = 3600000): any {
    const cutoff = Date.now() - timeRange;
    const relevantMetrics = this.metricsHistory.filter(m => m.timestamp >= cutoff);

    if (relevantMetrics.length === 0) return null;

    const values = relevantMetrics.map(m => this.getNestedValue(m, metric)).filter(v => v !== undefined);

    if (values.length === 0) return null;

    return {
      current: values[values.length - 1],
      average: values.reduce((sum, val) => sum + val, 0) / values.length,
      min: Math.min(...values),
      max: Math.max(...values),
      trend: values.length > 1 ? values[values.length - 1] - values[0] : 0,
      count: values.length
    };
  }

  disconnect() {
    this.stopPingInterval();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.isConnected = false;
  }

  // Solicitar métricas sob demanda
  requestMetrics() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'request_metrics' }));
    }
  }

  // Configurar alertas customizados
  configureCustomAlert(config: {
    name: string;
    condition: string;
    message: string;
    type: Alert['type'];
  }) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'configure_alert',
        payload: config
      }));
    }
  }
}

export const monitoringService = new MonitoringService();
export default monitoringService;