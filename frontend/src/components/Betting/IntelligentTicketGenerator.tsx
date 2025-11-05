import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Brain,
  Zap,
  Shield,
  TrendingUp,
  DollarSign,
  Target,
  AlertTriangle,
  CheckCircle,
  BarChart3,
  Download,
  RefreshCw,
  Sparkles
} from 'lucide-react';
import { IntelligentTicket, TICKET_STRATEGIES } from '../../types/betting';
import { mlBettingService } from '../../services/mlBetting';

interface IntelligentTicketGeneratorProps {
  availableMatches: any[];
  bankroll: number;
  onTicketGenerated: (ticket: IntelligentTicket) => void;
}

export const IntelligentTicketGenerator: React.FC<IntelligentTicketGeneratorProps> = ({
  availableMatches,
  bankroll,
  onTicketGenerated
}) => {
  const [selectedStrategy, setSelectedStrategy] = useState<keyof typeof TICKET_STRATEGIES>('balanced');
  const [selectedMatches, setSelectedMatches] = useState<string[]>([]);
  const [generating, setGenerating] = useState(false);
  const [generatedTicket, setGeneratedTicket] = useState<IntelligentTicket | null>(null);
  const [showAnalysis, setShowAnalysis] = useState(false);

  const handleGenerateTicket = async () => {
    if (selectedMatches.length === 0) {
      alert('Selecione pelo menos uma partida');
      return;
    }

    if (bankroll <= 0) {
      alert('Configure um valor de bankroll válido');
      return;
    }

    setGenerating(true);
    try {
      const ticket = await mlBettingService.generateIntelligentTicket(
        selectedMatches,
        selectedStrategy,
        bankroll
      );

      setGeneratedTicket(ticket);
      setShowAnalysis(true);
      onTicketGenerated(ticket);
    } catch (error) {
      console.error('Erro ao gerar bilhete:', error);
      alert('Erro ao gerar bilhete inteligente');
    } finally {
      setGenerating(false);
    }
  };

  const getStrategyColor = (strategy: keyof typeof TICKET_STRATEGIES) => {
    switch (strategy) {
      case 'conservative': return 'from-green-500 to-green-600';
      case 'balanced': return 'from-blue-500 to-blue-600';
      case 'aggressive': return 'from-red-500 to-red-600';
      case 'value': return 'from-yellow-500 to-yellow-600';
      case 'combo': return 'from-purple-500 to-purple-600';
      default: return 'from-gray-500 to-gray-600';
    }
  };

  const getStrategyIcon = (strategy: keyof typeof TICKET_STRATEGIES) => {
    switch (strategy) {
      case 'conservative': return Shield;
      case 'balanced': return Target;
      case 'aggressive': return Zap;
      case 'value': return DollarSign;
      case 'combo': return Brain;
      default: return BarChart3;
    }
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low': return 'text-green-400 bg-green-400/20';
      case 'medium': return 'text-yellow-400 bg-yellow-400/20';
      case 'high': return 'text-red-400 bg-red-400/20';
      default: return 'text-gray-400 bg-gray-400/20';
    }
  };

  return (
    <div className="space-y-6">
      {/* Strategy Selection */}
      <div className="bg-bg-card rounded-lg border border-border-subtle p-6">
        <div className="flex items-center gap-3 mb-4">
          <Brain className="w-6 h-6 text-primary-400" />
          <h3 className="text-lg font-semibold text-text-primary">Gerador de Bilhetes Inteligentes</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
          {Object.entries(TICKET_STRATEGIES).map(([key, strategy]) => {
            const StrategyIcon = getStrategyIcon(key as keyof typeof TICKET_STRATEGIES);
            const isSelected = selectedStrategy === key;

            return (
              <motion.button
                key={key}
                onClick={() => setSelectedStrategy(key as keyof typeof TICKET_STRATEGIES)}
                className={`p-4 rounded-lg border-2 transition-all text-left ${
                  isSelected
                    ? 'border-primary-500 bg-primary-500/10'
                    : 'border-border-subtle hover:border-border-primary hover:bg-bg-secondary'
                }`}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <div className="flex items-center gap-3 mb-2">
                  <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${getStrategyColor(key as keyof typeof TICKET_STRATEGIES)} flex items-center justify-center`}>
                    <StrategyIcon className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-text-primary">{strategy.name}</h4>
                    <p className="text-xs text-text-secondary">
                      Odds até {strategy.max_odds}x
                    </p>
                  </div>
                </div>
                <p className="text-sm text-text-secondary">{strategy.description}</p>

                <div className="mt-3 flex items-center gap-4 text-xs">
                  <span className="text-text-tertiary">
                    Max {strategy.max_selections} seleções
                  </span>
                  <span className="text-text-tertiary">
                    {(strategy.bankroll_percentage * 100).toFixed(1)}% banca
                  </span>
                </div>
              </motion.button>
            );
          })}
        </div>

        {/* Match Selection */}
        <div className="mb-6">
          <h4 className="font-medium text-text-primary mb-3">Selecionar Partidas</h4>
          <div className="grid gap-2 max-h-40 overflow-y-auto">
            {availableMatches.map((match) => {
              const isSelected = selectedMatches.includes(match.id);

              return (
                <label
                  key={match.id}
                  className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all ${
                    isSelected
                      ? 'border-primary-500 bg-primary-500/10'
                      : 'border-border-subtle hover:border-border-primary hover:bg-bg-secondary'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedMatches([...selectedMatches, match.id]);
                      } else {
                        setSelectedMatches(selectedMatches.filter(id => id !== match.id));
                      }
                    }}
                    className="rounded"
                  />
                  <div className="flex-1">
                    <div className="font-medium text-text-primary">
                      {match.homeTeam} vs {match.awayTeam}
                    </div>
                    <div className="text-sm text-text-secondary">
                      {match.league} • {match.time}
                    </div>
                  </div>
                  <div className="text-sm">
                    <span className="text-primary-400">{(match.confidence * 100).toFixed(0)}%</span>
                  </div>
                </label>
              );
            })}
          </div>

          {availableMatches.length === 0 && (
            <div className="text-center py-8">
              <AlertTriangle className="w-12 h-12 text-text-tertiary mx-auto mb-3" />
              <p className="text-text-secondary">Nenhuma partida disponível para análise</p>
            </div>
          )}
        </div>

        {/* Generate Button */}
        <button
          onClick={handleGenerateTicket}
          disabled={generating || selectedMatches.length === 0 || bankroll <= 0}
          className="w-full bg-gradient-to-r from-primary-600 to-primary-700 text-white py-3 px-6 rounded-lg hover:from-primary-700 hover:to-primary-800 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {generating ? (
            <RefreshCw className="w-5 h-5 animate-spin" />
          ) : (
            <Sparkles className="w-5 h-5" />
          )}
          {generating ? 'Analisando...' : 'Gerar Bilhete Inteligente'}
        </button>
      </div>

      {/* Generated Ticket Analysis */}
      <AnimatePresence>
        {generatedTicket && showAnalysis && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="bg-bg-card rounded-lg border border-border-subtle overflow-hidden"
          >
            {/* Header */}
            <div className="bg-gradient-to-r from-primary-600 to-primary-700 p-6 text-white">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Brain className="w-8 h-8" />
                  <div>
                    <h3 className="text-xl font-bold">Bilhete Inteligente Gerado</h3>
                    <p className="text-primary-200">
                      Estratégia: {TICKET_STRATEGIES[generatedTicket.ticket_type].name}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold">
                    R$ {generatedTicket.financial.potential_profit.toFixed(2)}
                  </div>
                  <div className="text-primary-200 text-sm">Lucro Potencial</div>
                </div>
              </div>
            </div>

            <div className="p-6">
              {/* Risk Analysis */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <div className="text-center">
                  <div className={`text-2xl font-bold px-3 py-1 rounded-lg ${getRiskColor(generatedTicket.risk_analysis.total_risk)}`}>
                    {generatedTicket.risk_analysis.total_risk.toUpperCase()}
                  </div>
                  <div className="text-sm text-text-secondary mt-1">Risco Total</div>
                </div>

                <div className="text-center">
                  <div className="text-2xl font-bold text-primary-400">
                    {generatedTicket.risk_analysis.expected_roi.toFixed(1)}%
                  </div>
                  <div className="text-sm text-text-secondary">ROI Esperado</div>
                </div>

                <div className="text-center">
                  <div className="text-2xl font-bold text-accent-400">
                    {(generatedTicket.risk_analysis.win_probability * 100).toFixed(1)}%
                  </div>
                  <div className="text-sm text-text-secondary">Prob. Vitória</div>
                </div>

                <div className="text-center">
                  <div className="text-2xl font-bold text-text-primary">
                    {generatedTicket.financial.total_odds.toFixed(2)}x
                  </div>
                  <div className="text-sm text-text-secondary">Odds Total</div>
                </div>
              </div>

              {/* Financial Summary */}
              <div className="bg-bg-secondary rounded-lg p-4 mb-6">
                <h4 className="font-semibold text-text-primary mb-3">💰 Resumo Financeiro</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-text-secondary">Stake Total:</span>
                    <div className="font-bold text-text-primary">
                      R$ {generatedTicket.financial.total_stake.toFixed(2)}
                    </div>
                  </div>
                  <div>
                    <span className="text-text-secondary">Odds:</span>
                    <div className="font-bold text-text-primary">
                      {generatedTicket.financial.total_odds.toFixed(2)}x
                    </div>
                  </div>
                  <div>
                    <span className="text-text-secondary">Retorno:</span>
                    <div className="font-bold text-primary-400">
                      R$ {generatedTicket.financial.potential_return.toFixed(2)}
                    </div>
                  </div>
                  <div>
                    <span className="text-text-secondary">Lucro:</span>
                    <div className="font-bold text-green-400">
                      R$ {generatedTicket.financial.potential_profit.toFixed(2)}
                    </div>
                  </div>
                </div>
              </div>

              {/* Selections */}
              <div className="mb-6">
                <h4 className="font-semibold text-text-primary mb-3">🎯 Seleções ({generatedTicket.selections.length})</h4>
                <div className="space-y-3">
                  {generatedTicket.selections.map((selection, index) => (
                    <div
                      key={index}
                      className="bg-bg-secondary rounded-lg p-4"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div>
                          <div className="font-medium text-text-primary">
                            {selection.match_info.home_team} vs {selection.match_info.away_team}
                          </div>
                          <div className="text-sm text-text-secondary">
                            {selection.match_info.league}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="font-bold text-primary-400">
                            R$ {selection.individual_stake.toFixed(2)}
                          </div>
                          <div className="text-sm text-text-secondary">Stake</div>
                        </div>
                      </div>

                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <span className="text-2xl">
                            {selection.market.type === '1X2' ? '🏆' :
                             selection.market.type === 'over_under' ? '⚽' :
                             selection.market.type === 'btts' ? '🎯' : '📊'}
                          </span>
                          <div>
                            <div className="font-medium text-text-primary">
                              {selection.market.name}
                            </div>
                            <div className="text-sm text-text-secondary">
                              {selection.selection.toUpperCase()}
                            </div>
                          </div>
                        </div>

                        <div className="text-right">
                          <div className="font-bold text-accent-400">
                            {selection.market.odds[selection.selection]?.toFixed(2) || '0.00'}x
                          </div>
                          <div className="text-sm text-text-secondary">
                            {(selection.market.confidence).toFixed(0)}% conf.
                          </div>
                        </div>
                      </div>

                      <div className="mt-2 text-xs text-text-tertiary">
                        {selection.reasoning}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Strategy Reasoning */}
              <div className="bg-bg-secondary rounded-lg p-4 mb-6">
                <h4 className="font-semibold text-text-primary mb-3">🧠 Raciocínio da Estratégia</h4>
                <div className="space-y-2">
                  {generatedTicket.strategy.reasoning.map((reason, index) => (
                    <div key={index} className="flex items-start gap-2">
                      <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                      <span className="text-sm text-text-secondary">{reason}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3">
                <button
                  onClick={() => setShowAnalysis(false)}
                  className="flex-1 bg-bg-secondary text-text-primary py-2 px-4 rounded-lg hover:bg-bg-tertiary transition-all"
                >
                  Fechar Análise
                </button>

                <button
                  className="flex-1 bg-accent-600 text-white py-2 px-4 rounded-lg hover:bg-accent-700 transition-all flex items-center justify-center gap-2"
                >
                  <Download className="w-4 h-4" />
                  Exportar Bilhete
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};