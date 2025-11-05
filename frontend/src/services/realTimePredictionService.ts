import { liveDataService, LiveMatch, TeamStatistics, H2HData } from './liveDataService';
import { matchPredictionService, MatchPrediction } from './matchPredictionService';
import { realTimeAPIService, WeatherData } from './realTimeApi';
import { notificationService } from './notifications';

// Interfaces avançadas para predições em tempo real
export interface RealTimePrediction extends MatchPrediction {
  liveData: {
    isLive: boolean;
    currentMinute?: number;
    currentScore?: {
      home: number;
      away: number;
    };
    momentum: {
      direction: 'home' | 'away' | 'neutral';
      strength: number; // 0-1
      recentEvents: string[];
    };
    oddsMovement: {
      homeChange: number;
      drawChange: number;
      awayChange: number;
      trend: 'stable' | 'volatile' | 'significant_movement';
    };
  };
  updatedProbabilities: {
    homeWin: number;
    draw: number;
    awayWin: number;
    nextGoalHome: number;
    nextGoalAway: number;
  };
  liveMarkets: {
    correctScore: Array<{
      score: string;
      probability: number;
      odds: number;
    }>;
    timeOfNextGoal: {
      next5Min: number;
      next10Min: number;
      next15Min: number;
    };
    cards: {
      nextYellow: number;
      nextRed: number;
    };
  };
  alerts: {
    valueOdds: Array<{
      market: string;
      recommendation: 'strong_buy' | 'buy' | 'hold' | 'avoid';
      value: number;
      reasoning: string;
    }>;
    momentum: Array<{
      type: 'positive' | 'negative' | 'warning';
      message: string;
      confidence: number;
    }>;
  };
}

export interface AdvancedStatistics {
  xG: {
    home: number;
    away: number;
    difference: number;
  };
  possession: {
    home: number;
    away: number;
  };
  shotQuality: {
    home: number;
    away: number;
  };
  defensiveStrength: {
    home: number;
    away: number;
  };
  formMomentum: {
    home: number;
    away: number;
  };
  injuryImpact: {
    home: number;
    away: number;
  };
  weatherImpact: {
    attackingPlayImpact: number;
    defensivePlayImpact: number;
  };
}

class RealTimePredictionService {
  private activePredictions = new Map<string, RealTimePrediction>();
  private updateIntervals = new Map<string, NodeJS.Timeout>();
  private predictionHistory = new Map<string, RealTimePrediction[]>();

  // Criar predição em tempo real para um jogo
  async createRealTimePrediction(match: LiveMatch): Promise<RealTimePrediction> {
    try {
      console.log(`🔄 Criando predição em tempo real para ${match.homeTeam.name} vs ${match.awayTeam.name}`);

      // 1. Coletar dados básicos
      const [homeStats, awayStats, h2hData, weather] = await Promise.all([
        liveDataService.getTeamStatistics(match.homeTeam.id),
        liveDataService.getTeamStatistics(match.awayTeam.id),
        liveDataService.getH2HData(match.homeTeam.id, match.awayTeam.id),
        this.getWeatherForMatch(match)
      ]);

      // 2. Calcular estatísticas avançadas
      const advancedStats = await this.calculateAdvancedStatistics(
        match, homeStats, awayStats, h2hData, weather
      );

      // 3. Gerar predição base
      const basePrediction = await matchPredictionService.analyzeMatch(
        match.homeTeam.name,
        match.awayTeam.name,
        match.fixture.date
      );

      // 4. Criar predição em tempo real
      const realTimePrediction: RealTimePrediction = {
        ...basePrediction,
        liveData: {
          isLive: match.status.short === 'LIVE' || match.status.short === '1H' || match.status.short === '2H',
          currentMinute: match.status.elapsed ?? undefined,
          currentScore: match.status.short === 'NS' ? undefined : {
            home: 0, // Em produção, viria dos dados da API
            away: 0
          },
          momentum: this.calculateMomentum(match, advancedStats),
          oddsMovement: await this.calculateOddsMovement(match.id)
        },
        updatedProbabilities: this.calculateUpdatedProbabilities(
          basePrediction, advancedStats, match
        ),
        liveMarkets: this.generateLiveMarkets(advancedStats, match),
        alerts: this.generateAlerts(advancedStats, match)
      };

      // 5. Armazenar e iniciar monitoramento
      this.activePredictions.set(match.id, realTimePrediction);
      this.startLiveUpdates(match.id);

      // 6. Notificar
      notificationService.notifyPredictionReady(
        match.id,
        match.homeTeam.name,
        match.awayTeam.name,
        realTimePrediction.prediction.confidence
      );

      console.log(`✅ Predição criada com ${(realTimePrediction.prediction.confidence * 100).toFixed(1)}% de confiança`);

      return realTimePrediction;

    } catch (error) {
      console.error('Erro ao criar predição em tempo real:', error);
      throw new Error('Falha ao gerar predição em tempo real');
    }
  }

  // Atualizar predição durante o jogo
  async updateLivePrediction(matchId: string): Promise<RealTimePrediction | null> {
    const existingPrediction = this.activePredictions.get(matchId);
    if (!existingPrediction) return null;

    try {
      // 1. Buscar dados atualizados
      const [currentMatches, odds] = await Promise.all([
        liveDataService.getLiveMatches(),
        liveDataService.getLiveOdds(matchId)
      ]);

      const currentMatch = currentMatches.find(m => m.id === matchId);
      if (!currentMatch) return existingPrediction;

      // 2. Recalcular probabilidades baseado no estado atual
      const updatedProbabilities = this.recalculateLiveProbabilities(
        existingPrediction,
        currentMatch
      );

      // 3. Atualizar dados do jogo
      const updatedPrediction: RealTimePrediction = {
        ...existingPrediction,
        liveData: {
          ...existingPrediction.liveData,
          isLive: currentMatch.status.short === 'LIVE' ||
                 currentMatch.status.short === '1H' ||
                 currentMatch.status.short === '2H',
          currentMinute: currentMatch.status.elapsed ?? undefined,
          oddsMovement: await this.calculateOddsMovement(matchId),
          momentum: this.updateMomentum(existingPrediction.liveData.momentum, currentMatch)
        },
        updatedProbabilities,
        alerts: this.updateAlerts(existingPrediction, currentMatch)
      };

      // 4. Detectar mudanças significativas
      this.detectSignificantChanges(existingPrediction, updatedPrediction);

      // 5. Armazenar histórico
      this.addToHistory(matchId, updatedPrediction);

      // 6. Atualizar cache
      this.activePredictions.set(matchId, updatedPrediction);

      return updatedPrediction;

    } catch (error) {
      console.error('Erro ao atualizar predição:', error);
      return existingPrediction;
    }
  }

  // Calcular estatísticas avançadas
  private async calculateAdvancedStatistics(
    match: LiveMatch,
    homeStats: TeamStatistics,
    awayStats: TeamStatistics,
    h2hData: H2HData,
    weather: WeatherData | null
  ): Promise<AdvancedStatistics> {

    // Calcular xG baseado em histórico e qualidade dos times
    const homeXG = this.calculateExpectedGoals(homeStats, awayStats, true);
    const awayXG = this.calculateExpectedGoals(awayStats, homeStats, false);

    // Calcular força defensiva
    const homeDefStrength = this.calculateDefensiveStrength(homeStats);
    const awayDefStrength = this.calculateDefensiveStrength(awayStats);

    // Calcular momentum da forma
    const homeFormMomentum = this.calculateFormMomentum(homeStats.form.recent);
    const awayFormMomentum = this.calculateFormMomentum(awayStats.form.recent);

    // Buscar e calcular impacto de lesões
    const [homeInjuries, awayInjuries] = await Promise.all([
      liveDataService.getInjuryReport(match.homeTeam.id),
      liveDataService.getInjuryReport(match.awayTeam.id)
    ]);

    const homeInjuryImpact = this.calculateInjuryImpact(homeInjuries.players);
    const awayInjuryImpact = this.calculateInjuryImpact(awayInjuries.players);

    // Calcular impacto do clima
    const weatherImpact = weather ? this.calculateWeatherImpact(weather) : {
      attackingPlayImpact: 0,
      defensivePlayImpact: 0
    };

    return {
      xG: {
        home: homeXG,
        away: awayXG,
        difference: homeXG - awayXG
      },
      possession: {
        home: 50 + (homeStats.league.position < awayStats.league.position ? 5 : -5),
        away: 50 + (awayStats.league.position < homeStats.league.position ? 5 : -5)
      },
      shotQuality: {
        home: homeStats.goals.for.average / (homeStats.goals.for.average + homeStats.goals.against.average),
        away: awayStats.goals.for.average / (awayStats.goals.for.average + awayStats.goals.against.average)
      },
      defensiveStrength: {
        home: homeDefStrength,
        away: awayDefStrength
      },
      formMomentum: {
        home: homeFormMomentum,
        away: awayFormMomentum
      },
      injuryImpact: {
        home: homeInjuryImpact,
        away: awayInjuryImpact
      },
      weatherImpact
    };
  }

  // Calcular gols esperados (xG)
  private calculateExpectedGoals(teamStats: TeamStatistics, opponentStats: TeamStatistics, isHome: boolean): number {
    const baseXG = teamStats.goals.for.average;
    const homeBonus = isHome ? 0.15 : 0;
    const opponentDefense = 1 - (opponentStats.goals.against.average / 3); // Normalizar

    return Math.max(0.5, baseXG * (1 + homeBonus) * Math.max(0.7, opponentDefense));
  }

  // Calcular força defensiva
  private calculateDefensiveStrength(stats: TeamStatistics): number {
    const goalsAgainstAvg = stats.goals.against.average;
    const leaguePosition = stats.league.position;

    // Quanto menor o número de gols sofridos e melhor a posição, maior a força defensiva
    return Math.max(0.3, Math.min(1.0, (2.5 - goalsAgainstAvg) * 0.4 + (21 - leaguePosition) / 20 * 0.6));
  }

  // Calcular momentum da forma
  private calculateFormMomentum(recentForm: string): number {
    const formPoints = recentForm.split('').reduce((acc, result) => {
      if (result === 'W') return acc + 3;
      if (result === 'D') return acc + 1;
      return acc;
    }, 0);

    return formPoints / 15; // Máximo 15 pontos em 5 jogos
  }

  // Calcular impacto de lesões
  private calculateInjuryImpact(injuries: any[]): number {
    if (injuries.length === 0) return 0;

    return injuries.reduce((impact, injury) => {
      const positionWeight = {
        'Forward': 0.3,
        'Midfielder': 0.25,
        'Defender': 0.2,
        'Goalkeeper': 0.4
      };

      return impact + (positionWeight[injury.position as keyof typeof positionWeight] || 0.2);
    }, 0);
  }

  // Calcular impacto do clima
  private calculateWeatherImpact(weather: WeatherData): {
    attackingPlayImpact: number;
    defensivePlayImpact: number;
  } {
    let attackingImpact = 0;
    let defensiveImpact = 0;

    // Chuva afeta mais o ataque
    if (weather.precipitation > 10) {
      attackingImpact -= 0.15;
      defensiveImpact += 0.05;
    }

    // Vento forte afeta passes longos
    if (weather.windSpeed > 20) {
      attackingImpact -= 0.1;
    }

    // Temperatura extrema afeta performance
    if (weather.temperature > 35 || weather.temperature < 5) {
      attackingImpact -= 0.08;
      defensiveImpact -= 0.05;
    }

    return {
      attackingPlayImpact: attackingImpact,
      defensivePlayImpact: defensiveImpact
    };
  }

  // Calcular movimento das odds
  private async calculateOddsMovement(matchId: string): Promise<any> {
    // Em produção, compararia odds atuais com odds históricas
    return {
      homeChange: (Math.random() - 0.5) * 0.2, // -0.1 a +0.1
      drawChange: (Math.random() - 0.5) * 0.3,
      awayChange: (Math.random() - 0.5) * 0.2,
      trend: Math.random() > 0.7 ? 'volatile' : 'stable' as 'stable' | 'volatile' | 'significant_movement'
    };
  }

  // Calcular momentum do jogo
  private calculateMomentum(match: LiveMatch, stats: AdvancedStatistics): any {
    const xGDiff = stats.xG.difference;
    let direction: 'home' | 'away' | 'neutral' = 'neutral';
    let strength = 0;

    if (Math.abs(xGDiff) > 0.5) {
      direction = xGDiff > 0 ? 'home' : 'away';
      strength = Math.min(1, Math.abs(xGDiff) / 2);
    }

    return {
      direction,
      strength,
      recentEvents: [`${match.homeTeam.name} criando mais chances`, 'Jogo equilibrado']
    };
  }

  // Atualizar momentum
  private updateMomentum(currentMomentum: any, match: LiveMatch): any {
    // Em produção, analisaria eventos recentes do jogo
    return {
      ...currentMomentum,
      recentEvents: [
        `Minuto ${match.status.elapsed || 0}: Jogo equilibrado`,
        ...currentMomentum.recentEvents.slice(0, 2)
      ]
    };
  }

  // Calcular probabilidades atualizadas
  private calculateUpdatedProbabilities(
    basePrediction: MatchPrediction,
    stats: AdvancedStatistics,
    match: LiveMatch
  ): any {
    const base = basePrediction.prediction.probability;

    // Ajustar baseado em xG
    const xGAdjustment = stats.xG.difference * 0.1;

    // Ajustar baseado em lesões
    const injuryAdjustment = (stats.injuryImpact.away - stats.injuryImpact.home) * 0.05;

    let homeWin = base.homeWin + xGAdjustment + injuryAdjustment;
    let awayWin = base.awayWin - xGAdjustment - injuryAdjustment;
    let draw = base.draw;

    // Normalizar
    const total = homeWin + awayWin + draw;
    homeWin /= total;
    awayWin /= total;
    draw /= total;

    return {
      homeWin: Math.round(homeWin * 100) / 100,
      draw: Math.round(draw * 100) / 100,
      awayWin: Math.round(awayWin * 100) / 100,
      nextGoalHome: 0.6,
      nextGoalAway: 0.4
    };
  }

  // Recalcular probabilidades durante o jogo
  private recalculateLiveProbabilities(
    prediction: RealTimePrediction,
    currentMatch: LiveMatch
  ): any {
    const current = prediction.updatedProbabilities;

    // Ajustar baseado no tempo de jogo
    const minute = currentMatch.status.elapsed || 0;
    const timeAdjustment = minute > 75 ? 0.1 : 0; // Menos empates no final

    return {
      ...current,
      draw: Math.max(0.1, current.draw - timeAdjustment),
      homeWin: current.homeWin + timeAdjustment * 0.5,
      awayWin: current.awayWin + timeAdjustment * 0.5
    };
  }

  // Gerar mercados ao vivo
  private generateLiveMarkets(stats: AdvancedStatistics, match: LiveMatch): any {
    return {
      correctScore: [
        { score: '1-0', probability: 0.15, odds: 6.5 },
        { score: '2-1', probability: 0.12, odds: 8.0 },
        { score: '1-1', probability: 0.18, odds: 5.5 },
        { score: '0-0', probability: 0.08, odds: 12.0 },
        { score: '2-0', probability: 0.10, odds: 10.0 }
      ],
      timeOfNextGoal: {
        next5Min: 0.15,
        next10Min: 0.28,
        next15Min: 0.42
      },
      cards: {
        nextYellow: 0.35,
        nextRed: 0.05
      }
    };
  }

  // Gerar alertas
  private generateAlerts(stats: AdvancedStatistics, match: LiveMatch): any {
    const alerts = {
      valueOdds: [] as any[],
      momentum: [] as any[]
    };

    // Alertas de value betting
    if (stats.xG.difference > 0.8) {
      alerts.valueOdds.push({
        market: 'Home Win',
        recommendation: 'strong_buy' as const,
        value: 0.85,
        reasoning: `${match.homeTeam.name} tem xG significativamente superior`
      });
    }

    // Alertas de momentum
    if (Math.abs(stats.xG.difference) > 1.0) {
      alerts.momentum.push({
        type: 'positive' as const,
        message: 'Uma das equipes está criando muito mais chances',
        confidence: 0.8
      });
    }

    if (stats.injuryImpact.home > 0.3 || stats.injuryImpact.away > 0.3) {
      alerts.momentum.push({
        type: 'warning' as const,
        message: 'Lesões importantes podem impactar significativamente o jogo',
        confidence: 0.7
      });
    }

    return alerts;
  }

  // Atualizar alertas
  private updateAlerts(existing: RealTimePrediction, currentMatch: LiveMatch): any {
    return {
      ...existing.alerts,
      momentum: [
        {
          type: 'positive' as const,
          message: `Minuto ${currentMatch.status.elapsed || 0}: Jogo seguindo conforme previsto`,
          confidence: 0.75
        },
        ...existing.alerts.momentum.slice(0, 2)
      ]
    };
  }

  // Detectar mudanças significativas
  private detectSignificantChanges(
    oldPrediction: RealTimePrediction,
    newPrediction: RealTimePrediction
  ): void {
    const oldProb = oldPrediction.updatedProbabilities;
    const newProb = newPrediction.updatedProbabilities;

    const homeChange = Math.abs(newProb.homeWin - oldProb.homeWin);
    const awayChange = Math.abs(newProb.awayWin - oldProb.awayWin);

    if (homeChange > 0.1 || awayChange > 0.1) {
      notificationService.addNotification({
        type: 'prediction_ready',
        title: 'Predição Atualizada',
        message: 'Probabilidades do jogo mudaram significativamente',
        metadata: {
          matchId: newPrediction.matchId,
          homeChange,
          awayChange
        }
      });
    }
  }

  // Adicionar ao histórico
  private addToHistory(matchId: string, prediction: RealTimePrediction): void {
    const history = this.predictionHistory.get(matchId) || [];
    history.push({ ...prediction, lastUpdated: new Date() });

    // Manter apenas últimas 10 atualizações
    if (history.length > 10) {
      history.shift();
    }

    this.predictionHistory.set(matchId, history);
  }

  // Iniciar atualizações ao vivo
  private startLiveUpdates(matchId: string): void {
    // Atualizar a cada 2 minutos durante o jogo
    const interval = setInterval(async () => {
      await this.updateLivePrediction(matchId);
    }, 2 * 60 * 1000);

    this.updateIntervals.set(matchId, interval);

    // Parar atualizações após 2 horas
    setTimeout(() => {
      this.stopLiveUpdates(matchId);
    }, 2 * 60 * 60 * 1000);
  }

  // Parar atualizações ao vivo
  private stopLiveUpdates(matchId: string): void {
    const interval = this.updateIntervals.get(matchId);
    if (interval) {
      clearInterval(interval);
      this.updateIntervals.delete(matchId);
    }
  }

  // Buscar dados meteorológicos
  private async getWeatherForMatch(match: LiveMatch): Promise<WeatherData | null> {
    try {
      return await realTimeAPIService.getWeatherData(match.fixture.venue.city);
    } catch (error) {
      console.warn('Erro ao buscar dados meteorológicos:', error);
      return null;
    }
  }

  // Métodos públicos
  async getRealTimePrediction(matchId: string): Promise<RealTimePrediction | null> {
    return this.activePredictions.get(matchId) || null;
  }

  async getAllActivePredictions(): Promise<RealTimePrediction[]> {
    return Array.from(this.activePredictions.values());
  }

  async getPredictionHistory(matchId: string): Promise<RealTimePrediction[]> {
    return this.predictionHistory.get(matchId) || [];
  }

  // Criar predições para todos os jogos de hoje
  async createTodayPredictions(): Promise<RealTimePrediction[]> {
    try {
      const todayMatches = await liveDataService.getLiveMatches();
      const predictions: RealTimePrediction[] = [];

      for (const match of todayMatches) {
        try {
          const prediction = await this.createRealTimePrediction(match);
          predictions.push(prediction);
        } catch (error) {
          console.error(`Erro ao criar predição para ${match.homeTeam.name} vs ${match.awayTeam.name}:`, error);
        }
      }

      return predictions;
    } catch (error) {
      console.error('Erro ao criar predições de hoje:', error);
      return [];
    }
  }

  // Limpar dados antigos
  cleanup(): void {
    // Parar todos os intervalos
    this.updateIntervals.forEach(interval => clearInterval(interval));
    this.updateIntervals.clear();

    // Limpar predições antigas (mais de 24 horas)
    const oneDayAgo = Date.now() - 24 * 60 * 60 * 1000;

    this.activePredictions.forEach((prediction, matchId) => {
      if (new Date(prediction.lastUpdated).getTime() < oneDayAgo) {
        this.activePredictions.delete(matchId);
      }
    });

    this.predictionHistory.forEach((history, matchId) => {
      const filtered = history.filter(p => new Date(p.lastUpdated).getTime() >= oneDayAgo);
      if (filtered.length === 0) {
        this.predictionHistory.delete(matchId);
      } else {
        this.predictionHistory.set(matchId, filtered);
      }
    });
  }
}

export const realTimePredictionService = new RealTimePredictionService();
export default realTimePredictionService;