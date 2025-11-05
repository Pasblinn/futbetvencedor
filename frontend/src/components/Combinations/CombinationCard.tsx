import React from 'react';
import {
  Target,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Clock,
  DollarSign,
  BarChart3
} from 'lucide-react';
import { BetCombination } from '../../types';

interface CombinationCardProps {
  combination: BetCombination;
  onSelectCombination?: (combination: BetCombination) => void;
}

const CombinationCard: React.FC<CombinationCardProps> = ({
  combination,
  onSelectCombination
}) => {
  const getTypeColor = (type: string) => {
    const colors = {
      single: 'bg-blue-100 text-blue-800',
      double: 'bg-green-100 text-green-800',
      treble: 'bg-yellow-100 text-yellow-800',
      multiple: 'bg-purple-100 text-purple-800'
    };
    return colors[type as keyof typeof colors] || colors.single;
  };

  const getRiskLevelColor = (riskLevel: string) => {
    const colors = {
      LOW: 'text-success-600 bg-success-50',
      MEDIUM: 'text-warning-600 bg-warning-50',
      HIGH: 'text-danger-600 bg-danger-50'
    };
    return colors[riskLevel as keyof typeof colors] || colors.MEDIUM;
  };

  const getExpectedValueColor = (value: number) => {
    if (value >= 0.1) return 'text-success-700';
    if (value >= 0.05) return 'text-warning-700';
    return 'text-slate-600';
  };

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  const formatOdds = (odds: number) => {
    return odds.toFixed(2);
  };

  return (
    <div className="card p-6 card-hover">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <span className={`badge ${getTypeColor(combination.type)}`}>
            {combination.type.charAt(0).toUpperCase() + combination.type.slice(1)}
          </span>
          <span className={`badge ${getRiskLevelColor(combination.risk_level)}`}>
            {combination.risk_level} Risk
          </span>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-slate-900">
            {formatOdds(combination.combined_odds)}
          </div>
          <div className="text-xs text-slate-500">Combined Odds</div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-3 gap-4 mb-4">
        <div className="text-center">
          <div className="text-lg font-semibold text-slate-900">
            {formatPercentage(combination.combined_probability)}
          </div>
          <div className="text-xs text-slate-500">Probability</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-semibold text-slate-900">
            {formatPercentage(combination.combined_confidence)}
          </div>
          <div className="text-xs text-slate-500">Confidence</div>
        </div>
        <div className="text-center">
          <div className={`text-lg font-semibold ${getExpectedValueColor(combination.expected_value)}`}>
            {formatPercentage(combination.expected_value)}
          </div>
          <div className="text-xs text-slate-500">Expected Value</div>
        </div>
      </div>

      {/* Selections */}
      <div className="space-y-2 mb-4">
        <h4 className="text-sm font-medium text-slate-700">Selections:</h4>
        {combination.selections.map((selection, index) => (
          <div key={index} className="flex items-center justify-between p-2 bg-slate-50 rounded-lg">
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-900 truncate">
                {selection.match_name}
              </p>
              <p className="text-xs text-slate-500">
                {selection.market}: {selection.selection}
              </p>
            </div>
            <div className="text-right ml-2">
              <div className="text-sm font-medium text-slate-900">
                {formatOdds(selection.odds)}
              </div>
              <div className="text-xs text-slate-500">
                {formatPercentage(selection.probability)}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Additional Info */}
      <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
        <div className="flex items-center space-x-2">
          <DollarSign className="w-4 h-4 text-slate-400" />
          <span className="text-slate-600">Kelly: {formatPercentage(combination.kelly_percentage)}</span>
        </div>
        {combination.diversification_score && (
          <div className="flex items-center space-x-2">
            <BarChart3 className="w-4 h-4 text-slate-400" />
            <span className="text-slate-600">Diversification: {combination.diversification_score}</span>
          </div>
        )}
      </div>

      {/* Correlation Warning */}
      {combination.correlation_check && combination.correlation_check.risk !== 'LOW' && (
        <div className="flex items-start space-x-2 p-3 bg-warning-50 rounded-lg border border-warning-200 mb-4">
          <AlertTriangle className="w-4 h-4 text-warning-600 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-sm font-medium text-warning-800">Correlation Risk</p>
            <p className="text-xs text-warning-700">{combination.correlation_check.note}</p>
          </div>
        </div>
      )}

      {/* Recommendation */}
      <div className="flex items-center justify-between pt-4 border-t border-slate-200">
        <div className="flex items-center space-x-2">
          {combination.expected_value > 0.05 ? (
            <>
              <CheckCircle className="w-4 h-4 text-success-600" />
              <span className="text-sm text-success-600 font-medium">Recommended</span>
            </>
          ) : (
            <>
              <Clock className="w-4 h-4 text-warning-600" />
              <span className="text-sm text-warning-600 font-medium">Monitor</span>
            </>
          )}
        </div>

        <div className="flex items-center space-x-2">
          <button className="btn-secondary text-sm py-1 px-3 flex items-center space-x-1">
            <TrendingUp className="w-3 h-3" />
            <span>Analysis</span>
          </button>
          {onSelectCombination && (
            <button
              onClick={() => onSelectCombination(combination)}
              className="btn-primary text-sm py-1 px-3 flex items-center space-x-1"
            >
              <Target className="w-3 h-3" />
              <span>Select</span>
            </button>
          )}
        </div>
      </div>

      {/* Performance Indicator */}
      <div className="mt-3 flex items-center justify-center">
        <div className="w-full bg-slate-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-300 ${
              combination.expected_value > 0.1 ? 'bg-success-500' :
              combination.expected_value > 0.05 ? 'bg-warning-500' :
              'bg-slate-400'
            }`}
            style={{ width: `${Math.min(combination.expected_value * 500, 100)}%` }}
          ></div>
        </div>
      </div>
    </div>
  );
};

export default CombinationCard;