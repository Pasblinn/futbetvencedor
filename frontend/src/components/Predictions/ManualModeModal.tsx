import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Trophy, Award, AlertCircle, CheckCircle } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { useTranslation } from '../../contexts/I18nContext';

interface ManualModeModalProps {
  isOpen: boolean;
  onClose: () => void;
  availableMatches: any[];
}

const MARKETS = [
  { id: '1X2', name: 'Resultado Final (1X2)' },
  { id: 'BTTS', name: 'Ambas Marcam' },
  { id: 'OVER_UNDER_2_5', name: 'Acima/Abaixo 2.5 Gols' },
  { id: 'DOUBLE_CHANCE', name: 'Dupla Chance' },
  { id: 'CORNERS', name: 'Escanteios' },
  { id: 'CARDS', name: 'Cartões' },
];

export const ManualModeModal: React.FC<ManualModeModalProps> = ({
  isOpen,
  onClose,
  availableMatches,
}) => {
  const { t } = useTranslation();
  const [selectedMatch, setSelectedMatch] = useState<any>(null);
  const [marketType, setMarketType] = useState('');
  const [predictedOutcome, setPredictedOutcome] = useState('');
  const [userConfidence, setUserConfidence] = useState(75);
  const [userReasoning, setUserReasoning] = useState('');
  const [stakePercentage, setStakePercentage] = useState(2.0);

  // Mutation para criar prediction manual
  const createManualPrediction = useMutation({
    mutationFn: async (data: any) => {
      const response = await fetch('http://localhost:8000/api/v1/predictions-modes/manual/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!response.ok) throw new Error('Failed to create prediction');
      return response.json();
    },
    onSuccess: (data) => {
      // Reset form
      setSelectedMatch(null);
      setMarketType('');
      setPredictedOutcome('');
      setUserConfidence(75);
      setUserReasoning('');
      setStakePercentage(2.0);
    },
  });

  const handleSubmit = () => {
    if (!selectedMatch || !marketType || !predictedOutcome || !userReasoning) {
      alert(t('predictions.manual.required_fields'));
      return;
    }

    createManualPrediction.mutate({
      match_id: parseInt(selectedMatch.id),
      market_type: marketType,
      predicted_outcome: predictedOutcome,
      user_confidence: userConfidence / 100,
      user_reasoning: userReasoning,
      stake_percentage: stakePercentage,
    });
  };

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
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          onClick={(e) => e.stopPropagation()}
          className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-hidden border border-slate-700"
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-yellow-600 to-yellow-700 p-6 border-b border-yellow-500/30">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="bg-white/20 p-3 rounded-lg">
                  <Trophy className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                    {t('predictions.manual.title')}
                    <span className="bg-gradient-to-r from-yellow-400 to-orange-400 text-yellow-900 px-2 py-0.5 rounded text-xs font-bold">
                      {t('predictions.manual.gold_data')}
                    </span>
                  </h2>
                  <p className="text-yellow-100 text-sm">
                    {t('predictions.manual.subtitle')}
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

            {/* GOLD Data Badge */}
            <div className="mt-4 bg-white/10 rounded-lg p-3 backdrop-blur-sm">
              <div className="flex items-center gap-2 text-white text-sm">
                <Award className="w-5 h-5 text-yellow-300" />
                <span className="font-semibold">
                  {t('predictions.manual.gold_badge')}
                </span>
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="p-6 overflow-y-auto max-h-[calc(90vh-240px)]">
            {createManualPrediction.isSuccess ? (
              <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className="text-center py-12"
              >
                <CheckCircle className="w-20 h-20 text-green-400 mx-auto mb-4" />
                <h3 className="text-2xl font-bold text-white mb-2">
                  {t('predictions.manual.success_title')}
                </h3>
                <p className="text-slate-400 mb-6">
                  {t('predictions.manual.success_desc')}
                </p>
                <button
                  onClick={() => createManualPrediction.reset()}
                  className="px-6 py-3 bg-gradient-to-r from-yellow-600 to-yellow-700 hover:from-yellow-700 hover:to-yellow-800 text-white rounded-lg transition-all font-semibold"
                >
                  {t('predictions.manual.create_new')}
                </button>
              </motion.div>
            ) : (
              <div className="space-y-6">
                {/* Select Match */}
                <div>
                  <label className="block text-white font-semibold mb-2">
                    {t('predictions.manual.step1')} <span className="text-red-400">*</span>
                  </label>
                  <select
                    value={selectedMatch?.id || ''}
                    onChange={(e) => {
                      const match = availableMatches.find((m) => m.id === e.target.value);
                      setSelectedMatch(match);
                    }}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg p-3 text-white focus:ring-2 focus:ring-yellow-500 focus:border-yellow-500"
                  >
                    <option value="">{t('predictions.manual.select_match_placeholder')}</option>
                    {availableMatches.slice(0, 20).map((match) => (
                      <option key={match.id} value={match.id}>
                        {match.homeTeam} vs {match.awayTeam} - {match.league}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Select Market */}
                <div>
                  <label className="block text-white font-semibold mb-2">
                    {t('predictions.manual.step2')} <span className="text-red-400">*</span>
                  </label>
                  <div className="grid grid-cols-2 gap-3">
                    {MARKETS.map((market) => (
                      <button
                        key={market.id}
                        onClick={() => setMarketType(market.id)}
                        className={`p-3 rounded-lg border-2 transition-all ${
                          marketType === market.id
                            ? 'border-yellow-500 bg-yellow-500/10 text-yellow-400'
                            : 'border-slate-700 bg-slate-800/50 text-slate-300 hover:border-yellow-500/50'
                        }`}
                      >
                        {market.name}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Predicted Outcome */}
                <div>
                  <label className="block text-white font-semibold mb-2">
                    {t('predictions.manual.step3')} <span className="text-red-400">*</span>
                  </label>
                  <input
                    type="text"
                    value={predictedOutcome}
                    onChange={(e) => setPredictedOutcome(e.target.value)}
                    placeholder={t('predictions.manual.outcome_placeholder')}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg p-3 text-white focus:ring-2 focus:ring-yellow-500 focus:border-yellow-500"
                  />
                  <p className="text-xs text-slate-400 mt-1">
                    {t('predictions.manual.outcome_help')}
                  </p>
                </div>

                {/* User Confidence */}
                <div>
                  <label className="block text-white font-semibold mb-2">
                    {t('predictions.manual.step4')}: {userConfidence}%
                  </label>
                  <input
                    type="range"
                    min="50"
                    max="100"
                    value={userConfidence}
                    onChange={(e) => setUserConfidence(Number(e.target.value))}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-slate-400 mt-1">
                    <span>{t('predictions.manual.confidence_low')}</span>
                    <span>{t('predictions.manual.confidence_medium')}</span>
                    <span>{t('predictions.manual.confidence_high')}</span>
                  </div>
                </div>

                {/* Stake Percentage */}
                <div>
                  <label className="block text-white font-semibold mb-2">
                    {t('predictions.manual.step5')}: {stakePercentage.toFixed(1)}%
                  </label>
                  <input
                    type="range"
                    min="0.5"
                    max="10"
                    step="0.5"
                    value={stakePercentage}
                    onChange={(e) => setStakePercentage(Number(e.target.value))}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-slate-400 mt-1">
                    <span>{t('predictions.manual.stake_conservative')}</span>
                    <span>{t('predictions.manual.stake_moderate')}</span>
                    <span>{t('predictions.manual.stake_aggressive')}</span>
                  </div>
                </div>

                {/* User Reasoning */}
                <div>
                  <label className="block text-white font-semibold mb-2">
                    {t('predictions.manual.step6')} <span className="text-red-400">*</span>
                  </label>
                  <textarea
                    value={userReasoning}
                    onChange={(e) => setUserReasoning(e.target.value)}
                    placeholder={t('predictions.manual.reasoning_placeholder')}
                    rows={4}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg p-3 text-white focus:ring-2 focus:ring-yellow-500 focus:border-yellow-500 resize-none"
                  />
                  <p className="text-xs text-slate-400 mt-1">
                    {t('predictions.manual.reasoning_help')}
                  </p>
                </div>

                {/* Warning Box */}
                <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
                    <div className="text-sm text-yellow-200">
                      <div className="font-semibold mb-1">{t('predictions.manual.warning_title')}</div>
                      <p>
                        {t('predictions.manual.warning_desc')}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          {!createManualPrediction.isSuccess && (
            <div className="bg-slate-800 border-t border-slate-700 p-4">
              <div className="flex items-center justify-between">
                <button
                  onClick={onClose}
                  className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
                >
                  {t('predictions.manual.cancel')}
                </button>
                <button
                  onClick={handleSubmit}
                  disabled={
                    !selectedMatch ||
                    !marketType ||
                    !predictedOutcome ||
                    !userReasoning ||
                    createManualPrediction.isPending
                  }
                  className="px-6 py-3 bg-gradient-to-r from-yellow-600 to-yellow-700 hover:from-yellow-700 hover:to-yellow-800 text-white rounded-lg transition-all font-bold flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {createManualPrediction.isPending ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      {t('predictions.manual.creating')}
                    </>
                  ) : (
                    <>
                      <Trophy className="w-5 h-5" />
                      {t('predictions.manual.create_gold')}
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};
