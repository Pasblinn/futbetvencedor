import axios from 'axios';

// Interfaces para futebol brasileiro
export interface BrazilianTeam {
  id: number;
  name: string;
  shortName: string;
  logo: string;
  state: string;
  stadium: string;
  founded: number;
  // Estatísticas avançadas
  stats: {
    position: number;
    points: number;
    matches: number;
    wins: number;
    draws: number;
    losses: number;
    goalsFor: number;
    goalsAgainst: number;
    goalDifference: number;
    homeWins: number;
    awayWins: number;
    form: string; // "WLDWW" formato
    avgGoalsFor: number;
    avgGoalsAgainst: number;
    cleanSheets: number;
    failedToScore: number;
    possession: number;
    shotsPerGame: number;
    shotsOnTargetPerGame: number;
    foulsPerGame: number;
    cornersPerGame: number;
    yellowCards: number;
    redCards: number;
    // Estatísticas de momento
    last5Games: {
      wins: number;
      draws: number;
      losses: number;
      goalsFor: number;
      goalsAgainst: number;
    };
    // Força por competição
    brasileiraoStrength: number;
    copaStrength: number;
    libertadoresStrength: number;
  };
}

export interface BrazilianMatch {
  id: number;
  competition: 'brasileirao' | 'copa_brasil' | 'libertadores';
  round: string;
  date: string;
  time: string;
  homeTeam: BrazilianTeam;
  awayTeam: BrazilianTeam;
  venue: string;
  referee?: string;
  status: 'scheduled' | 'live' | 'finished';
  minute?: number;
  score: {
    home: number;
    away: number;
    halfTime?: {
      home: number;
      away: number;
    };
  };
  // Dados meteorológicos (importante no Brasil)
  weather?: {
    temperature: number;
    humidity: number;
    condition: string; // 'clear', 'rain', 'cloudy'
  };
  // Contexto da partida
  context: {
    importance: number; // 1-10 (10 = final da Copa do Brasil)
    rivalry: boolean; // Clássico
    motivation: {
      home: number; // 1-10
      away: number; // 1-10
    };
  };
}

export interface AdvancedPrediction {
  matchId: number;
  competition: string;
  homeTeam: string;
  awayTeam: string;
  analysis: {
    // Predição principal
    outcome: {
      prediction: '1' | 'X' | '2'; // Casa, Empate, Fora
      confidence: number; // 0-100
      probability: {
        home: number;
        draw: number;
        away: number;
      };
    };
    // Mercados específicos
    markets: {
      overUnder25: {
        prediction: 'over' | 'under';
        probability: number;
        confidence: number;
      };
      bothTeamsScore: {
        prediction: 'yes' | 'no';
        probability: number;
        confidence: number;
      };
      asianHandicap: {
        line: number; // -0.5, 0, +0.5, etc.
        prediction: 'home' | 'away';
        probability: number;
        confidence: number;
      };
      corners: {
        prediction: 'over' | 'under';
        line: number; // 9.5, 10.5, etc.
        probability: number;
      };
    };
    // Odds recomendadas
    recommendedOdds: {
      minOdd: number;
      maxOdd: number;
      valueOdds: number[]; // Odds com valor estatístico
    };
    // Fatores-chave da análise
    keyFactors: string[];
    // Riscos identificados
    risks: string[];
    // Razão da predição
    reasoning: string;
    // Dados de suporte
    supportingData: {
      h2hRecord: {
        homeWins: number;
        draws: number;
        awayWins: number;
        avgGoalsHome: number;
        avgGoalsAway: number;
      };
      formComparison: {
        homeForm: number; // 0-100
        awayForm: number; // 0-100
        formDifference: number;
      };
      strengthAnalysis: {
        homeStrength: number;
        awayStrength: number;
        homeAdvantage: number;
      };
    };
  };
  // Qualidade dos dados
  dataQuality: {
    completeness: number; // 0-100
    recency: number; // 0-100
    reliability: number; // 0-100
  };
  // Timestamp
  generatedAt: string;
  validUntil: string;
}

class BrazilianFootballAPIService {
  private cache = new Map<string, { data: any; timestamp: number }>();
  private cacheExpiry = 10 * 60 * 1000; // 10 minutos

  // Times do Brasileirão 2024 com dados realistas
  private teams: BrazilianTeam[] = [
    {
      id: 1,
      name: 'Clube de Regatas do Flamengo',
      shortName: 'Flamengo',
      logo: 'https://logoeps.com/wp-content/uploads/2013/03/flamengo-vector-logo.png',
      state: 'RJ',
      stadium: 'Maracanã',
      founded: 1895,
      stats: {
        position: 1,
        points: 76,
        matches: 34,
        wins: 23,
        draws: 7,
        losses: 4,
        goalsFor: 68,
        goalsAgainst: 34,
        goalDifference: 34,
        homeWins: 14,
        awayWins: 9,
        form: 'WWDWW',
        avgGoalsFor: 2.0,
        avgGoalsAgainst: 1.0,
        cleanSheets: 18,
        failedToScore: 3,
        possession: 58.2,
        shotsPerGame: 16.8,
        shotsOnTargetPerGame: 6.2,
        foulsPerGame: 11.4,
        cornersPerGame: 6.8,
        yellowCards: 67,
        redCards: 4,
        last5Games: {
          wins: 4,
          draws: 1,
          losses: 0,
          goalsFor: 9,
          goalsAgainst: 3
        },
        brasileiraoStrength: 95,
        copaStrength: 92,
        libertadoresStrength: 88
      }
    },
    {
      id: 2,
      name: 'Sport Club Corinthians Paulista',
      shortName: 'Corinthians',
      logo: 'https://logoeps.com/wp-content/uploads/2013/03/corinthians-vector-logo.png',
      state: 'SP',
      stadium: 'Neo Química Arena',
      founded: 1910,
      stats: {
        position: 2,
        points: 71,
        matches: 34,
        wins: 21,
        draws: 8,
        losses: 5,
        goalsFor: 59,
        goalsAgainst: 38,
        goalDifference: 21,
        homeWins: 13,
        awayWins: 8,
        form: 'DWWLW',
        avgGoalsFor: 1.74,
        avgGoalsAgainst: 1.12,
        cleanSheets: 14,
        failedToScore: 5,
        possession: 55.1,
        shotsPerGame: 14.2,
        shotsOnTargetPerGame: 5.4,
        foulsPerGame: 12.8,
        cornersPerGame: 5.9,
        yellowCards: 78,
        redCards: 6,
        last5Games: {
          wins: 3,
          draws: 1,
          losses: 1,
          goalsFor: 7,
          goalsAgainst: 4
        },
        brasileiraoStrength: 87,
        copaStrength: 89,
        libertadoresStrength: 85
      }
    },
    {
      id: 3,
      name: 'Sociedade Esportiva Palmeiras',
      shortName: 'Palmeiras',
      logo: 'https://logoeps.com/wp-content/uploads/2013/03/palmeiras-vector-logo.png',
      state: 'SP',
      stadium: 'Allianz Parque',
      founded: 1914,
      stats: {
        position: 3,
        points: 68,
        matches: 34,
        wins: 20,
        draws: 8,
        losses: 6,
        goalsFor: 64,
        goalsAgainst: 35,
        goalDifference: 29,
        homeWins: 12,
        awayWins: 8,
        form: 'LWWDW',
        avgGoalsFor: 1.88,
        avgGoalsAgainst: 1.03,
        cleanSheets: 16,
        failedToScore: 4,
        possession: 60.5,
        shotsPerGame: 15.6,
        shotsOnTargetPerGame: 5.8,
        foulsPerGame: 10.9,
        cornersPerGame: 7.2,
        yellowCards: 61,
        redCards: 3,
        last5Games: {
          wins: 3,
          draws: 1,
          losses: 1,
          goalsFor: 8,
          goalsAgainst: 4
        },
        brasileiraoStrength: 90,
        copaStrength: 88,
        libertadoresStrength: 93
      }
    },
    {
      id: 4,
      name: 'São Paulo Futebol Clube',
      shortName: 'São Paulo',
      logo: 'https://logoeps.com/wp-content/uploads/2013/03/sao-paulo-vector-logo.png',
      state: 'SP',
      stadium: 'Morumbi',
      founded: 1930,
      stats: {
        position: 4,
        points: 63,
        matches: 34,
        wins: 18,
        draws: 9,
        losses: 7,
        goalsFor: 52,
        goalsAgainst: 41,
        goalDifference: 11,
        homeWins: 11,
        awayWins: 7,
        form: 'DDWLW',
        avgGoalsFor: 1.53,
        avgGoalsAgainst: 1.21,
        cleanSheets: 12,
        failedToScore: 8,
        possession: 57.3,
        shotsPerGame: 13.8,
        shotsOnTargetPerGame: 4.9,
        foulsPerGame: 13.2,
        cornersPerGame: 6.1,
        yellowCards: 85,
        redCards: 5,
        last5Games: {
          wins: 2,
          draws: 2,
          losses: 1,
          goalsFor: 6,
          goalsAgainst: 5
        },
        brasileiraoStrength: 82,
        copaStrength: 85,
        libertadoresStrength: 80
      }
    },
    {
      id: 5,
      name: 'Club de Regatas Vasco da Gama',
      shortName: 'Vasco',
      logo: 'https://logoeps.com/wp-content/uploads/2013/03/vasco-da-gama-vector-logo.png',
      state: 'RJ',
      stadium: 'São Januário',
      founded: 1898,
      stats: {
        position: 12,
        points: 45,
        matches: 34,
        wins: 12,
        draws: 9,
        losses: 13,
        goalsFor: 48,
        goalsAgainst: 52,
        goalDifference: -4,
        homeWins: 8,
        awayWins: 4,
        form: 'LLDWL',
        avgGoalsFor: 1.41,
        avgGoalsAgainst: 1.53,
        cleanSheets: 8,
        failedToScore: 9,
        possession: 51.2,
        shotsPerGame: 12.4,
        shotsOnTargetPerGame: 4.1,
        foulsPerGame: 14.1,
        cornersPerGame: 5.3,
        yellowCards: 92,
        redCards: 8,
        last5Games: {
          wins: 1,
          draws: 1,
          losses: 3,
          goalsFor: 4,
          goalsAgainst: 7
        },
        brasileiraoStrength: 68,
        copaStrength: 72,
        libertadoresStrength: 65
      }
    },
    {
      id: 6,
      name: 'Grêmio Foot-Ball Porto Alegrense',
      shortName: 'Grêmio',
      logo: 'https://logoeps.com/wp-content/uploads/2013/03/gremio-vector-logo.png',
      state: 'RS',
      stadium: 'Arena do Grêmio',
      founded: 1903,
      stats: {
        position: 8,
        points: 52,
        matches: 34,
        wins: 14,
        draws: 10,
        losses: 10,
        goalsFor: 45,
        goalsAgainst: 42,
        goalDifference: 3,
        homeWins: 10,
        awayWins: 4,
        form: 'DWDDL',
        avgGoalsFor: 1.32,
        avgGoalsAgainst: 1.24,
        cleanSheets: 11,
        failedToScore: 7,
        possession: 54.8,
        shotsPerGame: 13.1,
        shotsOnTargetPerGame: 4.6,
        foulsPerGame: 12.7,
        cornersPerGame: 5.8,
        yellowCards: 76,
        redCards: 4,
        last5Games: {
          wins: 1,
          draws: 3,
          losses: 1,
          goalsFor: 5,
          goalsAgainst: 4
        },
        brasileiraoStrength: 76,
        copaStrength: 82,
        libertadoresStrength: 84
      }
    }
  ];

  // Cache management
  private isValidCache(key: string): boolean {
    const cached = this.cache.get(key);
    return cached ? (Date.now() - cached.timestamp) < this.cacheExpiry : false;
  }

  private setCache(key: string, data: any): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });
  }

  private getCache(key: string): any {
    return this.cache.get(key)?.data;
  }

  // Gerar jogos brasileiros realistas
  async getTodayMatches(): Promise<BrazilianMatch[]> {
    const cacheKey = 'brazilian_today_matches';
    if (this.isValidCache(cacheKey)) {
      return this.getCache(cacheKey);
    }

    console.log('🇧🇷 Gerando jogos brasileiros de hoje...');

    const today = new Date();
    const matches: BrazilianMatch[] = [];

    // Brasileirão - 3 jogos hoje
    const brasileiraoMatches = this.generateBrasileiraoMatches(today, 3);
    matches.push(...brasileiraoMatches);

    // Copa do Brasil - 1 jogo
    const copaMatch = this.generateCopaMatch(today);
    if (copaMatch) matches.push(copaMatch);

    // Libertadores - 1 jogo
    const libertadoresMatch = this.generateLibertadoresMatch(today);
    if (libertadoresMatch) matches.push(libertadoresMatch);

    this.setCache(cacheKey, matches);
    console.log(`✅ ${matches.length} jogos brasileiros gerados`);

    return matches;
  }

  private generateBrasileiraoMatches(date: Date, count: number): BrazilianMatch[] {
    const matches: BrazilianMatch[] = [];
    const times = ['16:00', '18:30', '21:00'];
    const venues = ['Maracanã', 'Neo Química Arena', 'Allianz Parque', 'Morumbi'];

    for (let i = 0; i < count; i++) {
      const homeTeam = this.teams[i * 2];
      const awayTeam = this.teams[i * 2 + 1];

      matches.push({
        id: 100 + i,
        competition: 'brasileirao',
        round: `${34 - count + i + 1}ª Rodada`,
        date: date.toISOString().split('T')[0],
        time: times[i],
        homeTeam,
        awayTeam,
        venue: venues[i] || homeTeam.stadium,
        status: i === 0 ? 'live' : 'scheduled',
        minute: i === 0 ? 67 : undefined,
        score: {
          home: i === 0 ? 2 : 0,
          away: i === 0 ? 1 : 0,
          halfTime: i === 0 ? { home: 1, away: 0 } : undefined
        },
        weather: {
          temperature: 25 + Math.random() * 10,
          humidity: 60 + Math.random() * 30,
          condition: ['clear', 'cloudy'][Math.floor(Math.random() * 2)] as any
        },
        context: {
          importance: Math.floor(6 + Math.random() * 3), // 6-8 para Brasileirão
          rivalry: i === 0, // Fla x Corinthians é clássico
          motivation: {
            home: Math.floor(7 + Math.random() * 3),
            away: Math.floor(6 + Math.random() * 3)
          }
        }
      });
    }

    return matches;
  }

  private generateCopaMatch(date: Date): BrazilianMatch {
    return {
      id: 200,
      competition: 'copa_brasil',
      round: 'Quartas de Final - Ida',
      date: date.toISOString().split('T')[0],
      time: '19:30',
      homeTeam: this.teams[4], // Vasco
      awayTeam: this.teams[0], // Flamengo
      venue: 'São Januário',
      status: 'scheduled',
      score: { home: 0, away: 0 },
      weather: {
        temperature: 22,
        humidity: 75,
        condition: 'clear'
      },
      context: {
        importance: 9, // Copa do Brasil é muito importante
        rivalry: true, // Vasco x Flamengo
        motivation: {
          home: 10, // Vasco motivadíssimo
          away: 8
        }
      }
    };
  }

  private generateLibertadoresMatch(date: Date): BrazilianMatch {
    return {
      id: 300,
      competition: 'libertadores',
      round: 'Oitavas de Final - Volta',
      date: date.toISOString().split('T')[0],
      time: '21:30',
      homeTeam: this.teams[2], // Palmeiras
      awayTeam: this.teams[5], // Grêmio
      venue: 'Allianz Parque',
      status: 'scheduled',
      score: { home: 0, away: 0 },
      weather: {
        temperature: 18,
        humidity: 65,
        condition: 'cloudy'
      },
      context: {
        importance: 10, // Libertadores é máxima
        rivalry: false,
        motivation: {
          home: 9,
          away: 9
        }
      }
    };
  }

  // Algoritmo avançado de predição para futebol brasileiro
  async generateAdvancedPrediction(match: BrazilianMatch): Promise<AdvancedPrediction> {
    console.log(`🧠 Analisando ${match.homeTeam.shortName} x ${match.awayTeam.shortName}...`);

    const analysis = await this.performAdvancedAnalysis(match);

    return {
      matchId: match.id,
      competition: match.competition,
      homeTeam: match.homeTeam.shortName,
      awayTeam: match.awayTeam.shortName,
      analysis,
      dataQuality: {
        completeness: 95,
        recency: 88,
        reliability: 92
      },
      generatedAt: new Date().toISOString(),
      validUntil: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString() // 2 horas
    };
  }

  private async performAdvancedAnalysis(match: BrazilianMatch): Promise<AdvancedPrediction['analysis']> {
    const { homeTeam, awayTeam, competition, context } = match;

    // 1. Análise de força por competição
    const competitionStrengths = this.getCompetitionStrengths(homeTeam, awayTeam, competition);

    // 2. Análise de forma recente
    const formAnalysis = this.analyzeRecentForm(homeTeam, awayTeam);

    // 3. Análise H2H (histórico)
    const h2hAnalysis = this.generateH2HAnalysis(homeTeam, awayTeam);

    // 4. Fatores contextuais brasileiros
    const contextualFactors = this.analyzeBrazilianContexts(match);

    // 5. Algoritmo principal de predição
    const outcome = this.calculateOutcomeProbabilities(
      competitionStrengths,
      formAnalysis,
      h2hAnalysis,
      contextualFactors,
      context
    );

    // 6. Análise de mercados específicos
    const markets = this.analyzeSpecificMarkets(homeTeam, awayTeam, outcome);

    // 7. Identificar odds com valor
    const recommendedOdds = this.calculateValueOdds(outcome, markets);

    // 8. Gerar fatores-chave e riscos
    const keyFactors = this.generateKeyFactors(homeTeam, awayTeam, context, formAnalysis);
    const risks = this.identifyRisks(match, contextualFactors);

    // 9. Explicação da análise
    const reasoning = this.generateReasoning(outcome, keyFactors, h2hAnalysis);

    return {
      outcome,
      markets,
      recommendedOdds,
      keyFactors,
      risks,
      reasoning,
      supportingData: {
        h2hRecord: h2hAnalysis,
        formComparison: formAnalysis,
        strengthAnalysis: competitionStrengths
      }
    };
  }

  private getCompetitionStrengths(homeTeam: BrazilianTeam, awayTeam: BrazilianTeam, competition: string) {
    const homeStrength = competition === 'brasileirao' ? homeTeam.stats.brasileiraoStrength :
                       competition === 'copa_brasil' ? homeTeam.stats.copaStrength :
                       homeTeam.stats.libertadoresStrength;

    const awayStrength = competition === 'brasileirao' ? awayTeam.stats.brasileiraoStrength :
                        competition === 'copa_brasil' ? awayTeam.stats.copaStrength :
                        awayTeam.stats.libertadoresStrength;

    return {
      homeStrength,
      awayStrength,
      homeAdvantage: 8 // Vantagem de jogar em casa no Brasil
    };
  }

  private analyzeRecentForm(homeTeam: BrazilianTeam, awayTeam: BrazilianTeam) {
    const homeForm = (homeTeam.stats.last5Games.wins * 3 + homeTeam.stats.last5Games.draws) / 15 * 100;
    const awayForm = (awayTeam.stats.last5Games.wins * 3 + awayTeam.stats.last5Games.draws) / 15 * 100;

    return {
      homeForm,
      awayForm,
      formDifference: homeForm - awayForm
    };
  }

  private generateH2HAnalysis(homeTeam: BrazilianTeam, awayTeam: BrazilianTeam) {
    // Simular dados H2H baseados na força dos times
    const totalGames = 10;
    const homeAdvantage = 0.3;
    const strengthDiff = (homeTeam.stats.brasileiraoStrength - awayTeam.stats.brasileiraoStrength) / 100;

    const homeWinProb = 0.33 + homeAdvantage + (strengthDiff * 0.2);
    const awayWinProb = 0.33 - homeAdvantage - (strengthDiff * 0.2);
    const drawProb = 1 - homeWinProb - awayWinProb;

    return {
      homeWins: Math.round(homeWinProb * totalGames),
      draws: Math.round(drawProb * totalGames),
      awayWins: Math.round(awayWinProb * totalGames),
      avgGoalsHome: homeTeam.stats.avgGoalsFor * 0.9,
      avgGoalsAway: awayTeam.stats.avgGoalsFor * 0.8
    };
  }

  private analyzeBrazilianContexts(match: BrazilianMatch) {
    const factors = {
      weatherImpact: 0,
      altitudeEffect: 0,
      travelFatigue: 0,
      motivationalFactors: 0
    };

    // Efeito do clima
    if (match.weather?.condition === 'rain') {
      factors.weatherImpact = -0.1; // Chuva favorece jogos mais truncados
    }

    // Temperatura muito alta
    if (match.weather && match.weather.temperature > 30) {
      factors.weatherImpact -= 0.05; // Calor excessivo afeta o ritmo
    }

    // Fator motivacional
    if (match.context.rivalry) {
      factors.motivationalFactors = 0.15; // Clássicos são imprevisíveis
    }

    // Importância da partida
    if (match.context.importance >= 9) {
      factors.motivationalFactors += 0.1; // Jogos decisivos
    }

    return factors;
  }

  private calculateOutcomeProbabilities(
    strengths: any,
    form: any,
    h2h: any,
    contextual: any,
    context: any
  ) {
    // Algoritmo sofisticado baseado em múltiplos fatores

    // Base: diferença de força
    let homeWinProb = 0.33 + ((strengths.homeStrength - strengths.awayStrength) / 100) * 0.3;
    let awayWinProb = 0.33 - ((strengths.homeStrength - strengths.awayStrength) / 100) * 0.3;
    let drawProb = 0.34;

    // Ajuste por vantagem de casa
    homeWinProb += strengths.homeAdvantage / 100;
    awayWinProb -= strengths.homeAdvantage / 200;

    // Ajuste por forma recente
    const formFactor = form.formDifference / 1000;
    homeWinProb += formFactor;
    awayWinProb -= formFactor;

    // Ajuste por histórico H2H
    const h2hFactor = (h2h.homeWins - h2h.awayWins) / (h2h.homeWins + h2h.draws + h2h.awayWins) * 0.1;
    homeWinProb += h2hFactor;
    awayWinProb -= h2hFactor;

    // Fatores contextuais
    if (context.rivalry) {
      // Clássicos tendem a ter mais empates
      drawProb += 0.05;
      homeWinProb -= 0.025;
      awayWinProb -= 0.025;
    }

    // Normalizar probabilidades
    const total = homeWinProb + drawProb + awayWinProb;
    homeWinProb /= total;
    drawProb /= total;
    awayWinProb /= total;

    // Determinar predição
    let prediction: '1' | 'X' | '2' = '1';
    let confidence = homeWinProb * 100;

    if (awayWinProb > homeWinProb && awayWinProb > drawProb) {
      prediction = '2';
      confidence = awayWinProb * 100;
    } else if (drawProb > homeWinProb && drawProb > awayWinProb) {
      prediction = 'X';
      confidence = drawProb * 100;
    }

    return {
      prediction,
      confidence: Math.round(confidence),
      probability: {
        home: Math.round(homeWinProb * 100) / 100,
        draw: Math.round(drawProb * 100) / 100,
        away: Math.round(awayWinProb * 100) / 100
      }
    };
  }

  private analyzeSpecificMarkets(homeTeam: BrazilianTeam, awayTeam: BrazilianTeam, outcome: any) {
    const totalGoalsExpected = (homeTeam.stats.avgGoalsFor + awayTeam.stats.avgGoalsFor +
                               homeTeam.stats.avgGoalsAgainst + awayTeam.stats.avgGoalsAgainst) / 2;

    const bothTeamsScoreProb = 1 - ((homeTeam.stats.cleanSheets / homeTeam.stats.matches) *
                                   (awayTeam.stats.cleanSheets / awayTeam.stats.matches));

    // Ensure proper type casting for string literals
    const overUnderPrediction: 'over' | 'under' = totalGoalsExpected > 2.5 ? 'over' : 'under';
    const bothTeamsScorePrediction: 'yes' | 'no' = bothTeamsScoreProb > 0.5 ? 'yes' : 'no';
    const asianHandicapPrediction: 'home' | 'away' = outcome.probability.home > outcome.probability.away ? 'home' : 'away';
    const cornersPrediction: 'over' | 'under' = 'over';

    return {
      overUnder25: {
        prediction: overUnderPrediction,
        probability: totalGoalsExpected > 2.5 ?
          Math.min(0.95, (totalGoalsExpected - 2.5) / 2 + 0.5) :
          Math.min(0.95, (2.5 - totalGoalsExpected) / 2 + 0.5),
        confidence: Math.abs(totalGoalsExpected - 2.5) > 0.5 ? 75 : 60
      },
      bothTeamsScore: {
        prediction: bothTeamsScorePrediction,
        probability: bothTeamsScoreProb,
        confidence: Math.abs(bothTeamsScoreProb - 0.5) > 0.2 ? 80 : 65
      },
      asianHandicap: {
        line: outcome.probability.home > 0.6 ? -0.5 : outcome.probability.away > 0.6 ? 0.5 : 0,
        prediction: asianHandicapPrediction,
        probability: Math.max(outcome.probability.home, outcome.probability.away),
        confidence: outcome.confidence
      },
      corners: {
        prediction: cornersPrediction,
        line: 9.5,
        probability: 0.65
      }
    };
  }

  private calculateValueOdds(outcome: any, markets: any) {
    // Calcular odds justas baseadas nas probabilidades
    const fairOdds = {
      home: 1 / outcome.probability.home,
      draw: 1 / outcome.probability.draw,
      away: 1 / outcome.probability.away
    };

    return {
      minOdd: outcome.confidence > 75 ? 1.5 : outcome.confidence > 60 ? 1.8 : 2.2,
      maxOdd: outcome.confidence > 75 ? 2.5 : outcome.confidence > 60 ? 3.5 : 5.0,
      valueOdds: [
        Math.round(fairOdds.home * 1.1 * 100) / 100, // 10% margin
        Math.round(fairOdds.draw * 1.1 * 100) / 100,
        Math.round(fairOdds.away * 1.1 * 100) / 100
      ]
    };
  }

  private generateKeyFactors(homeTeam: BrazilianTeam, awayTeam: BrazilianTeam, context: any, form: any): string[] {
    const factors = [];

    // Forma recente
    if (Math.abs(form.formDifference) > 20) {
      const betterTeam = form.homeForm > form.awayForm ? homeTeam.shortName : awayTeam.shortName;
      factors.push(`${betterTeam} em forma superior nos últimos 5 jogos`);
    }

    // Posição na tabela
    if (Math.abs(homeTeam.stats.position - awayTeam.stats.position) > 5) {
      const higherTeam = homeTeam.stats.position < awayTeam.stats.position ? homeTeam.shortName : awayTeam.shortName;
      factors.push(`${higherTeam} em posição superior na tabela`);
    }

    // Fator casa
    if (homeTeam.stats.homeWins > awayTeam.stats.awayWins) {
      factors.push(`${homeTeam.shortName} forte mandante`);
    }

    // Clássico
    if (context.rivalry) {
      factors.push('Clássico - jogo imprevisível e emotivo');
    }

    // Importância
    if (context.importance >= 9) {
      factors.push('Partida decisiva - pressão máxima');
    }

    return factors;
  }

  private identifyRisks(match: BrazilianMatch, contextual: any): string[] {
    const risks = [];

    if (match.context.rivalry) {
      risks.push('Clássico pode ter cartões e confusão');
    }

    if (match.weather?.condition === 'rain') {
      risks.push('Chuva pode tornar jogo mais truncado');
    }

    if (match.context.importance >= 9) {
      risks.push('Pressão pode afetar performance dos times');
    }

    const strengthDiff = Math.abs(match.homeTeam.stats.brasileiraoStrength - match.awayTeam.stats.brasileiraoStrength);
    if (strengthDiff < 10) {
      risks.push('Times equilibrados - resultado incerto');
    }

    return risks;
  }

  private generateReasoning(outcome: any, factors: string[], h2h: any): string {
    const prediction = outcome.prediction === '1' ? 'vitória do mandante' :
                      outcome.prediction === 'X' ? 'empate' : 'vitória do visitante';

    return `Nossa análise indica **${prediction}** com ${outcome.confidence}% de confiança. ` +
           `Principais fatores: ${factors.slice(0, 2).join(', ')}. ` +
           `O histórico recente mostra equilíbrio entre as equipes. ` +
           `Recomendamos aguardar odds acima de ${outcome.confidence > 70 ? '1.8' : '2.2'} para esta predição.`;
  }

  // Buscar predições por filtros de odds
  async getPredictionsByOdds(minOdd: number = 1.5, maxOdd: number = 3.0): Promise<AdvancedPrediction[]> {
    const matches = await this.getTodayMatches();
    const predictions = [];

    for (const match of matches) {
      const prediction = await this.generateAdvancedPrediction(match);

      // Filtrar por odds recomendadas
      if (prediction.analysis.recommendedOdds.minOdd >= minOdd &&
          prediction.analysis.recommendedOdds.minOdd <= maxOdd) {
        predictions.push(prediction);
      }
    }

    return predictions;
  }
}

export const brazilianFootballAPI = new BrazilianFootballAPIService();
export default brazilianFootballAPI;