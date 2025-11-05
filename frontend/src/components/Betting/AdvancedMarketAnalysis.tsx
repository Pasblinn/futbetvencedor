import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  TrendingUp,
  Target,
  Shield,
  Zap,
  BarChart3,
  Brain,
  DollarSign,
  Percent,
  AlertTriangle,
  CheckCircle,
  Star
} from 'lucide-react';
import { MatchAnalysis, BettingMarket, MARKET_CONFIGS } from '../../types/betting';

interface AdvancedMarketAnalysisProps {
  analysis: MatchAnalysis;
  onAddToTicket: (market: BettingMarket, selection: string) => void;
  selectedMarkets: string[];
}

export const AdvancedMarketAnalysis: React.FC<AdvancedMarketAnalysisProps> = ({
  analysis,
  onAddToTicket,
  selectedMarkets
}) => {
  const [activeTab, setActiveTab] = useState<'all' | 'value' | 'safe' | 'high_odds'>('all');
  const [expandedMarket, setExpandedMarket] = useState<string | null>(null);

  const getMarketsForTab = () => {
    switch (activeTab) {
      case 'value': return analysis.best_value_bets;
      case 'safe': return analysis.safest_bets;
      case 'high_odds': return analysis.highest_odds_bets;
      default: return analysis.markets;
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 75) return 'text-green-400 bg-green-400/20';
    if (confidence >= 65) return 'text-yellow-400 bg-yellow-400/20';
    if (confidence >= 55) return 'text-orange-400 bg-orange-400/20';
    return 'text-red-400 bg-red-400/20';
  };

  const getValueColor = (value: number) => {
    if (value >= 0.1) return 'text-green-400';
    if (value >= 0.05) return 'text-yellow-400';
    if (value >= 0.02) return 'text-orange-400';
    return 'text-red-400';
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low': return 'text-green-400 bg-green-400/10 border-green-400/30';
      case 'medium': return 'text-yellow-400 bg-yellow-400/10 border-yellow-400/30';
      case 'high': return 'text-red-400 bg-red-400/10 border-red-400/30';
      default: return 'text-gray-400 bg-gray-400/10 border-gray-400/30';
    }
  };

  const renderMarketCard = (market: BettingMarket) => {
    const config = MARKET_CONFIGS[market.type];
    const isSelected = selectedMarkets.includes(market.id);
    const isExpanded = expandedMarket === market.id;

    return (
      <motion.div
        key={market.id}
        layout
        className={`bg-bg-card rounded-xl border transition-all duration-300 ${
          isSelected
            ? 'border-primary-500 bg-primary-500/5'
            : 'border-border-subtle hover:border-border-primary'
        }`}
      >
        <div className="p-4">
          {/* Header */}
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-start gap-3">
              <div className="text-2xl">{config.icon}</div>
              <div>
                <h4 className="font-semibold text-text-primary">{config.name}</h4>
                <p className="text-sm text-text-secondary">{config.description}</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className={`px-2 py-1 rounded text-xs font-medium ${getRiskColor(market.risk_level)}`}>
                {market.risk_level.toUpperCase()}
              </span>
            </div>
          </div>

          {/* Metrics Row */}
          <div className="grid grid-cols-3 gap-3 mb-3">
            <div className="text-center">
              <div className={`text-lg font-bold ${getConfidenceColor(market.confidence)}`}>
                {market.confidence.toFixed(0)}%
              </div>
              <div className="text-xs text-text-tertiary">Confiança</div>
            </div>

            <div className="text-center">
              <div className={`text-lg font-bold ${getValueColor(market.value)}`}>
                {(market.value * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-text-tertiary">Valor</div>
            </div>

            <div className="text-center">
              <div className="text-lg font-bold text-accent-400">
                {(market.kelly_percentage * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-text-tertiary">Kelly</div>
            </div>
          </div>

          {/* Odds Grid */}
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2 mb-3">
            {Object.entries(market.odds).map(([selection, odds]) => {
              const probability = market.probability[selection] || 0;
              const isRecommended = market.recommendation === selection;

              return (
                <button
                  key={selection}
                  onClick={() => onAddToTicket(market, selection)}
                  className={`p-3 rounded-lg text-center transition-all hover:scale-105 ${
                    isRecommended
                      ? 'bg-primary-600/20 border border-primary-500 text-primary-400'
                      : 'bg-bg-secondary hover:bg-bg-tertiary text-text-primary'
                  }`}
                >
                  <div className="text-xs text-text-tertiary capitalize mb-1">
                    {selection}
                  </div>
                  <div className="font-bold text-lg">
                    {odds.toFixed(2)}
                  </div>
                  <div className="text-xs text-text-secondary">
                    {(probability * 100).toFixed(0)}%
                  </div>
                  {isRecommended && (
                    <div className="text-xs text-primary-400 mt-1">
                      <Star className="w-3 h-3 inline" /> Recomendado
                    </div>
                  )}
                </button>
              );
            })}
          </div>

          {/* Expand Button */}
          <button
            onClick={() => setExpandedMarket(isExpanded ? null : market.id)}
            className="w-full text-sm text-text-secondary hover:text-text-primary transition-colors py-2"
          >
            {isExpanded ? 'Menos detalhes ↑' : 'Mais detalhes ↓'}
          </button>
        </div>

        {/* Expanded Content */}
        <AnimatePresence>
          {isExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="border-t border-border-subtle p-4 bg-bg-secondary/50"
            >
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <h5 className="font-medium text-text-primary mb-2">📊 Análise Estatística</h5>
                  <div className="space-y-1 text-text-secondary">
                    <div>Confiança: {market.confidence.toFixed(1)}%</div>
                    <div>Expected Value: {(market.value * 100).toFixed(2)}%</div>
                    <div>Kelly %: {(market.kelly_percentage * 100).toFixed(2)}%</div>
                    <div>Risco: {market.risk_level}</div>
                  </div>
                </div>

                <div>
                  <h5 className="font-medium text-text-primary mb-2">🎯 Probabilidades</h5>
                  <div className="space-y-1 text-text-secondary">
                    {Object.entries(market.probability).map(([selection, prob]) => (
                      <div key={selection} className="flex justify-between">
                        <span className="capitalize">{selection}:</span>
                        <span>{(prob * 100).toFixed(1)}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="mt-4 p-3 bg-bg-card rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <Brain className="w-4 h-4 text-primary-400" />
                  <span className="font-medium text-text-primary">Análise ML</span>
                </div>
                <p className="text-sm text-text-secondary">
                  {config.description}. Baseado em modelos preditivos avançados e
                  análise de {analysis.ml_analysis ? 'dados históricos' : 'padrões estatísticos'}.
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Match Header */}
      <div className="bg-bg-card rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-xl font-bold text-text-primary">
              {analysis.home_team} vs {analysis.away_team}
            </h3>
            <p className="text-text-secondary">
              {analysis.league} • {new Date(analysis.match_date).toLocaleDateString()}
            </p>
          </div>

          <div className="text-right">
            <div className="text-2xl font-bold text-primary-400">
              {analysis.markets.length}
            </div>
            <div className="text-sm text-text-secondary">Mercados</div>
          </div>
        </div>

        {/* ML Analysis Summary */}
        {analysis.ml_analysis && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-bg-secondary rounded-lg p-4">
              <h4 className="font-medium text-text-primary mb-2">🏆 Probabilidades</h4>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Casa:</span>
                  <span className="font-mono">{(analysis.ml_analysis.win_probabilities.home * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Empate:</span>
                  <span className="font-mono">{(analysis.ml_analysis.win_probabilities.draw * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Fora:</span>
                  <span className="font-mono">{(analysis.ml_analysis.win_probabilities.away * 100).toFixed(1)}%</span>
                </div>
              </div>
            </div>

            <div className="bg-bg-secondary rounded-lg p-4">
              <h4 className="font-medium text-text-primary mb-2">⚽ Análise de Gols</h4>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Esperado Casa:</span>
                  <span className="font-mono">{analysis.ml_analysis.goals_analysis.expected_home_goals.toFixed(1)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Esperado Fora:</span>
                  <span className="font-mono">{analysis.ml_analysis.goals_analysis.expected_away_goals.toFixed(1)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Total:</span>
                  <span className="font-mono">{analysis.ml_analysis.goals_analysis.total_expected.toFixed(1)}</span>
                </div>
              </div>
            </div>

            <div className="bg-bg-secondary rounded-lg p-4">
              <h4 className="font-medium text-text-primary mb-2">📊 Extras</h4>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>BTTS:</span>
                  <span className="font-mono">{(analysis.ml_analysis.advanced_stats.btts_probability * 100).toFixed(0)}%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Cartões:</span>
                  <span className="font-mono">{analysis.ml_analysis.advanced_stats.cards_expected.toFixed(1)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Escanteios:</span>
                  <span className="font-mono">{analysis.ml_analysis.advanced_stats.corners_expected.toFixed(1)}</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Market Tabs */}
      <div className="bg-bg-card rounded-xl">
        <div className="flex border-b border-border-subtle">
          {[
            { id: 'all', label: 'Todos os Mercados', icon: Target },
            { id: 'value', label: 'Melhor Valor', icon: DollarSign },
            { id: 'safe', label: 'Mais Seguros', icon: Shield },
            { id: 'high_odds', label: 'Odds Altas', icon: TrendingUp }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-6 py-4 border-b-2 transition-all ${
                activeTab === tab.id
                  ? 'border-primary-600 text-primary-400'
                  : 'border-transparent text-text-secondary hover:text-text-primary'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
              <span className="text-xs bg-bg-secondary px-2 py-1 rounded-full">
                {getMarketsForTab().length}
              </span>
            </button>
          ))}
        </div>

        <div className="p-6">
          <div className="grid gap-4">
            {getMarketsForTab().map(renderMarketCard)}
          </div>

          {getMarketsForTab().length === 0 && (
            <div className="text-center py-8">
              <AlertTriangle className="w-12 h-12 text-text-tertiary mx-auto mb-3" />
              <h4 className="text-lg font-medium text-text-primary mb-2">
                Nenhum mercado encontrado
              </h4>
              <p className="text-text-secondary">
                Não há mercados disponíveis para os critérios selecionados.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};