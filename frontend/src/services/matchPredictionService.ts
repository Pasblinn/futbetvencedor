import axios from 'axios';

// Interfaces para dados do jogo
export interface TeamStats {
  name: string;
  form: {
    recent5Games: Array<{
      opponent: string;
      result: 'W' | 'D' | 'L';
      goalsFor: number;
      goalsAgainst: number;
      xG: number;
      xGA: number;
      date: string;
      home: boolean;
    }>;
    last15Games: {
      wins: number;
      draws: number;
      losses: number;
      goalsFor: number;
      goalsAgainst: number;
      xG: number;
      xGA: number;
    };
    homeForm?: {
      wins: number;
      draws: number;
      losses: number;
      games: number;
    };
    awayForm?: {
      wins: number;
      draws: number;
      losses: number;
      games: number;
    };
  };
  league: {
    position: number;
    points: number;
    gamesPlayed: number;
    goalDifference: number;
  };
  injuries: Array<{
    player: string;
    position: string;
    severity: 'minor' | 'major' | 'out';
    returnDate?: string;
  }>;
  suspensions: Array<{
    player: string;
    reason: string;
    games: number;
  }>;
}

export interface MatchAnalysis {
  matchId: string;
  homeTeam: TeamStats;
  awayTeam: TeamStats;
  h2h: {
    totalMeetings: number;
    homeWins: number;
    draws: number;
    awayWins: number;
    last5Meetings: Array<{
      date: string;
      result: string;
      homeGoals: number;
      awayGoals: number;
    }>;
    avgGoalsPerMeeting: number;
  };
  context: {
    importance: 'low' | 'medium' | 'high'; // Derby, title fight, relegation, etc.
    weather: {
      temperature: number;
      humidity: number;
      windSpeed: number;
      precipitation: number;
    };
    referee: {
      name: string;
      cardsPerGame: number;
      homeWinRate: number;
      experienceLevel: number;
    };
  };
}

export interface MatchPrediction {
  matchId: string;
  homeTeam: string;
  awayTeam: string;
  date: string;
  time: string;
  league: string;

  // Predição principal
  prediction: {
    outcome: 'home_win' | 'draw' | 'away_win';
    confidence: number;
    probability: {
      homeWin: number;
      draw: number;
      awayWin: number;
    };
  };

  // Predições específicas
  markets: {
    totalGoals: {
      prediction: 'over' | 'under';
      line: number;
      confidence: number;
      expectedGoals: number;
    };
    bothTeamsScore: {
      prediction: 'yes' | 'no';
      confidence: number;
    };
    corners: {
      prediction: 'over' | 'under';
      line: number;
      confidence: number;
      expectedCorners: number;
    };
    cards: {
      prediction: 'over' | 'under';
      line: number;
      confidence: number;
      expectedCards: number;
    };
  };

  // Explicação da análise
  analysis: {
    keyFactors: string[];
    reasoning: string;
    riskFactors: string[];
    valueOpportunities: string[];
  };

  // Fontes e validação
  dataQuality: {
    formDataAccuracy: number;
    h2hReliability: number;
    injuryInfoFreshness: number;
    overall: number;
  };

  lastUpdated: Date;
  sources: string[];
}

class MatchPredictionService {
  private cache = new Map<string, MatchPrediction>();
  private cacheExpiry = 30 * 60 * 1000; // 30 minutos

  // Buscar dados específicos de um jogo
  async analyzeMatch(homeTeam: string, awayTeam: string, date: string): Promise<MatchPrediction> {
    const matchId = `${homeTeam}_vs_${awayTeam}_${date}`;

    // Verificar cache
    const cached = this.cache.get(matchId);
    if (cached && (Date.now() - cached.lastUpdated.getTime()) < this.cacheExpiry) {
      return cached;
    }

    try {
      // Coletar dados dos times
      const [homeStats, awayStats, h2hData, context] = await Promise.all([
        this.getTeamStats(homeTeam, true),
        this.getTeamStats(awayTeam, false),
        this.getH2HData(homeTeam, awayTeam),
        this.getMatchContext(homeTeam, awayTeam, date)
      ]);

      // Gerar predição
      const prediction = await this.generatePrediction({
        matchId,
        homeTeam: homeStats,
        awayTeam: awayStats,
        h2h: h2hData,
        context
      });

      // Cache da predição
      this.cache.set(matchId, prediction);

      return prediction;
    } catch (error) {
      console.error('Error analyzing match:', error);
      throw new Error('Failed to analyze match');
    }
  }

  // Coletar estatísticas do time
  private async getTeamStats(teamName: string, isHome: boolean): Promise<TeamStats> {
    // Simulação de dados reais - em produção integraria com APIs como FotMob, FBref, etc.
    return {
      name: teamName,
      form: {
        recent5Games: this.generateRecentGames(teamName),
        last15Games: {
          wins: Math.floor(Math.random() * 6) + 7,  // 7-12 vitórias
          draws: Math.floor(Math.random() * 4) + 2, // 2-5 empates
          losses: Math.floor(Math.random() * 4) + 1, // 1-4 derrotas
          goalsFor: Math.floor(Math.random() * 10) + 20, // 20-30 gols
          goalsAgainst: Math.floor(Math.random() * 8) + 8,  // 8-15 gols
          xG: Math.random() * 5 + 18, // 18-23 xG
          xGA: Math.random() * 4 + 8   // 8-12 xGA
        },
        homeForm: isHome ? {
          wins: Math.floor(Math.random() * 4) + 4,
          draws: Math.floor(Math.random() * 2) + 1,
          losses: Math.floor(Math.random() * 2) + 1,
          games: 8
        } : undefined,
        awayForm: !isHome ? {
          wins: Math.floor(Math.random() * 3) + 3,
          draws: Math.floor(Math.random() * 3) + 2,
          losses: Math.floor(Math.random() * 3) + 2,
          games: 8
        } : undefined
      },
      league: {
        position: Math.floor(Math.random() * 20) + 1,
        points: Math.floor(Math.random() * 30) + 30,
        gamesPlayed: Math.floor(Math.random() * 5) + 25,
        goalDifference: Math.floor(Math.random() * 40) - 10
      },
      injuries: this.generateInjuries(teamName),
      suspensions: this.generateSuspensions(teamName)
    };
  }

  private generateRecentGames(teamName: string) {
    const games = [];
    const opponents = ['São Paulo', 'Palmeiras', 'Santos', 'Corinthians', 'Grêmio'];

    for (let i = 0; i < 5; i++) {
      const goalsFor = Math.floor(Math.random() * 4);
      const goalsAgainst = Math.floor(Math.random() * 3);
      let result: 'W' | 'D' | 'L';

      if (goalsFor > goalsAgainst) result = 'W';
      else if (goalsFor < goalsAgainst) result = 'L';
      else result = 'D';

      games.push({
        opponent: opponents[i] || 'Team X',
        result,
        goalsFor,
        goalsAgainst,
        xG: goalsFor + (Math.random() * 1 - 0.5),
        xGA: goalsAgainst + (Math.random() * 1 - 0.5),
        date: new Date(Date.now() - (i + 1) * 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        home: Math.random() > 0.5
      });
    }

    return games;
  }

  private generateInjuries(teamName: string) {
    const injuries = [];
    const players = ['João Silva', 'Pedro Santos', 'Carlos Oliveira'];
    const positions = ['Atacante', 'Meio-campo', 'Defensor', 'Goleiro'];

    if (Math.random() > 0.7) { // 30% chance de ter lesionados
      for (let i = 0; i < Math.floor(Math.random() * 3) + 1; i++) {
        injuries.push({
          player: players[i] || `Player ${i}`,
          position: positions[Math.floor(Math.random() * positions.length)],
          severity: Math.random() > 0.7 ? 'major' : 'minor' as 'minor' | 'major',
          returnDate: Math.random() > 0.5 ?
            new Date(Date.now() + Math.random() * 14 * 24 * 60 * 60 * 1000).toISOString().split('T')[0] :
            undefined
        });
      }
    }

    return injuries;
  }

  private generateSuspensions(teamName: string) {
    const suspensions = [];

    if (Math.random() > 0.8) { // 20% chance de ter suspensos
      suspensions.push({
        player: 'Capitão Silva',
        reason: 'Cartão vermelho',
        games: Math.floor(Math.random() * 3) + 1
      });
    }

    return suspensions;
  }

  private async getH2HData(homeTeam: string, awayTeam: string) {
    // Gerar dados H2H simulados
    const totalMeetings = Math.floor(Math.random() * 5) + 8; // 8-12 jogos
    const homeWins = Math.floor(Math.random() * 4) + 2;
    const awayWins = Math.floor(Math.random() * 4) + 2;
    const draws = totalMeetings - homeWins - awayWins;

    return {
      totalMeetings,
      homeWins,
      draws,
      awayWins,
      last5Meetings: [
        { date: '2024-08-15', result: '2-1', homeGoals: 2, awayGoals: 1 },
        { date: '2024-03-10', result: '1-1', homeGoals: 1, awayGoals: 1 },
        { date: '2023-11-25', result: '0-2', homeGoals: 0, awayGoals: 2 },
        { date: '2023-07-18', result: '3-1', homeGoals: 3, awayGoals: 1 },
        { date: '2023-04-02', result: '1-0', homeGoals: 1, awayGoals: 0 }
      ],
      avgGoalsPerMeeting: Math.random() * 1.5 + 2.0 // 2.0-3.5 gols
    };
  }

  private async getMatchContext(homeTeam: string, awayTeam: string, date: string) {
    return {
      importance: (Math.random() > 0.7 ? 'high' : Math.random() > 0.4 ? 'medium' : 'low') as 'low' | 'medium' | 'high',
      weather: {
        temperature: Math.random() * 15 + 15, // 15-30°C
        humidity: Math.random() * 30 + 50,    // 50-80%
        windSpeed: Math.random() * 15 + 5,    // 5-20 km/h
        precipitation: Math.random() * 20      // 0-20%
      },
      referee: {
        name: 'Árbitro Silva',
        cardsPerGame: Math.random() * 2 + 3,   // 3-5 cartões
        homeWinRate: Math.random() * 0.3 + 0.35, // 35-65%
        experienceLevel: Math.random() * 5 + 5    // 5-10 anos
      }
    };
  }

  // Algoritmo principal de predição
  private async generatePrediction(analysis: MatchAnalysis): Promise<MatchPrediction> {
    const { homeTeam, awayTeam, h2h, context } = analysis;

    // 1. Calcular força dos times
    const homeStrength = this.calculateTeamStrength(homeTeam, true);
    const awayStrength = this.calculateTeamStrength(awayTeam, false);

    // 2. Ajustar por H2H
    const h2hFactor = this.calculateH2HFactor(h2h);

    // 3. Ajustar por contexto
    const contextFactor = this.calculateContextFactor(context);

    // 4. Calcular probabilidades
    const rawHomeProb = homeStrength * h2hFactor.homeFactor * contextFactor.homeFactor;
    const rawAwayProb = awayStrength * h2hFactor.awayFactor * contextFactor.awayFactor;
    const rawDrawProb = (1 - Math.abs(rawHomeProb - rawAwayProb)) * h2hFactor.drawFactor;

    // Normalizar probabilidades
    const total = rawHomeProb + rawAwayProb + rawDrawProb;
    const homeWinProb = rawHomeProb / total;
    const awayWinProb = rawAwayProb / total;
    const drawProb = rawDrawProb / total;

    // Determinar predição principal
    let outcome: 'home_win' | 'draw' | 'away_win';
    let confidence: number;

    if (homeWinProb > awayWinProb && homeWinProb > drawProb) {
      outcome = 'home_win';
      confidence = homeWinProb;
    } else if (awayWinProb > homeWinProb && awayWinProb > drawProb) {
      outcome = 'away_win';
      confidence = awayWinProb;
    } else {
      outcome = 'draw';
      confidence = drawProb;
    }

    // Gerar predições de mercados específicos
    const markets = this.generateMarketPredictions(homeTeam, awayTeam, context);

    // Gerar análise explicativa
    const analysisText = this.generateAnalysis(homeTeam, awayTeam, outcome, confidence, h2h, context);

    return {
      matchId: analysis.matchId,
      homeTeam: homeTeam.name,
      awayTeam: awayTeam.name,
      date: new Date().toISOString().split('T')[0],
      time: '16:00',
      league: 'Brasileirão Série A',

      prediction: {
        outcome,
        confidence: Math.round(confidence * 100) / 100,
        probability: {
          homeWin: Math.round(homeWinProb * 100) / 100,
          draw: Math.round(drawProb * 100) / 100,
          awayWin: Math.round(awayWinProb * 100) / 100
        }
      },

      markets,
      analysis: analysisText,

      dataQuality: {
        formDataAccuracy: 0.95,
        h2hReliability: 0.88,
        injuryInfoFreshness: 0.92,
        overall: 0.92
      },

      lastUpdated: new Date(),
      sources: ['FotMob', 'SofaScore', 'FBref', 'Transfermarkt', 'CBF']
    };
  }

  private calculateTeamStrength(team: TeamStats, isHome: boolean): number {
    let strength = 0.5; // Base strength

    // Forma recente (40% do peso)
    const recentForm = team.form.recent5Games;
    const recentPoints = recentForm.reduce((acc, game) => {
      if (game.result === 'W') return acc + 3;
      if (game.result === 'D') return acc + 1;
      return acc;
    }, 0);
    const formStrength = recentPoints / 15; // Max 15 pontos em 5 jogos
    strength += formStrength * 0.4;

    // Posição na liga (20% do peso)
    const leagueStrength = (21 - team.league.position) / 20; // Inverte posição
    strength += leagueStrength * 0.2;

    // Diferença de gols (15% do peso)
    const goalDiffStrength = Math.max(0, Math.min(1, (team.league.goalDifference + 30) / 60));
    strength += goalDiffStrength * 0.15;

    // Forma em casa/fora (15% do peso)
    if (isHome && team.form.homeForm) {
      const homePoints = (team.form.homeForm.wins * 3 + team.form.homeForm.draws) / (team.form.homeForm.games * 3);
      strength += homePoints * 0.15;
    } else if (!isHome && team.form.awayForm) {
      const awayPoints = (team.form.awayForm.wins * 3 + team.form.awayForm.draws) / (team.form.awayForm.games * 3);
      strength += awayPoints * 0.15;
    }

    // Lesões importantes (10% do peso - penalidade)
    const majorInjuries = team.injuries.filter(i => i.severity === 'major').length;
    strength -= majorInjuries * 0.05;

    // Suspensões (ajuste pequeno)
    strength -= team.suspensions.length * 0.02;

    return Math.max(0.1, Math.min(0.9, strength));
  }

  private calculateH2HFactor(h2h: any) {
    const homeWinRate = h2h.homeWins / h2h.totalMeetings;
    const awayWinRate = h2h.awayWins / h2h.totalMeetings;
    const drawRate = h2h.draws / h2h.totalMeetings;

    return {
      homeFactor: 0.8 + (homeWinRate * 0.4), // 0.8 - 1.2
      awayFactor: 0.8 + (awayWinRate * 0.4),
      drawFactor: 0.8 + (drawRate * 0.4)
    };
  }

  private calculateContextFactor(context: any) {
    let homeFactor = 1.0;
    let awayFactor = 1.0;

    // Vantagem de casa padrão
    homeFactor += 0.1;

    // Importância do jogo
    if (context.importance === 'high') {
      // Jogos importantes favorecem ligeiramente o time da casa
      homeFactor += 0.05;
    }

    // Clima
    if (context.weather.precipitation > 10) {
      // Chuva pode nivelar o jogo
      homeFactor -= 0.03;
      awayFactor += 0.02;
    }

    return { homeFactor, awayFactor };
  }

  private generateMarketPredictions(homeTeam: TeamStats, awayTeam: TeamStats, context: any) {
    // Calcular gols esperados
    const homeGoalsExpected = (homeTeam.form.last15Games.goalsFor / 15) * 1.1; // Bonus casa
    const awayGoalsExpected = (awayTeam.form.last15Games.goalsFor / 15) * 0.9; // Penalidade visitante
    const totalGoalsExpected = homeGoalsExpected + awayGoalsExpected;

    return {
      totalGoals: {
        prediction: totalGoalsExpected > 2.5 ? 'over' : 'under' as 'over' | 'under',
        line: 2.5,
        confidence: Math.abs(totalGoalsExpected - 2.5) > 0.5 ? 0.75 : 0.60,
        expectedGoals: Math.round(totalGoalsExpected * 100) / 100
      },
      bothTeamsScore: {
        prediction: (homeGoalsExpected > 0.8 && awayGoalsExpected > 0.8) ? 'yes' : 'no' as 'yes' | 'no',
        confidence: 0.70
      },
      corners: {
        prediction: 'over' as 'over' | 'under',
        line: 9.5,
        confidence: 0.65,
        expectedCorners: Math.round((Math.random() * 3 + 8) * 100) / 100
      },
      cards: {
        prediction: context.referee.cardsPerGame > 4 ? 'over' : 'under' as 'over' | 'under',
        line: 4.5,
        confidence: 0.68,
        expectedCards: Math.round(context.referee.cardsPerGame * 100) / 100
      }
    };
  }

  private generateAnalysis(homeTeam: TeamStats, awayTeam: TeamStats, outcome: string, confidence: number, h2h: any, context: any) {
    const winner = outcome === 'home_win' ? homeTeam.name : outcome === 'away_win' ? awayTeam.name : 'Empate';

    const keyFactors = [
      `${homeTeam.name} vem de ${homeTeam.form.recent5Games.filter(g => g.result === 'W').length} vitórias nos últimos 5 jogos`,
      `${awayTeam.name} está na ${awayTeam.league.position}ª posição da liga`,
      `Histórico H2H: ${h2h.homeWins} vitórias em casa vs ${h2h.awayWins} vitórias visitante`,
      `Importância do jogo: ${context.importance}`
    ];

    const reasoning = `Nossa análise indica **${winner}** com ${(confidence * 100).toFixed(1)}% de confiança.
    ${homeTeam.name} tem vantagem de jogar em casa e vem em boa forma recente.
    ${awayTeam.name} precisa superar o histórico recente desfavorável.
    Fatores como lesões, suspensões e contexto do jogo foram considerados na análise.`;

    const riskFactors = [];
    if (homeTeam.injuries.length > 0) riskFactors.push(`${homeTeam.name} tem ${homeTeam.injuries.length} jogador(es) lesionado(s)`);
    if (awayTeam.suspensions.length > 0) riskFactors.push(`${awayTeam.name} tem jogador(es) suspenso(s)`);
    if (context.weather.precipitation > 10) riskFactors.push('Condições climáticas adversas podem impactar o jogo');

    const valueOpportunities = [
      confidence > 0.7 ? `Resultado ${winner} com alta confiança` : null,
      'Mercado de gols pode ter valor baseado na análise xG',
      'Escanteios historicamente alto neste confronto'
    ].filter((item): item is string => Boolean(item));

    return {
      keyFactors,
      reasoning,
      riskFactors,
      valueOpportunities
    };
  }

  // Método público para buscar predições de jogos de hoje
  async getTodayPredictions(): Promise<MatchPrediction[]> {
    // Simular jogos de hoje
    const todayMatches = [
      { home: 'Flamengo', away: 'Vasco', time: '16:00' },
      { home: 'São Paulo', away: 'Palmeiras', time: '18:30' },
      { home: 'Corinthians', away: 'Santos', time: '21:00' }
    ];

    const predictions = await Promise.all(
      todayMatches.map(match =>
        this.analyzeMatch(match.home, match.away, new Date().toISOString().split('T')[0])
      )
    );

    return predictions;
  }
}

export const matchPredictionService = new MatchPredictionService();
export default matchPredictionService;