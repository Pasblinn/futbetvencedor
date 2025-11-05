import React from 'react';
import {
  TrendingUp,
  TrendingDown,
  CheckCircle,
  XCircle,
  BarChart3,
  Clock,
  RefreshCw,
  Target,
  Wallet
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../contexts/AuthContext';

interface Bankroll {
  id: number;
  current_bankroll: number;
  initial_bankroll: number;
  total_deposited: number;
  total_withdrawn: number;
  total_staked: number;
  total_profit: number;
  roi: number;
  win_rate: number;
  total_bets: number;
  greens: number;
  reds: number;
  pending: number;
}

const GreenRedDashboard: React.FC = () => {
  const { token } = useAuth();

  const { data: bankroll, isLoading, error, refetch } = useQuery<Bankroll>({
    queryKey: ['bankroll'],
    queryFn: async () => {
      const response = await fetch('http://localhost:8000/api/v1/user/bankroll', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      if (!response.ok) throw new Error('Failed to fetch bankroll');
      return response.json();
    },
    enabled: !!token,
    refetchInterval: 60000, // Atualizar a cada 60 segundos
  });

  const stats = bankroll ? {
    total_analyzed: bankroll.total_bets,
    greens: bankroll.greens,
    reds: bankroll.reds,
    pending: bankroll.pending,
    accuracy: bankroll.win_rate,
    green_percentage: bankroll.total_bets > 0 ? (bankroll.greens / bankroll.total_bets) * 100 : 0,
    red_percentage: bankroll.total_bets > 0 ? (bankroll.reds / bankroll.total_bets) * 100 : 0,
    total_profit_loss: bankroll.total_profit,
    roi: bankroll.roi,
  } : null;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 animate-spin mx-auto mb-4 text-blue-500" />
          <p className="text-lg text-gray-600 dark:text-gray-300">Carregando suas estatísticas...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
            🟢🔴 Meu Dashboard GREEN/RED
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Análise da sua performance de apostas
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <RefreshCw className="w-5 h-5" />
          Atualizar
        </button>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
          <p className="text-red-700 dark:text-red-400">Erro ao carregar estatísticas. Por favor, tente novamente.</p>
        </div>
      )}

      {/* Main Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {/* Total Apostas */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center gap-3 mb-3">
            <BarChart3 className="w-6 h-6 text-blue-600" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Total de Apostas</h3>
          </div>
          <p className="text-4xl font-bold text-gray-900 dark:text-white">{stats?.total_analyzed || 0}</p>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">Bilhetes criados</p>
        </div>

        {/* GREEN */}
        <div className="bg-green-50 dark:bg-green-900/20 rounded-lg shadow p-6 border-2 border-green-200 dark:border-green-800">
          <div className="flex items-center gap-3 mb-3">
            <CheckCircle className="w-6 h-6 text-green-600" />
            <h3 className="text-lg font-semibold text-green-900 dark:text-green-300">GREEN (Acertos)</h3>
          </div>
          <p className="text-4xl font-bold text-green-600">{stats?.greens || 0}</p>
          <p className="text-sm text-green-700 dark:text-green-400 mt-2">
            {stats?.green_percentage.toFixed(1)}% do total
          </p>
        </div>

        {/* RED */}
        <div className="bg-red-50 dark:bg-red-900/20 rounded-lg shadow p-6 border-2 border-red-200 dark:border-red-800">
          <div className="flex items-center gap-3 mb-3">
            <XCircle className="w-6 h-6 text-red-600" />
            <h3 className="text-lg font-semibold text-red-900 dark:text-red-300">RED (Erros)</h3>
          </div>
          <p className="text-4xl font-bold text-red-600">{stats?.reds || 0}</p>
          <p className="text-sm text-red-700 dark:text-red-400 mt-2">
            {stats?.red_percentage.toFixed(1)}% do total
          </p>
        </div>

        {/* Pendentes */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center gap-3 mb-3">
            <Clock className="w-6 h-6 text-gray-600" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Pendentes</h3>
          </div>
          <p className="text-4xl font-bold text-gray-900 dark:text-white">{stats?.pending || 0}</p>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">Aguardando jogos</p>
        </div>
      </div>

      {/* Performance Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Acurácia */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white flex items-center gap-2 mb-6">
            <Target className="w-6 h-6 text-blue-600" />
            Minha Taxa de Acerto
          </h3>
          <div className="text-center my-6">
            <p className="text-6xl font-bold text-blue-600">{stats?.accuracy.toFixed(1)}%</p>
            <p className="text-gray-600 dark:text-gray-400 mt-2">Win Rate das suas apostas</p>
          </div>
          <div className="space-y-4 mt-6">
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-700 dark:text-gray-300">GREEN</span>
                <span className="font-semibold text-green-600">{stats?.green_percentage.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                <div
                  className="bg-green-500 h-3 rounded-full transition-all duration-300"
                  style={{ width: `${stats?.green_percentage || 0}%` }}
                />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-700 dark:text-gray-300">RED</span>
                <span className="font-semibold text-red-600">{stats?.red_percentage.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                <div
                  className="bg-red-500 h-3 rounded-full transition-all duration-300"
                  style={{ width: `${stats?.red_percentage || 0}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* ROI */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white flex items-center gap-2 mb-6">
            💰 Retorno sobre Investimento
          </h3>
          <div className="text-center my-6">
            <div className="flex items-center justify-center gap-3">
              {(stats?.roi || 0) >= 0 ? (
                <TrendingUp className="w-12 h-12 text-green-500" />
              ) : (
                <TrendingDown className="w-12 h-12 text-red-500" />
              )}
              <p className={`text-6xl font-bold ${(stats?.roi || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {stats?.roi.toFixed(2)}%
              </p>
            </div>
            <p className="text-gray-600 dark:text-gray-400 mt-2">ROI baseado em stake de R$ 100</p>
          </div>
          <hr className="border-gray-200 dark:border-gray-700 my-4" />
          <div className="flex justify-between items-center">
            <span className="text-gray-700 dark:text-gray-300">Lucro/Prejuízo Total:</span>
            <span className={`text-xl font-bold ${(stats?.total_profit_loss || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              R$ {stats?.total_profit_loss.toFixed(2)}
            </span>
          </div>
        </div>

        {/* Informações Adicionais */}
        <div className="lg:col-span-2 bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            ℹ️ Informações do Sistema
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
              <p className="text-blue-900 dark:text-blue-300"><strong>Análise Automática:</strong> Executa a cada 30 minutos</p>
            </div>
            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
              <p className="text-blue-900 dark:text-blue-300"><strong>Stake Padrão:</strong> R$ 100 por aposta</p>
            </div>
            <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
              <p className="text-green-900 dark:text-green-300"><strong>🟢 GREEN:</strong> Prediction correta (acertou o resultado)</p>
            </div>
            <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4">
              <p className="text-red-900 dark:text-red-300"><strong>🔴 RED:</strong> Prediction incorreta (errou o resultado)</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GreenRedDashboard;
