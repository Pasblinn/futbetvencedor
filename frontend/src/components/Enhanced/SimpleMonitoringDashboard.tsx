import React, { useState, useEffect } from 'react';
import {
  Activity,
  AlertTriangle,
  Bell,
  CheckCircle,
  Clock,
  Monitor,
  RefreshCw,
  Wifi,
  WifiOff
} from 'lucide-react';
import { useMonitoring } from '../../hooks/useMonitoring';
import { format } from 'date-fns';

const SimpleMonitoringDashboard: React.FC = () => {
  const {
    metrics,
    metricsHistory,
    alerts,
    connectionStatus,
    isHealthy,
    actions
  } = useMonitoring();

  const [activeTab, setActiveTab] = useState<'overview' | 'alerts'>('overview');

  const getConnectionStatusIcon = () => {
    return connectionStatus === 'connected' ?
      <Wifi className="w-5 h-5 text-green-600" /> :
      <WifiOff className="w-5 h-5 text-red-600" />;
  };

  if (!metrics) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 mx-auto mb-4 animate-spin text-blue-600" />
          <p className="text-gray-600">Initializing Monitoring System...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">System Monitoring</h1>
          <div className="flex items-center space-x-4 mt-1">
            <div className="flex items-center space-x-2">
              {getConnectionStatusIcon()}
              <span className={`text-sm ${connectionStatus === 'connected' ? 'text-green-600' : 'text-red-600'}`}>
                {connectionStatus}
              </span>
            </div>
            <span className="text-xs text-gray-500">
              Last update: {format(metrics.timestamp, 'HH:mm:ss')}
            </span>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={actions.requestMetrics}
            className="flex items-center space-x-2 px-3 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200"
          >
            <RefreshCw className="w-4 h-4" />
            <span className="text-sm">Refresh</span>
          </button>
        </div>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center space-x-2">
            <Monitor className="w-5 h-5 text-blue-600" />
            <h3 className="text-sm font-medium">Response Time</h3>
          </div>
          <div className="mt-2">
            <span className="text-2xl font-bold">{metrics.performance.responseTime}</span>
            <span className="text-sm text-gray-500 ml-1">ms</span>
          </div>
        </div>

        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center space-x-2">
            <Activity className="w-5 h-5 text-green-600" />
            <h3 className="text-sm font-medium">Success Rate</h3>
          </div>
          <div className="mt-2">
            <span className="text-2xl font-bold">{(metrics.performance.successRate * 100).toFixed(1)}</span>
            <span className="text-sm text-gray-500 ml-1">%</span>
          </div>
        </div>

        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center space-x-2">
            <Monitor className="w-5 h-5 text-purple-600" />
            <h3 className="text-sm font-medium">CPU Usage</h3>
          </div>
          <div className="mt-2">
            <span className="text-2xl font-bold">{metrics.system.cpuUsage}</span>
            <span className="text-sm text-gray-500 ml-1">%</span>
          </div>
        </div>

        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center space-x-2">
            <Bell className="w-5 h-5 text-orange-600" />
            <h3 className="text-sm font-medium">Active Alerts</h3>
          </div>
          <div className="mt-2">
            <span className="text-2xl font-bold">{alerts.filter(a => !a.resolved).length}</span>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', name: 'Overview', icon: Monitor },
            { id: 'alerts', name: 'Alerts', icon: AlertTriangle, count: alerts.filter(a => !a.resolved).length }
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
                {tab.count !== undefined && tab.count > 0 && (
                  <span className="bg-red-100 text-red-600 px-2 py-1 text-xs rounded-full">
                    {tab.count}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">System Status</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Connection Status</span>
                <span className={`text-sm font-medium ${isHealthy ? 'text-green-600' : 'text-red-600'}`}>
                  {isHealthy ? 'Healthy' : 'Degraded'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Live Matches</span>
                <span className="text-sm font-medium">{metrics.realTime.liveMatches}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Predictions Today</span>
                <span className="text-sm font-medium">{metrics.predictions.totalGenerated}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Accuracy Rate</span>
                <span className="text-sm font-medium">{(metrics.predictions.accuracyRate * 100).toFixed(1)}%</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Metrics</h3>
            <div className="space-y-2">
              {metricsHistory.slice(-5).map((metric, index) => (
                <div key={index} className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">{format(metric.timestamp, 'HH:mm:ss')}</span>
                  <span className="text-gray-900">{metric.performance.responseTime}ms</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'alerts' && (
        <div className="bg-white rounded-lg border">
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">
                System Alerts
                {alerts.filter(a => !a.resolved).length > 0 && (
                  <span className="ml-2 px-2 py-1 text-xs bg-red-100 text-red-600 rounded-full">
                    {alerts.filter(a => !a.resolved).length} unresolved
                  </span>
                )}
              </h3>
            </div>
          </div>

          <div className="max-h-96 overflow-y-auto">
            {alerts.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-500" />
                <p>No alerts - System is healthy</p>
              </div>
            ) : (
              alerts.slice(0, 10).map((alert) => (
                <div
                  key={alert.id}
                  className={`border-l-4 p-4 border-b border-gray-100 last:border-b-0 ${
                    alert.type === 'critical' ? 'border-l-red-500 bg-red-50' :
                    alert.type === 'warning' ? 'border-l-yellow-500 bg-yellow-50' :
                    'border-l-blue-500 bg-blue-50'
                  } ${alert.resolved ? 'opacity-50' : ''}`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-3">
                      <AlertTriangle className={`w-4 h-4 ${
                        alert.type === 'critical' ? 'text-red-500' :
                        alert.type === 'warning' ? 'text-yellow-500' :
                        'text-blue-500'
                      }`} />
                      <div className="min-w-0 flex-1">
                        <h4 className="text-sm font-medium text-gray-900">{alert.title}</h4>
                        <p className="text-sm text-gray-600 mt-1">{alert.message}</p>
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
                        onClick={() => actions.resolveAlert(alert.id)}
                        className="text-xs text-green-600 hover:text-green-800 ml-2 whitespace-nowrap"
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
      )}
    </div>
  );
};

export default SimpleMonitoringDashboard;