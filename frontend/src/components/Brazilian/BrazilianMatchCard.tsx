import React from 'react';
import {
  Clock,
  MapPin,
  Thermometer,
  Users,
  Star,
  Trophy,
  Calendar,
  Activity
} from 'lucide-react';
import { BrazilianMatch, AdvancedPrediction } from '../../services/brazilianFootballAPI';
import PredictButton from './PredictButton';

interface BrazilianMatchCardProps {
  match: BrazilianMatch;
  onPredictionGenerated?: (prediction: AdvancedPrediction) => void;
}

const BrazilianMatchCard: React.FC<BrazilianMatchCardProps> = ({ match, onPredictionGenerated }) => {
  const getCompetitionInfo = (competition: string) => {
    switch (competition) {
      case 'brasileirao':
        return {
          name: 'Brasileirão Série A',
          emoji: '🏆',
          color: 'bg-green-500',
          textColor: 'text-green-700',
          bgColor: 'bg-green-50'
        };
      case 'copa_brasil':
        return {
          name: 'Copa do Brasil',
          emoji: '🏅',
          color: 'bg-blue-500',
          textColor: 'text-blue-700',
          bgColor: 'bg-blue-50'
        };
      case 'libertadores':
        return {
          name: 'Copa Libertadores',
          emoji: '🌎',
          color: 'bg-yellow-500',
          textColor: 'text-yellow-700',
          bgColor: 'bg-yellow-50'
        };
      default:
        return {
          name: 'Futebol Brasileiro',
          emoji: '⚽',
          color: 'bg-gray-500',
          textColor: 'text-gray-700',
          bgColor: 'bg-gray-50'
        };
    }
  };

  const getStatusInfo = (status: string, minute?: number) => {
    switch (status) {
      case 'live':
        return {
          text: `AO VIVO - ${minute}'`,
          color: 'bg-red-500',
          pulse: true
        };
      case 'finished':
        return {
          text: 'FINALIZADO',
          color: 'bg-gray-500',
          pulse: false
        };
      default:
        return {
          text: match.time,
          color: 'bg-blue-500',
          pulse: false
        };
    }
  };

  const getWeatherIcon = (condition: string) => {
    switch (condition) {
      case 'rain': return '🌧️';
      case 'cloudy': return '☁️';
      case 'clear': return '☀️';
      default: return '🌤️';
    }
  };

  const getFormRating = (form: string) => {
    const wins = (form.match(/W/g) || []).length;
    const rating = (wins / 5) * 100;

    if (rating >= 80) return { color: 'text-green-600', bg: 'bg-green-100' };
    if (rating >= 60) return { color: 'text-yellow-600', bg: 'bg-yellow-100' };
    return { color: 'text-red-600', bg: 'bg-red-100' };
  };

  const competitionInfo = getCompetitionInfo(match.competition);
  const statusInfo = getStatusInfo(match.status, match.minute);
  const homeFormRating = getFormRating(match.homeTeam.stats.form);
  const awayFormRating = getFormRating(match.awayTeam.stats.form);

  return (
    <div className="bg-white rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 border border-gray-100 overflow-hidden">
      {/* Header */}
      <div className={`${competitionInfo.bgColor} border-b border-gray-100 p-4`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-2xl">{competitionInfo.emoji}</span>
            <div>
              <h3 className={`font-bold ${competitionInfo.textColor}`}>
                {competitionInfo.name}
              </h3>
              <p className="text-sm text-gray-600">{match.round}</p>
            </div>
          </div>

          <div className="text-right">
            <div className={`inline-block px-3 py-1 rounded-full text-white text-sm font-semibold ${statusInfo.color} ${statusInfo.pulse ? 'animate-pulse' : ''}`}>
              {statusInfo.text}
            </div>
            <div className="text-sm text-gray-600 mt-1 flex items-center">
              <Calendar className="w-3 h-3 mr-1" />
              {new Date(match.date).toLocaleDateString('pt-BR')}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="p-6">
        {/* Teams */}
        <div className="grid grid-cols-3 items-center gap-4 mb-6">
          {/* Home Team */}
          <div className="text-center">
            <div className="w-16 h-16 mx-auto mb-3 bg-gray-100 rounded-full flex items-center justify-center">
              <img
                src={match.homeTeam.logo}
                alt={match.homeTeam.name}
                className="w-12 h-12 object-contain"
                onError={(e) => {
                  (e.target as HTMLImageElement).src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGNpcmNsZSBjeD0iMjAiIGN5PSIyMCIgcj0iMjAiIGZpbGw9IiNGM0Y0RjYiLz4KPHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDJDNi40ODYgMiAyIDYuNDg2IDIgMTJTNi40ODYgMjIgMTIgMjJTMjIgMTcuNTE0IDIyIDEyUzE3LjUxNCAyIDEyIDJaTTEyIDIwQzcuNTg5IDIwIDQgMTYuNDExIDQgMTJTNy41ODkgNDEyIDRTMjAgNy41ODkgMjAgMTJTMTYuNDExIDIwIDEyIDIwWiIgZmlsbD0iIzlCA0E5RCIvPgo8L3N2Zz4KPC9zdmc+';
                }}
              />
            </div>
            <h4 className="font-bold text-gray-800 text-sm mb-1">{match.homeTeam.shortName}</h4>
            <div className="text-xs text-gray-500 mb-2">{match.homeTeam.state}</div>

            {/* Home Stats */}
            <div className="space-y-1">
              <div className="text-xs text-gray-600">
                <span className="font-semibold">{match.homeTeam.stats.position}º</span> • {match.homeTeam.stats.points}pts
              </div>
              <div className={`inline-block px-2 py-1 rounded text-xs font-medium ${homeFormRating.bg} ${homeFormRating.color}`}>
                {match.homeTeam.stats.form}
              </div>
            </div>
          </div>

          {/* Score/VS */}
          <div className="text-center">
            {match.status === 'live' || match.status === 'finished' ? (
              <div>
                <div className="text-3xl font-bold text-gray-800 mb-1">
                  {match.score.home} - {match.score.away}
                </div>
                {match.score.halfTime && (
                  <div className="text-sm text-gray-500">
                    HT: {match.score.halfTime.home}-{match.score.halfTime.away}
                  </div>
                )}
              </div>
            ) : (
              <div>
                <div className="text-2xl font-bold text-gray-400 mb-2">VS</div>
                <div className="text-sm text-gray-600 flex items-center justify-center">
                  <Clock className="w-3 h-3 mr-1" />
                  {match.time}
                </div>
              </div>
            )}
          </div>

          {/* Away Team */}
          <div className="text-center">
            <div className="w-16 h-16 mx-auto mb-3 bg-gray-100 rounded-full flex items-center justify-center">
              <img
                src={match.awayTeam.logo}
                alt={match.awayTeam.name}
                className="w-12 h-12 object-contain"
                onError={(e) => {
                  (e.target as HTMLImageElement).src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGNpcmNsZSBjeD0iMjAiIGN5PSIyMCIgcj0iMjAiIGZpbGw9IiNGM0Y0RjYiLz4KPHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDJDNi40ODYgMiAyIDYuNDg2IDIgMTJTNi40ODYgMjIgMTIgMjJTMjIgMTcuNTE0IDIyIDEyUzE3LjUxNCAyIDEyIDJaTTEyIDIwQzcuNTg5IDIwIDQgMTYuNDExIDQgMTJTNy41ODkgNDEyIDRTMjAgNy41ODkgMjAgMTJTMTYuNDExIDIwIDEyIDIwWiIgZmlsbD0iIzlCA0E5RCIvPgo8L3N2Zz4KPC9zdmc+';
                }}
              />
            </div>
            <h4 className="font-bold text-gray-800 text-sm mb-1">{match.awayTeam.shortName}</h4>
            <div className="text-xs text-gray-500 mb-2">{match.awayTeam.state}</div>

            {/* Away Stats */}
            <div className="space-y-1">
              <div className="text-xs text-gray-600">
                <span className="font-semibold">{match.awayTeam.stats.position}º</span> • {match.awayTeam.stats.points}pts
              </div>
              <div className={`inline-block px-2 py-1 rounded text-xs font-medium ${awayFormRating.bg} ${awayFormRating.color}`}>
                {match.awayTeam.stats.form}
              </div>
            </div>
          </div>
        </div>

        {/* Match Details */}
        <div className="border-t border-gray-100 pt-4 mb-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div className="flex items-center space-x-2 text-gray-600">
              <MapPin className="w-4 h-4" />
              <span className="truncate">{match.venue}</span>
            </div>

            {match.weather && (
              <div className="flex items-center space-x-2 text-gray-600">
                <span>{getWeatherIcon(match.weather.condition)}</span>
                <span>{match.weather.temperature}°C</span>
              </div>
            )}

            {match.context.rivalry && (
              <div className="flex items-center space-x-2 text-red-600">
                <Star className="w-4 h-4" />
                <span className="font-semibold">Clássico</span>
              </div>
            )}

            <div className="flex items-center space-x-2 text-gray-600">
              <Activity className="w-4 h-4" />
              <span>Importância: {match.context.importance}/10</span>
            </div>
          </div>
        </div>

        {/* Quick Stats Comparison */}
        <div className="bg-gray-50 rounded-lg p-4 mb-4">
          <h5 className="font-semibold text-gray-700 mb-3 text-center">Comparação Rápida</h5>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div className="text-center">
              <div className="text-lg font-bold text-blue-600">{match.homeTeam.stats.avgGoalsFor.toFixed(1)}</div>
              <div className="text-xs text-gray-500">Gols/Jogo</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold text-green-600">
                {((match.homeTeam.stats.wins + match.awayTeam.stats.wins) / (match.homeTeam.stats.matches + match.awayTeam.stats.matches) * 100).toFixed(0)}%
              </div>
              <div className="text-xs text-gray-500">Taxa Vitórias</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold text-blue-600">{match.awayTeam.stats.avgGoalsFor.toFixed(1)}</div>
              <div className="text-xs text-gray-500">Gols/Jogo</div>
            </div>
          </div>
        </div>

        {/* Predict Button */}
        <div className="text-center">
          <PredictButton
            match={match}
            onPredictionGenerated={onPredictionGenerated}
          />
        </div>
      </div>

      {/* Context Indicators */}
      {(match.context.rivalry || match.context.importance >= 8) && (
        <div className="bg-gradient-to-r from-red-50 to-yellow-50 border-t border-gray-100 px-6 py-3">
          <div className="flex items-center justify-center space-x-4 text-sm">
            {match.context.rivalry && (
              <div className="flex items-center space-x-1 text-red-600">
                <Star className="w-4 h-4" />
                <span className="font-semibold">Clássico</span>
              </div>
            )}
            {match.context.importance >= 8 && (
              <div className="flex items-center space-x-1 text-yellow-600">
                <Trophy className="w-4 h-4" />
                <span className="font-semibold">Jogo Decisivo</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default BrazilianMatchCard;