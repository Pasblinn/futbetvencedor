import React from 'react';
import {
  Wifi,
  WifiOff,
  AlertTriangle,
  CheckCircle,
  Clock,
  Activity
} from 'lucide-react';
import { useMonitoring } from '../../hooks/useMonitoring';

interface SystemHealthIndicatorProps {
  showDetails?: boolean;
  compact?: boolean;
  className?: string;
}

const SystemHealthIndicator: React.FC<SystemHealthIndicatorProps> = ({
  showDetails = false,
  compact = false,
  className = ''
}) => {
  const { connectionStatus, isHealthy, metrics, stats } = useMonitoring();

  const getStatusColor = () => {
    if (!isHealthy) return 'text-red-500';
    if (connectionStatus === 'connecting') return 'text-yellow-500';
    if (connectionStatus === 'connected') return 'text-green-500';
    return 'text-gray-500';
  };

  const getStatusIcon = () => {
    if (!isHealthy) return <WifiOff className="w-4 h-4" />;
    if (connectionStatus === 'connecting') return <Clock className="w-4 h-4 animate-spin" />;
    if (connectionStatus === 'connected') return <Wifi className="w-4 h-4" />;
    return <WifiOff className="w-4 h-4" />;
  };

  const getStatusText = () => {
    switch (connectionStatus) {
      case 'connected':
        return isHealthy ? 'System Healthy' : 'Connected (Issues Detected)';
      case 'connecting':
        return 'Connecting...';
      case 'error':
        return 'Connection Error';
      default:
        return 'Disconnected';
    }
  };

  const getHealthScore = () => {
    if (!metrics) return 0;

    let score = 100;

    // Penalizar por alta latência
    if (metrics.performance.responseTime > 2000) score -= 30;
    else if (metrics.performance.responseTime > 1000) score -= 15;

    // Penalizar por alta taxa de erro
    if (metrics.performance.errorRate > 0.1) score -= 40;
    else if (metrics.performance.errorRate > 0.05) score -= 20;

    // Penalizar por alto uso de CPU
    if (metrics.system.cpuUsage > 80) score -= 20;
    else if (metrics.system.cpuUsage > 60) score -= 10;

    // Penalizar por alto uso de memória
    if (metrics.system.memoryUsage > 90) score -= 20;
    else if (metrics.system.memoryUsage > 70) score -= 10;

    return Math.max(0, score);
  };

  const healthScore = getHealthScore();

  const getHealthScoreColor = () => {
    if (healthScore >= 80) return 'text-green-600';
    if (healthScore >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (compact) {
    return (
      <div className={`flex items-center space-x-2 ${className}`}>
        <div className={getStatusColor()}>
          {getStatusIcon()}
        </div>
        <span className={`text-sm ${getStatusColor()}`}>
          {connectionStatus === 'connected' && isHealthy ? '●' : '○'}
        </span>
        {showDetails && metrics && (
          <span className="text-xs text-gray-500">
            {metrics.performance.responseTime}ms
          </span>
        )}
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg border shadow-sm p-4 ${className}`}>
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-900">System Health</h3>
        <div className={`flex items-center space-x-2 ${getStatusColor()}`}>
          {getStatusIcon()}
          <span className="text-sm font-medium">{getStatusText()}</span>
        </div>
      </div>

      {metrics && (
        <div className="space-y-3">
          {/* Health Score */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-gray-600">Health Score</span>
              <span className={`text-sm font-bold ${getHealthScoreColor()}`}>
                {healthScore}/100
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all duration-300 ${
                  healthScore >= 80 ? 'bg-green-500' :
                  healthScore >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                }`}
                style={{ width: `${healthScore}%` }}
              />
            </div>
          </div>

          {showDetails && (
            <>
              {/* Key Metrics */}
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <span className="text-gray-600">Response Time</span>
                  <div className="font-semibold">
                    {metrics.performance.responseTime.toFixed(0)}ms
                  </div>
                </div>
                <div>
                  <span className="text-gray-600">Success Rate</span>
                  <div className="font-semibold">
                    {(metrics.performance.successRate * 100).toFixed(1)}%
                  </div>
                </div>
                <div>
                  <span className="text-gray-600">CPU Usage</span>
                  <div className="font-semibold">
                    {metrics.system.cpuUsage.toFixed(1)}%
                  </div>
                </div>
                <div>
                  <span className="text-gray-600">Live Matches</span>
                  <div className="font-semibold">
                    {metrics.realTime.liveMatches}
                  </div>
                </div>
              </div>

              {/* Issues */}
              {healthScore < 80 && (
                <div className="mt-3 p-2 bg-yellow-50 border border-yellow-200 rounded">
                  <div className="flex items-center space-x-1">
                    <AlertTriangle className="w-3 h-3 text-yellow-600" />
                    <span className="text-xs font-medium text-yellow-800">
                      Performance Issues Detected
                    </span>
                  </div>
                  <div className="text-xs text-yellow-700 mt-1">
                    {metrics.performance.responseTime > 1000 && 'High latency, '}
                    {metrics.performance.errorRate > 0.05 && 'High error rate, '}
                    {metrics.system.cpuUsage > 60 && 'High CPU usage, '}
                    {metrics.system.memoryUsage > 70 && 'High memory usage'}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {!metrics && connectionStatus === 'connected' && (
        <div className="text-center py-2">
          <Activity className="w-4 h-4 mx-auto mb-1 text-gray-400 animate-pulse" />
          <span className="text-xs text-gray-500">Waiting for metrics...</span>
        </div>
      )}
    </div>
  );
};

export default SystemHealthIndicator;