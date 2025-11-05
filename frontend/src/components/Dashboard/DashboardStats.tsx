import React from 'react';
import {
  Calendar,
  Target,
  TrendingUp,
  Zap,
  Users,
  BarChart3,
  Clock,
  Star
} from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  change?: string;
  changeType?: 'positive' | 'negative' | 'neutral';
  icon: React.ComponentType<{ className?: string }>;
  description?: string;
}

const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  change,
  changeType = 'neutral',
  icon: Icon,
  description
}) => {
  const changeColorClass = {
    positive: 'text-success-600 bg-success-50',
    negative: 'text-danger-600 bg-danger-50',
    neutral: 'text-slate-600 bg-slate-50'
  }[changeType];

  return (
    <div className="card p-6 card-hover">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-primary-50 rounded-lg">
            <Icon className="w-6 h-6 text-primary-600" />
          </div>
          <div>
            <h3 className="text-sm font-medium text-slate-600">{title}</h3>
            <p className="text-2xl font-bold text-slate-900">{value}</p>
            {description && (
              <p className="text-xs text-slate-500 mt-1">{description}</p>
            )}
          </div>
        </div>
        {change && (
          <div className={`px-2 py-1 rounded-full text-xs font-medium ${changeColorClass}`}>
            {change}
          </div>
        )}
      </div>
    </div>
  );
};

const DashboardStats: React.FC = () => {
  const stats = [
    {
      title: 'Today\'s Matches',
      value: 12,
      change: '+3 from yesterday',
      changeType: 'positive' as const,
      icon: Calendar,
      description: '8 with predictions'
    },
    {
      title: 'Active Predictions',
      value: 24,
      change: '89% confidence avg',
      changeType: 'positive' as const,
      icon: Target,
      description: '16 recommended bets'
    },
    {
      title: 'Combinations Generated',
      value: 48,
      change: '+12 new',
      changeType: 'positive' as const,
      icon: Zap,
      description: '1.5-2.0 odds range'
    },
    {
      title: 'Win Rate (30d)',
      value: '95.2%',
      change: '+2.1%',
      changeType: 'positive' as const,
      icon: TrendingUp,
      description: '156/164 predictions'
    },
    {
      title: 'Teams Analyzed',
      value: 240,
      change: 'All major leagues',
      changeType: 'neutral' as const,
      icon: Users,
      description: '15+ metrics per team'
    },
    {
      title: 'ROI (30d)',
      value: '+18.4%',
      change: '+3.2%',
      changeType: 'positive' as const,
      icon: BarChart3,
      description: 'Based on recommendations'
    }
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Analytics Overview</h2>
          <p className="text-slate-600">Real-time insights and performance metrics</p>
        </div>
        <div className="flex items-center space-x-2">
          <Clock className="w-4 h-4 text-slate-400" />
          <span className="text-sm text-slate-600">Last updated: 2 min ago</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {stats.map((stat, index) => (
          <StatCard key={index} {...stat} />
        ))}
      </div>

      {/* Performance Indicators */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* System Health */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-slate-900">System Health</h3>
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-success-500 rounded-full"></div>
              <span className="text-sm text-success-600 font-medium">Operational</span>
            </div>
          </div>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-600">API Response Time</span>
              <span className="text-sm font-medium text-slate-900">127ms</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-600">Prediction Engine</span>
              <span className="text-sm font-medium text-success-600">Active</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-600">Data Sources</span>
              <span className="text-sm font-medium text-slate-900">5/5 Online</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-600">Cache Hit Rate</span>
              <span className="text-sm font-medium text-slate-900">94.2%</span>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Quick Actions</h3>
          <div className="grid grid-cols-2 gap-3">
            <button className="btn-primary text-left p-3 flex items-center space-x-2">
              <Target className="w-4 h-4" />
              <span className="text-sm">Generate Predictions</span>
            </button>
            <button className="btn-secondary text-left p-3 flex items-center space-x-2">
              <Zap className="w-4 h-4" />
              <span className="text-sm">View Combinations</span>
            </button>
            <button className="btn-secondary text-left p-3 flex items-center space-x-2">
              <BarChart3 className="w-4 h-4" />
              <span className="text-sm">Analytics Report</span>
            </button>
            <button className="btn-secondary text-left p-3 flex items-center space-x-2">
              <Star className="w-4 h-4" />
              <span className="text-sm">Top Picks</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardStats;