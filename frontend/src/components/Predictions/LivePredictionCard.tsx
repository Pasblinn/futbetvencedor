import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  Target,
  Clock,
  MapPin,
  Users,
  Activity,
  Zap,
  AlertCircle,
  RefreshCw,
  CheckCircle,
  Shield,
  BarChart3,
  TrendingDown,
  Eye,
  Star,
  AlertTriangle
} from 'lucide-react';
import { LiveMatch } from '../../services/liveDataService';
import { RealTimePrediction } from '../../services/realTimePredictionService';

interface LivePredictionCardProps {
  match: LiveMatch;
  prediction: RealTimePrediction | null;
  onRefresh: () => void;
  loading?: boolean;
  showAdvanced?: boolean;
}

const LivePredictionCard: React.FC<LivePredictionCardProps> = ({
  match,
  prediction,
  onRefresh,
  loading = false,
  showAdvanced = false
}) => {
  const [timeToKickoff, setTimeToKickoff] = useState<string>('');
  const [isLive, setIsLive] = useState(false);
  const [showMomentum, setShowMomentum] = useState(false);

  useEffect(() => {
    const updateTime = () => {
      const matchTime = new Date(`${match.fixture.date}T${match.fixture.time}`).getTime();
      const now = Date.now();
      const diff = matchTime - now;

      if (diff > 0) {
        const hours = Math.floor(diff / (1000 * 60 * 60));
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        setTimeToKickoff(`${hours}h ${minutes}m`);
        setIsLive(false);
      } else {
        setTimeToKickoff('AO VIVO');
        setIsLive(true);
      }
    };

    updateTime();
    const interval = setInterval(updateTime, 60000); // Atualiza a cada minuto

    return () => clearInterval(interval);
  }, [match.fixture.date, match.fixture.time]);

  const getPredictionColor = (outcome: string) => {
    switch (outcome) {
      case 'home_win': return 'text-blue-600 bg-blue-50';
      case 'away_win': return 'text-red-600 bg-red-50';
      case 'draw': return 'text-yellow-600 bg-yellow-50';
      default: return 'text-slate-600 bg-slate-50';
    }
  };

  const getPredictionText = (outcome: string) => {
    switch (outcome) {
      case 'home_win': return `${match.homeTeam.name} Vence`;
      case 'away_win': return `${match.awayTeam.name} Vence`;
      case 'draw': return 'Empate';
      default: return 'Indefinido';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-success-700 bg-success-100';
    if (confidence >= 0.7) return 'text-warning-600 bg-warning-100';
    return 'text-danger-600 bg-danger-100';
  };

  const formatPercentage = (value: number) => `${(value * 100).toFixed(1)}%`;

  const getMomentumColor = (direction: string, strength: number) => {
    if (strength < 0.3) return 'text-slate-500 bg-slate-100';
    switch (direction) {
      case 'home': return 'text-blue-700 bg-blue-100';
      case 'away': return 'text-red-700 bg-red-100';
      default: return 'text-slate-600 bg-slate-100';
    }
  };

  const getValueColor = (recommendation: string) => {
    switch (recommendation) {
      case 'strong_buy': return 'text-success-700 bg-success-100 border-success-300';
      case 'buy': return 'text-success-600 bg-success-50 border-success-200';
      case 'hold': return 'text-warning-600 bg-warning-50 border-warning-200';
      case 'avoid': return 'text-danger-600 bg-danger-50 border-danger-200';
      default: return 'text-slate-600 bg-slate-50 border-slate-200';
    }
  };

  return (
    <div className="card p-6 card-hover">
      {/* Header com Status */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className={`w-3 h-3 rounded-full ${isLive ? 'bg-red-500 animate-pulse' : 'bg-green-500'}`}></div>
          <div>
            <h3 className="text-lg font-semibold text-slate-900">
              {match.homeTeam.name} vs {match.awayTeam.name}
            </h3>
            <p className="text-sm text-slate-600">{match.league.name}</p>
          </div>
        </div>

        <div className="text-right">
          <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
            isLive ? 'text-red-700 bg-red-100' : 'text-slate-700 bg-slate-100'
          }`}>
            <Clock className="w-4 h-4 mr-1" />
            {timeToKickoff}
          </div>
          <p className="text-xs text-slate-500 mt-1">{match.fixture.time}</p>
        </div>
      </div>

      {/* Live Data - Se o jogo estiver ao vivo */}
      {prediction?.liveData?.isLive && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
                <span className="text-sm font-medium text-red-700">AO VIVO</span>
                <span className="text-sm text-red-600">{prediction.liveData.currentMinute}'</span>
              </div>
              {prediction.liveData.currentScore && (
                <div className="text-lg font-bold text-red-700">
                  {prediction.liveData.currentScore.home} - {prediction.liveData.currentScore.away}
                </div>
              )}
            </div>

            {/* Momentum Indicator */}
            <div className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
              getMomentumColor(prediction.liveData.momentum.direction, prediction.liveData.momentum.strength)
            }`}>
              {prediction.liveData.momentum.direction === 'home' && <TrendingUp className="w-3 h-3 mr-1" />}
              {prediction.liveData.momentum.direction === 'away' && <TrendingDown className="w-3 h-3 mr-1" />}
              {prediction.liveData.momentum.direction === 'neutral' && <BarChart3 className="w-3 h-3 mr-1" />}
              Momentum: {prediction.liveData.momentum.direction === 'neutral' ? 'Equilibrado' :
                        prediction.liveData.momentum.direction === 'home' ? match.homeTeam.name : match.awayTeam.name}
            </div>
          </div>
        </div>
      )}

      {/* Times e Odds */}
      <div className="grid grid-cols-3 gap-4 mb-4">
        <div className="text-center">
          <div className="flex flex-col items-center mb-2">
            <img
              src={match.homeTeam.logo}
              alt={match.homeTeam.name}
              className="w-12 h-12 mb-2"
              onError={(e) => {
                e.currentTarget.src = '/api/placeholder/48/48';
              }}
            />
            <p className="text-sm font-medium text-slate-900">{match.homeTeam.name}</p>
            <p className="text-xs text-slate-500">Forma: {match.homeTeam.form}</p>
          </div>
          {match.odds && (
            <div className="text-lg font-bold text-blue-600">{match.odds.home}</div>
          )}
        </div>

        <div className="text-center flex flex-col justify-center">
          <div className="text-2xl font-bold text-slate-400 mb-2">VS</div>
          {match.odds && (
            <div className="text-sm text-yellow-600 font-medium">
              Empate: {match.odds.draw}
            </div>
          )}
        </div>

        <div className="text-center">
          <div className="flex flex-col items-center mb-2">
            <img
              src={match.awayTeam.logo}
              alt={match.awayTeam.name}
              className="w-12 h-12 mb-2"
              onError={(e) => {
                e.currentTarget.src = '/api/placeholder/48/48';
              }}
            />
            <p className="text-sm font-medium text-slate-900">{match.awayTeam.name}</p>
            <p className="text-xs text-slate-500">Forma: {match.awayTeam.form}</p>
          </div>
          {match.odds && (
            <div className="text-lg font-bold text-red-600">{match.odds.away}</div>
          )}
        </div>
      </div>

      {/* Predição Principal */}
      {prediction ? (
        <div className="mb-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-medium text-slate-900 flex items-center">
              <Target className="w-4 h-4 mr-2" />
              Predição IA
            </h4>
            <button
              onClick={onRefresh}
              disabled={loading}
              className="p-1 rounded hover:bg-slate-100 transition-colors"
            >
              <RefreshCw className={`w-4 h-4 text-slate-500 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>

          <div className="grid grid-cols-2 gap-4 mb-3">
            <div className={`p-3 rounded-lg ${getPredictionColor(prediction.prediction.outcome)}`}>
              <div className="text-sm font-medium mb-1">Resultado Mais Provável</div>
              <div className="text-lg font-bold">
                {getPredictionText(prediction.prediction.outcome)}
              </div>
              <div className="text-sm opacity-75">
                {formatPercentage(prediction.prediction.confidence)} confiança
              </div>
            </div>

            <div className="p-3 rounded-lg bg-slate-50">
              <div className="text-sm font-medium text-slate-700 mb-2">
                Probabilidades {prediction.liveData?.isLive ? '(Atualizadas)' : ''}
              </div>
              <div className="space-y-1 text-xs">
                <div className="flex justify-between">
                  <span>Casa:</span>
                  <span className="font-medium">
                    {formatPercentage(prediction.updatedProbabilities?.homeWin || prediction.prediction.probability.homeWin)}
                    {prediction.liveData?.isLive && (
                      <span className="ml-1 text-blue-500">⬆</span>
                    )}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Empate:</span>
                  <span className="font-medium">
                    {formatPercentage(prediction.updatedProbabilities?.draw || prediction.prediction.probability.draw)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Visitante:</span>
                  <span className="font-medium">
                    {formatPercentage(prediction.updatedProbabilities?.awayWin || prediction.prediction.probability.awayWin)}
                    {prediction.liveData?.isLive && (
                      <span className="ml-1 text-red-500">⬇</span>
                    )}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Mercados Secundários */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
            <div className="p-2 bg-primary-50 rounded">
              <div className="text-xs text-primary-600 font-medium">Gols</div>
              <div className="text-sm font-bold text-primary-900">
                {prediction.markets.totalGoals.prediction === 'over' ? 'Mais' : 'Menos'} {prediction.markets.totalGoals.line}
              </div>
              <div className="text-xs text-primary-600">
                Esp: {prediction.markets.totalGoals.expectedGoals}
              </div>
            </div>

            <div className="p-2 bg-success-50 rounded">
              <div className="text-xs text-success-600 font-medium">Ambos Marcam</div>
              <div className="text-sm font-bold text-success-900">
                {prediction.markets.bothTeamsScore.prediction === 'yes' ? 'Sim' : 'Não'}
              </div>
              <div className="text-xs text-success-600">
                {formatPercentage(prediction.markets.bothTeamsScore.confidence)}
              </div>
            </div>

            <div className="p-2 bg-warning-50 rounded">
              <div className="text-xs text-warning-600 font-medium">Escanteios</div>
              <div className="text-sm font-bold text-warning-900">
                {prediction.markets.corners.prediction === 'over' ? 'Mais' : 'Menos'} {prediction.markets.corners.line}
              </div>
              <div className="text-xs text-warning-600">
                Esp: {prediction.markets.corners.expectedCorners}
              </div>
            </div>

            <div className="p-2 bg-danger-50 rounded">
              <div className="text-xs text-danger-600 font-medium">Cartões</div>
              <div className="text-sm font-bold text-danger-900">
                {prediction.markets.cards.prediction === 'over' ? 'Mais' : 'Menos'} {prediction.markets.cards.line}
              </div>
              <div className="text-xs text-danger-600">
                Esp: {prediction.markets.cards.expectedCards}
              </div>
            </div>
          </div>

          {/* Alertas de Valor - Se disponível */}
          {prediction.alerts?.valueOdds && prediction.alerts.valueOdds.length > 0 && (
            <div className="mb-4">
              <div className="text-sm font-medium text-slate-900 mb-2 flex items-center">
                <Star className="w-4 h-4 mr-2 text-warning-500" />
                Oportunidades de Valor
              </div>
              <div className="space-y-2">
                {prediction.alerts.valueOdds.slice(0, 2).map((alert, index) => (
                  <div key={index} className={`p-2 rounded border ${getValueColor(alert.recommendation)}`}>
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-xs font-medium">{alert.market}</div>
                        <div className="text-xs opacity-75">{alert.reasoning}</div>
                      </div>
                      <div className="text-xs font-bold">
                        {(alert.value * 100).toFixed(0)}% valor
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Mercados Ao Vivo - Se jogo estiver ao vivo */}
          {prediction.liveData?.isLive && prediction.liveMarkets && (
            <div className="mb-4">
              <div className="text-sm font-medium text-slate-900 mb-2 flex items-center">
                <Eye className="w-4 h-4 mr-2 text-red-500" />
                Mercados Ao Vivo
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div className="p-2 bg-red-50 rounded">
                  <div className="text-xs text-red-600 font-medium">Próximo Gol</div>
                  <div className="text-sm font-bold text-red-900">
                    Casa: {formatPercentage(prediction.updatedProbabilities?.nextGoalHome || 0.5)}
                  </div>
                </div>
                <div className="p-2 bg-blue-50 rounded">
                  <div className="text-xs text-blue-600 font-medium">Tempo do Gol</div>
                  <div className="text-sm font-bold text-blue-900">
                    5min: {formatPercentage(prediction.liveMarkets.timeOfNextGoal?.next5Min || 0.15)}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Análise Resumida */}
          <div className="p-3 bg-slate-50 rounded-lg">
            <div className="flex items-start space-x-2">
              <Activity className="w-4 h-4 text-slate-500 mt-0.5" />
              <div>
                <div className="text-sm font-medium text-slate-900 mb-1">Análise Resumida</div>
                <p className="text-xs text-slate-600 leading-relaxed">
                  {prediction.analysis.reasoning.slice(0, 200)}...
                </p>
              </div>
            </div>
          </div>

        </div>
      ) : (
        <div className="text-center py-8">
          <div className="w-12 h-12 bg-slate-100 rounded-lg flex items-center justify-center mx-auto mb-3">
            <Zap className="w-6 h-6 text-slate-400" />
          </div>
          <p className="text-sm text-slate-600">Gerando predição...</p>
          <button
            onClick={onRefresh}
            className="btn-primary mt-3 text-sm px-4 py-2"
          >
            Analisar Jogo
          </button>
        </div>
      )}

      {/* Footer com informações do jogo */}
      <div className="pt-3 border-t border-slate-200">
        <div className="flex items-center justify-between text-xs text-slate-500">
          <div className="flex items-center space-x-4">
            <div className="flex items-center">
              <MapPin className="w-3 h-3 mr-1" />
              {match.fixture.venue.name}
            </div>
            <div className="flex items-center">
              <Users className="w-3 h-3 mr-1" />
              {match.fixture.referee}
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {prediction && (
              <div className={`inline-flex items-center px-2 py-1 rounded text-xs ${
                getConfidenceColor(prediction.dataQuality.overall)
              }`}>
                <Shield className="w-3 h-3 mr-1" />
                Qualidade: {formatPercentage(prediction.dataQuality.overall)}
              </div>
            )}

            {match.odds && (
              <div className="text-xs text-slate-400">
                Odds: {match.odds.source}
              </div>
            )}
          </div>
        </div>

        {/* Alertas de Momentum */}
        {prediction?.alerts?.momentum && prediction.alerts.momentum.length > 0 && (
          <div className="mt-2 space-y-1">
            {prediction.alerts.momentum.slice(0, 2).map((alert, index) => (
              <div key={index} className={`p-2 rounded border ${
                alert.type === 'positive' ? 'bg-success-50 border-success-200' :
                alert.type === 'warning' ? 'bg-warning-50 border-warning-200' :
                'bg-danger-50 border-danger-200'
              }`}>
                <div className="flex items-center space-x-2">
                  {alert.type === 'positive' && <CheckCircle className="w-4 h-4 text-success-600" />}
                  {alert.type === 'warning' && <AlertTriangle className="w-4 h-4 text-warning-600" />}
                  {alert.type === 'negative' && <AlertCircle className="w-4 h-4 text-danger-600" />}
                  <div className={`text-xs ${
                    alert.type === 'positive' ? 'text-success-700' :
                    alert.type === 'warning' ? 'text-warning-700' :
                    'text-danger-700'
                  }`}>
                    <strong>{alert.type === 'positive' ? 'Oportunidade:' :
                             alert.type === 'warning' ? 'Atenção:' : 'Risco:'}</strong> {alert.message}
                    <span className="ml-2 opacity-75">({formatPercentage(alert.confidence)} confiança)</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Risk Factors (fallback) */}
        {prediction && prediction.analysis.riskFactors.length > 0 &&
         (!prediction.alerts?.momentum || prediction.alerts.momentum.length === 0) && (
          <div className="mt-2 p-2 bg-warning-50 border border-warning-200 rounded">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 text-warning-600" />
              <div className="text-xs text-warning-700">
                <strong>Atenção:</strong> {prediction.analysis.riskFactors[0]}
              </div>
            </div>
          </div>
        )}

        {/* Movimento de Odds - Se disponível */}
        {prediction?.liveData?.oddsMovement && prediction.liveData.oddsMovement.trend !== 'stable' && (
          <div className="mt-2 p-2 bg-blue-50 border border-blue-200 rounded">
            <div className="flex items-center justify-between">
              <div className="text-xs text-blue-700">
                <strong>Odds em movimento:</strong> {prediction.liveData.oddsMovement.trend === 'volatile' ? 'Voláteis' : 'Mudança significativa'}
              </div>
              <div className="text-xs text-blue-600">
                Casa: {prediction.liveData.oddsMovement.homeChange > 0 ? '+' : ''}{(prediction.liveData.oddsMovement.homeChange * 100).toFixed(1)}%
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default LivePredictionCard;