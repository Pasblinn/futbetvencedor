import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from '../contexts/I18nContext';
import {
  Ticket,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  TrendingUp,
  Target,
  Calendar,
  DollarSign,
  Eye,
  Trash2
} from 'lucide-react';

interface TicketSelection {
  id: number;
  match_id: number;
  market: string;
  outcome: string;
  odd: number;
  status: string;
  match_info?: {
    home_team: string;
    away_team: string;
    league: string;
    match_date: string;
    status: string;
  };
}

interface Ticket {
  id: number;
  ticket_type: string;
  source: string;
  stake: number;
  total_odds: number;
  potential_return: number;
  actual_return: number;
  profit_loss: number;
  status: string;
  notes?: string;
  confidence_level?: string;
  selections_count: number;
  selections_won: number;
  selections_lost: number;
  selections_pending: number;
  created_at: string;
  updated_at?: string;
  settled_at?: string;
  selections?: TicketSelection[];
}

interface TicketStatistics {
  total_tickets: number;
  pending: number;
  won: number;
  lost: number;
  cancelled: number;
  win_rate: number;
  avg_odds: number;
  avg_stake: number;
  total_staked: number;
  total_return: number;
  total_profit: number;
  roi: number;
  by_type: any;
  best_ticket: Ticket | null;
  worst_ticket: Ticket | null;
  biggest_win: number | null;
  biggest_loss: number | null;
}

const UserTickets: React.FC = () => {
  const { t } = useTranslation();
  const { token } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);

  // Fetch tickets
  const { data: tickets, isLoading } = useQuery<Ticket[]>({
    queryKey: ['user-tickets', filterStatus],
    queryFn: async () => {
      let url = 'http://localhost:8000/api/v1/user/tickets?limit=50';
      if (filterStatus !== 'all') {
        url += `&status=${filterStatus}`;
      }
      const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (!response.ok) throw new Error('Failed to fetch');
      return response.json();
    },
    enabled: !!token,
  });

  // Fetch statistics
  const { data: stats } = useQuery<TicketStatistics>({
    queryKey: ['user-statistics'],
    queryFn: async () => {
      const response = await fetch('http://localhost:8000/api/v1/user/statistics', {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (!response.ok) throw new Error('Failed to fetch');
      return response.json();
    },
    enabled: !!token,
  });

  // Cancel ticket mutation
  const cancelMutation = useMutation({
    mutationFn: async (ticketId: number) => {
      const response = await fetch(`http://localhost:8000/api/v1/user/tickets/${ticketId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to cancel');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-tickets'] });
      queryClient.invalidateQueries({ queryKey: ['user-statistics'] });
      queryClient.invalidateQueries({ queryKey: ['bankroll'] });
      setShowDetailsModal(false);
    },
  });

  const handleViewDetails = async (ticketId: number) => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/user/tickets/${ticketId}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (!response.ok) throw new Error('Failed to fetch');
      const ticket = await response.json();
      setSelectedTicket(ticket);
      setShowDetailsModal(true);
    } catch (error) {
      console.error('Error fetching ticket details:', error);
    }
  };

  const handleCancelTicket = (ticketId: number) => {
    if (window.confirm(t('tickets.cancel_confirm'))) {
      cancelMutation.mutate(ticketId);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  const statusColors: any = {
    pending: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
    won: 'bg-green-500/10 text-green-400 border-green-500/20',
    lost: 'bg-red-500/10 text-red-400 border-red-500/20',
    cancelled: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
  };

  const statusIcons: any = {
    pending: Clock,
    won: CheckCircle,
    lost: XCircle,
    cancelled: AlertCircle,
  };

  const statusLabels: any = {
    pending: t('tickets.status_pending'),
    won: t('tickets.status_won'),
    lost: t('tickets.status_lost'),
    cancelled: t('tickets.status_cancelled'),
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <button
              onClick={() => navigate('/user/dashboard')}
              className="text-slate-400 hover:text-white mb-2 flex items-center space-x-2"
            >
              <span>← {t('tickets.back')}</span>
            </button>
            <h1 className="text-3xl font-bold text-white mb-2">
              {t('tickets.title')} 🎫
            </h1>
            <p className="text-slate-400">
              {t('tickets.subtitle')}
            </p>
          </div>
          <button
            onClick={() => navigate('/predictions')}
            className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-6 rounded-lg transition-colors flex items-center space-x-2"
          >
            <Target className="w-5 h-5" />
            <span>{t('tickets.new_bet')}</span>
          </button>
        </div>

        {/* Statistics */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
            <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6">
              <div className="flex items-center justify-between mb-4">
                <Ticket className="w-10 h-10 text-blue-400" />
                <span className="text-3xl font-bold text-white">{stats.total_tickets}</span>
              </div>
              <h3 className="text-slate-400 text-sm">{t('tickets.total_tickets')}</h3>
              <p className="text-white text-lg font-semibold mt-2">
                R$ {stats.total_staked.toFixed(2)}
              </p>
            </div>

            <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6">
              <div className="flex items-center justify-between mb-4">
                <CheckCircle className="w-10 h-10 text-green-400" />
                <span className="text-3xl font-bold text-green-400">{stats.won}</span>
              </div>
              <h3 className="text-slate-400 text-sm">{t('tickets.win_rate')}</h3>
              <p className="text-white text-lg font-semibold mt-2">
                {stats.win_rate.toFixed(1)}%
              </p>
            </div>

            <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6">
              <div className="flex items-center justify-between mb-4">
                <TrendingUp className="w-10 h-10 text-purple-400" />
                <span className={`text-3xl font-bold ${stats.total_profit >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {stats.total_profit >= 0 ? '+' : ''}R$ {stats.total_profit.toFixed(2)}
                </span>
              </div>
              <h3 className="text-slate-400 text-sm">{t('tickets.total_profit')}</h3>
              <p className={`text-lg font-semibold mt-2 ${stats.roi >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                ROI: {stats.roi.toFixed(2)}%
              </p>
            </div>

            <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6">
              <div className="flex items-center justify-between mb-4">
                <Clock className="w-10 h-10 text-yellow-400" />
                <span className="text-3xl font-bold text-yellow-400">{stats.pending}</span>
              </div>
              <h3 className="text-slate-400 text-sm">{t('tickets.pending')}</h3>
              <p className="text-white text-lg font-semibold mt-2">
                {t('tickets.waiting')}
              </p>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-4 mb-6">
          <div className="flex items-center space-x-2 overflow-x-auto">
            <button
              onClick={() => setFilterStatus('all')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors whitespace-nowrap ${
                filterStatus === 'all'
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              {t('tickets.filter_all')}
            </button>
            <button
              onClick={() => setFilterStatus('pending')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors whitespace-nowrap ${
                filterStatus === 'pending'
                  ? 'bg-yellow-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              {t('tickets.filter_pending')}
            </button>
            <button
              onClick={() => setFilterStatus('won')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors whitespace-nowrap ${
                filterStatus === 'won'
                  ? 'bg-green-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              {t('tickets.filter_won')}
            </button>
            <button
              onClick={() => setFilterStatus('lost')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors whitespace-nowrap ${
                filterStatus === 'lost'
                  ? 'bg-red-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              {t('tickets.filter_lost')}
            </button>
          </div>
        </div>

        {/* Tickets List */}
        <div className="space-y-4">
          {tickets?.map((ticket) => {
            const StatusIcon = statusIcons[ticket.status];
            return (
              <div
                key={ticket.id}
                className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6 hover:border-slate-600 transition-colors"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center space-x-4">
                    <div className={`px-3 py-1 rounded-full border ${statusColors[ticket.status]}`}>
                      <div className="flex items-center space-x-2">
                        <StatusIcon className="w-4 h-4" />
                        <span className="text-sm font-medium">{statusLabels[ticket.status]}</span>
                      </div>
                    </div>
                    <div>
                      <h3 className="text-white font-semibold">
                        {t('tickets.ticket_number')}{ticket.id} - {ticket.ticket_type === 'single' ? t('tickets.type_single') : t('tickets.type_multiple')}
                      </h3>
                      <p className="text-slate-400 text-sm">
                        {new Date(ticket.created_at).toLocaleString('pt-BR')}
                      </p>
                      {/* Resumo rápido das apostas */}
                      {ticket.selections && ticket.selections.length > 0 && (
                        <div className="mt-2 space-y-1">
                          {ticket.selections.slice(0, 2).map((sel, idx) => (
                            <div key={idx} className="text-sm">
                              <span className="text-blue-400">⚽ {sel.match_info?.home_team || 'Time'} vs {sel.match_info?.away_team || 'Time'}</span>
                              <span className="text-slate-500 mx-2">•</span>
                              <span className="text-white">{sel.market}: {sel.outcome}</span>
                              <span className="text-slate-500 mx-2">•</span>
                              <span className="text-green-400 font-medium">{sel.odd.toFixed(2)}</span>
                            </div>
                          ))}
                          {ticket.selections.length > 2 && (
                            <p className="text-slate-500 text-xs">
                              +{ticket.selections.length - 2} {t('tickets.more')} {ticket.selections.length - 2 === 1 ? t('tickets.game') : t('tickets.games')}
                            </p>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-slate-400 text-sm">{t('tickets.total_odds')}</p>
                    <p className="text-white text-2xl font-bold">{ticket.total_odds.toFixed(2)}</p>
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-4">
                  <div>
                    <p className="text-slate-400 text-sm">{t('tickets.stake')}</p>
                    <p className="text-white font-semibold">R$ {ticket.stake.toFixed(2)}</p>
                  </div>
                  <div>
                    <p className="text-slate-400 text-sm">{t('tickets.potential_return')}</p>
                    <p className="text-white font-semibold">R$ {ticket.potential_return.toFixed(2)}</p>
                  </div>
                  <div>
                    <p className="text-slate-400 text-sm">{t('tickets.selections')}</p>
                    <p className="text-white font-semibold">{ticket.selections_count}</p>
                  </div>
                  <div>
                    <p className="text-slate-400 text-sm">{t('tickets.green_red')}</p>
                    <p className="text-white font-semibold">
                      <span className="text-green-400">{ticket.selections_won}</span>
                      {' / '}
                      <span className="text-red-400">{ticket.selections_lost}</span>
                    </p>
                  </div>
                  <div>
                    <p className="text-slate-400 text-sm">{t('tickets.result')}</p>
                    <p className={`font-semibold ${
                      ticket.status === 'won' ? 'text-green-400' :
                      ticket.status === 'lost' ? 'text-red-400' :
                      'text-yellow-400'
                    }`}>
                      {ticket.status === 'won' && `+R$ ${ticket.profit_loss.toFixed(2)}`}
                      {ticket.status === 'lost' && `-R$ ${Math.abs(ticket.profit_loss).toFixed(2)}`}
                      {ticket.status === 'pending' && t('tickets.status_pending')}
                      {ticket.status === 'cancelled' && t('tickets.status_cancelled')}
                    </p>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-4 border-t border-slate-700">
                  <button
                    onClick={() => handleViewDetails(ticket.id)}
                    className="flex items-center space-x-2 text-blue-400 hover:text-blue-300 transition-colors"
                  >
                    <Eye className="w-4 h-4" />
                    <span>{t('tickets.view_details')}</span>
                  </button>
                  {ticket.status === 'pending' && (
                    <button
                      onClick={() => handleCancelTicket(ticket.id)}
                      disabled={cancelMutation.isPending}
                      className="flex items-center space-x-2 text-red-400 hover:text-red-300 transition-colors disabled:opacity-50"
                    >
                      <Trash2 className="w-4 h-4" />
                      <span>{t('tickets.cancel')}</span>
                    </button>
                  )}
                </div>
              </div>
            );
          })}

          {tickets?.length === 0 && (
            <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-12 text-center">
              <Ticket className="w-16 h-16 text-slate-600 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-white mb-2">{t('tickets.no_tickets_found')}</h3>
              <p className="text-slate-400 mb-6">
                {filterStatus === 'all'
                  ? t('tickets.no_bets_yet')
                  : `${t('tickets.no_tickets_status')} "${statusLabels[filterStatus]}"`}
              </p>
              <button
                onClick={() => navigate('/predictions')}
                className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-6 rounded-lg transition-colors inline-flex items-center space-x-2"
              >
                <Target className="w-5 h-5" />
                <span>{t('tickets.make_bet')}</span>
              </button>
            </div>
          )}
        </div>

        {/* Details Modal */}
        {showDetailsModal && selectedTicket && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 overflow-y-auto">
            <div className="bg-slate-800 rounded-2xl border border-slate-700 p-8 max-w-3xl w-full my-8">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-2xl font-bold text-white">
                  {t('tickets.details_title')}{selectedTicket.id}
                </h3>
                <button
                  onClick={() => setShowDetailsModal(false)}
                  className="text-slate-400 hover:text-white"
                >
                  <XCircle className="w-6 h-6" />
                </button>
              </div>

              {/* Ticket Info */}
              <div className="bg-slate-900/50 rounded-lg p-6 mb-6">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <p className="text-slate-400 text-sm mb-1">{t('tickets.status')}</p>
                    <div className={`inline-flex px-3 py-1 rounded-full border ${statusColors[selectedTicket.status]}`}>
                      <span className="text-sm font-medium">{statusLabels[selectedTicket.status]}</span>
                    </div>
                  </div>
                  <div>
                    <p className="text-slate-400 text-sm mb-1">{t('tickets.type')}</p>
                    <p className="text-white font-semibold">
                      {selectedTicket.ticket_type === 'single' ? t('tickets.type_single') : t('tickets.type_multiple')}
                    </p>
                  </div>
                  <div>
                    <p className="text-slate-400 text-sm mb-1">{t('tickets.stake')}</p>
                    <p className="text-white font-semibold">R$ {selectedTicket.stake.toFixed(2)}</p>
                  </div>
                  <div>
                    <p className="text-slate-400 text-sm mb-1">{t('tickets.total_odds')}</p>
                    <p className="text-white font-semibold text-xl">{selectedTicket.total_odds.toFixed(2)}</p>
                  </div>
                </div>
              </div>

              {/* Selections */}
              <div className="mb-6">
                <h4 className="text-lg font-semibold text-white mb-4">{t('tickets.selections')}</h4>
                <div className="space-y-3">
                  {selectedTicket.selections?.map((selection) => (
                    <div key={selection.id} className="bg-slate-900/50 rounded-lg p-4">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <p className="text-white font-semibold">
                            {selection.match_info?.home_team} vs {selection.match_info?.away_team}
                          </p>
                          <p className="text-slate-400 text-sm">
                            {selection.match_info?.league} • {selection.match_info?.match_date && new Date(selection.match_info.match_date).toLocaleDateString('pt-BR')}
                          </p>
                        </div>
                        <div className="text-right ml-4">
                          <p className="text-white font-bold text-xl">{selection.odd.toFixed(2)}</p>
                          <div className={`inline-flex px-2 py-1 rounded text-xs font-medium ${
                            selection.status === 'won' ? 'bg-green-500/20 text-green-400' :
                            selection.status === 'lost' ? 'bg-red-500/20 text-red-400' :
                            'bg-yellow-500/20 text-yellow-400'
                          }`}>
                            {selection.status === 'won' ? t('tickets.green') : selection.status === 'lost' ? t('tickets.red') : t('tickets.status_pending')}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-4 text-sm">
                        <span className="text-slate-400">{t('tickets.market')}: <span className="text-white">{selection.market}</span></span>
                        <span className="text-slate-400">{t('tickets.choice')}: <span className="text-white">{selection.outcome}</span></span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Summary */}
              <div className="bg-slate-900/50 rounded-lg p-6">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-slate-400 text-sm mb-1">{t('tickets.potential_return')}</p>
                    <p className="text-white font-semibold text-xl">
                      R$ {selectedTicket.potential_return.toFixed(2)}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-slate-400 text-sm mb-1">{t('tickets.final_result')}</p>
                    <p className={`font-semibold text-xl ${
                      selectedTicket.status === 'won' ? 'text-green-400' :
                      selectedTicket.status === 'lost' ? 'text-red-400' :
                      'text-yellow-400'
                    }`}>
                      {selectedTicket.status === 'won' && `+R$ ${selectedTicket.profit_loss.toFixed(2)}`}
                      {selectedTicket.status === 'lost' && `-R$ ${Math.abs(selectedTicket.profit_loss).toFixed(2)}`}
                      {selectedTicket.status === 'pending' && t('tickets.waiting')}
                      {selectedTicket.status === 'cancelled' && t('tickets.status_cancelled')}
                    </p>
                  </div>
                </div>
              </div>

              {selectedTicket.status === 'pending' && (
                <button
                  onClick={() => handleCancelTicket(selectedTicket.id)}
                  disabled={cancelMutation.isPending}
                  className="w-full mt-6 bg-red-600 hover:bg-red-700 text-white font-medium py-3 rounded-lg transition-colors disabled:opacity-50 flex items-center justify-center space-x-2"
                >
                  {cancelMutation.isPending ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                      <span>{t('tickets.canceling')}</span>
                    </>
                  ) : (
                    <>
                      <Trash2 className="w-5 h-5" />
                      <span>{t('tickets.cancel_ticket')}</span>
                    </>
                  )}
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default UserTickets;
