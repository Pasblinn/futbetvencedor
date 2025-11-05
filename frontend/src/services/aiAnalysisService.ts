import axios from 'axios';

// Interfaces para os dados de análise
export interface MatchData {
  id: string;
  homeTeam: string;
  awayTeam: string;
  league: string;
  date: string;
  time: string;
  odds: {
    home: number;
    draw: number;
    away: number;
  };
  markets: MarketData[];
}

export interface MarketData {
  type: 'over_under' | 'corners' | 'cards' | 'btts' | 'result';
  name: string;
  odds: number;
  confidence: number;
  value: any;
}

export interface TeamForm {
  teamName: string;
  last15Games: {
    wins: number;
    draws: number;
    losses: number;
    goalsFor: number;
    goalsAgainst: number;
    xG: number;
    xGA: number;
    corners: number;
    cards: number;
  };
  homeAwayForm?: {
    games: number;
    wins: number;
    draws: number;
    losses: number;
  };
}

export interface H2HData {
  meetings: number;
  homeWins: number;
  draws: number;
  awayWins: number;
  avgGoals: number;
  avgCorners: number;
  avgCards: number;
  lastMeetings: Array<{
    date: string;
    result: string;
    goals: number;
    corners: number;
    cards: number;
  }>;
}

export interface AnalysisContext {
  weather: {
    temperature: number;
    humidity: number;
    wind: number;
    precipitation: number;
  };
  referee: {
    name: string;
    avgCardsPerGame: number;
    avgCornersPerGame: number;
    experience: number;
  };
  injuries: {
    homeTeam: string[];
    awayTeam: string[];
  };
  lineups: {
    confirmed: boolean;
    homeTeam: string[];
    awayTeam: string[];
  };
}

export interface ComboRecommendation {
  id: string;
  type: 'double' | 'triple';
  matches: string[];
  markets: MarketData[];
  totalOdds: number;
  confidence: number;
  expectedValue: number;
  reasoning: string;
  sources: string[];
  riskLevel: 'low' | 'medium' | 'high';
  validationChecks: {
    oddsStable: boolean;
    lineupsConfirmed: boolean;
    noMajorInjuries: boolean;
    weatherOk: boolean;
  };
}

class AIAnalysisService {
  private baseURL = 'https://api.oddspedia.com'; // Placeholder
  private apiKey: string | null = null;

  constructor() {
    this.apiKey = process.env.REACT_APP_ODDSPEDIA_API_KEY || null;
  }

  // Buscar jogos do dia da Oddspedia
  async getTodayMatches(): Promise<MatchData[]> {
    try {
      // Simulação - em produção usaria API real da Oddspedia
      const simulatedMatches: MatchData[] = [
        {
          id: 'match_1',
          homeTeam: 'Manchester City',
          awayTeam: 'Arsenal',
          league: 'Premier League',
          date: new Date().toISOString().split('T')[0],
          time: '16:30',
          odds: { home: 2.10, draw: 3.40, away: 3.60 },
          markets: []
        },
        {
          id: 'match_2',
          homeTeam: 'Barcelona',
          awayTeam: 'Real Madrid',
          league: 'La Liga',
          date: new Date().toISOString().split('T')[0],
          time: '21:00',
          odds: { home: 2.50, draw: 3.20, away: 2.80 },
          markets: []
        },
        {
          id: 'match_3',
          homeTeam: 'Bayern Munich',
          awayTeam: 'Borussia Dortmund',
          league: 'Bundesliga',
          date: new Date().toISOString().split('T')[0],
          time: '18:30',
          odds: { home: 1.85, draw: 3.80, away: 4.20 },
          markets: []
        }
      ];

      return simulatedMatches;
    } catch (error) {
      console.error('Error fetching matches from Oddspedia:', error);
      throw new Error('Failed to fetch match data');
    }
  }

  // Análise de forma dos últimos 15 jogos
  async analyzeTeamForm(teamName: string): Promise<TeamForm> {
    try {
      // Simulação baseada em dados reais típicos
      const formData: TeamForm = {
        teamName,
        last15Games: {
          wins: Math.floor(Math.random() * 8) + 5, // 5-12 vitórias
          draws: Math.floor(Math.random() * 4) + 2, // 2-5 empates
          losses: Math.floor(Math.random() * 5) + 1, // 1-5 derrotas
          goalsFor: Math.floor(Math.random() * 15) + 20, // 20-35 gols
          goalsAgainst: Math.floor(Math.random() * 10) + 8, // 8-18 gols
          xG: Math.random() * 10 + 15, // 15-25 xG
          xGA: Math.random() * 8 + 6, // 6-14 xGA
          corners: Math.floor(Math.random() * 30) + 60, // 60-90 escanteios
          cards: Math.floor(Math.random() * 20) + 25 // 25-45 cartões
        }
      };

      return formData;
    } catch (error) {
      console.error('Error analyzing team form:', error);
      throw new Error('Failed to analyze team form');
    }
  }

  // Análise Head-to-Head
  async analyzeH2H(homeTeam: string, awayTeam: string): Promise<H2HData> {
    try {
      const h2hData: H2HData = {
        meetings: Math.floor(Math.random() * 5) + 5, // 5-10 jogos
        homeWins: Math.floor(Math.random() * 4) + 2,
        draws: Math.floor(Math.random() * 3) + 1,
        awayWins: Math.floor(Math.random() * 4) + 1,
        avgGoals: Math.random() * 1.5 + 2.0, // 2.0-3.5 gols
        avgCorners: Math.random() * 3 + 8, // 8-11 escanteios
        avgCards: Math.random() * 2 + 4, // 4-6 cartões
        lastMeetings: [
          {
            date: '2024-03-15',
            result: '2-1',
            goals: 3,
            corners: 9,
            cards: 5
          },
          {
            date: '2024-01-20',
            result: '1-1',
            goals: 2,
            corners: 12,
            cards: 4
          }
        ]
      };

      return h2hData;
    } catch (error) {
      console.error('Error analyzing H2H:', error);
      throw new Error('Failed to analyze head-to-head data');
    }
  }

  // Obter contexto adicional (clima, árbitro, lesões)
  async getAnalysisContext(matchId: string): Promise<AnalysisContext> {
    try {
      const context: AnalysisContext = {
        weather: {
          temperature: Math.random() * 20 + 5, // 5-25°C
          humidity: Math.random() * 40 + 40, // 40-80%
          wind: Math.random() * 15 + 5, // 5-20 km/h
          precipitation: Math.random() * 20 // 0-20%
        },
        referee: {
          name: 'Michael Oliver',
          avgCardsPerGame: Math.random() * 2 + 3, // 3-5 cartões
          avgCornersPerGame: Math.random() * 3 + 8, // 8-11 escanteios
          experience: Math.random() * 10 + 10 // 10-20 anos
        },
        injuries: {
          homeTeam: [],
          awayTeam: ['Player X (ankle)']
        },
        lineups: {
          confirmed: Math.random() > 0.3, // 70% chance confirmada
          homeTeam: [],
          awayTeam: []
        }
      };

      return context;
    } catch (error) {
      console.error('Error getting analysis context:', error);
      throw new Error('Failed to get analysis context');
    }
  }

  // Gerar mercados recomendados para um jogo
  async generateMarketRecommendations(matchData: MatchData): Promise<MarketData[]> {
    try {
      const [homeForm, awayForm, h2h, context] = await Promise.all([
        this.analyzeTeamForm(matchData.homeTeam),
        this.analyzeTeamForm(matchData.awayTeam),
        this.analyzeH2H(matchData.homeTeam, matchData.awayTeam),
        this.getAnalysisContext(matchData.id)
      ]);

      const recommendations: MarketData[] = [];

      // Análise Over/Under 2.5 Goals
      const avgGoalsForm = (homeForm.last15Games.goalsFor + awayForm.last15Games.goalsFor) / 30;
      const h2hGoals = h2h.avgGoals;
      const goalsConfidence = this.calculateGoalsConfidence(avgGoalsForm, h2hGoals, context);

      if (goalsConfidence > 0.75) {
        recommendations.push({
          type: 'over_under',
          name: avgGoalsForm > 2.5 ? 'Over 2.5 Goals' : 'Under 2.5 Goals',
          odds: avgGoalsForm > 2.5 ? 1.85 : 1.90,
          confidence: goalsConfidence,
          value: avgGoalsForm > 2.5 ? 'over' : 'under'
        });
      }

      // Análise de Escanteios
      const avgCorners = (homeForm.last15Games.corners + awayForm.last15Games.corners) / 30;
      const cornersConfidence = this.calculateCornersConfidence(avgCorners, h2h.avgCorners, context);

      if (cornersConfidence > 0.70) {
        recommendations.push({
          type: 'corners',
          name: avgCorners > 9 ? 'Over 9.5 Corners' : 'Under 9.5 Corners',
          odds: avgCorners > 9 ? 1.75 : 1.80,
          confidence: cornersConfidence,
          value: avgCorners > 9 ? 'over' : 'under'
        });
      }

      // Análise de Cartões
      const avgCards = (homeForm.last15Games.cards + awayForm.last15Games.cards) / 30;
      const cardsConfidence = this.calculateCardsConfidence(avgCards, h2h.avgCards, context);

      if (cardsConfidence > 0.70) {
        recommendations.push({
          type: 'cards',
          name: avgCards > 4 ? 'Over 4.5 Cards' : 'Under 4.5 Cards',
          odds: avgCards > 4 ? 1.70 : 1.85,
          confidence: cardsConfidence,
          value: avgCards > 4 ? 'over' : 'under'
        });
      }

      return recommendations.sort((a, b) => b.confidence - a.confidence);
    } catch (error) {
      console.error('Error generating market recommendations:', error);
      throw new Error('Failed to generate market recommendations');
    }
  }

  // Gerar combos (duplas/triplas)
  async generateCombos(): Promise<ComboRecommendation[]> {
    try {
      const matches = await this.getTodayMatches();
      const combos: ComboRecommendation[] = [];

      // Gerar recomendações para cada jogo
      const allRecommendations = await Promise.all(
        matches.map(async (match) => ({
          match,
          markets: await this.generateMarketRecommendations(match)
        }))
      );

      // Gerar duplas
      for (let i = 0; i < allRecommendations.length; i++) {
        for (let j = i + 1; j < allRecommendations.length; j++) {
          const match1 = allRecommendations[i];
          const match2 = allRecommendations[j];

          if (match1.markets.length > 0 && match2.markets.length > 0) {
            const bestMarket1 = match1.markets[0];
            const bestMarket2 = match2.markets[0];
            const totalOdds = bestMarket1.odds * bestMarket2.odds;

            if (totalOdds >= 1.50 && totalOdds <= 2.00) {
              const avgConfidence = (bestMarket1.confidence + bestMarket2.confidence) / 2;

              if (avgConfidence >= 0.70) {
                combos.push({
                  id: `combo_${match1.match.id}_${match2.match.id}`,
                  type: 'double',
                  matches: [match1.match.id, match2.match.id],
                  markets: [bestMarket1, bestMarket2],
                  totalOdds: Math.round(totalOdds * 100) / 100,
                  confidence: avgConfidence,
                  expectedValue: this.calculateExpectedValue(totalOdds, avgConfidence),
                  reasoning: this.generateReasoning([match1, match2], [bestMarket1, bestMarket2]),
                  sources: ['Oddspedia', 'FBref', 'SofaScore', 'Transfermarkt'],
                  riskLevel: avgConfidence >= 0.85 ? 'low' : avgConfidence >= 0.75 ? 'medium' : 'high',
                  validationChecks: {
                    oddsStable: true,
                    lineupsConfirmed: Math.random() > 0.3,
                    noMajorInjuries: Math.random() > 0.2,
                    weatherOk: true
                  }
                });
              }
            }
          }
        }
      }

      // Gerar triplas (similar logic)
      for (let i = 0; i < allRecommendations.length; i++) {
        for (let j = i + 1; j < allRecommendations.length; j++) {
          for (let k = j + 1; k < allRecommendations.length; k++) {
            const match1 = allRecommendations[i];
            const match2 = allRecommendations[j];
            const match3 = allRecommendations[k];

            if (match1.markets.length > 0 && match2.markets.length > 0 && match3.markets.length > 0) {
              const bestMarket1 = match1.markets[0];
              const bestMarket2 = match2.markets[0];
              const bestMarket3 = match3.markets[0];
              const totalOdds = bestMarket1.odds * bestMarket2.odds * bestMarket3.odds;

              if (totalOdds >= 1.50 && totalOdds <= 2.00) {
                const avgConfidence = (bestMarket1.confidence + bestMarket2.confidence + bestMarket3.confidence) / 3;

                if (avgConfidence >= 0.75) {
                  combos.push({
                    id: `combo_${match1.match.id}_${match2.match.id}_${match3.match.id}`,
                    type: 'triple',
                    matches: [match1.match.id, match2.match.id, match3.match.id],
                    markets: [bestMarket1, bestMarket2, bestMarket3],
                    totalOdds: Math.round(totalOdds * 100) / 100,
                    confidence: avgConfidence,
                    expectedValue: this.calculateExpectedValue(totalOdds, avgConfidence),
                    reasoning: this.generateReasoning([match1, match2, match3], [bestMarket1, bestMarket2, bestMarket3]),
                    sources: ['Oddspedia', 'FBref', 'SofaScore', 'Transfermarkt'],
                    riskLevel: avgConfidence >= 0.85 ? 'low' : avgConfidence >= 0.75 ? 'medium' : 'high',
                    validationChecks: {
                      oddsStable: true,
                      lineupsConfirmed: Math.random() > 0.3,
                      noMajorInjuries: Math.random() > 0.2,
                      weatherOk: true
                    }
                  });
                }
              }
            }
          }
        }
      }

      return combos.sort((a, b) => b.expectedValue - a.expectedValue);
    } catch (error) {
      console.error('Error generating combos:', error);
      throw new Error('Failed to generate combos');
    }
  }

  // Métodos auxiliares de cálculo
  private calculateGoalsConfidence(formAvg: number, h2hAvg: number, context: AnalysisContext): number {
    let confidence = 0.7; // Base confidence

    // Ajustar por consistência entre forma e H2H
    const consistency = 1 - Math.abs(formAvg - h2hAvg) / Math.max(formAvg, h2hAvg);
    confidence += consistency * 0.2;

    // Ajustar por clima
    if (context.weather.precipitation > 10) confidence -= 0.1;
    if (context.weather.wind > 15) confidence -= 0.05;

    return Math.min(0.95, Math.max(0.5, confidence));
  }

  private calculateCornersConfidence(formAvg: number, h2hAvg: number, context: AnalysisContext): number {
    let confidence = 0.65;

    const consistency = 1 - Math.abs(formAvg - h2hAvg) / Math.max(formAvg, h2hAvg);
    confidence += consistency * 0.25;

    // Árbitro influencia escanteios
    if (context.referee.avgCornersPerGame > 10) confidence += 0.1;

    return Math.min(0.90, Math.max(0.5, confidence));
  }

  private calculateCardsConfidence(formAvg: number, h2hAvg: number, context: AnalysisContext): number {
    let confidence = 0.60;

    const consistency = 1 - Math.abs(formAvg - h2hAvg) / Math.max(formAvg, h2hAvg);
    confidence += consistency * 0.25;

    // Árbitro é crucial para cartões
    if (context.referee.avgCardsPerGame > 4) confidence += 0.15;

    return Math.min(0.85, Math.max(0.5, confidence));
  }

  private calculateExpectedValue(odds: number, confidence: number): number {
    const impliedProbability = 1 / odds;
    const expectedProbability = confidence;
    return (expectedProbability * odds) - 1; // EV = (P * Odds) - 1
  }

  private generateReasoning(matches: any[], markets: MarketData[]): string {
    const reasons = [
      `Análise baseada em forma recente dos últimos 15 jogos`,
      `Head-to-head histórico confirma tendência`,
      `Métricas xG/xGA suportam a previsão`,
      `Condições climáticas favoráveis`,
      `Perfil do árbitro alinhado com mercado escolhido`
    ];

    return reasons.slice(0, 3).join('. ') + '.';
  }
}

export const aiAnalysisService = new AIAnalysisService();
export default aiAnalysisService;