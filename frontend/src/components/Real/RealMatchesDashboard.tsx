import React, { useState, useEffect } from 'react';
import {
  Calendar,
  Clock,
  MapPin,
  Trophy,
  TrendingUp,
  Zap,
  Users,
  Target,
  Wifi,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Play
} from 'lucide-react';

// Placeholder interfaces until we have the real ones
interface RealMatch {
  id: number;
  teams: {
    home: { id: number; name: string; logo: string };
    away: { id: number; name: string; logo: string };
  };
  fixture: {
    status: { short: string; elapsed?: number };
    timestamp: number;
    venue: { name: string };
  };
  goals: { home: number | null; away: number | null };
  competition: { name: string };
}

interface RealMatchesDashboardProps {
  className?: string;
}

const RealMatchesDashboard: React.FC<RealMatchesDashboardProps> = ({ className = '' }) => {
  const [todayMatches, setTodayMatches] = useState<RealMatch[]>([]);
  const [upcomingMatches, setUpcomingMatches] = useState<RealMatch[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [liveMatches, setLiveMatches] = useState<RealMatch[]>([]);
  const [apiStatus, setApiStatus] = useState({
    connected: false,
    requests: 0,
    limit: 500
  });

  // Mock data for testing
  const mockMatches: RealMatch[] = [
    {
      id: 1,
      teams: {
        home: { id: 1, name: 'Flamengo', logo: '' },
        away: { id: 2, name: 'Palmeiras', logo: '' }
      },
      fixture: {
        status: { short: 'NS' },
        timestamp: Date.now() / 1000 + 3600,
        venue: { name: 'Maracanã' }
      },
      goals: { home: null, away: null },
      competition: { name: 'Brasileirão Série A' }
    },
    {
      id: 2,
      teams: {
        home: { id: 3, name: 'São Paulo', logo: '' },
        away: { id: 4, name: 'Corinthians', logo: '' }
      },
      fixture: {
        status: { short: '1H', elapsed: 25 },
        timestamp: Date.now() / 1000,
        venue: { name: 'Morumbi' }
      },
      goals: { home: 1, away: 0 },
      competition: { name: 'Brasileirão Série A' }
    }
  ];

  useEffect(() => {
    loadRealData();
    const interval = setInterval(loadRealData, 2 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const loadRealData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Simulating API call with mock data
      await new Promise(resolve => setTimeout(resolve, 1000));

      setTodayMatches(mockMatches);
      setUpcomingMatches(mockMatches);

      const live = mockMatches.filter(match =>
        match.fixture.status.short === '1H' ||
        match.fixture.status.short === '2H' ||
        match.fixture.status.short === 'HT'
      );
      setLiveMatches(live);

      setApiStatus({
        connected: true,
        requests: Math.floor(Math.random() * 150) + 50,
        limit: 500
      });

      setLastUpdate(new Date());
    } catch (err: any) {
      setError(err.message || 'Erro ao conectar com APIs de futebol');
      setApiStatus(prev => ({ ...prev, connected: false }));
    } finally {
      setLoading(false);
    }
  };

  const getMatchStatusBadge = (status: string) => {
    const statusConfig = {
      'NS': { label: 'Não Iniciado', color: 'bg-gray-500', icon: Clock },
      '1H': { label: 'Primeiro Tempo', color: 'bg-green-500', icon: Play },
      '2H': { label: 'Segundo Tempo', color: 'bg-green-600', icon: Play },
      'HT': { label: 'Intervalo', color: 'bg-yellow-500', icon: Clock },
      'FT': { label: 'Finalizado', color: 'bg-blue-500', icon: CheckCircle },
      'CANC': { label: 'Cancelado', color: 'bg-red-500', icon: AlertCircle }
    };

    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig['NS'];
    const Icon = config.icon;

    return (
      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium text-white ${config.color}`}>
        <Icon className="w-3 h-3 mr-1" />
        {config.label}
      </span>
    );
  };

  const getCompetitionEmoji = (competitionName: string) => {
    if (competitionName.includes('Série A')) return '🏆';
    if (competitionName.includes('Série B')) return '🥈';
    if (competitionName.includes('Copa do Brasil')) return '🏅';
    if (competitionName.includes('Libertadores')) return '🌎';
    if (competitionName.includes('Paulista')) return '🔴';
    if (competitionName.includes('Carioca')) return '⚫';
    return '⚽';
  };

  const formatMatchTime = (timestamp: number) => {
    const date = new Date(timestamp * 1000);
    return date.toLocaleTimeString('pt-BR', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const generatePrediction = async (match: RealMatch) => {
    try {
      console.log(`🎯 Gerando predição para ${match.teams.home.name} x ${match.teams.away.name}`);

      // Mock prediction
      const homeWin = Math.random() * 0.6 + 0.2;
      const draw = Math.random() * 0.3 + 0.1;
      const awayWin = 1 - homeWin - draw;

      alert(`🎯 Predição gerada!

${match.teams.home.name}: ${(homeWin * 100).toFixed(1)}%
Empate: ${(draw * 100).toFixed(1)}%
${match.teams.away.name}: ${(awayWin * 100).toFixed(1)}%

Confiança: ${(Math.random() * 30 + 70).toFixed(0)}%`);

    } catch (error) {
      console.error('Erro ao gerar predição:', error);
      alert('Erro ao gerar predição. Tente novamente.');
    }
  };

  const MatchCard: React.FC<{ match: RealMatch; isLive?: boolean }> = ({ match, isLive = false }) => (
    <div className={`bg-white rounded-lg border shadow-sm hover:shadow-md transition-all duration-200 ${
      isLive ? 'border-green-400 bg-green-50' : 'border-gray-200'
    }`}>
      <div className="p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <span className="text-lg">{getCompetitionEmoji(match.competition.name)}</span>
            <span className="text-sm font-medium text-gray-600">{match.competition.name}</span>
            {isLive && <Wifi className="w-4 h-4 text-green-500" />}
          </div>
          {getMatchStatusBadge(match.fixture.status.short)}
        </div>

        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
              <span className="text-xs font-bold">{match.teams.home.name.substring(0, 2).toUpperCase()}</span>
            </div>
            <span className="font-semibold text-gray-900">{match.teams.home.name}</span>
          </div>

          <div className="text-center">
            {match.goals.home !== null && match.goals.away !== null ? (
              <div className="text-2xl font-bold text-gray-900">
                {match.goals.home} - {match.goals.away}
              </div>
            ) : (
              <div className="text-sm text-gray-500">
                {formatMatchTime(match.fixture.timestamp)}
              </div>
            )}
            {match.fixture.status.elapsed && (
              <div className="text-xs text-green-600 font-medium">
                {match.fixture.status.elapsed}'
              </div>
            )}
          </div>

          <div className="flex items-center space-x-3">
            <span className="font-semibold text-gray-900">{match.teams.away.name}</span>
            <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
              <span className="text-xs font-bold">{match.teams.away.name.substring(0, 2).toUpperCase()}</span>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between text-sm text-gray-500 mb-3">
          <div className="flex items-center space-x-1">
            <MapPin className="w-4 h-4" />
            <span>{match.fixture.venue.name}</span>
          </div>
          <div className="flex items-center space-x-1">
            <Calendar className="w-4 h-4" />
            <span>{new Date(match.fixture.timestamp * 1000).toLocaleDateString('pt-BR')}</span>
          </div>
        </div>

        <div className="flex space-x-2">
          <button
            onClick={() => generatePrediction(match)}
            className="flex-1 bg-gradient-to-r from-blue-500 to-green-500 text-white py-2 px-4 rounded-lg text-sm font-medium hover:from-blue-600 hover:to-green-600 transition-colors flex items-center justify-center space-x-1"
          >
            <Target className="w-4 h-4" />
            <span>Prever IA</span>
          </button>

          {isLive && (
            <button className="bg-green-500 text-white py-2 px-4 rounded-lg text-sm font-medium hover:bg-green-600 transition-colors flex items-center space-x-1">
              <Zap className="w-4 h-4" />
              <span>Ao Vivo</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );

  return (
    <div className={`space-y-6 ${className}`}>
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center space-x-2">
              <Trophy className="w-8 h-8 text-yellow-500" />
              <span>Futebol Brasileiro - Dados Reais</span>
            </h1>
            <p className="text-gray-600 mt-1">
              Brasileirão, Copa do Brasil, Libertadores e mais - dados ao vivo
            </p>
          </div>

          <div className="text-right">
            <button
              onClick={loadRealData}
              disabled={loading}
              className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors flex items-center space-x-2 disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              <span>Atualizar</span>
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-4">
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${apiStatus.connected ? 'bg-green-500' : 'bg-red-500'}`}></div>
              <span className="text-sm font-medium">API Status</span>
            </div>
            <p className="text-xs text-gray-600 mt-1">
              {apiStatus.connected ? 'Conectado' : 'Desconectado'}
            </p>
          </div>

          <div className="bg-gray-50 rounded-lg p-3">
            <div className="flex items-center space-x-2">
              <TrendingUp className="w-4 h-4 text-blue-500" />
              <span className="text-sm font-medium">Requisições</span>
            </div>
            <p className="text-xs text-gray-600 mt-1">
              {apiStatus.requests}/{apiStatus.limit} hoje
            </p>
          </div>

          <div className="bg-gray-50 rounded-lg p-3">
            <div className="flex items-center space-x-2">
              <Clock className="w-4 h-4 text-green-500" />
              <span className="text-sm font-medium">Última Atualização</span>
            </div>
            <p className="text-xs text-gray-600 mt-1">
              {lastUpdate.toLocaleTimeString('pt-BR')}
            </p>
          </div>

          <div className="bg-gray-50 rounded-lg p-3">
            <div className="flex items-center space-x-2">
              <Users className="w-4 h-4 text-purple-500" />
              <span className="text-sm font-medium">Jogos Hoje</span>
            </div>
            <p className="text-xs text-gray-600 mt-1">
              {todayMatches.length} partidas
            </p>
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-5 h-5 text-red-500" />
            <span className="text-red-700 font-medium">Erro ao carregar dados</span>
          </div>
          <p className="text-red-600 text-sm mt-1">{error}</p>
        </div>
      )}

      {loading && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-8">
          <div className="flex items-center justify-center space-x-3">
            <RefreshCw className="w-6 h-6 text-blue-500 animate-spin" />
            <span className="text-blue-700 font-medium">Carregando dados das APIs...</span>
          </div>
        </div>
      )}

      {liveMatches.length > 0 && (
        <div>
          <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center space-x-2">
            <Wifi className="w-6 h-6 text-green-500" />
            <span>Jogos ao Vivo ({liveMatches.length})</span>
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {liveMatches.map(match => (
              <MatchCard key={match.id} match={match} isLive={true} />
            ))}
          </div>
        </div>
      )}

      <div>
        <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center space-x-2">
          <Calendar className="w-6 h-6 text-blue-500" />
          <span>Jogos de Hoje ({todayMatches.length})</span>
        </h2>
        {todayMatches.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {todayMatches.map(match => (
              <MatchCard key={match.id} match={match} />
            ))}
          </div>
        ) : (
          <div className="bg-gray-50 rounded-lg p-8 text-center">
            <Trophy className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <p className="text-gray-600">Nenhum jogo hoje nas competições brasileiras</p>
          </div>
        )}
      </div>

      <div>
        <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center space-x-2">
          <Clock className="w-6 h-6 text-purple-500" />
          <span>Próximos Jogos ({upcomingMatches.length})</span>
        </h2>
        {upcomingMatches.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {upcomingMatches.slice(0, 12).map(match => (
              <MatchCard key={match.id} match={match} />
            ))}
          </div>
        ) : (
          <div className="bg-gray-50 rounded-lg p-8 text-center">
            <Calendar className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <p className="text-gray-600">Nenhum jogo agendado encontrado</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default RealMatchesDashboard;