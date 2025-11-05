import React from 'react';
import {
  Calendar,
  MapPin,
  Clock,
  Target,
  TrendingUp,
  Zap,
  Star,
  MoreHorizontal
} from 'lucide-react';
import { Match } from '../../types';
import { format, parseISO } from 'date-fns';

interface MatchCardProps {
  match: Match;
  showPrediction?: boolean;
  onPredictClick?: (match: Match) => void;
  onFavoriteClick?: (match: Match) => void;
  isFavorite?: boolean;
}

const MatchCard: React.FC<MatchCardProps> = ({
  match,
  showPrediction = true,
  onPredictClick,
  onFavoriteClick,
  isFavorite = false
}) => {
  const formatMatchTime = (dateString: string) => {
    try {
      const date = parseISO(dateString);
      return {
        date: format(date, 'MMM dd'),
        time: format(date, 'HH:mm')
      };
    } catch {
      return { date: 'TBD', time: 'TBD' };
    }
  };

  const { date, time } = formatMatchTime(match.match_date);

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      SCHEDULED: { color: 'badge-secondary', text: 'Scheduled' },
      LIVE: { color: 'badge-danger', text: 'Live' },
      FINISHED: { color: 'badge-success', text: 'Finished' },
      POSTPONED: { color: 'badge-warning', text: 'Postponed' }
    };

    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.SCHEDULED;
    return (
      <span className={`badge ${config.color}`}>
        {config.text}
      </span>
    );
  };

  const getConfidenceBadge = (confidence?: number) => {
    if (!confidence) return null;

    const confidencePercent = Math.round(confidence * 100);
    let badgeColor = 'badge-secondary';

    if (confidencePercent >= 80) badgeColor = 'badge-success';
    else if (confidencePercent >= 60) badgeColor = 'badge-warning';
    else badgeColor = 'badge-danger';

    return (
      <span className={`badge ${badgeColor}`}>
        {confidencePercent}% confidence
      </span>
    );
  };

  return (
    <div className="card p-6 card-hover">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          {getStatusBadge(match.status)}
          {match.is_predicted && getConfidenceBadge(match.confidence_score)}
        </div>
        <div className="flex items-center space-x-1">
          {onFavoriteClick && (
            <button
              onClick={() => onFavoriteClick(match)}
              className={`p-1 rounded-full hover:bg-slate-100 transition-colors ${
                isFavorite ? 'text-warning-500' : 'text-slate-400'
              }`}
            >
              <Star className={`w-4 h-4 ${isFavorite ? 'fill-current' : ''}`} />
            </button>
          )}
          <button className="p-1 rounded-full hover:bg-slate-100 transition-colors">
            <MoreHorizontal className="w-4 h-4 text-slate-400" />
          </button>
        </div>
      </div>

      {/* Teams */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-slate-100 rounded-full flex items-center justify-center">
            <span className="text-sm font-medium text-slate-600">
              {match.home_team.name.substring(0, 2).toUpperCase()}
            </span>
          </div>
          <div>
            <p className="font-medium text-slate-900">{match.home_team.name}</p>
            <p className="text-xs text-slate-500">{match.home_team.league}</p>
          </div>
        </div>

        <div className="text-center">
          {match.status === 'FINISHED' && match.home_score !== undefined && match.away_score !== undefined ? (
            <div className="text-xl font-bold text-slate-900">
              {match.home_score} - {match.away_score}
            </div>
          ) : (
            <div className="text-slate-400">
              <div className="text-sm">{date}</div>
              <div className="text-lg font-semibold">{time}</div>
            </div>
          )}
        </div>

        <div className="flex items-center space-x-3">
          <div className="text-right">
            <p className="font-medium text-slate-900">{match.away_team.name}</p>
            <p className="text-xs text-slate-500">{match.away_team.league}</p>
          </div>
          <div className="w-10 h-10 bg-slate-100 rounded-full flex items-center justify-center">
            <span className="text-sm font-medium text-slate-600">
              {match.away_team.name.substring(0, 2).toUpperCase()}
            </span>
          </div>
        </div>
      </div>

      {/* Match details */}
      <div className="flex items-center space-x-4 text-sm text-slate-500 mb-4">
        <div className="flex items-center space-x-1">
          <MapPin className="w-4 h-4" />
          <span>{match.venue || 'TBD'}</span>
        </div>
        <div className="flex items-center space-x-1">
          <Calendar className="w-4 h-4" />
          <span>{match.league}</span>
        </div>
        {match.referee && (
          <div className="flex items-center space-x-1">
            <span>Ref: {match.referee}</span>
          </div>
        )}
      </div>

      {/* Weather info */}
      {match.weather_condition && (
        <div className="flex items-center space-x-4 text-sm text-slate-500 mb-4">
          <span>{match.weather_condition}</span>
          {match.temperature && <span>{match.temperature}°C</span>}
          {match.wind_speed && <span>Wind: {match.wind_speed} km/h</span>}
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center justify-between pt-4 border-t border-slate-200">
        <div className="flex items-center space-x-2">
          {match.is_predicted ? (
            <span className="flex items-center space-x-1 text-sm text-success-600">
              <Target className="w-4 h-4" />
              <span>Predicted</span>
            </span>
          ) : (
            showPrediction && onPredictClick && (
              <button
                onClick={() => onPredictClick(match)}
                className="btn-primary text-sm py-1 px-3 flex items-center space-x-1"
              >
                <Target className="w-4 h-4" />
                <span>Predict</span>
              </button>
            )
          )}
        </div>

        <div className="flex items-center space-x-2">
          <button className="btn-secondary text-sm py-1 px-3 flex items-center space-x-1">
            <TrendingUp className="w-4 h-4" />
            <span>Analytics</span>
          </button>
          <button className="btn-secondary text-sm py-1 px-3 flex items-center space-x-1">
            <Zap className="w-4 h-4" />
            <span>Odds</span>
          </button>
        </div>
      </div>

      {/* Live match info */}
      {match.status === 'LIVE' && (
        <div className="mt-4 p-3 bg-danger-50 rounded-lg border border-danger-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-danger-500 rounded-full animate-pulse"></div>
              <span className="text-sm font-medium text-danger-700">Live</span>
            </div>
            {match.minute && (
              <span className="text-sm text-danger-600">{match.minute}'</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default MatchCard;