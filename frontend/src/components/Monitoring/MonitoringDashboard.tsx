import React, { useState } from 'react';
import {
  Activity,
  AlertTriangle,
  CheckCircle,
  Cpu,
  Database,
  Globe,
  Monitor,
  Server,
  Wifi,
  WifiOff,
  Clock,
  Target,
  TrendingUp,
  TrendingDown,
  BarChart3,
  AlertCircle
} from 'lucide-react';
import { useMonitoring, useMonitoringAlerts } from '../../hooks/useMonitoring';
import { Line, Area, Bar } from 'recharts';
import {
  LineChart,
  AreaChart,
  BarChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';
import { format } from 'date-fns';

interface MetricCardProps {
  title: string;
  value: string | number;
  unit?: string;
  trend?: 'up' | 'down' | 'stable';
  trendValue?: number;
  status?: 'good' | 'warning' | 'critical';
  icon: React.ReactNode;
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  unit,
  trend,
  trendValue,
  status = 'good',
  icon
}) => {
  const statusColors = {
    good: 'bg-green-50 border-green-200 text-green-800',
    warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    critical: 'bg-red-50 border-red-200 text-red-800'
  };

  const iconColors = {
    good: 'text-green-600',
    warning: 'text-yellow-600',
    critical: 'text-red-600'
  };

  const getTrendIcon = () => {
    if (!trend || trend === 'stable') return null;
    return trend === 'up' ?
      <TrendingUp className="w-4 h-4 text-green-500" /> :
      <TrendingDown className="w-4 h-4 text-red-500" />;
  };

  return (
    <div className={`rounded-lg border p-4 ${statusColors[status]}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className={iconColors[status]}>{icon}</div>
          <h3 className="text-sm font-medium">{title}</h3>
        </div>
        {status !== 'good' && (
          <AlertTriangle className="w-4 h-4 text-current" />
        )}
      </div>

      <div className="mt-2 flex items-baseline space-x-2">
        <span className="text-2xl font-bold">
          {typeof value === 'number' ? value.toFixed(2) : value}
        </span>
        {unit && <span className="text-sm opacity-70">{unit}</span>}
      </div>

      {trend && trendValue !== undefined && (
        <div className="mt-1 flex items-center space-x-1">
          {getTrendIcon()}
          <span className="text-xs">
            {trendValue > 0 ? '+' : ''}{trendValue.toFixed(1)}% vs última hora
          </span>
        </div>
      )}
    </div>
  );
};

interface AlertListProps {
  className?: string;
}

const AlertList: React.FC<AlertListProps> = ({ className = '' }) => {
  const { alerts, unreadCount, resolveAlert, resolveAllAlerts } = useMonitoringAlerts();

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'critical': return <AlertCircle className="w-4 h-4 text-red-500" />;
      case 'warning': return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      default: return <CheckCircle className="w-4 h-4 text-blue-500" />;
    }
  };

  const getAlertColor = (type: string) => {
    switch (type) {
      case 'critical': return 'border-l-red-500 bg-red-50';
      case 'warning': return 'border-l-yellow-500 bg-yellow-50';
      default: return 'border-l-blue-500 bg-blue-50';
    }
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm border ${className}`}>
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">
            System Alerts
            {unreadCount > 0 && (
              <span className="ml-2 px-2 py-1 text-xs bg-red-100 text-red-600 rounded-full">
                {unreadCount}
              </span>
            )}
          </h3>
          {unreadCount > 0 && (
            <button
              onClick={resolveAllAlerts}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              Resolve All
            </button>
          )}
        </div>
      </div>

      <div className="max-h-96 overflow-y-auto">
        {alerts.length === 0 ? (
          <div className="p-4 text-center text-gray-500">
            <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-500" />
            <p>No alerts - System is healthy</p>
          </div>
        ) : (
          alerts.slice(0, 10).map((alert) => (
            <div
              key={alert.id}
              className={`border-l-4 p-4 border-b border-gray-100 last:border-b-0 ${getAlertColor(alert.type)} ${
                alert.resolved ? 'opacity-50' : ''
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3">
                  {getAlertIcon(alert.type)}
                  <div className="min-w-0 flex-1">
                    <h4 className="text-sm font-medium text-gray-900">
                      {alert.title}
                    </h4>
                    <p className="text-sm text-gray-600 mt-1">
                      {alert.message}
                    </p>
                    <div className="flex items-center space-x-2 mt-2 text-xs text-gray-500">
                      <Clock className="w-3 h-3" />
                      <span>{format(alert.timestamp, 'HH:mm:ss dd/MM')}</span>
                      <span>•</span>
                      <span>{alert.source}</span>
                    </div>
                  </div>
                </div>

                {!alert.resolved && (
                  <button
                    onClick={() => resolveAlert(alert.id)}
                    className="text-xs text-blue-600 hover:text-blue-800 ml-2 whitespace-nowrap"
                  >
                    Resolve
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

interface MetricsChartProps {
  title: string;
  data: any[];
  dataKey: string;
  color?: string;
  type?: 'line' | 'area' | 'bar';
  className?: string;
}

const MetricsChart: React.FC<MetricsChartProps> = ({
  title,
  data,
  dataKey,
  color = '#3B82F6',
  type = 'line',
  className = ''
}) => {
  const formatXAxis = (timestamp: number) => {
    return format(timestamp, 'HH:mm');
  };

  const formatTooltip = (value: any, name: string) => {
    if (typeof value === 'number') {
      return [value.toFixed(2), name];
    }
    return [value, name];
  };

  const ChartComponent = type === 'area' ? AreaChart : type === 'bar' ? BarChart : LineChart;
  const DataComponent = type === 'area' ? Area : type === 'bar' ? Bar : Line;

  return (
    <div className={`bg-white rounded-lg shadow-sm border p-4 ${className}`}>
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>

      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <ChartComponent data={data}>
            <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
            <XAxis
              dataKey="timestamp"
              tickFormatter={formatXAxis}
              className="text-xs"
            />
            <YAxis className="text-xs" />
            <Tooltip
              formatter={formatTooltip}
              labelFormatter={(timestamp) => format(timestamp, 'HH:mm:ss dd/MM/yyyy')}
              contentStyle={{
                backgroundColor: 'white',
                border: '1px solid #e5e7eb',
                borderRadius: '6px',
                fontSize: '12px'
              }}
            />
            <DataComponent
              dataKey={dataKey}
              stroke={color}
              fill={type === 'area' ? color : undefined}
              fillOpacity={type === 'area' ? 0.3 : undefined}
              strokeWidth={2}
            />
          </ChartComponent>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

const MonitoringDashboard: React.FC = () => {
  const {
    metrics,
    metricsHistory,
    connectionStatus,
    isHealthy,
    stats,
    actions
  } = useMonitoring();

  const [activeTab, setActiveTab] = useState<'overview' | 'performance' | 'system' | 'alerts'>('overview');

  // Preparar dados para gráficos
  const chartData = metricsHistory.map(metric => ({
    timestamp: metric.timestamp,
    responseTime: metric.performance.responseTime,
    errorRate: metric.performance.errorRate * 100,
    successRate: metric.performance.successRate * 100,
    cpuUsage: metric.system.cpuUsage,
    memoryUsage: metric.system.memoryUsage,
    liveMatches: metric.realTime.liveMatches,
    accuracyRate: metric.predictions.accuracyRate * 100
  }));

  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'text-green-600';
      case 'connecting': return 'text-yellow-600';
      case 'error': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getConnectionIcon = () => {
    if (connectionStatus === 'connected' && isHealthy) {
      return <Wifi className="w-4 h-4" />;
    }
    return <WifiOff className="w-4 h-4" />;
  };

  if (!metrics) {
    return (
      <div className="p-6 text-center">
        <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <Monitor className="w-6 h-6 text-blue-600" />
        </div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">
          Monitoring Dashboard
        </h2>
        <p className="text-gray-600 mb-4">
          Connecting to monitoring system...
        </p>
        <button
          onClick={actions.connect}
          className="btn-primary"
          disabled={connectionStatus === 'connecting'}
        >
          {connectionStatus === 'connecting' ? 'Connecting...' : 'Connect'}
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">System Monitoring</h1>
          <div className={`flex items-center space-x-2 mt-1 ${getConnectionStatusColor()}`}>
            {getConnectionIcon()}
            <span className="text-sm capitalize">{connectionStatus}</span>
            {metrics && (
              <span className="text-xs text-gray-500">
                • Last update: {format(metrics.timestamp, 'HH:mm:ss')}
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={actions.requestMetrics}
            className="btn-secondary"
            disabled={!isHealthy}
          >
            Refresh
          </button>
          {connectionStatus === 'disconnected' && (
            <button
              onClick={actions.connect}
              className="btn-primary"
            >
              Reconnect
            </button>
          )}
        </div>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Response Time"
          value={metrics.performance.responseTime}
          unit="ms"
          trend={stats.responseTime?.trend > 0 ? 'up' : stats.responseTime?.trend < 0 ? 'down' : 'stable'}
          trendValue={stats.responseTime?.trend}
          status={metrics.performance.responseTime > 2000 ? 'critical' :
                  metrics.performance.responseTime > 1000 ? 'warning' : 'good'}
          icon={<Clock className="w-5 h-5" />}
        />

        <MetricCard
          title="Success Rate"
          value={metrics.performance.successRate * 100}
          unit="%"
          trend={stats.successRate?.trend > 0 ? 'up' : stats.successRate?.trend < 0 ? 'down' : 'stable'}
          trendValue={stats.successRate?.trend}
          status={metrics.performance.successRate < 0.9 ? 'critical' :
                  metrics.performance.successRate < 0.95 ? 'warning' : 'good'}
          icon={<Target className="w-5 h-5" />}
        />

        <MetricCard
          title="CPU Usage"
          value={metrics.system.cpuUsage}
          unit="%"
          trend={stats.cpuUsage?.trend > 0 ? 'up' : stats.cpuUsage?.trend < 0 ? 'down' : 'stable'}
          trendValue={stats.cpuUsage?.trend}
          status={metrics.system.cpuUsage > 80 ? 'critical' :
                  metrics.system.cpuUsage > 60 ? 'warning' : 'good'}
          icon={<Cpu className="w-5 h-5" />}
        />

        <MetricCard
          title="Live Matches"
          value={metrics.realTime.liveMatches}
          trend={stats.liveMatches?.trend > 0 ? 'up' : stats.liveMatches?.trend < 0 ? 'down' : 'stable'}
          trendValue={stats.liveMatches?.trend}
          status="good"
          icon={<Activity className="w-5 h-5" />}
        />
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', name: 'Overview', icon: Monitor },
            { id: 'performance', name: 'Performance', icon: BarChart3 },
            { id: 'system', name: 'System', icon: Server },
            { id: 'alerts', name: 'Alerts', icon: AlertTriangle }
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm ${
                  isActive
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.name}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <MetricsChart
            title="Response Time (Last Hour)"
            data={chartData}
            dataKey="responseTime"
            color="#3B82F6"
            type="line"
          />
          <MetricsChart
            title="Success Rate (%)"
            data={chartData}
            dataKey="successRate"
            color="#10B981"
            type="area"
          />
        </div>
      )}

      {activeTab === 'performance' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <MetricsChart
            title="Response Time Trend"
            data={chartData}
            dataKey="responseTime"
            color="#3B82F6"
            type="line"
          />
          <MetricsChart
            title="Error Rate (%)"
            data={chartData}
            dataKey="errorRate"
            color="#EF4444"
            type="area"
          />
          <MetricsChart
            title="Prediction Accuracy (%)"
            data={chartData}
            dataKey="accuracyRate"
            color="#8B5CF6"
            type="line"
          />
          <MetricsChart
            title="Live Matches"
            data={chartData}
            dataKey="liveMatches"
            color="#F59E0B"
            type="bar"
          />
        </div>
      )}

      {activeTab === 'system' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <MetricsChart
            title="CPU Usage (%)"
            data={chartData}
            dataKey="cpuUsage"
            color="#EF4444"
            type="area"
          />
          <MetricsChart
            title="Memory Usage (%)"
            data={chartData}
            dataKey="memoryUsage"
            color="#F59E0B"
            type="area"
          />
        </div>
      )}

      {activeTab === 'alerts' && (
        <AlertList />
      )}
    </div>
  );
};

export default MonitoringDashboard;