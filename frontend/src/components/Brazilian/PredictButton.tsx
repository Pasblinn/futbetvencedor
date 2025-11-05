import React, { useState } from 'react';
import {
  Brain,
  TrendingUp,
  Target,
  Zap,
  CheckCircle,
  AlertTriangle,
  Filter,
  Layers,
  BarChart3
} from 'lucide-react';
import { brazilianFootballAPI, BrazilianMatch, AdvancedPrediction } from '../../services/brazilianFootballAPI';
import { advancedPredictionEngine, SuperPrediction } from '../../services/advancedPredictionEngine';

interface PredictButtonProps {
  match: BrazilianMatch;
  onPredictionGenerated?: (prediction: AdvancedPrediction) => void;
}

type BetType = 'simples' | 'dupla' | 'tripla';
type OddsFilter = 1.5 | 3.0;

interface BettingStrategy {
  type: BetType;
  minOdd: OddsFilter;
  confidence: number;
  selections: string[];
}

const PredictButton: React.FC<PredictButtonProps> = ({ match, onPredictionGenerated }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [prediction, setPrediction] = useState<AdvancedPrediction | null>(null);
  const [superPrediction, setSuperPrediction] = useState<SuperPrediction | null>(null);
  const [useAdvancedEngine, setUseAdvancedEngine] = useState(true);
  const [selectedBetType, setSelectedBetType] = useState<BetType>('simples');
  const [selectedOdds, setSelectedOdds] = useState<OddsFilter>(1.5);
  const [strategy, setStrategy] = useState<BettingStrategy | null>(null);

  const generatePrediction = async () => {
    setLoading(true);
    try {
      console.log(`🎯 Gerando predição ${useAdvancedEngine ? 'AVANÇADA' : 'padrão'} para ${match.homeTeam.shortName} x ${match.awayTeam.shortName}`);

      if (useAdvancedEngine) {
        // Usar o novo engine avançado
        const superPred = advancedPredictionEngine.generateSuperPrediction(match);
        setSuperPrediction(superPred);

        // Converter para formato compatível
        const advancedPrediction = convertSuperToAdvanced(superPred, match);
        setPrediction(advancedPrediction);

        // Gerar estratégia baseada no super prediction
        const bettingStrategy = generateAdvancedBettingStrategy(superPred, selectedBetType, selectedOdds);
        setStrategy(bettingStrategy);

        if (onPredictionGenerated) {
          onPredictionGenerated(advancedPrediction);
        }
      } else {
        // Usar engine padrão
        const advancedPrediction = await brazilianFootballAPI.generateAdvancedPrediction(match);
        setPrediction(advancedPrediction);

        const bettingStrategy = generateBettingStrategy(advancedPrediction, selectedBetType, selectedOdds);
        setStrategy(bettingStrategy);

        if (onPredictionGenerated) {
          onPredictionGenerated(advancedPrediction);
        }
      }
    } catch (error) {
      console.error('Erro ao gerar predição:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateBettingStrategy = (pred: AdvancedPrediction, type: BetType, minOdd: OddsFilter): BettingStrategy => {
    const selections = [];

    // Seleção principal baseada na predição
    const mainOutcome = pred.analysis.outcome.prediction === '1' ?
      `${pred.homeTeam} vence` :
      pred.analysis.outcome.prediction === 'X' ? 'Empate' :
      `${pred.awayTeam} vence`;

    selections.push(mainOutcome);

    // Para dupla e tripla, adicionar mercados complementares
    if (type === 'dupla' || type === 'tripla') {
      // Adicionar Over/Under 2.5
      const overUnder = pred.analysis.markets.overUnder25.prediction === 'over' ?
        'Mais de 2.5 gols' : 'Menos de 2.5 gols';
      selections.push(overUnder);
    }

    if (type === 'tripla') {
      // Adicionar Both Teams Score
      const btts = pred.analysis.markets.bothTeamsScore.prediction === 'yes' ?
        'Ambos marcam' : 'Nem ambos marcam';
      selections.push(btts);
    }

    return {
      type,
      minOdd,
      confidence: pred.analysis.outcome.confidence,
      selections
    };
  };

  const convertSuperToAdvanced = (superPred: SuperPrediction, match: BrazilianMatch): AdvancedPrediction => {
    const outcome = superPred.ensemble_outcome.home_win > superPred.ensemble_outcome.away_win ?
      (superPred.ensemble_outcome.home_win > superPred.ensemble_outcome.draw ? '1' : 'X') :
      (superPred.ensemble_outcome.away_win > superPred.ensemble_outcome.draw ? '2' : 'X');

    // Cálculos otimizados para mercados baseados em xG
    const homeXG = superPred.ensemble_outcome.home_win * 2.1;
    const awayXG = superPred.ensemble_outcome.away_win * 1.8;
    const totalXG = homeXG + awayXG;

    // Over/Under 2.5 otimizado com distribuição de Poisson
    const overProb = 1 - Math.exp(-totalXG) * (1 + totalXG + Math.pow(totalXG, 2) / 2);

    // Both Teams Score baseado em eficiência ofensiva
    const homeScoreProb = 1 - Math.exp(-homeXG);
    const awayScoreProb = 1 - Math.exp(-awayXG);
    const bttsProb = homeScoreProb * awayScoreProb;

    // Asian Handicap dinâmico baseado na diferença de força
    const strengthDiff = superPred.ensemble_outcome.home_win - superPred.ensemble_outcome.away_win;
    const handicapLine = strengthDiff > 0.2 ? -0.5 : strengthDiff < -0.2 ? 0.5 : 0;

    // Escanteios baseados em pressão ofensiva
    const cornersXG = (homeXG + awayXG) * 3.2;
    const cornersLine = Math.round(cornersXG * 10) / 10;

    return {
      matchId: match.id,
      competition: match.competition,
      homeTeam: match.homeTeam.shortName,
      awayTeam: match.awayTeam.shortName,
      analysis: {
        outcome: {
          prediction: outcome as any,
          confidence: superPred.ensemble_outcome.confidence,
          probability: {
            home: superPred.ensemble_outcome.home_win,
            draw: superPred.ensemble_outcome.draw,
            away: superPred.ensemble_outcome.away_win
          }
        },
        markets: {
          overUnder25: {
            prediction: overProb > 0.5 ? 'over' : 'under',
            probability: overProb > 0.5 ? overProb : 1 - overProb,
            confidence: Math.round(Math.abs(overProb - 0.5) * 200)
          },
          bothTeamsScore: {
            prediction: bttsProb > 0.5 ? 'yes' : 'no',
            probability: bttsProb > 0.5 ? bttsProb : 1 - bttsProb,
            confidence: Math.round(Math.abs(bttsProb - 0.5) * 200)
          },
          asianHandicap: {
            line: handicapLine,
            prediction: strengthDiff > 0 ? 'home' : 'away',
            probability: Math.max(superPred.ensemble_outcome.home_win, superPred.ensemble_outcome.away_win),
            confidence: superPred.ensemble_outcome.confidence
          },
          corners: {
            prediction: cornersXG > 9.5 ? 'over' : 'under',
            line: cornersLine,
            probability: cornersXG > 9.5 ? 0.65 : 0.55
          }
        },
        recommendedOdds: {
          minOdd: 1.4 + (superPred.ensemble_outcome.consensus_strength / 100) * 0.6,
          maxOdd: 4.0 - (superPred.ensemble_outcome.consensus_strength / 100) * 1.5,
          valueOdds: [
            Math.round((1 / superPred.ensemble_outcome.home_win) * 0.9 * 100) / 100,
            Math.round((1 / superPred.ensemble_outcome.draw) * 0.85 * 100) / 100,
            Math.round((1 / superPred.ensemble_outcome.away_win) * 0.9 * 100) / 100
          ]
        },
        keyFactors: superPred.key_insights.value_opportunities || [],
        risks: superPred.key_insights.risk_factors || [],
        reasoning: superPred.key_insights.primary_factor,
        supportingData: {
          h2hRecord: {
            homeWins: Math.round(homeXG),
            draws: Math.round(Math.min(homeXG, awayXG)),
            awayWins: Math.round(awayXG),
            avgGoalsHome: Math.round(homeXG * 100) / 100,
            avgGoalsAway: Math.round(awayXG * 100) / 100
          },
          formComparison: {
            homeForm: Math.round(superPred.ensemble_outcome.home_win * 100),
            awayForm: Math.round(superPred.ensemble_outcome.away_win * 100),
            formDifference: Math.round(strengthDiff * 100)
          },
          strengthAnalysis: {
            homeStrength: Math.round((superPred.ensemble_outcome.home_win * 0.6 + 0.4) * 100),
            awayStrength: Math.round((superPred.ensemble_outcome.away_win * 0.6 + 0.4) * 100),
            homeAdvantage: Math.round(superPred.ensemble_outcome.consensus_strength / 10)
          }
        }
      },
      dataQuality: {
        completeness: superPred.prediction_quality.feature_completeness * 100,
        recency: 92 + (superPred.prediction_quality.model_agreement * 8),
        reliability: superPred.prediction_quality.historical_accuracy * 100
      },
      generatedAt: new Date().toISOString(),
      validUntil: new Date(Date.now() + 3 * 60 * 60 * 1000).toISOString()
    };
  };

  const generateAdvancedBettingStrategy = (superPred: SuperPrediction, type: BetType, minOdd: OddsFilter): BettingStrategy => {
    const selections = [];
    const confidence = superPred.ensemble_outcome.confidence;
    const consensusStrength = superPred.ensemble_outcome.consensus_strength;

    // Estratégia principal baseada em maior probabilidade e consenso
    const primaryBet = superPred.betting_strategy.primary_bet;
    const enhancedPrimary = `${primaryBet.selection} (${primaryBet.market}) - Confiança: ${confidence}%`;
    selections.push(enhancedPrimary);

    if (type === 'dupla' || type === 'tripla') {
      // Hedge inteligente baseado em correlação
      const homeWin = superPred.ensemble_outcome.home_win;
      const awayWin = superPred.ensemble_outcome.away_win;
      const draw = superPred.ensemble_outcome.draw;

      // Selecionar hedge com menor correlação
      if (Math.max(homeWin, awayWin, draw) === homeWin && homeWin > 0.5) {
        // Se casa favorita, hedge com Over ou BTTS
        const overProb = homeWin * 0.7 + awayWin * 0.6;
        selections.push(`${overProb > 0.55 ? 'Over 2.5' : 'Under 2.5'} gols (Total de Gols)`);
      } else if (Math.max(homeWin, awayWin, draw) === awayWin) {
        // Se visitante favorito, hedge conservador
        selections.push('Dupla chance X2 (Resultado)');
      } else {
        // Se empate provável, hedge com gols
        selections.push('Ambos marcam SIM (Gols)');
      }

      // Adicionar hedge dos hedge_bets se disponível
      superPred.betting_strategy.hedge_bets.slice(0, 1).forEach(hedge => {
        if (selections.length < (type === 'dupla' ? 2 : 3)) {
          selections.push(`${hedge.selection} (${hedge.market}) - Peso: ${(hedge.weight * 100).toFixed(0)}%`);
        }
      });
    }

    if (type === 'tripla' && selections.length < 3) {
      // Terceira seleção baseada em analytics avançados
      const totalXG = superPred.ensemble_outcome.home_win * 2.1 + superPred.ensemble_outcome.away_win * 1.8;
      if (totalXG > 2.3) {
        selections.push('Over 1.5 gols HT (Primeiro Tempo)');
      } else {
        selections.push('Menos de 3.5 escanteios (Escanteios)');
      }
    }

    // Calcular confiança ajustada por tipo de aposta
    const adjustedConfidence = type === 'simples' ? confidence :
                              type === 'dupla' ? confidence * 0.8 :
                              confidence * 0.65;

    return {
      type,
      minOdd,
      confidence: Math.round(adjustedConfidence),
      selections: selections.slice(0, type === 'simples' ? 1 : type === 'dupla' ? 2 : 3)
    };
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return 'text-green-600 bg-green-50';
    if (confidence >= 65) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  const getCompetitionEmoji = (competition: string) => {
    switch (competition) {
      case 'brasileirao': return '🏆';
      case 'copa_brasil': return '🏅';
      case 'libertadores': return '🌎';
      default: return '⚽';
    }
  };

  const formatOdd = (odd: number) => odd.toFixed(2);

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="group relative bg-gradient-to-r from-green-500 to-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:from-green-600 hover:to-blue-700 transition-all duration-300 shadow-lg hover:shadow-xl transform hover:-translate-y-1"
      >
        <div className="flex items-center space-x-2">
          <Brain className="w-5 h-5" />
          <span>Predict</span>
          <TrendingUp className="w-4 h-4 opacity-75" />
        </div>
        <div className="absolute -top-2 -right-2 bg-yellow-500 text-black text-xs px-2 py-1 rounded-full font-bold">
          BR
        </div>
      </button>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="bg-gradient-to-r from-green-600 to-blue-600 text-white p-6 rounded-t-xl">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold flex items-center space-x-2">
                <span>{getCompetitionEmoji(match.competition)}</span>
                <span>Predição Avançada</span>
              </h2>
              <p className="text-green-100 mt-1">
                {match.homeTeam.shortName} vs {match.awayTeam.shortName} • {match.competition.toUpperCase()}
              </p>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="text-white hover:text-gray-200 text-2xl font-bold"
            >
              ×
            </button>
          </div>
        </div>

        <div className="p-6">
          {/* Configuração de Aposta */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            {/* Tipo de Aposta */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-3">
                <Layers className="w-4 h-4 inline mr-2" />
                Tipo de Aposta
              </label>
              <div className="grid grid-cols-3 gap-2">
                {(['simples', 'dupla', 'tripla'] as BetType[]).map((type) => (
                  <button
                    key={type}
                    onClick={() => setSelectedBetType(type)}
                    className={`p-3 rounded-lg border-2 transition-all ${
                      selectedBetType === type
                        ? 'border-blue-500 bg-blue-50 text-blue-700'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="text-center">
                      <div className="font-semibold capitalize">{type}</div>
                      <div className="text-xs text-gray-500 mt-1">
                        {type === 'simples' && '1 seleção'}
                        {type === 'dupla' && '2 seleções'}
                        {type === 'tripla' && '3 seleções'}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Filtro de Odds */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-3">
                <Filter className="w-4 h-4 inline mr-2" />
                Odds Mínimas
              </label>
              <div className="grid grid-cols-2 gap-2">
                {([1.5, 3.0] as OddsFilter[]).map((odd) => (
                  <button
                    key={odd}
                    onClick={() => setSelectedOdds(odd)}
                    className={`p-3 rounded-lg border-2 transition-all ${
                      selectedOdds === odd
                        ? 'border-green-500 bg-green-50 text-green-700'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="text-center">
                      <div className="font-bold text-lg">{odd}+</div>
                      <div className="text-xs text-gray-500">
                        {odd === 1.5 ? 'Conservador' : 'Arrojado'}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Botão Gerar */}
          <div className="text-center mb-6">
            <button
              onClick={generatePrediction}
              disabled={loading}
              className="bg-gradient-to-r from-green-500 to-blue-600 text-white px-8 py-4 rounded-lg font-bold text-lg hover:from-green-600 hover:to-blue-700 transition-all duration-300 shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  <span>Analisando...</span>
                </div>
              ) : (
                <div className="flex items-center space-x-2">
                  <Brain className="w-5 h-5" />
                  <span>Gerar Predição IA</span>
                  <Target className="w-5 h-5" />
                </div>
              )}
            </button>
          </div>

          {/* Resultados */}
          {prediction && strategy && (
            <div className="space-y-6">
              {/* Estratégia de Aposta */}
              <div className="bg-gradient-to-r from-blue-50 to-green-50 border border-blue-200 rounded-lg p-6">
                <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
                  <Zap className="w-5 h-5 text-blue-600 mr-2" />
                  Estratégia Recomendada
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">{strategy.type.toUpperCase()}</div>
                    <div className="text-sm text-gray-600">Tipo de Aposta</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">{strategy.minOdd}+</div>
                    <div className="text-sm text-gray-600">Odds Mínimas</div>
                  </div>
                  <div className="text-center">
                    <div className={`text-2xl font-bold px-3 py-1 rounded-full ${getConfidenceColor(strategy.confidence)}`}>
                      {strategy.confidence}%
                    </div>
                    <div className="text-sm text-gray-600">Confiança</div>
                  </div>
                </div>

                <div className="bg-white rounded-lg p-4">
                  <h4 className="font-semibold text-gray-700 mb-2">Seleções:</h4>
                  <div className="space-y-2">
                    {strategy.selections.map((selection, index) => (
                      <div key={index} className="flex items-center space-x-2">
                        <CheckCircle className="w-4 h-4 text-green-500" />
                        <span>{selection}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Análise Detalhada */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Predição Principal */}
                <div className="bg-white border border-gray-200 rounded-lg p-6">
                  <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center">
                    <Target className="w-5 h-5 text-red-500 mr-2" />
                    Predição Principal
                  </h3>

                  <div className="text-center mb-4">
                    <div className="text-3xl font-bold text-blue-600 mb-2">
                      {prediction.analysis.outcome.prediction === '1' && prediction.homeTeam}
                      {prediction.analysis.outcome.prediction === 'X' && 'EMPATE'}
                      {prediction.analysis.outcome.prediction === '2' && prediction.awayTeam}
                    </div>
                    <div className={`inline-block px-4 py-2 rounded-full ${getConfidenceColor(prediction.analysis.outcome.confidence)}`}>
                      {prediction.analysis.outcome.confidence}% de confiança
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>Vitória {prediction.homeTeam}:</span>
                      <span className="font-semibold">{(prediction.analysis.outcome.probability.home * 100).toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Empate:</span>
                      <span className="font-semibold">{(prediction.analysis.outcome.probability.draw * 100).toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Vitória {prediction.awayTeam}:</span>
                      <span className="font-semibold">{(prediction.analysis.outcome.probability.away * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                </div>

                {/* Mercados Específicos */}
                <div className="bg-white border border-gray-200 rounded-lg p-6">
                  <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center">
                    <BarChart3 className="w-5 h-5 text-purple-500 mr-2" />
                    Mercados
                  </h3>

                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Over/Under 2.5:</span>
                      <span className={`px-2 py-1 rounded text-sm font-semibold ${
                        prediction.analysis.markets.overUnder25.prediction === 'over'
                          ? 'bg-red-100 text-red-700'
                          : 'bg-blue-100 text-blue-700'
                      }`}>
                        {prediction.analysis.markets.overUnder25.prediction === 'over' ? 'OVER' : 'UNDER'}
                      </span>
                    </div>

                    <div className="flex justify-between items-center">
                      <span className="text-sm">Ambos Marcam:</span>
                      <span className={`px-2 py-1 rounded text-sm font-semibold ${
                        prediction.analysis.markets.bothTeamsScore.prediction === 'yes'
                          ? 'bg-green-100 text-green-700'
                          : 'bg-gray-100 text-gray-700'
                      }`}>
                        {prediction.analysis.markets.bothTeamsScore.prediction === 'yes' ? 'SIM' : 'NÃO'}
                      </span>
                    </div>

                    <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
                      <div className="flex items-center space-x-2 text-yellow-800">
                        <AlertTriangle className="w-4 h-4" />
                        <span className="text-sm font-semibold">Odds Recomendadas:</span>
                      </div>
                      <div className="text-sm text-yellow-700 mt-1">
                        Entre {formatOdd(prediction.analysis.recommendedOdds.minOdd)} e {formatOdd(prediction.analysis.recommendedOdds.maxOdd)}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Fatores-Chave */}
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h3 className="text-lg font-bold text-gray-800 mb-4">Fatores-Chave da Análise</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <h4 className="font-semibold text-green-700 mb-2">Pontos Fortes:</h4>
                    <ul className="space-y-1">
                      {prediction.analysis.keyFactors.map((factor, index) => (
                        <li key={index} className="text-sm flex items-start space-x-2">
                          <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                          <span>{factor}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h4 className="font-semibold text-red-700 mb-2">Riscos:</h4>
                    <ul className="space-y-1">
                      {prediction.analysis.risks.map((risk, index) => (
                        <li key={index} className="text-sm flex items-start space-x-2">
                          <AlertTriangle className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" />
                          <span>{risk}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>

              {/* Explicação */}
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
                <h3 className="text-lg font-bold text-gray-800 mb-3">Explicação da Análise</h3>
                <p className="text-gray-700 leading-relaxed">{prediction.analysis.reasoning}</p>

                <div className="mt-4 flex items-center justify-between text-sm text-gray-500">
                  <span>Gerado em: {new Date(prediction.generatedAt).toLocaleString('pt-BR')}</span>
                  <span>Qualidade dos dados: {prediction.dataQuality.reliability}%</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PredictButton;