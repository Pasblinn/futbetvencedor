import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Brain, ArrowRight, ArrowLeft, Target, AlertTriangle, CheckCircle, Lightbulb, BarChart3 } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { LoadingState } from '../UI/LoadingStates';
import { ALL_MARKETS, MARKET_CATEGORIES, translateMarket } from '../../utils/marketTranslations';
import { useTranslation } from '../../contexts/I18nContext';

interface AssistedModeModalProps {
  isOpen: boolean;
  onClose: () => void;
  availableMatches: any[];
}

interface AssistedAnalysis {
  match_id: number;
  match_info: {
    home_team: string;
    away_team: string;
    league: string;
  };
  selected_market: string;  // 🔥 Mercado selecionado
  selected_category?: string;  // 🔥 NOVO: Categoria escolhida (quando MULTI_CATEGORY)
  ml_analysis: {
    probability: number;
    fair_odds: number;
    market_odds: number;
    edge: number;
    confidence: number;
    variance: number;
    sample_size: number;
    historical_accuracy: number;
  };
  ai_insights: {
    validation_mode: string;
    ai_insights: string[];
    strengths: string[];
    weaknesses: string[];
    historical_performance: {
      market: string;
      total_predictions: number;
      accuracy: number;
      avg_edge: number;
      roi: number;
    };
    risk_assessment: {
      risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
      confidence_score: number;
      variance: number;
    };
    recommendation: {
      should_bet: boolean;
      stake_percentage: number;
      reasoning: string;
    };
  };
  recommendation: {
    should_bet: boolean;
    stake_percentage: number;
    reasoning: string;
  };
}

interface AssistedMultipleAnalysis {
  total_matches: number;
  selection_mode: string;  // 'AI_AUTO', 'CATEGORY', 'MULTI_CATEGORY', 'SPECIFIC'
  analyses: AssistedAnalysis[];
  combined_recommendation: {
    should_bet: boolean;
    total_odds: number;
    combined_probability: number;
    total_edge: number;
    avg_edge: number;
    approved_count: number;
    total_matches: number;
    stake_percentage: number;
    reasoning: string;
  };
}

// Mercados e categorias agora vêm de marketTranslations.ts

export const AssistedModeModal: React.FC<AssistedModeModalProps> = ({
  isOpen,
  onClose,
  availableMatches,
}) => {
  const { t } = useTranslation();
  const [step, setStep] = useState(1);
  const [selectedMatches, setSelectedMatches] = useState<any[]>([]); // 🔥 Múltiplos jogos
  const [selectedMarket, setSelectedMarket] = useState<string>(''); // Agora opcional
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]); // 🔥 NOVO: Múltiplas categorias
  const [isAIAuto, setIsAIAuto] = useState(false); // 🔥 NOVO: Flag para AI Auto mode

  // Fetch AI analysis - agora suporta múltiplos jogos e múltiplas categorias
  const { data: multipleAnalysis, isLoading: isAnalyzing, refetch } = useQuery<AssistedMultipleAnalysis>({
    queryKey: ['assisted-analysis', selectedMatches.map(m => m.id).join(','), selectedMarket, selectedCategories.join(','), isAIAuto],
    queryFn: async () => {
      const response = await fetch('http://localhost:8000/api/v1/predictions-modes/assisted/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          match_ids: selectedMatches.map(m => parseInt(m.id)), // 🔥 Array de IDs
          market_type: selectedMarket || null, // 🔥 Opcional (null = AI decide)
          market_categories: selectedCategories.length > 0 ? selectedCategories : null, // 🔥 NOVO: Múltiplas categorias
          selected_outcome: selectedMarket, // The market IS the outcome now
        }),
      });
      if (!response.ok) throw new Error('Failed to analyze');
      return response.json();
    },
    enabled: false,
  });

  const handleNext = () => {
    if (step === 1 && selectedMatches.length > 0) setStep(2);
    else if (step === 2) {
      // 🔥 NOVO: Mercado agora é opcional - pode prosseguir mesmo sem selecionar
      refetch();
      setStep(3);
    }
  };

  const handleBack = () => {
    if (step > 1) setStep(step - 1);
  };

  const handleReset = () => {
    setStep(1);
    setSelectedMatches([]);
    setSelectedMarket('');
    setSelectedCategories([]);
    setIsAIAuto(false);
  };

  // 🔥 Toggle múltipla seleção de jogos
  const toggleMatchSelection = (match: any) => {
    setSelectedMatches(prev => {
      const isSelected = prev.some(m => m.id === match.id);
      if (isSelected) {
        return prev.filter(m => m.id !== match.id);
      } else {
        return [...prev, match];
      }
    });
  };

  // 🔥 NOVO: Toggle múltipla seleção de categorias
  const toggleCategorySelection = (category: string) => {
    setSelectedCategories(prev => {
      const isSelected = prev.includes(category);
      if (isSelected) {
        return prev.filter(c => c !== category);
      } else {
        return [...prev, category];
      }
    });
    setSelectedMarket(''); // Limpa mercado específico
    setIsAIAuto(false); // Desativa AI Auto
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
          className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden border border-slate-700"
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-purple-600 to-purple-700 p-6 border-b border-purple-500/30">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="bg-white/20 p-3 rounded-lg">
                  <Brain className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-white">{t('predictions.assisted.title')}</h2>
                  <p className="text-purple-100 text-sm">
                    {t('predictions.assisted.subtitle')}
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

            {/* Progress Steps */}
            <div className="flex items-center justify-center gap-2 mt-6">
              {[1, 2, 3].map((s) => (
                <div key={s} className="flex items-center">
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center font-bold transition-all ${
                      step >= s
                        ? 'bg-white text-purple-600'
                        : 'bg-white/20 text-white/50'
                    }`}
                  >
                    {s}
                  </div>
                  {s < 3 && (
                    <div
                      className={`w-12 h-1 mx-1 rounded transition-all ${
                        step > s ? 'bg-white' : 'bg-white/20'
                      }`}
                    />
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Content */}
          <div className="p-6 overflow-y-auto max-h-[calc(90vh-240px)]">
            {/* Step 1: Escolher Jogos (Múltiplos) */}
            {step === 1 && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
              >
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xl font-bold text-white flex items-center gap-2">
                    <Target className="w-5 h-5" />
                    {t('predictions.assisted.step1_title')}
                  </h3>
                  <div className="bg-purple-500/20 border border-purple-500 rounded-lg px-3 py-1">
                    <span className="text-purple-400 font-semibold text-sm">
                      {selectedMatches.length} {selectedMatches.length === 1 ? t('predictions.assisted.match_selected') : t('predictions.assisted.matches_selected')}
                    </span>
                  </div>
                </div>
                <p className="text-slate-400 text-sm mb-4">
                  {t('predictions.assisted.step1_desc')}
                </p>
                <div className="space-y-3">
                  {availableMatches.slice(0, 15).map((match) => {
                    const isSelected = selectedMatches.some(m => m.id === match.id);
                    return (
                      <button
                        key={match.id}
                        onClick={() => toggleMatchSelection(match)}
                        className={`w-full p-4 rounded-lg border-2 transition-all text-left relative ${
                          isSelected
                            ? 'border-purple-500 bg-purple-500/10'
                            : 'border-slate-700 bg-slate-800/50 hover:border-purple-500/50'
                        }`}
                      >
                        {/* Checkbox visual indicator */}
                        <div className={`absolute top-3 right-3 w-6 h-6 rounded border-2 flex items-center justify-center transition-all ${
                          isSelected
                            ? 'bg-purple-500 border-purple-500'
                            : 'border-slate-500'
                        }`}>
                          {isSelected && (
                            <CheckCircle className="w-4 h-4 text-white" />
                          )}
                        </div>

                        <div className="text-white font-semibold mb-1 pr-8">
                          {match.homeTeam} <span className="text-slate-500">vs</span> {match.awayTeam}
                        </div>
                        <div className="text-sm text-slate-400">
                          {match.league} • {match.date} {match.time}
                        </div>
                      </button>
                    );
                  })}
                </div>
              </motion.div>
            )}

            {/* Step 2: Escolher Mercado (Opcional) */}
            {step === 2 && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="max-h-[60vh] overflow-y-auto custom-scrollbar"
              >
                <h3 className="text-xl font-bold text-white mb-2">
                  {t('predictions.assisted.step2_title')}
                </h3>
                <p className="text-slate-400 text-sm mb-4">
                  {t('predictions.assisted.step2_desc')}
                </p>

                {/* Opção: AI Decide Automaticamente */}
                <div className="mb-6">
                  <button
                    onClick={() => {
                      setSelectedMarket('');
                      setSelectedCategories([]);
                      setIsAIAuto(true);
                    }}
                    className={`w-full p-4 rounded-lg border-2 transition-all text-left ${
                      isAIAuto
                        ? 'border-green-500 bg-green-500/10'
                        : 'border-slate-600 bg-slate-700/50 hover:border-green-500/50'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <Brain className="w-6 h-6 text-green-400" />
                      <div>
                        <div className="text-white font-semibold">
                          🤖 {t('predictions.assisted.ai_auto')}
                        </div>
                        <div className="text-sm text-slate-400">
                          {t('predictions.assisted.ai_auto_desc')}
                        </div>
                      </div>
                    </div>
                  </button>
                </div>

                {/* Categorias de Mercado - MÚLTIPLA SELEÇÃO */}
                <h4 className="text-sm font-semibold text-slate-400 mb-3">
                  {t('predictions.assisted.or_categories')}
                  {selectedCategories.length > 0 && (
                    <span className="ml-2 text-purple-400">
                      ({selectedCategories.length} {selectedCategories.length > 1 ? t('predictions.assisted.categories_selected_plural') : t('predictions.assisted.categories_selected')})
                    </span>
                  )}
                </h4>
                <div className="grid grid-cols-2 gap-3 mb-6">
                  {MARKET_CATEGORIES.map((category) => {
                    const isSelected = selectedCategories.includes(category);
                    return (
                      <button
                        key={category}
                        onClick={() => toggleCategorySelection(category)}
                        className={`p-3 rounded-lg border-2 transition-all relative ${
                          isSelected
                            ? 'border-blue-500 bg-blue-500/10'
                            : 'border-slate-700 bg-slate-800/50 hover:border-blue-500/50'
                        }`}
                      >
                        {/* Checkbox visual indicator */}
                        <div className={`absolute top-2 right-2 w-5 h-5 rounded border-2 flex items-center justify-center transition-all ${
                          isSelected
                            ? 'bg-blue-500 border-blue-500'
                            : 'border-slate-500'
                        }`}>
                          {isSelected && (
                            <CheckCircle className="w-3 h-3 text-white" />
                          )}
                        </div>
                        <div className="text-white font-semibold text-sm pr-6">{category}</div>
                        <div className="text-xs text-slate-400 mt-1">
                          {t('predictions.assisted.ai_decides')}
                        </div>
                      </button>
                    );
                  })}
                </div>

                {/* Mercados Específicos (Expandido) */}
                <details className="mb-4">
                  <summary className="text-sm font-semibold text-slate-400 mb-3 cursor-pointer hover:text-purple-400 transition-colors">
                    {t('predictions.assisted.or_specific')}
                  </summary>
                  <div className="mt-3">
                    {MARKET_CATEGORIES.map((category) => {
                      const categoryMarkets = ALL_MARKETS.filter(m => m.category === category);
                      return (
                        <div key={category} className="mb-6">
                          <h4 className="text-sm font-semibold text-purple-400 mb-3">{category}</h4>
                          <div className="grid grid-cols-2 gap-3">
                            {categoryMarkets.map((market) => (
                              <button
                                key={market.id}
                                onClick={() => {
                                  setSelectedMarket(market.id);
                                  setSelectedCategories([]); // Limpa categorias
                                  setIsAIAuto(false); // Desativa AI Auto
                                }}
                                className={`p-4 rounded-lg border-2 transition-all text-left ${
                                  selectedMarket === market.id
                                    ? 'border-purple-500 bg-purple-500/10'
                                    : 'border-slate-700 bg-slate-800/50 hover:border-purple-500/50'
                                }`}
                              >
                                <div className="text-white font-semibold text-sm">
                                  {market.name}
                                </div>
                              </button>
                            ))}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </details>
              </motion.div>
            )}

            {/* Step 3: Ver Análise */}
            {step === 3 && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
              >
                {isAnalyzing ? (
                  <LoadingState type="skeleton" message="AI analisando suas escolhas..." />
                ) : multipleAnalysis ? (
                  <div className="space-y-4">
                    <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                      <Brain className="w-5 h-5" />
                      Análise Completa - {multipleAnalysis.total_matches} {multipleAnalysis.total_matches === 1 ? 'Jogo' : 'Jogos'}
                    </h3>

                    {/* Selection Mode Info */}
                    <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-slate-400">
                          <strong>Modo:</strong>{' '}
                          {multipleAnalysis.selection_mode === 'AI_AUTO' && '🤖 AI Escolha Automática'}
                          {multipleAnalysis.selection_mode === 'CATEGORY' && `📊 Categoria: ${selectedCategories[0]}`}
                          {multipleAnalysis.selection_mode === 'MULTI_CATEGORY' && `🎯 Múltiplas Categorias: ${selectedCategories.join(', ')}`}
                          {multipleAnalysis.selection_mode === 'SPECIFIC' && `🎯 Mercado Específico`}
                        </span>
                        <span className="text-purple-400 font-semibold text-sm">
                          {multipleAnalysis.analyses.length} análise{multipleAnalysis.analyses.length > 1 ? 's' : ''}
                        </span>
                      </div>
                    </div>

                    {/* Individual Analyses for each match */}
                    {multipleAnalysis.analyses.map((analysis, idx) => (
                      <div key={`${analysis.match_id}-${idx}`} className="bg-slate-800/30 rounded-lg p-4 border border-slate-700">
                        <div className="flex items-center justify-between mb-3">
                          <div>
                            <div className="text-white font-semibold">
                              {idx + 1}. {analysis.match_info.home_team} <span className="text-slate-500">vs</span> {analysis.match_info.away_team}
                            </div>
                            <div className="text-xs text-slate-400 mt-1">
                              Mercado: <span className="text-purple-400">{translateMarket(analysis.selected_market)}</span>
                              {analysis.selected_category && (
                                <span className="ml-2 text-blue-400">
                                  (Categoria: {analysis.selected_category})
                                </span>
                              )}
                            </div>
                          </div>
                          {analysis.recommendation.should_bet ? (
                            <CheckCircle className="w-6 h-6 text-green-400" />
                          ) : (
                            <AlertTriangle className="w-6 h-6 text-red-400" />
                          )}
                        </div>

                        {/* Quick stats for this match */}
                        <div className="grid grid-cols-4 gap-2">
                          <div className="bg-blue-500/10 rounded p-2 border border-blue-500/30">
                            <div className="text-xs text-slate-400">Prob</div>
                            <div className="text-blue-400 text-sm font-bold">
                              {(analysis.ml_analysis.probability * 100).toFixed(1)}%
                            </div>
                          </div>
                          <div className="bg-green-500/10 rounded p-2 border border-green-500/30">
                            <div className="text-xs text-slate-400">Edge</div>
                            <div className="text-green-400 text-sm font-bold">
                              +{analysis.ml_analysis.edge.toFixed(1)}%
                            </div>
                          </div>
                          <div className="bg-purple-500/10 rounded p-2 border border-purple-500/30">
                            <div className="text-xs text-slate-400">Conf</div>
                            <div className="text-purple-400 text-sm font-bold">
                              {(analysis.ml_analysis.confidence * 100).toFixed(0)}%
                            </div>
                          </div>
                          <div className="bg-yellow-500/10 rounded p-2 border border-yellow-500/30">
                            <div className="text-xs text-slate-400">Kelly</div>
                            <div className="text-yellow-400 text-sm font-bold">
                              {analysis.recommendation.stake_percentage.toFixed(1)}%
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}

                    {/* Combined Recommendation (if multiple matches) */}
                    {multipleAnalysis.total_matches > 1 && (
                      <div className={`rounded-lg p-4 border-2 ${
                        multipleAnalysis.combined_recommendation.should_bet
                          ? 'bg-green-500/10 border-green-500'
                          : 'bg-red-500/10 border-red-500'
                      }`}>
                        <div className="flex items-center gap-2 mb-3">
                          {multipleAnalysis.combined_recommendation.should_bet ? (
                            <CheckCircle className="w-6 h-6 text-green-400" />
                          ) : (
                            <AlertTriangle className="w-6 h-6 text-red-400" />
                          )}
                          <span className={`text-lg font-bold ${
                            multipleAnalysis.combined_recommendation.should_bet
                              ? 'text-green-400'
                              : 'text-red-400'
                          }`}>
                            MÚLTIPLA: {multipleAnalysis.combined_recommendation.should_bet ? 'RECOMENDADA' : 'NÃO RECOMENDADA'}
                          </span>
                        </div>

                        <div className="grid grid-cols-3 gap-3 mb-3">
                          <div>
                            <div className="text-xs text-slate-400">Odd Total</div>
                            <div className="text-white font-bold">{multipleAnalysis.combined_recommendation.total_odds.toFixed(2)}</div>
                          </div>
                          <div>
                            <div className="text-xs text-slate-400">Prob. Combinada</div>
                            <div className="text-white font-bold">{(multipleAnalysis.combined_recommendation.combined_probability * 100).toFixed(1)}%</div>
                          </div>
                          <div>
                            <div className="text-xs text-slate-400">Edge Médio</div>
                            <div className="text-white font-bold">+{multipleAnalysis.combined_recommendation.avg_edge.toFixed(1)}%</div>
                          </div>
                        </div>

                        <p className="text-white text-sm">
                          {multipleAnalysis.combined_recommendation.reasoning}
                        </p>
                      </div>
                    )}

                    {/* Individual Analysis Details (for single match or first match) */}
                    {multipleAnalysis.analyses.length > 0 && (
                      <div className="space-y-4">
                        <div className="grid grid-cols-4 gap-3">
                          <div className="bg-blue-500/10 rounded-lg p-3 border border-blue-500/30">
                            <div className="text-xs text-slate-400 mb-1">Probabilidade</div>
                            <div className="text-blue-400 text-xl font-bold">
                              {(multipleAnalysis.analyses[0].ml_analysis.probability * 100).toFixed(1)}%
                            </div>
                          </div>
                          <div className="bg-green-500/10 rounded-lg p-3 border border-green-500/30">
                            <div className="text-xs text-slate-400 mb-1">Edge</div>
                            <div className="text-green-400 text-xl font-bold">
                              +{multipleAnalysis.analyses[0].ml_analysis.edge.toFixed(1)}%
                            </div>
                          </div>
                          <div className="bg-purple-500/10 rounded-lg p-3 border border-purple-500/30">
                            <div className="text-xs text-slate-400 mb-1">Confiança</div>
                            <div className="text-purple-400 text-xl font-bold">
                              {(multipleAnalysis.analyses[0].ml_analysis.confidence * 100).toFixed(0)}%
                            </div>
                          </div>
                          <div className="bg-yellow-500/10 rounded-lg p-3 border border-yellow-500/30">
                            <div className="text-xs text-slate-400 mb-1">Kelly</div>
                            <div className="text-yellow-400 text-xl font-bold">
                              {multipleAnalysis.analyses[0].recommendation.stake_percentage.toFixed(1)}%
                            </div>
                          </div>
                        </div>

                    {/* AI Insights */}
                    <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
                      <div className="flex items-center gap-2 mb-3">
                        <Lightbulb className="w-5 h-5 text-yellow-400" />
                        <span className="text-white font-semibold">Insights da AI</span>
                      </div>
                      <ul className="space-y-2">
                        {multipleAnalysis.analyses[0].ai_insights.ai_insights.map((insight: string, idx: number) => (
                          <li key={idx} className="text-slate-300 text-sm flex items-start gap-2">
                            <span className="text-purple-400 mt-1">•</span>
                            {insight}
                          </li>
                        ))}
                      </ul>
                    </div>

                    {/* Strengths & Weaknesses */}
                    <div className="grid grid-cols-2 gap-4">
                      <div className="bg-green-500/10 rounded-lg p-4 border border-green-500/30">
                        <div className="flex items-center gap-2 mb-3">
                          <CheckCircle className="w-5 h-5 text-green-400" />
                          <span className="text-white font-semibold">Pontos Fortes</span>
                        </div>
                        <ul className="space-y-2">
                          {multipleAnalysis.analyses[0].ai_insights.strengths.map((strength: string, idx: number) => (
                            <li key={idx} className="text-green-300 text-sm flex items-start gap-2">
                              <span>✓</span>
                              {strength}
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div className="bg-red-500/10 rounded-lg p-4 border border-red-500/30">
                        <div className="flex items-center gap-2 mb-3">
                          <AlertTriangle className="w-5 h-5 text-red-400" />
                          <span className="text-white font-semibold">Pontos Fracos</span>
                        </div>
                        <ul className="space-y-2">
                          {multipleAnalysis.analyses[0].ai_insights.weaknesses.map((weakness: string, idx: number) => (
                            <li key={idx} className="text-red-300 text-sm flex items-start gap-2">
                              <span>⚠</span>
                              {weakness}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>

                    {/* Historical Performance */}
                    <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
                      <div className="flex items-center gap-2 mb-3">
                        <BarChart3 className="w-5 h-5 text-blue-400" />
                        <span className="text-white font-semibold">Performance Histórica</span>
                      </div>
                      <div className="grid grid-cols-4 gap-4 text-center">
                        <div>
                          <div className="text-2xl font-bold text-white">
                            {multipleAnalysis.analyses[0].ai_insights.historical_performance.total_predictions}
                          </div>
                          <div className="text-xs text-slate-400">Predictions</div>
                        </div>
                        <div>
                          <div className="text-2xl font-bold text-green-400">
                            {(multipleAnalysis.analyses[0].ai_insights.historical_performance.accuracy * 100).toFixed(0)}%
                          </div>
                          <div className="text-xs text-slate-400">Acurácia</div>
                        </div>
                        <div>
                          <div className="text-2xl font-bold text-blue-400">
                            +{multipleAnalysis.analyses[0].ai_insights.historical_performance.avg_edge.toFixed(1)}%
                          </div>
                          <div className="text-xs text-slate-400">Edge Médio</div>
                        </div>
                        <div>
                          <div className="text-2xl font-bold text-purple-400">
                            {multipleAnalysis.analyses[0].ai_insights.historical_performance.roi.toFixed(1)}%
                          </div>
                          <div className="text-xs text-slate-400">ROI</div>
                        </div>
                      </div>
                    </div>

                    {/* Recommendation */}
                    <div
                      className={`rounded-lg p-4 border-2 ${
                        multipleAnalysis.analyses[0].recommendation.should_bet
                          ? 'bg-green-500/10 border-green-500'
                          : 'bg-red-500/10 border-red-500'
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        {multipleAnalysis.analyses[0].recommendation.should_bet ? (
                          <CheckCircle className="w-6 h-6 text-green-400" />
                        ) : (
                          <AlertTriangle className="w-6 h-6 text-red-400" />
                        )}
                        <span
                          className={`text-lg font-bold ${
                            multipleAnalysis.analyses[0].recommendation.should_bet
                              ? 'text-green-400'
                              : 'text-red-400'
                          }`}
                        >
                          {multipleAnalysis.analyses[0].recommendation.should_bet
                            ? 'RECOMENDADO'
                            : 'NÃO RECOMENDADO'}
                        </span>
                      </div>
                      <p className="text-white text-sm">
                        {multipleAnalysis.analyses[0].recommendation.reasoning}
                      </p>
                    </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-8 text-slate-400">
                    Erro ao carregar análise
                  </div>
                )}
              </motion.div>
            )}
          </div>

          {/* Footer */}
          <div className="bg-slate-800 border-t border-slate-700 p-4">
            <div className="flex items-center justify-between">
              <button
                onClick={step === 3 ? handleReset : handleBack}
                disabled={step === 1}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ArrowLeft className="w-4 h-4" />
                {step === 3 ? 'Nova Análise' : 'Voltar'}
              </button>
              <div className="flex items-center gap-3">
                <button
                  onClick={onClose}
                  className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
                >
                  Fechar
                </button>
                {step < 3 && (
                  <button
                    onClick={handleNext}
                    disabled={step === 1 && selectedMatches.length === 0}
                    className="px-6 py-2 bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white rounded-lg transition-all flex items-center gap-2 font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {step === 1 ? 'Próximo' : 'Analisar'}
                    <ArrowRight className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};
