import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../contexts/AuthContext';
import { useTranslation } from '../contexts/I18nContext';
import {
  Wallet,
  TrendingUp,
  Target,
  Award,
  Clock,
  AlertTriangle,
  Settings,
  BarChart3
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';

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
  risk_level: string;
  max_bet_percentage: number;
}

interface Transaction {
  id: number;
  transaction_type: string;
  amount: number;
  balance_before: number;
  balance_after: number;
  description: string | null;
  created_at: string;
}

const UserDashboard: React.FC = () => {
  const { user, token, logout } = useAuth();
  const navigate = useNavigate();
  const { t } = useTranslation();

  const { data: bankroll, isLoading } = useQuery<Bankroll>({
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
  });

  const { data: transactions, isLoading: isLoadingHistory } = useQuery<Transaction[]>({
    queryKey: ['bankroll-history'],
    queryFn: async () => {
      const response = await fetch('http://localhost:8000/api/v1/user/bankroll/history?limit=100', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      if (!response.ok) throw new Error('Failed to fetch history');
      return response.json();
    },
    enabled: !!token,
  });

  // Processar dados para o gráfico de evolução
  const bankrollEvolution = React.useMemo(() => {
    if (!transactions || transactions.length === 0) return [];

    // Reverter ordem para mostrar do mais antigo ao mais recente
    const sorted = [...transactions].reverse();

    // Adicionar ponto inicial (banca inicial)
    const chartData = [
      {
        date: t('dashboard.start'),
        balance: bankroll?.initial_bankroll || 0,
        profit: 0,
        timestamp: new Date(sorted[0]?.created_at || Date.now()).getTime() - 86400000
      }
    ];

    // Adicionar cada transação
    sorted.forEach((tx) => {
      const date = new Date(tx.created_at);
      const formattedDate = date.toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: '2-digit'
      });

      chartData.push({
        date: formattedDate,
        balance: tx.balance_after,
        profit: tx.balance_after - (bankroll?.initial_bankroll || 0),
        timestamp: date.getTime()
      });
    });

    return chartData;
  }, [transactions, bankroll, t]);

  // Calcular estatísticas de performance por tipo de transação
  const performanceStats = React.useMemo(() => {
    if (!transactions) return { wins: 0, losses: 0, winAmount: 0, lossAmount: 0 };

    let wins = 0;
    let losses = 0;
    let winAmount = 0;
    let lossAmount = 0;

    transactions.forEach(tx => {
      if (tx.transaction_type === 'BET_WIN') {
        wins++;
        winAmount += tx.amount;
      } else if (tx.transaction_type === 'BET_LOSS') {
        losses++;
        lossAmount += Math.abs(tx.amount);
      }
    });

    return { wins, losses, winAmount, lossAmount };
  }, [transactions]);

  if (isLoading || isLoadingHistory) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  const riskLevelColors = {
    conservative: 'text-green-400 bg-green-500/10 border-green-500/20',
    moderate: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20',
    aggressive: 'text-red-400 bg-red-500/10 border-red-500/20',
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">
              {t('dashboard.greeting')}, {user?.full_name || user?.username}! 👋
            </h1>
            <p className="text-slate-400">
              {t('dashboard.welcome')}
            </p>
          </div>
          <button
            onClick={logout}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
          >
            {t('dashboard.logout')}
          </button>
        </div>

        {/* Main Bankroll Card */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl shadow-2xl p-8 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <Wallet className="w-8 h-8 text-white" />
              <h2 className="text-xl font-semibold text-white">{t('dashboard.current_bankroll')}</h2>
            </div>
            <div className={`px-3 py-1 rounded-full border ${riskLevelColors[bankroll?.risk_level as keyof typeof riskLevelColors]}`}>
              <span className="text-xs font-medium uppercase">
                {bankroll?.risk_level === 'conservative' && t('dashboard.risk_conservative')}
                {bankroll?.risk_level === 'moderate' && t('dashboard.risk_moderate')}
                {bankroll?.risk_level === 'aggressive' && t('dashboard.risk_aggressive')}
              </span>
            </div>
          </div>

          <div className="flex items-baseline space-x-2 mb-4">
            <span className="text-5xl font-bold text-white">
              R$ {bankroll?.current_bankroll.toFixed(2)}
            </span>
          </div>

          <div className="grid grid-cols-3 gap-4 mt-6">
            <div>
              <p className="text-blue-100 text-sm mb-1">{t('dashboard.initial')}</p>
              <p className="text-white font-semibold">
                R$ {bankroll?.initial_bankroll.toFixed(2)}
              </p>
            </div>
            <div>
              <p className="text-blue-100 text-sm mb-1">{t('dashboard.total_profit')}</p>
              <p className={`font-semibold ${(bankroll?.total_profit ?? 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {(bankroll?.total_profit ?? 0) >= 0 ? '+' : ''}R$ {bankroll?.total_profit.toFixed(2)}
              </p>
            </div>
            <div>
              <p className="text-blue-100 text-sm mb-1">{t('dashboard.roi')}</p>
              <p className={`font-semibold ${(bankroll?.roi ?? 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {(bankroll?.roi ?? 0) >= 0 ? '+' : ''}{bankroll?.roi.toFixed(2)}%
              </p>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="mt-6">
            <button
              onClick={() => navigate('/bankroll')}
              className="w-full bg-white/10 hover:bg-white/20 backdrop-blur-sm text-white font-medium py-3 px-4 rounded-lg transition-all duration-200 flex items-center justify-center space-x-2"
            >
              <Settings className="w-5 h-5" />
              <span>{t('dashboard.configure_bankroll')}</span>
            </button>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
          {/* Total Apostado */}
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <Target className="w-10 h-10 text-blue-400" />
              <span className="text-2xl font-bold text-white">{bankroll?.total_bets}</span>
            </div>
            <h3 className="text-slate-400 text-sm">{t('dashboard.total_bets')}</h3>
            <p className="text-white text-lg font-semibold mt-2">
              R$ {bankroll?.total_staked.toFixed(2)}
            </p>
          </div>

          {/* Win Rate */}
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <Award className="w-10 h-10 text-green-400" />
              <span className="text-2xl font-bold text-green-400">{bankroll?.greens}</span>
            </div>
            <h3 className="text-slate-400 text-sm">{t('dashboard.win_rate')}</h3>
            <p className="text-white text-lg font-semibold mt-2">
              {bankroll?.win_rate.toFixed(1)}%
            </p>
          </div>

          {/* Perdas */}
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <AlertTriangle className="w-10 h-10 text-red-400" />
              <span className="text-2xl font-bold text-red-400">{bankroll?.reds}</span>
            </div>
            <h3 className="text-slate-400 text-sm">{t('dashboard.lost_bets')}</h3>
            <p className="text-white text-lg font-semibold mt-2">
              {bankroll?.total_bets ? ((bankroll.reds / bankroll.total_bets) * 100).toFixed(1) : 0}%
            </p>
          </div>

          {/* Pendentes */}
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <Clock className="w-10 h-10 text-yellow-400" />
              <span className="text-2xl font-bold text-yellow-400">{bankroll?.pending}</span>
            </div>
            <h3 className="text-slate-400 text-sm">{t('dashboard.pending_bets')}</h3>
            <p className="text-white text-lg font-semibold mt-2">
              {t('dashboard.waiting')}
            </p>
          </div>
        </div>

        {/* Bankroll Evolution Chart */}
        {bankrollEvolution.length > 0 && (
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6 mb-6">
            <div className="flex items-center space-x-3 mb-6">
              <BarChart3 className="w-6 h-6 text-blue-400" />
              <h3 className="text-xl font-semibold text-white">{t('dashboard.bankroll_evolution')}</h3>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={bankrollEvolution}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis
                  dataKey="date"
                  stroke="#94a3b8"
                  style={{ fontSize: '12px' }}
                />
                <YAxis
                  stroke="#94a3b8"
                  style={{ fontSize: '12px' }}
                  tickFormatter={(value) => `R$ ${value.toFixed(0)}`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #334155',
                    borderRadius: '8px',
                    color: '#fff'
                  }}
                  formatter={(value: any) => [`R$ ${Number(value).toFixed(2)}`, '']}
                  labelStyle={{ color: '#94a3b8' }}
                />
                <Legend
                  wrapperStyle={{ paddingTop: '20px' }}
                  iconType="line"
                />
                <Line
                  type="monotone"
                  dataKey="balance"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={{ fill: '#3b82f6', r: 4 }}
                  activeDot={{ r: 6 }}
                  name={t('dashboard.balance')}
                />
                <Line
                  type="monotone"
                  dataKey="profit"
                  stroke="#10b981"
                  strokeWidth={2}
                  dot={{ fill: '#10b981', r: 4 }}
                  activeDot={{ r: 6 }}
                  name={t('dashboard.profit')}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Performance Analysis */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Wins vs Losses Chart */}
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6">
            <div className="flex items-center space-x-3 mb-6">
              <TrendingUp className="w-6 h-6 text-green-400" />
              <h3 className="text-xl font-semibold text-white">{t('dashboard.wins_vs_losses')}</h3>
            </div>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart
                data={[
                  {
                    name: t('dashboard.wins'),
                    value: performanceStats.winAmount,
                    count: performanceStats.wins
                  },
                  {
                    name: t('dashboard.losses'),
                    value: performanceStats.lossAmount,
                    count: performanceStats.losses
                  }
                ]}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="name" stroke="#94a3b8" />
                <YAxis
                  stroke="#94a3b8"
                  tickFormatter={(value) => `R$ ${value.toFixed(0)}`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #334155',
                    borderRadius: '8px',
                    color: '#fff'
                  }}
                  formatter={(value: any, _name: any, props: any) => [
                    `R$ ${Number(value).toFixed(2)} (${props.payload.count} ${t('dashboard.bets')})`,
                    ''
                  ]}
                />
                <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                  {[
                    { fill: '#10b981' }, // Green for wins
                    { fill: '#ef4444' }  // Red for losses
                  ].map((entry, index) => (
                    <rect key={`cell-${index}`} {...entry} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Performance Stats */}
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6">
            <div className="flex items-center space-x-3 mb-4">
              <TrendingUp className="w-6 h-6 text-green-400" />
              <h3 className="text-xl font-semibold text-white">{t('dashboard.financial_summary')}</h3>
            </div>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">{t('dashboard.total_staked')}</span>
                <span className="text-white font-semibold">
                  R$ {bankroll?.total_staked.toFixed(2)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">{t('dashboard.total_return')}</span>
                <span className="text-white font-semibold">
                  R$ {((bankroll?.total_staked ?? 0) + (bankroll?.total_profit ?? 0)).toFixed(2)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">{t('dashboard.net_profit')}</span>
                <span className={`font-semibold ${(bankroll?.total_profit ?? 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {(bankroll?.total_profit ?? 0) >= 0 ? '+' : ''}R$ {bankroll?.total_profit.toFixed(2)}
                </span>
              </div>
              <div className="border-t border-slate-700 pt-4 mt-4">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">{t('dashboard.avg_win')}</span>
                  <span className="text-green-400 font-semibold">
                    R$ {performanceStats.wins > 0 ? (performanceStats.winAmount / performanceStats.wins).toFixed(2) : '0.00'}
                  </span>
                </div>
                <div className="flex items-center justify-between mt-2">
                  <span className="text-slate-400">{t('dashboard.avg_loss')}</span>
                  <span className="text-red-400 font-semibold">
                    R$ {performanceStats.losses > 0 ? (performanceStats.lossAmount / performanceStats.losses).toFixed(2) : '0.00'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Risk Management */}
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6">
            <div className="flex items-center space-x-3 mb-4">
              <Target className="w-6 h-6 text-purple-400" />
              <h3 className="text-xl font-semibold text-white">{t('dashboard.risk_management')}</h3>
            </div>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">{t('dashboard.max_stake')}</span>
                <span className="text-white font-semibold">
                  {bankroll?.max_bet_percentage}%
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">{t('dashboard.max_value')}</span>
                <span className="text-white font-semibold">
                  R$ {((bankroll?.current_bankroll ?? 0) * ((bankroll?.max_bet_percentage ?? 0) / 100)).toFixed(2)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">{t('dashboard.risk_level')}</span>
                <span className="text-white font-semibold uppercase">
                  {bankroll?.risk_level}
                </span>
              </div>
            </div>
            <button
              onClick={() => navigate('/user/bankroll')}
              className="w-full mt-4 bg-purple-600 hover:bg-purple-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
            >
              {t('dashboard.configure')}
            </button>
          </div>
        </div>

        {/* Quick Links */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => navigate('/user/tickets')}
            className="bg-slate-800/50 hover:bg-slate-700/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6 text-left transition-all"
          >
            <h4 className="text-white font-semibold mb-2">{t('dashboard.my_tickets')}</h4>
            <p className="text-slate-400 text-sm">{t('dashboard.view_history')}</p>
          </button>
          <button
            onClick={() => navigate('/user/bankroll')}
            className="bg-slate-800/50 hover:bg-slate-700/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6 text-left transition-all"
          >
            <h4 className="text-white font-semibold mb-2">{t('dashboard.manage_bankroll')}</h4>
            <p className="text-slate-400 text-sm">{t('dashboard.deposits_withdrawals')}</p>
          </button>
          <button
            onClick={() => navigate('/predictions')}
            className="bg-slate-800/50 hover:bg-slate-700/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6 text-left transition-all"
          >
            <h4 className="text-white font-semibold mb-2">{t('dashboard.view_predictions')}</h4>
            <p className="text-slate-400 text-sm">{t('dashboard.find_best_bets')}</p>
          </button>
        </div>
      </div>
    </div>
  );
};

export default UserDashboard;
