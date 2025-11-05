import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import {
  Wallet,
  Settings as SettingsIcon,
  TrendingUp,
  Clock,
  DollarSign,
  AlertCircle,
  CheckCircle,
  X,
  Edit3
} from 'lucide-react';
import { useTranslation } from '../contexts/I18nContext';

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
  use_kelly_criterion: boolean;
  profit_goal: number | null;
  stop_loss: number | null;
}

interface Transaction {
  id: number;
  transaction_type: string;
  amount: number;
  balance_before: number;
  balance_after: number;
  description: string;
  created_at: string;
}

const UserBankroll: React.FC = () => {
  const { t } = useTranslation();
  const { token } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [showEditModal, setShowEditModal] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);

  const [initialBankroll, setInitialBankroll] = useState('');

  const [settings, setSettings] = useState({
    max_bet_percentage: 5,
    use_kelly_criterion: false,
    risk_level: 'moderate',
    profit_goal: '',
    stop_loss: '',
  });

  // Fetch bankroll
  const { data: bankroll, isLoading, error: bankrollError } = useQuery<Bankroll>({
    queryKey: ['bankroll'],
    queryFn: async () => {
      const response = await fetch('http://localhost:8000/api/v1/user/bankroll', {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (response.status === 401) {
        // Token expirado - fazer logout e redirecionar
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        navigate('/login');
        throw new Error(t('bankroll.session_expired'));
      }
      if (!response.ok) throw new Error('Failed to fetch');
      const data = await response.json();

      // Sincronizar settings
      setSettings({
        max_bet_percentage: data.max_bet_percentage || 5,
        use_kelly_criterion: data.use_kelly_criterion || false,
        risk_level: data.risk_level || 'moderate',
        profit_goal: data.profit_goal || '',
        stop_loss: data.stop_loss || '',
      });

      return data;
    },
    enabled: !!token,
  });

  // Fetch history
  const { data: history } = useQuery<Transaction[]>({
    queryKey: ['bankroll-history'],
    queryFn: async () => {
      const response = await fetch('http://localhost:8000/api/v1/user/bankroll/history?limit=50', {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (!response.ok) throw new Error('Failed to fetch');
      return response.json();
    },
    enabled: !!token,
  });

  const settingsMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await fetch('http://localhost:8000/api/v1/user/bankroll/settings', {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
      if (!response.ok) throw new Error('Failed to update settings');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bankroll'] });
      setShowSettingsModal(false);
    },
  });

  const updateInitialBankrollMutation = useMutation({
    mutationFn: async (amount: number) => {
      if (!token) {
        throw new Error('Você precisa estar autenticado. Por favor, faça login novamente.');
      }

      const response = await fetch('http://localhost:8000/api/v1/user/bankroll/reset', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ initial_bankroll: amount }),
      });

      if (!response.ok) {
        if (response.status === 401) {
          // Token expirado - fazer logout e redirecionar
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          setTimeout(() => navigate('/login'), 1500);
          throw new Error('Sessão expirada. Redirecionando para login...');
        }
        const errorData = await response.json().catch(() => ({ detail: 'Erro desconhecido' }));
        throw new Error(errorData.detail || 'Failed to update initial bankroll');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bankroll'] });
      queryClient.invalidateQueries({ queryKey: ['bankroll-history'] });
      setShowEditModal(false);
      setInitialBankroll('');
      alert(t('bankroll.success_reset'));
    },
    onError: (error: Error) => {
      console.error(t('bankroll.error_reset'), error);
      alert(`${t('bankroll.error_reset')}: ${error.message}`);
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'conservative': return 'text-green-400 bg-green-500/10';
      case 'moderate': return 'text-yellow-400 bg-yellow-500/10';
      case 'aggressive': return 'text-red-400 bg-red-500/10';
      default: return 'text-gray-400 bg-gray-500/10';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">{t('bankroll.title')}</h1>
            <p className="text-slate-400">{t('bankroll.subtitle')}</p>
          </div>
          <button
            onClick={() => navigate('/dashboard')}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
          >
            {t('bankroll.back')}
          </button>
        </div>

        {/* Main Bankroll Card */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl shadow-2xl p-8 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <Wallet className="w-8 h-8 text-white" />
              <h2 className="text-xl font-semibold text-white">{t('bankroll.current')}</h2>
            </div>
            <div className={`px-3 py-1 rounded-full ${getRiskColor(bankroll?.risk_level || 'moderate')}`}>
              <span className="text-xs font-medium uppercase">
                {bankroll?.risk_level === 'conservative' && t('bankroll.conservative')}
                {bankroll?.risk_level === 'moderate' && t('bankroll.moderate')}
                {bankroll?.risk_level === 'aggressive' && t('bankroll.aggressive')}
              </span>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <div className="text-5xl font-bold text-white mb-2">
                R$ {bankroll?.current_bankroll.toFixed(2)}
              </div>
              <div className="grid grid-cols-3 gap-6 mt-4">
                <div>
                  <p className="text-blue-200 text-sm">{t('bankroll.initial')}</p>
                  <p className="text-white font-semibold">R$ {bankroll?.initial_bankroll.toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-blue-200 text-sm">{t('bankroll.profit')}</p>
                  <p className={`font-semibold ${(bankroll?.total_profit || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    R$ {bankroll?.total_profit.toFixed(2)}
                  </p>
                </div>
                <div>
                  <p className="text-blue-200 text-sm">ROI</p>
                  <p className={`font-semibold ${(bankroll?.roi || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {bankroll?.roi.toFixed(2)}%
                  </p>
                </div>
              </div>
            </div>

            <button
              onClick={() => {
                setInitialBankroll(bankroll?.initial_bankroll.toString() || '');
                setShowEditModal(true);
              }}
              className="flex flex-col items-center gap-2 px-6 py-3 bg-white/10 hover:bg-white/20 text-white rounded-lg transition-colors"
            >
              <Edit3 className="w-6 h-6" />
              <span className="text-sm">{t('bankroll.setup')}</span>
            </button>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-sm">{t('bankroll.total_staked')}</p>
                <p className="text-2xl font-bold text-white">R$ {bankroll?.total_staked.toFixed(2)}</p>
              </div>
              <DollarSign className="w-8 h-8 text-blue-400" />
            </div>
          </div>

          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-sm">{t('bankroll.win_rate')}</p>
                <p className="text-2xl font-bold text-white">{bankroll?.win_rate.toFixed(1)}%</p>
              </div>
              <TrendingUp className="w-8 h-8 text-green-400" />
            </div>
          </div>

          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-sm">{t('bankroll.total_bets')}</p>
                <p className="text-2xl font-bold text-white">{bankroll?.total_bets}</p>
              </div>
              <CheckCircle className="w-8 h-8 text-purple-400" />
            </div>
          </div>

          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-sm">{t('bankroll.pending')}</p>
                <p className="text-2xl font-bold text-white">{bankroll?.pending}</p>
              </div>
              <Clock className="w-8 h-8 text-yellow-400" />
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 mb-6">
          <h3 className="text-lg font-semibold text-white mb-4">{t('bankroll.settings_title')}</h3>
          <div className="flex flex-wrap gap-4">
            <button
              onClick={() => setShowSettingsModal(true)}
              className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
            >
              <SettingsIcon className="w-5 h-5" />
              {t('bankroll.configure_limits')}
            </button>
          </div>
        </div>

        {/* Transaction History */}
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h3 className="text-lg font-semibold text-white mb-4">{t('bankroll.transaction_history')}</h3>
          <div className="space-y-3">
            {history && history.length > 0 ? (
              history.map((transaction) => (
                <div
                  key={transaction.id}
                  className="flex items-center justify-between p-4 bg-slate-700/50 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${
                      transaction.transaction_type === 'BET_WIN' ? 'bg-green-500' :
                      transaction.transaction_type === 'BET_LOSS' ? 'bg-red-500' :
                      'bg-yellow-500'
                    }`} />
                    <div>
                      <p className="text-white font-medium">{transaction.description}</p>
                      <p className="text-slate-400 text-sm">
                        {new Date(transaction.created_at).toLocaleDateString('pt-BR')} às{' '}
                        {new Date(transaction.created_at).toLocaleTimeString('pt-BR')}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className={`font-semibold ${
                      transaction.amount >= 0 ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {transaction.amount >= 0 ? '+' : ''}R$ {Math.abs(transaction.amount).toFixed(2)}
                    </p>
                    <p className="text-slate-400 text-sm">
                      {t('bankroll.balance')}: R$ {transaction.balance_after.toFixed(2)}
                    </p>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-slate-400">
                {t('bankroll.no_transactions')}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Edit Initial Bankroll Modal */}
      {showEditModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-white">{t('bankroll.modal_setup_title')}</h3>
              <button onClick={() => setShowEditModal(false)} className="text-slate-400 hover:text-white">
                <X className="w-6 h-6" />
              </button>
            </div>

            <div className="mb-4">
              <label className="block text-slate-300 mb-2">{t('bankroll.initial_value_label')}</label>
              <input
                type="number"
                value={initialBankroll}
                onChange={(e) => setInitialBankroll(e.target.value)}
                className="w-full p-3 bg-slate-700 border border-slate-600 rounded-lg text-white"
                placeholder={t('bankroll.initial_value_placeholder')}
              />
              <p className="text-sm text-slate-400 mt-2">
                <AlertCircle className="w-4 h-4 inline mr-1" />
                {t('bankroll.reset_warning')}
              </p>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setShowEditModal(false)}
                className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
              >
                {t('bankroll.cancel')}
              </button>
              <button
                onClick={() => {
                  console.log('Token:', token ? 'existe' : 'null', token?.substring(0, 20) + '...');
                  const amount = parseFloat(initialBankroll);
                  if (amount > 0) {
                    updateInitialBankrollMutation.mutate(amount);
                  } else {
                    alert(t('bankroll.invalid_value'));
                  }
                }}
                disabled={updateInitialBankrollMutation.isPending || !initialBankroll || parseFloat(initialBankroll) <= 0}
                className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {updateInitialBankrollMutation.isPending ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>{t('bankroll.saving')}</span>
                  </>
                ) : (
                  t('bankroll.confirm')
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Settings Modal */}
      {showSettingsModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 overflow-y-auto">
          <div className="bg-slate-800 rounded-lg p-6 max-w-md w-full mx-4 my-8">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-white">{t('bankroll.settings_modal_title')}</h3>
              <button onClick={() => setShowSettingsModal(false)} className="text-slate-400 hover:text-white">
                <X className="w-6 h-6" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-slate-300 mb-2">{t('bankroll.max_bet_label')}</label>
                <input
                  type="range"
                  min="1"
                  max="20"
                  value={settings.max_bet_percentage}
                  onChange={(e) => setSettings({ ...settings, max_bet_percentage: parseInt(e.target.value) })}
                  className="w-full"
                />
                <p className="text-white text-center mt-2">{settings.max_bet_percentage}%</p>
              </div>

              <div>
                <label className="block text-slate-300 mb-2">{t('bankroll.risk_level_label')}</label>
                <select
                  value={settings.risk_level}
                  onChange={(e) => setSettings({ ...settings, risk_level: e.target.value })}
                  className="w-full p-3 bg-slate-700 border border-slate-600 rounded-lg text-white"
                >
                  <option value="conservative">{t('bankroll.conservative')}</option>
                  <option value="moderate">{t('bankroll.moderate')}</option>
                  <option value="aggressive">{t('bankroll.aggressive')}</option>
                </select>
              </div>

              <div className="flex items-center justify-between p-3 bg-slate-700 rounded-lg">
                <span className="text-slate-300">{t('bankroll.kelly_criterion')}</span>
                <button
                  onClick={() => setSettings({ ...settings, use_kelly_criterion: !settings.use_kelly_criterion })}
                  className={`w-12 h-6 rounded-full transition-colors ${
                    settings.use_kelly_criterion ? 'bg-blue-600' : 'bg-slate-600'
                  }`}
                >
                  <div className={`w-5 h-5 bg-white rounded-full transform transition-transform ${
                    settings.use_kelly_criterion ? 'translate-x-6' : 'translate-x-1'
                  }`} />
                </button>
              </div>

              <div>
                <label className="block text-slate-300 mb-2">{t('bankroll.profit_goal_label')}</label>
                <input
                  type="number"
                  value={settings.profit_goal}
                  onChange={(e) => setSettings({ ...settings, profit_goal: e.target.value })}
                  className="w-full p-3 bg-slate-700 border border-slate-600 rounded-lg text-white"
                  placeholder={t('bankroll.profit_goal_placeholder')}
                />
              </div>

              <div>
                <label className="block text-slate-300 mb-2">{t('bankroll.stop_loss_label')}</label>
                <input
                  type="number"
                  value={settings.stop_loss}
                  onChange={(e) => setSettings({ ...settings, stop_loss: e.target.value })}
                  className="w-full p-3 bg-slate-700 border border-slate-600 rounded-lg text-white"
                  placeholder={t('bankroll.stop_loss_placeholder')}
                />
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowSettingsModal(false)}
                className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
              >
                {t('bankroll.cancel')}
              </button>
              <button
                onClick={() => {
                  settingsMutation.mutate({
                    max_bet_percentage: settings.max_bet_percentage,
                    use_kelly_criterion: settings.use_kelly_criterion,
                    risk_level: settings.risk_level,
                    profit_goal: settings.profit_goal ? parseFloat(settings.profit_goal) : null,
                    stop_loss: settings.stop_loss ? parseFloat(settings.stop_loss) : null,
                  });
                }}
                className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
              >
                {t('bankroll.save')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserBankroll;
