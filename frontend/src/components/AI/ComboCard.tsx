import React, { useState } from 'react';
import {
  Brain,
  TrendingUp,
  Shield,
  CheckCircle,
  AlertTriangle,
  Clock,
  Target,
  BarChart3,
  Info
} from 'lucide-react';
import { ComboRecommendation } from '../../services/aiAnalysisService';

interface ComboCardProps {
  combo: ComboRecommendation;
  onSelect?: (combo: ComboRecommendation) => void;
}

const ComboCard: React.FC<ComboCardProps> = ({ combo, onSelect }) => {
  const [showDetails, setShowDetails] = useState(false);

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel) {
      case 'low': return 'text-success-600 bg-success-50';
      case 'medium': return 'text-warning-600 bg-warning-50';
      case 'high': return 'text-danger-600 bg-danger-50';
      default: return 'text-slate-600 bg-slate-50';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'text-success-700 bg-success-100';
    if (confidence >= 0.8) return 'text-success-600 bg-success-50';
    if (confidence >= 0.7) return 'text-warning-600 bg-warning-50';
    return 'text-danger-600 bg-danger-50';
  };

  const formatOdds = (odds: number) => odds.toFixed(2);
  const formatConfidence = (confidence: number) => `${(confidence * 100).toFixed(1)}%`;
  const formatEV = (ev: number) => `${(ev * 100).toFixed(1)}%`;

  return (
    <div className="card p-6 card-hover">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
            <Brain className="w-5 h-5 text-primary-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-slate-900">
              {combo.type === 'double' ? 'Dupla' : 'Tripla'} IA
            </h3>
            <p className="text-sm text-slate-600">
              {combo.matches.length} jogos • Odds {formatOdds(combo.totalOdds)}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getRiskColor(combo.riskLevel)}`}>
            <Shield className="w-3 h-3 mr-1" />
            {combo.riskLevel === 'low' ? 'Baixo Risco' : combo.riskLevel === 'medium' ? 'Médio Risco' : 'Alto Risco'}
          </span>
        </div>
      </div>

      {/* Métricas principais */}
      <div className="grid grid-cols-3 gap-4 mb-4">
        <div className="text-center">
          <div className={`inline-flex items-center px-3 py-1 rounded-lg text-sm font-medium ${getConfidenceColor(combo.confidence)}`}>
            <Target className="w-4 h-4 mr-1" />
            {formatConfidence(combo.confidence)}
          </div>
          <p className="text-xs text-slate-500 mt-1">Confiança</p>
        </div>

        <div className="text-center">
          <div className="inline-flex items-center px-3 py-1 rounded-lg text-sm font-medium text-primary-700 bg-primary-100">
            <TrendingUp className="w-4 h-4 mr-1" />
            {formatEV(combo.expectedValue)}
          </div>
          <p className="text-xs text-slate-500 mt-1">Valor Esperado</p>
        </div>

        <div className="text-center">
          <div className="inline-flex items-center px-3 py-1 rounded-lg text-sm font-medium text-slate-700 bg-slate-100">
            <BarChart3 className="w-4 h-4 mr-1" />
            {formatOdds(combo.totalOdds)}
          </div>
          <p className="text-xs text-slate-500 mt-1">Odds Total</p>
        </div>
      </div>

      {/* Mercados */}
      <div className="space-y-2 mb-4">
        <h4 className="text-sm font-medium text-slate-900">Mercados Selecionados:</h4>
        {combo.markets.map((market, index) => (
          <div key={index} className="flex items-center justify-between p-2 bg-slate-50 rounded-lg">
            <span className="text-sm text-slate-700">{market.name}</span>
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium text-slate-900">{formatOdds(market.odds)}</span>
              <span className="text-xs text-slate-500">({formatConfidence(market.confidence)})</span>
            </div>
          </div>
        ))}
      </div>

      {/* Validações */}
      <div className="mb-4">
        <h4 className="text-sm font-medium text-slate-900 mb-2">Validações em Tempo Real:</h4>
        <div className="grid grid-cols-2 gap-2">
          <div className="flex items-center space-x-2">
            {combo.validationChecks.oddsStable ? (
              <CheckCircle className="w-4 h-4 text-success-500" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-warning-500" />
            )}
            <span className="text-xs text-slate-600">Odds Estáveis</span>
          </div>

          <div className="flex items-center space-x-2">
            {combo.validationChecks.lineupsConfirmed ? (
              <CheckCircle className="w-4 h-4 text-success-500" />
            ) : (
              <Clock className="w-4 h-4 text-warning-500" />
            )}
            <span className="text-xs text-slate-600">Escalações</span>
          </div>

          <div className="flex items-center space-x-2">
            {combo.validationChecks.noMajorInjuries ? (
              <CheckCircle className="w-4 h-4 text-success-500" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-danger-500" />
            )}
            <span className="text-xs text-slate-600">Sem Lesões</span>
          </div>

          <div className="flex items-center space-x-2">
            {combo.validationChecks.weatherOk ? (
              <CheckCircle className="w-4 h-4 text-success-500" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-warning-500" />
            )}
            <span className="text-xs text-slate-600">Clima OK</span>
          </div>
        </div>
      </div>

      {/* Reasoning */}
      <div className="mb-4">
        <button
          onClick={() => setShowDetails(!showDetails)}
          className="flex items-center space-x-2 text-sm text-primary-600 hover:text-primary-700"
        >
          <Info className="w-4 h-4" />
          <span>{showDetails ? 'Ocultar' : 'Ver'} Análise Detalhada</span>
        </button>

        {showDetails && (
          <div className="mt-3 p-3 bg-primary-50 rounded-lg">
            <p className="text-sm text-slate-700 mb-2">{combo.reasoning}</p>
            <div className="text-xs text-slate-500">
              <strong>Fontes:</strong> {combo.sources.join(', ')}
            </div>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between pt-4 border-t border-slate-200">
        <div className="text-xs text-slate-500">
          Atualizado há {Math.floor(Math.random() * 5) + 1} min
        </div>

        <div className="flex items-center space-x-2">
          <button className="btn-secondary text-xs px-3 py-1">
            Analisar
          </button>
          <button
            onClick={() => onSelect?.(combo)}
            className="btn-primary text-xs px-3 py-1"
          >
            Selecionar
          </button>
        </div>
      </div>

      {/* Warning */}
      {combo.confidence < 0.8 && (
        <div className="mt-3 p-2 bg-warning-50 border border-warning-200 rounded-lg">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-warning-600" />
            <span className="text-xs text-warning-700">
              Confiança abaixo de 80%. Validação extra recomendada.
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default ComboCard;