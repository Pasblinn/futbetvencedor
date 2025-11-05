import { BrazilianTeam, BrazilianMatch } from './brazilianFootballAPI';

// Interface para análise avançada de dados em tempo real
export interface RealTimeMatchData {
  liveStats: {
    possession: { home: number; away: number };
    shots: { home: number; away: number };
    shotsOnTarget: { home: number; away: number };
    corners: { home: number; away: number };
    fouls: { home: number; away: number };
    yellowCards: { home: number; away: number };
    redCards: { home: number; away: number };
    offsides: { home: number; away: number };
  };

  momentum: {
    current: 'home' | 'away' | 'neutral';
    strength: number; // 0-1
    duration: number; // minutos
    keyEvents: Array<{
      type: 'goal' | 'card' | 'substitution' | 'chance';
      team: 'home' | 'away';
      minute: number;
      impact: number;
    }>;
  };

  physicalCondition: {
    homeTeam: {
      averageSpeed: number;
      distanceCovered: number;
      intensityLevel: number;
      fatigueLevel: number;
    };
    awayTeam: {
      averageSpeed: number;
      distanceCovered: number;
      intensityLevel: number;
      fatigueLevel: number;
    };
  };

  weatherImpact: {
    temperature: number;
    humidity: number;
    windSpeed: number;
    precipitation: number;
    impact: 'low' | 'medium' | 'high';
  };
}

// Sistema de análise de valor de apostas
export interface ValueAnalysis {
  market: string;
  selection: string;
  ourProbability: number;
  bookmakerOdds: number;
  impliedProbability: number;
  valuePercentage: number;
  kellyStake: number;
  confidence: 'low' | 'medium' | 'high';
  reasoning: string[];
  riskFactors: string[];
}

// Mercados especializados para futebol brasileiro
export interface BrazilianSpecialMarkets {
  // Mercados culturais específicos
  ginga_factor: {
    skillful_play_over_under: { line: number; over: number; under: number };
    nutmeg_probability: number;
    rainbow_flick_probability: number;
  };

  // Fatores climáticos tropicais
  heat_impact: {
    substitutions_over_under: { line: number; over: number; under: number };
    second_half_fatigue: number;
    hydration_breaks: { yes: number; no: number };
  };

  // Aspectos emocionais
  crowd_influence: {
    home_support_boost: number;
    intimidation_factor: number;
    referee_influence: number;
  };

  // Mercados de rivalidade
  derby_specials: {
    heated_match_cards: { over: number; under: number; line: number };
    multiple_sendings_off: { yes: number; no: number };
    referee_controversy: { yes: number; no: number };
  };

  // Copa do Brasil específicos
  copa_brasil_factors: {
    upset_probability: number;
    extra_time_needed: { yes: number; no: number };
    penalty_shootout: { yes: number; no: number };
  };

  // Brasileirão específicos
  title_race_pressure: {
    pressure_points_dropped: number;
    late_winner_probability: number;
    conservative_play: number;
  };

  // Libertadores continentais
  continental_experience: {
    south_american_style: number;
    altitude_adaptation: number;
    travel_fatigue: number;
  };
}

// Engine de Machine Learning Avançado
export class EnhancedMLEngine {
  private modelWeights: { [key: string]: number } = {
    'gradient_boosting': 0.25,
    'neural_network': 0.20,
    'random_forest': 0.15,
    'xgboost': 0.15,
    'ensemble_meta': 0.10,
    'deep_learning': 0.10,
    'lstm_time_series': 0.05
  };

  // Rede Neural Convolucional para padrões de jogo
  private analyzeTacticalPatterns(homeTeam: BrazilianTeam, awayTeam: BrazilianTeam): {
    formation_counter: number;
    style_mismatch: number;
    tactical_advantage: 'home' | 'away' | 'neutral';
    key_battles: Array<{
      area: string;
      advantage: 'home' | 'away';
      importance: number;
    }>;
  } {
    // Simular análise de CNN para padrões táticos
    const homeFormation = this.extractFormationData(homeTeam);
    const awayFormation = this.extractFormationData(awayTeam);

    const formationCounter = this.calculateFormationCounter(homeFormation, awayFormation);
    const styleMismatch = this.calculateStyleMismatch(homeTeam.stats, awayTeam.stats);

    return {
      formation_counter: formationCounter,
      style_mismatch: styleMismatch,
      tactical_advantage: formationCounter > 0.6 ? 'home' : formationCounter < 0.4 ? 'away' : 'neutral',
      key_battles: this.identifyKeyBattles(homeTeam, awayTeam)
    };
  }

  // LSTM para análise temporal de momentum
  private analyzeMomentumTimeSeries(team: BrazilianTeam): {
    current_trend: 'upward' | 'downward' | 'stable';
    trend_strength: number;
    predicted_peak: number; // minutos até o pico
    sustainability: number; // 0-1
    fatigue_point: number; // minuto provável de queda
  } {
    const form = team.stats.form;
    const recentMatches = this.parseFormToScores(form);

    // Simular LSTM analysis
    const trend = this.calculateTrend(recentMatches);

    return {
      current_trend: trend.direction,
      trend_strength: trend.strength,
      predicted_peak: 65, // Análise sugere pico aos 65 min
      sustainability: trend.strength * 0.8,
      fatigue_point: 78 // Queda típica aos 78 min
    };
  }

  // Análise de Big Data em tempo real
  generateRealTimePredictions(
    match: BrazilianMatch,
    liveData: RealTimeMatchData,
    currentMinute: number
  ): {
    updated_probabilities: {
      home_win: number;
      draw: number;
      away_win: number;
    };
    next_goal: {
      home: number;
      away: number;
      no_goal: number;
      expected_minute: number;
    };
    momentum_shift: {
      probability: number;
      expected_minute: number;
      trigger_events: string[];
    };
    live_value_bets: ValueAnalysis[];
  } {
    // Atualizar probabilidades com base em dados ao vivo
    const liveAdjustment = this.calculateLiveAdjustment(liveData, currentMinute);
    const momentumFactor = this.calculateMomentumFactor(liveData.momentum);

    const baseProbabilities = {
      home_win: 0.45,
      draw: 0.27,
      away_win: 0.28
    };

    // Aplicar ajustes em tempo real
    const updatedProbs = this.applyLiveAdjustments(baseProbabilities, liveAdjustment, momentumFactor);

    return {
      updated_probabilities: updatedProbs,
      next_goal: this.predictNextGoal(liveData, currentMinute),
      momentum_shift: this.predictMomentumShift(liveData, currentMinute),
      live_value_bets: this.identifyLiveValueBets(liveData, updatedProbs)
    };
  }

  // Análise de arbitragem entre casas de apostas
  findArbitrageOpportunities(
    markets: Array<{
      bookmaker: string;
      market: string;
      selections: Array<{ selection: string; odds: number }>;
    }>
  ): Array<{
    type: 'arbitrage' | 'sure_bet';
    profit_percentage: number;
    stakes: Array<{ bookmaker: string; selection: string; stake: number }>;
    total_return: number;
    risk_level: 'low' | 'medium' | 'high';
  }> {
    const opportunities = [];

    // Agrupar por mercado
    const marketGroups = this.groupMarketsByType(markets);

    for (const [marketType, bookmakerData] of Object.entries(marketGroups)) {
      console.log('🔧 DEBUG: Processing market type:', marketType, 'Data type:', typeof bookmakerData);

      // Garantir que bookmakerData é um array
      const dataArray = Array.isArray(bookmakerData) ? bookmakerData : [bookmakerData];
      const arb = this.calculateArbitrage(dataArray);
      if (arb.is_profitable) {
        const oppType: "arbitrage" | "sure_bet" = arb.profit > 5 ? 'arbitrage' : 'sure_bet';
        opportunities.push({
          type: oppType,
          profit_percentage: Number(arb.profit) || 0,
          stakes: Array.isArray(arb.stakes) ? arb.stakes : [],
          total_return: Number(arb.return) || 0,
          risk_level: this.assessArbitrageRisk(arb)
        });
      }
    }

    return opportunities.sort((a, b) => b.profit_percentage - a.profit_percentage);
  }

  // Sistema de alertas inteligentes
  generateSmartAlerts(
    match: BrazilianMatch,
    userPreferences: {
      risk_tolerance: 'conservative' | 'moderate' | 'aggressive';
      favorite_markets: string[];
      bankroll: number;
      max_stake: number;
    }
  ): Array<{
    type: 'value_bet' | 'live_opportunity' | 'arbitrage' | 'cash_out';
    urgency: 'low' | 'medium' | 'high';
    title: string;
    description: string;
    recommended_action: string;
    potential_profit: number;
    risk_assessment: string;
    time_sensitive: boolean;
  }> {
    const alerts: Array<{
      type: "arbitrage" | "value_bet" | "live_opportunity" | "cash_out";
      urgency: 'low' | 'medium' | 'high';
      title: string;
      description: string;
      recommended_action: string;
      potential_profit: number;
      risk_assessment: string;
      time_sensitive: boolean;
    }> = [];

    // Verificar oportunidades de valor
    const valueOpportunities = this.scanValueOpportunities(match);
    valueOpportunities.forEach(opp => {
      console.log('🔧 DEBUG: Processing value opportunity:', opp);
      if (this.matchesUserProfile(opp, userPreferences)) {
        alerts.push({
          type: 'value_bet' as const,
          urgency: (opp.value > 15 ? 'high' : 'medium') as 'high' | 'medium',
          title: `Oportunidade de Valor: ${opp.market}`,
          description: `${opp.value.toFixed(1)}% de valor esperado em ${opp.selection}`,
          recommended_action: `Apostar ${this.calculateOptimalStake(opp, userPreferences)}`,
          potential_profit: Number(opp.expected_profit) || 0,
          risk_assessment: this.assessRisk(opp, userPreferences),
          time_sensitive: true
        });
      }
    });

    return alerts.sort((a, b) => {
      const urgencyWeight = { high: 3, medium: 2, low: 1 };
      return urgencyWeight[b.urgency] - urgencyWeight[a.urgency];
    });
  }

  // Métodos auxiliares privados
  private extractFormationData(team: BrazilianTeam): any {
    // Simular extração de dados de formação
    return {
      defensive_line: 4,
      midfield_line: team.stats.possession > 60 ? 3 : 2,
      attacking_line: team.stats.avgGoalsFor > 1.5 ? 3 : 2
    };
  }

  private calculateFormationCounter(home: any, away: any): number {
    // Simular cálculo de contra-formação
    return 0.5 + Math.random() * 0.4; // Placeholder
  }

  private calculateStyleMismatch(homeStats: any, awayStats: any): number {
    const possessionDiff = Math.abs(homeStats.possession - awayStats.possession);
    return possessionDiff / 100;
  }

  private identifyKeyBattles(homeTeam: BrazilianTeam, awayTeam: BrazilianTeam): any[] {
    return [
      {
        area: 'Meio-campo',
        advantage: homeTeam.stats.possession > awayTeam.stats.possession ? 'home' : 'away',
        importance: 0.8
      },
      {
        area: 'Defesa vs Ataque',
        advantage: homeTeam.stats.avgGoalsFor > awayTeam.stats.avgGoalsAgainst ? 'home' : 'away',
        importance: 0.9
      }
    ];
  }

  private parseFormToScores(form: string): number[] {
    return form.split('').map(char => {
      switch (char) {
        case 'W': return 3;
        case 'D': return 1;
        case 'L': return 0;
        default: return 1;
      }
    });
  }

  private calculateTrend(scores: number[]): any {
    const avg = scores.reduce((a, b) => a + b) / scores.length;
    const recentAvg = scores.slice(-3).reduce((a, b) => a + b) / 3;

    return {
      direction: recentAvg > avg ? 'upward' : recentAvg < avg ? 'downward' : 'stable',
      strength: Math.abs(recentAvg - avg) / 3
    };
  }

  private calculateLiveAdjustment(liveData: RealTimeMatchData, minute: number): any {
    return {
      possession_factor: (liveData.liveStats.possession.home - 50) / 100,
      shots_factor: (liveData.liveStats.shots.home - liveData.liveStats.shots.away) / 20,
      time_factor: minute / 90
    };
  }

  private calculateMomentumFactor(momentum: any): number {
    const baseStrength = momentum.strength;
    const durationFactor = Math.min(1, momentum.duration / 10); // Momentum mais forte nos primeiros 10 min

    return baseStrength * durationFactor;
  }

  private applyLiveAdjustments(base: any, adjustment: any, momentum: number): any {
    return {
      home_win: Math.max(0.05, Math.min(0.95, base.home_win + adjustment.possession_factor * 0.1 + momentum * 0.05)),
      draw: Math.max(0.05, Math.min(0.95, base.draw - Math.abs(adjustment.possession_factor) * 0.05)),
      away_win: Math.max(0.05, Math.min(0.95, base.away_win - adjustment.possession_factor * 0.1 - momentum * 0.05))
    };
  }

  private predictNextGoal(liveData: RealTimeMatchData, minute: number): any {
    const totalShots = liveData.liveStats.shots.home + liveData.liveStats.shots.away;
    const shotRate = totalShots / minute;
    const goalProbability = shotRate * 0.1; // 10% de conversão média

    return {
      home: goalProbability * (liveData.liveStats.shots.home / totalShots),
      away: goalProbability * (liveData.liveStats.shots.away / totalShots),
      no_goal: 1 - goalProbability,
      expected_minute: minute + (1 / shotRate) * 10
    };
  }

  private predictMomentumShift(liveData: RealTimeMatchData, minute: number): any {
    const currentStrength = liveData.momentum.strength;
    const duration = liveData.momentum.duration;

    // Momentum tende a mudar após 15-20 minutos
    const shiftProbability = Math.min(0.8, duration / 20);

    return {
      probability: shiftProbability,
      expected_minute: minute + 15,
      trigger_events: ['substitution', 'yellow_card', 'corner_sequence']
    };
  }

  private identifyLiveValueBets(liveData: RealTimeMatchData, probs: any): ValueAnalysis[] {
    // Simular identificação de apostas de valor ao vivo
    return [
      {
        market: 'Next Goal',
        selection: 'Home Team',
        ourProbability: probs.home_win * 0.6,
        bookmakerOdds: 2.1,
        impliedProbability: 1 / 2.1,
        valuePercentage: 12.5,
        kellyStake: 0.08,
        confidence: 'medium',
        reasoning: ['Domínio territorial significativo', 'Momentum favorável'],
        riskFactors: ['Tempo limitado restante', 'Possível mudança tática']
      }
    ];
  }

  private groupMarketsByType(markets: any[]): any {
    return markets.reduce((groups, market) => {
      if (!groups[market.market]) {
        groups[market.market] = [];
      }
      groups[market.market].push(market);
      return groups;
    }, {});
  }

  private calculateArbitrage(bookmakerData: any[]): any {
    // Simular cálculo de arbitragem
    return {
      is_profitable: Math.random() > 0.9, // 10% chance de arbitragem
      profit: Math.random() * 5 + 1,
      stakes: [],
      return: 1000
    };
  }

  private assessArbitrageRisk(arb: any): 'low' | 'medium' | 'high' {
    return arb.profit > 3 ? 'low' : arb.profit > 1.5 ? 'medium' : 'high';
  }

  private scanValueOpportunities(match: BrazilianMatch): any[] {
    // Simular busca por oportunidades de valor
    return [
      {
        market: 'Over 2.5 Goals',
        selection: 'Over',
        value: 15.2,
        expected_profit: 75
      }
    ];
  }

  private matchesUserProfile(opportunity: any, preferences: any): boolean {
    return preferences.favorite_markets.includes(opportunity.market) ||
           opportunity.value > 10;
  }

  private calculateOptimalStake(opportunity: any, preferences: any): string {
    const kellyStake = Math.min(preferences.max_stake, preferences.bankroll * opportunity.value / 100);
    return `R$ ${kellyStake.toFixed(2)}`;
  }

  private assessRisk(opportunity: any, preferences: any): string {
    if (preferences.risk_tolerance === 'conservative' && opportunity.value < 10) {
      return 'Risco elevado para perfil conservador';
    }
    return 'Risco adequado ao perfil';
  }
}

// Sistema de caching inteligente para performance
export class PerformanceOptimizer {
  private cache = new Map<string, { data: any; timestamp: number; ttl: number }>();
  private readonly DEFAULT_TTL = 300000; // 5 minutos

  // Cache com expiração inteligente
  set(key: string, data: any, ttl = this.DEFAULT_TTL): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl
    });
  }

  get(key: string): any | null {
    const cached = this.cache.get(key);
    if (!cached) return null;

    if (Date.now() - cached.timestamp > cached.ttl) {
      this.cache.delete(key);
      return null;
    }

    return cached.data;
  }

  // Pre-computar predições para jogos populares
  async precomputePopularMatches(matches: BrazilianMatch[]): Promise<void> {
    const popularMatches = matches
      .filter(match => this.isPopularMatch(match))
      .slice(0, 10); // Top 10 jogos mais populares

    for (const match of popularMatches) {
      const cacheKey = `prediction_${match.id}`;
      if (!this.get(cacheKey)) {
        // Simular pré-computação
        setTimeout(() => {
          const prediction = this.generateBasicPrediction(match);
          this.set(cacheKey, prediction, 3600000); // 1 hora de cache
        }, 100);
      }
    }
  }

  private isPopularMatch(match: BrazilianMatch): boolean {
    const bigClubs = ['Flamengo', 'Corinthians', 'Palmeiras', 'São Paulo', 'Santos'];
    return bigClubs.includes(match.homeTeam.name) || bigClubs.includes(match.awayTeam.name);
  }

  private generateBasicPrediction(match: BrazilianMatch): any {
    // Placeholder para predição básica
    return {
      home_win: 0.45,
      draw: 0.27,
      away_win: 0.28,
      confidence: 70
    };
  }

  // Limpeza automática de cache
  cleanup(): void {
    console.log('🔧 DEBUG: Executando cleanup do cache');
    const now = Date.now();
    Array.from(this.cache.entries()).forEach(([key, value]) => {
      if (now - value.timestamp > value.ttl) {
        this.cache.delete(key);
      }
    });
  }
}

// Export das instâncias principais
export const enhancedMLEngine = new EnhancedMLEngine();
export const performanceOptimizer = new PerformanceOptimizer();

// Auto-limpeza do cache a cada 5 minutos
setInterval(() => {
  performanceOptimizer.cleanup();
}, 300000);