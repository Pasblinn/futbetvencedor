import React, { useState, useEffect } from 'react';
import {
  Play,
  Pause,
  RotateCcw,
  TrendingUp,
  Activity,
  Clock,
  Target,
  AlertCircle,
  Info
} from 'lucide-react';
import LivePredictionCard from '../Predictions/LivePredictionCard';
import { realTimePredictionService, RealTimePrediction } from '../../services/realTimePredictionService';
import { liveDataService, LiveMatch } from '../../services/liveDataService';

const PredictionExample: React.FC = () => {
  const [demoMatch, setDemoMatch] = useState<LiveMatch | null>(null);
  const [demoPrediction, setDemoPrediction] = useState<RealTimePrediction | null>(null);
  const [isSimulating, setIsSimulating] = useState(false);
  const [simulationStep, setSimulationStep] = useState(0);
  const [loading, setLoading] = useState(false);

  // Criar jogo demo
  const createDemoMatch = (): LiveMatch => {
    return {
      id: 'demo_match_001',
      homeTeam: {
        id: 1,
        name: 'Flamengo',
        logo: 'https://logos.com/flamengo.png',
        form: 'WWDLW'
      },
      awayTeam: {
        id: 2,
        name: 'Vasco',
        logo: 'https://logos.com/vasco.png',
        form: 'DLWDL'
      },
      league: {
        id: 71,
        name: 'Brasileirão Série A',
        country: 'Brazil',
        logo: 'https://logos.com/brasileirao.png',
        season: 2024
      },
      fixture: {
        date: new Date().toISOString().split('T')[0],
        time: '17:30',
        timestamp: Date.now() + 3600000,
        timezone: 'America/Sao_Paulo',
        venue: {
          name: 'Maracanã',
          city: 'Rio de Janeiro'
        },
        referee: 'Árbitro Silva'
      },
      status: {
        long: 'Not Started',
        short: 'NS',
        elapsed: null
      },
      odds: {
        home: 2.10,
        draw: 3.20,
        away: 3.50,
        source: 'Demo Bookmaker',
        lastUpdate: new Date().toISOString()
      }
    };
  };

  // Inicializar demo
  const initializeDemo = async () => {
    try {
      setLoading(true);

      const match = createDemoMatch();
      setDemoMatch(match);

      // Criar predição demo
      const prediction = await realTimePredictionService.createRealTimePrediction(match);
      setDemoPrediction(prediction);

    } catch (error) {
      console.error('Erro ao inicializar demo:', error);
    } finally {
      setLoading(false);
    }
  };

  // Simular jogo ao vivo
  const simulateLiveMatch = async () => {
    if (!demoMatch || !demoPrediction) return;

    const liveMatch: LiveMatch = {
      ...demoMatch,
      status: {
        long: 'First Half',
        short: '1H',
        elapsed: 25 + simulationStep * 10
      }
    };

    // Atualizar predição com dados "ao vivo"
    const updatedPrediction: RealTimePrediction = {
      ...demoPrediction,
      liveData: {
        ...demoPrediction.liveData,
        isLive: true,
        currentMinute: 25 + simulationStep * 10,
        currentScore: {
          home: simulationStep >= 2 ? 1 : 0,
          away: simulationStep >= 4 ? 1 : 0
        },
        momentum: {
          direction: simulationStep % 2 === 0 ? 'home' : 'away',
          strength: 0.3 + (simulationStep * 0.1),
          recentEvents: [
            `${25 + simulationStep * 10}': ${simulationStep % 2 === 0 ? 'Flamengo' : 'Vasco'} pressiona`,
            `${20 + simulationStep * 8}': Boa chance perdida`,
            `${15 + simulationStep * 5}': Cartão amarelo`
          ]
        },
        oddsMovement: {
          homeChange: (Math.random() - 0.5) * 0.2,
          drawChange: (Math.random() - 0.5) * 0.3,
          awayChange: (Math.random() - 0.5) * 0.2,
          trend: simulationStep > 3 ? 'volatile' : 'stable' as any
        }
      },
      updatedProbabilities: {
        homeWin: Math.max(0.2, Math.min(0.7, demoPrediction.prediction.probability.homeWin + (simulationStep * 0.05))),
        draw: Math.max(0.15, Math.min(0.4, demoPrediction.prediction.probability.draw - (simulationStep * 0.02))),
        awayWin: Math.max(0.15, Math.min(0.5, demoPrediction.prediction.probability.awayWin - (simulationStep * 0.03))),
        nextGoalHome: 0.6 + (simulationStep * 0.05),
        nextGoalAway: 0.4 - (simulationStep * 0.02)
      },
      alerts: {
        ...demoPrediction.alerts,
        momentum: [
          {
            type: simulationStep > 3 ? 'positive' : 'warning' as any,
            message: simulationStep > 3 ?
              'Flamengo dominando o jogo' :
              'Jogo equilibrado com pequenas variações',
            confidence: 0.75 + (simulationStep * 0.05)
          }
        ]
      }
    };

    setDemoMatch(liveMatch);
    setDemoPrediction(updatedPrediction);
  };

  // Controle da simulação
  useEffect(() => {
    let interval: NodeJS.Timeout;

    if (isSimulating && simulationStep < 8) {
      interval = setInterval(() => {
        setSimulationStep(prev => prev + 1);
        simulateLiveMatch();
      }, 3000); // Atualiza a cada 3 segundos
    } else if (simulationStep >= 8) {
      setIsSimulating(false);
    }

    return () => clearInterval(interval);
  }, [isSimulating, simulationStep]);

  // Reset simulação
  const resetSimulation = () => {
    setIsSimulating(false);
    setSimulationStep(0);
    initializeDemo();
  };

  // Inicializar ao montar
  useEffect(() => {
    initializeDemo();
  }, []);

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-4 flex items-center">
          <Target className="w-8 h-8 mr-3 text-primary-600" />
          Demo: Predições em Tempo Real
        </h1>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <div className="flex items-start space-x-3">
            <Info className="w-5 h-5 text-blue-600 mt-0.5" />
            <div>
              <h3 className="font-semibold text-blue-900 mb-2">Como Funciona</h3>
              <p className="text-blue-800 text-sm leading-relaxed">
                Esta demonstração mostra como nossas predições IA se adaptam em tempo real durante uma partida.
                Os algoritmos analisam constantemente: estatísticas dos times, momentum do jogo, movimento das odds,
                eventos ao vivo e muito mais. <strong>Clique em "Simular Jogo" para ver a magia acontecer!</strong>
              </p>
            </div>
          </div>
        </div>

        {/* Controles */}
        <div className="flex items-center space-x-4 mb-6">
          <button
            onClick={() => setIsSimulating(!isSimulating)}
            disabled={loading}
            className={`flex items-center px-6 py-3 rounded-lg font-medium transition-colors ${
              isSimulating
                ? 'bg-red-600 text-white hover:bg-red-700'
                : 'bg-primary-600 text-white hover:bg-primary-700'
            } disabled:opacity-50`}
          >
            {isSimulating ? (
              <>
                <Pause className="w-5 h-5 mr-2" />
                Pausar Simulação
              </>
            ) : (
              <>
                <Play className="w-5 h-5 mr-2" />
                {simulationStep > 0 ? 'Continuar' : 'Simular Jogo'}
              </>
            )}
          </button>

          <button
            onClick={resetSimulation}
            disabled={loading}
            className="flex items-center px-4 py-3 rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50 disabled:opacity-50"
          >
            <RotateCcw className="w-5 h-5 mr-2" />
            Reset
          </button>

          <div className="flex items-center space-x-3 text-sm text-slate-600">
            <div className="flex items-center">
              <Activity className="w-4 h-4 mr-1" />
              Status: {isSimulating ? 'Simulando' : 'Pausado'}
            </div>
            <div className="flex items-center">
              <Clock className="w-4 h-4 mr-1" />
              Passo: {simulationStep}/8
            </div>
          </div>
        </div>

        {/* Indicadores da Simulação */}
        {simulationStep > 0 && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-semibold text-green-900">Simulação Ativa</h4>
                <p className="text-green-700 text-sm">
                  Minuto {25 + simulationStep * 10} - Observe como as probabilidades se ajustam dinamicamente
                </p>
              </div>
              <div className="flex items-center space-x-4 text-sm">
                <div className="text-green-700">
                  <strong>Eventos:</strong> {simulationStep * 2}
                </div>
                <div className="text-green-700">
                  <strong>Atualizações:</strong> {simulationStep}
                </div>
              </div>
            </div>

            {/* Progress Bar */}
            <div className="mt-3">
              <div className="w-full bg-green-200 rounded-full h-2">
                <div
                  className="bg-green-600 h-2 rounded-full transition-all duration-1000"
                  style={{ width: `${(simulationStep / 8) * 100}%` }}
                ></div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Predição Card */}
      {loading && (
        <div className="text-center py-12">
          <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Activity className="w-8 h-8 text-primary-600 animate-spin" />
          </div>
          <h3 className="text-lg font-semibold text-slate-900 mb-2">Gerando Predição Demo...</h3>
          <p className="text-slate-600">Criando análise IA para o clássico Fla x Vasco</p>
        </div>
      )}

      {demoMatch && demoPrediction && !loading && (
        <div className="space-y-6">
          <LivePredictionCard
            match={demoMatch}
            prediction={demoPrediction}
            onRefresh={() => simulateLiveMatch()}
            loading={false}
            showAdvanced={true}
          />

          {/* Explicações */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">
            <div className="bg-white p-6 rounded-lg border">
              <h3 className="text-lg font-semibold text-slate-900 mb-3 flex items-center">
                <TrendingUp className="w-5 h-5 mr-2 text-success-600" />
                Análise IA em Ação
              </h3>
              <div className="space-y-3 text-sm text-slate-600">
                <div className="flex items-start space-x-2">
                  <div className="w-2 h-2 bg-primary-500 rounded-full mt-2"></div>
                  <p><strong>Forma dos Times:</strong> Últimos 5 jogos, estatísticas H2H</p>
                </div>
                <div className="flex items-start space-x-2">
                  <div className="w-2 h-2 bg-primary-500 rounded-full mt-2"></div>
                  <p><strong>Lesões & Suspensões:</strong> Impacto de jogadores ausentes</p>
                </div>
                <div className="flex items-start space-x-2">
                  <div className="w-2 h-2 bg-primary-500 rounded-full mt-2"></div>
                  <p><strong>Contexto:</strong> Importância do jogo, clima, árbitro</p>
                </div>
                <div className="flex items-start space-x-2">
                  <div className="w-2 h-2 bg-red-500 rounded-full mt-2"></div>
                  <p><strong>Tempo Real:</strong> Momentum, eventos, movimento de odds</p>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg border">
              <h3 className="text-lg font-semibold text-slate-900 mb-3 flex items-center">
                <AlertCircle className="w-5 h-5 mr-2 text-warning-600" />
                Recursos Avançados
              </h3>
              <div className="space-y-3 text-sm text-slate-600">
                <div className="flex items-start space-x-2">
                  <div className="w-2 h-2 bg-success-500 rounded-full mt-2"></div>
                  <p><strong>Oportunidades de Valor:</strong> Odds com valor estatístico</p>
                </div>
                <div className="flex items-start space-x-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                  <p><strong>Mercados Ao Vivo:</strong> Próximo gol, cartões, tempo</p>
                </div>
                <div className="flex items-start space-x-2">
                  <div className="w-2 h-2 bg-purple-500 rounded-full mt-2"></div>
                  <p><strong>Alertas Inteligentes:</strong> Mudanças significativas</p>
                </div>
                <div className="flex items-start space-x-2">
                  <div className="w-2 h-2 bg-orange-500 rounded-full mt-2"></div>
                  <p><strong>Qualidade dos Dados:</strong> Confiabilidade da análise</p>
                </div>
              </div>
            </div>
          </div>

          {/* Nota Final */}
          <div className="bg-slate-50 border border-slate-200 rounded-lg p-6 text-center">
            <h4 className="text-lg font-semibold text-slate-900 mb-2">🎓 Projeto Educativo</h4>
            <p className="text-slate-600 leading-relaxed">
              Esta demonstração ilustra como APIs modernas e algoritmos de IA podem ser combinados para criar
              experiências interativas em tempo real. O sistema integra múltiplas fontes de dados, processa
              informações complexas e apresenta insights de forma clara e acionável.
            </p>
            <div className="mt-4 flex items-center justify-center space-x-8 text-sm text-slate-500">
              <span>⚡ Real-time APIs</span>
              <span>🤖 Machine Learning</span>
              <span>📊 Data Processing</span>
              <span>🎯 User Experience</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PredictionExample;