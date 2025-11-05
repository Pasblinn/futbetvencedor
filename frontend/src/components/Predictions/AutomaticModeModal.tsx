import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, TrendingUp, AlertCircle, Target, Shield, Clock, Bot, CheckCircle } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { LoadingState, EmptyState } from '../UI/LoadingStates';
import { useTranslation } from '../../contexts/I18nContext';

interface AutomaticModeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAddToTicket?: (prediction: AutomaticPrediction) => void;
}

interface AutomaticPrediction {
  match_id: number;
  match_info: {
    home_team: string;
    away_team: string;
    league: string;
    match_date: string;
  };
  prediction: {
    market_type: string;
    outcome: string;
    confidence: number;
    edge: number;
    odds: number;
  };
  ai_validation: {
    validated: boolean;
    validation_mode: string;
    ai_confidence: number;
    edge_percentage: number;
    reasoning: string;
    risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
    recommended_stake: number;
  };
  status: string;
}

const getRiskColor = (risk: string) => {
  switch (risk) {
    case 'LOW':
      return { bg: 'bg-green-500/20', text: 'text-green-400', border: 'border-green-500' };
    case 'MEDIUM':
      return { bg: 'bg-yellow-500/20', text: 'text-yellow-400', border: 'border-yellow-500' };
    case 'HIGH':
      return { bg: 'bg-red-500/20', text: 'text-red-400', border: 'border-red-500' };
    default:
      return { bg: 'bg-gray-500/20', text: 'text-gray-400', border: 'border-gray-500' };
  }
};

const getOutcomeLabel = (outcome: string, market: string, t: (key: string) => string) => {
  if (market === '1X2') {
    if (outcome === '1') return t('predictions.automatic.home');
    if (outcome === 'X') return t('predictions.automatic.draw');
    if (outcome === '2') return t('predictions.automatic.away');
  }
  return outcome;
};

export const AutomaticModeModal: React.FC<AutomaticModeModalProps> = ({
  isOpen,
  onClose,
  onAddToTicket,
}) => {
  const { t } = useTranslation();

  // Fetch automatic predictions from API
  const { data: predictions, isLoading, error } = useQuery<AutomaticPrediction[]>({
    queryKey: ['automatic-predictions'],
    queryFn: async () => {
      const response = await fetch('http://localhost:8000/api/v1/predictions-modes/automatic/top-predictions?limit=50&min_confidence=0.6&min_edge=10');
      if (!response.ok) throw new Error('Failed to fetch predictions');
      return response.json();
    },
    enabled: isOpen,
    refetchInterval: 60000, // Atualizar a cada 60 segundos
  });

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0, y: 20 }}
          animate={{ scale: 1, opacity: 1, y: 0 }}
          exit={{ scale: 0.9, opacity: 0, y: 20 }}
          onClick={(e) => e.stopPropagation()}
          className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl shadow-2xl w-full max-w-5xl max-h-[90vh] overflow-hidden border border-slate-700"
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-blue-700 p-6 border-b border-blue-500/30">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="bg-white/20 p-3 rounded-lg">
                  <Bot className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-white">{t('predictions.automatic.title')}</h2>
                  <p className="text-blue-100 text-sm">
                    {t('predictions.automatic.subtitle')}
                  </p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-2 hover:bg-white/10 rounded-lg transition-colors"
              >
                <X className="w-6 h-6 text-white" />
              </button>
            </div>

            {/* Stats Summary */}
            {predictions && predictions.length > 0 && (
              <div className="grid grid-cols-3 gap-4 mt-4">
                <div className="bg-white/10 rounded-lg p-3 backdrop-blur-sm">
                  <div className="text-blue-100 text-xs mb-1">{t('predictions.automatic.total_approved')}</div>
                  <div className="text-white text-2xl font-bold">{predictions.length}</div>
                </div>
                <div className="bg-white/10 rounded-lg p-3 backdrop-blur-sm">
                  <div className="text-blue-100 text-xs mb-1">{t('predictions.automatic.avg_confidence')}</div>
                  <div className="text-white text-2xl font-bold">
                    {(predictions.reduce((acc, p) => acc + p.ai_validation.ai_confidence, 0) / predictions.length * 100).toFixed(0)}%
                  </div>
                </div>
                <div className="bg-white/10 rounded-lg p-3 backdrop-blur-sm">
                  <div className="text-blue-100 text-xs mb-1">{t('predictions.automatic.avg_edge')}</div>
                  <div className="text-white text-2xl font-bold">
                    +{(predictions.reduce((acc, p) => acc + p.ai_validation.edge_percentage, 0) / predictions.length).toFixed(1)}%
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Content */}
          <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
            {isLoading ? (
              <LoadingState type="skeleton" message={t('predictions.automatic.loading')} />
            ) : error ? (
              <EmptyState
                icon={<AlertCircle className="w-12 h-12 text-red-400" />}
                title={t('predictions.automatic.error_title')}
                description={t('predictions.automatic.error_message')}
              />
            ) : !predictions || predictions.length === 0 ? (
              <EmptyState
                icon={<Target className="w-12 h-12 text-slate-400" />}
                title={t('predictions.automatic.no_predictions')}
                description={t('predictions.automatic.no_predictions_desc')}
              />
            ) : (
              <div className="space-y-4">
                {predictions.map((pred, index) => {
                  const riskColors = getRiskColor(pred.ai_validation.risk_level);

                  return (
                    <motion.div
                      key={`${pred.match_id}-${index}`}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="bg-slate-800/50 rounded-xl border border-slate-700 hover:border-blue-500/50 transition-all overflow-hidden"
                    >
                      {/* Match Header */}
                      <div className="bg-gradient-to-r from-slate-700/50 to-slate-800/50 p-4 border-b border-slate-700">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <span className="px-2 py-1 bg-blue-500/20 text-blue-400 text-xs font-semibold rounded">
                                #{index + 1}
                              </span>
                              <span className="text-slate-400 text-xs">
                                {pred.match_info.league}
                              </span>
                            </div>
                            <h3 className="text-white text-lg font-bold mb-1">
                              {pred.match_info.home_team} <span className="text-slate-500">vs</span> {pred.match_info.away_team}
                            </h3>
                            <div className="flex items-center gap-3 text-xs text-slate-400">
                              <div className="flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                {new Date(pred.match_info.match_date).toLocaleString('pt-BR', {
                                  day: '2-digit',
                                  month: '2-digit',
                                  hour: '2-digit',
                                  minute: '2-digit'
                                })}
                              </div>
                            </div>
                          </div>

                          {/* Risk Badge */}
                          <div className={`${riskColors.bg} ${riskColors.text} px-3 py-1 rounded-lg border ${riskColors.border} flex items-center gap-2`}>
                            <Shield className="w-4 h-4" />
                            <span className="text-xs font-bold">{pred.ai_validation.risk_level}</span>
                          </div>
                        </div>
                      </div>

                      {/* Prediction Info */}
                      <div className="p-4">
                        <div className="grid grid-cols-2 gap-4 mb-4">
                          {/* Market & Outcome */}
                          <div className="bg-slate-900/50 rounded-lg p-3 border border-slate-700">
                            <div className="text-slate-400 text-xs mb-1">{t('predictions.automatic.market')}</div>
                            <div className="text-white font-semibold">{pred.prediction.market_type}</div>
                            <div className="text-blue-400 text-lg font-bold mt-1">
                              {getOutcomeLabel(pred.prediction.outcome, pred.prediction.market_type, t)}
                            </div>
                          </div>

                          {/* Odds */}
                          <div className="bg-slate-900/50 rounded-lg p-3 border border-slate-700">
                            <div className="text-slate-400 text-xs mb-1">{t('predictions.automatic.odd')}</div>
                            <div className="text-green-400 text-3xl font-bold font-mono">
                              {pred.prediction.odds.toFixed(2)}
                            </div>
                          </div>
                        </div>

                        {/* AI Metrics */}
                        <div className="grid grid-cols-3 gap-3 mb-4">
                          <div className="bg-blue-500/10 rounded-lg p-3 border border-blue-500/30">
                            <div className="flex items-center gap-2 mb-1">
                              <Target className="w-4 h-4 text-blue-400" />
                              <span className="text-xs text-slate-400">{t('predictions.automatic.ai_confidence')}</span>
                            </div>
                            <div className="text-blue-400 text-xl font-bold">
                              {(pred.ai_validation.ai_confidence * 100).toFixed(0)}%
                            </div>
                          </div>

                          <div className="bg-green-500/10 rounded-lg p-3 border border-green-500/30">
                            <div className="flex items-center gap-2 mb-1">
                              <TrendingUp className="w-4 h-4 text-green-400" />
                              <span className="text-xs text-slate-400">{t('predictions.automatic.edge')}</span>
                            </div>
                            <div className="text-green-400 text-xl font-bold">
                              +{pred.ai_validation.edge_percentage.toFixed(1)}%
                            </div>
                          </div>

                          <div className="bg-purple-500/10 rounded-lg p-3 border border-purple-500/30">
                            <div className="flex items-center gap-2 mb-1">
                              <Shield className="w-4 h-4 text-purple-400" />
                              <span className="text-xs text-slate-400">{t('predictions.automatic.kelly')}</span>
                            </div>
                            <div className="text-purple-400 text-xl font-bold">
                              {pred.ai_validation.recommended_stake.toFixed(1)}%
                            </div>
                          </div>
                        </div>

                        {/* AI Reasoning */}
                        <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700 mb-4">
                          <div className="flex items-center gap-2 mb-2">
                            <Bot className="w-4 h-4 text-blue-400" />
                            <span className="text-xs font-semibold text-slate-400 uppercase">{t('predictions.automatic.ai_analysis')}</span>
                          </div>
                          <p className="text-slate-300 text-sm leading-relaxed">
                            {pred.ai_validation.reasoning}
                          </p>
                        </div>

                        {/* Action Button */}
                        <button
                          onClick={() => onAddToTicket?.(pred)}
                          className="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white py-3 rounded-lg font-bold flex items-center justify-center gap-2 transition-all shadow-lg hover:shadow-green-500/20"
                        >
                          <CheckCircle className="w-5 h-5" />
                          {t('predictions.automatic.add_to_ticket')}
                        </button>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="bg-slate-800 border-t border-slate-700 p-4">
            <div className="flex items-center justify-between text-xs text-slate-400">
              <div className="flex items-center gap-4">
                <span className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  {t('predictions.automatic.auto_update')}
                </span>
                <span>•</span>
                <span>{t('predictions.automatic.approval_criteria')}</span>
              </div>
              <button
                onClick={onClose}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
              >
                {t('predictions.automatic.close')}
              </button>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};
