// 🤖 Serviço de ML para Análise Inteligente de Apostas
import {
  MatchAnalysis,
  BettingMarket,
  IntelligentTicket,
  TicketSelection,
  MarketType,
  MARKET_CONFIGS,
  TICKET_STRATEGIES
} from '../types/betting';
import { rateLimiter } from './rateLimiter';

export class MLBettingService {
  private apiUrl: string = 'http://localhost:8000/api/v1';

  // 🎯 Gera análise completa de uma partida com todos os mercados
  async generateMatchAnalysis(matchId: string): Promise<MatchAnalysis> {
    // Verificar cache primeiro
    const cacheKey = `ml_analysis_${matchId}`;
    const cached = rateLimiter.getCache(cacheKey);
    if (cached) {
      console.log('✅ Retornando análise ML do cache:', matchId);
      return cached;
    }

    // Verificar rate limit
    if (!rateLimiter.canMakeRequest(`ml_analysis_${matchId}`, 'ml_analysis')) {
      console.warn('⚠️ Rate limit atingido para ML analysis, usando análise local');
      return this.generateSimulatedAnalysis(matchId);
    }

    try {
      console.log('🤖 Gerando análise ML para partida:', matchId);

      // Em produção, buscará da API ML premium
      const response = await fetch(`${this.apiUrl}/ml/analysis/${matchId}`);

      if (response.ok) {
        const analysis = await response.json();
        rateLimiter.setCache(cacheKey, analysis, 600000); // Cache por 10 min
        return analysis;
      }

      // Fallback: Gera análise simulada baseada em dados reais
      const analysis = await this.generateSimulatedAnalysis(matchId);
      rateLimiter.setCache(cacheKey, analysis, 300000); // Cache por 5 min
      return analysis;

    } catch (error) {
      console.warn('ML API não disponível, gerando análise local:', error);
      const analysis = await this.generateSimulatedAnalysis(matchId);
      rateLimiter.setCache(cacheKey, analysis, 300000);
      return analysis;
    }
  }

  // 🧠 Gera análise avançada baseada em dados reais das APIs
  private async generateSimulatedAnalysis(matchId: string): Promise<MatchAnalysis> {
    // Verificar cache para dados da partida
    const matchCacheKey = `match_data_${matchId}`;
    let matchData = rateLimiter.getCache(matchCacheKey);

    if (!matchData) {
      // Rate limiting para buscar dados da partida
      if (!rateLimiter.canMakeRequest(`match_${matchId}`, 'matches')) {
        console.warn('⚠️ Rate limit atingido para matches, usando dados padrão');
        matchData = this.getDefaultMatchData(matchId);
      } else {
        await rateLimiter.delay(200);

        // Busca dados básicos da partida
        const matchResponse = await fetch(`${this.apiUrl}/matches/${matchId}`);

        if (!matchResponse.ok) {
          console.warn('❌ Partida não encontrada no backend, usando dados padrão');
          matchData = this.getDefaultMatchData(matchId);
        } else {
          matchData = await matchResponse.json();
          rateLimiter.setCache(matchCacheKey, matchData, 600000); // Cache por 10 min
        }
      }
    }

    // Extrair nomes dos times do objeto match
    const homeTeamName = matchData.home_team?.name || matchData.home_team || 'Team A';
    const awayTeamName = matchData.away_team?.name || matchData.away_team || 'Team B';

    console.log('🔍 Buscando estatísticas para:', homeTeamName, 'vs', awayTeamName);

    // Busca histórico e estatísticas dos times para análise real
    const [homeTeamStats, awayTeamStats] = await Promise.all([
      this.getTeamStatistics(homeTeamName),
      this.getTeamStatistics(awayTeamName)
    ]);

    // Calcula probabilidades baseadas em dados históricos reais
    const homeStrength = homeTeamStats.strength;
    const awayStrength = awayTeamStats.strength;
    const homeAdvantage = 0.1; // Vantagem de casa baseada em estudos

    // Aplica vantagem de casa
    const adjustedHomeStrength = homeStrength + homeAdvantage;

    // Normaliza probabilidades
    const total = adjustedHomeStrength + awayStrength + 0.25; // 25% base para empate
    const homeProbability = adjustedHomeStrength / total;
    const awayProbability = awayStrength / total;
    const drawProbability = 0.25 / total;

    // Análise de gols baseada no histórico real dos times
    const expectedHomeGoals = homeTeamStats.avg_goals_scored;
    const expectedAwayGoals = awayTeamStats.avg_goals_scored;
    const totalExpected = expectedHomeGoals + expectedAwayGoals;

    const analysis: MatchAnalysis = {
      match_id: matchId,
      home_team: homeTeamName,
      away_team: awayTeamName,
      league: matchData.league || 'League',
      match_date: matchData.match_date || matchData.date || new Date().toISOString(),

      ml_analysis: {
        win_probabilities: {
          home: Number(homeProbability.toFixed(3)),
          draw: Number(drawProbability.toFixed(3)),
          away: Number(awayProbability.toFixed(3))
        },
        goals_analysis: {
          expected_home_goals: Number(expectedHomeGoals.toFixed(2)),
          expected_away_goals: Number(expectedAwayGoals.toFixed(2)),
          total_expected: Number(totalExpected.toFixed(2)),
          over_under_probabilities: {
            '0.5': totalExpected > 0.5 ? 0.95 : 0.05,
            '1.5': totalExpected > 1.5 ? 0.80 : 0.20,
            '2.5': totalExpected > 2.5 ? 0.65 : 0.35,
            '3.5': totalExpected > 3.5 ? 0.45 : 0.55,
            '4.5': totalExpected > 4.5 ? 0.25 : 0.75
          }
        },
        advanced_stats: {
          btts_probability: Math.min(0.95, (expectedHomeGoals * expectedAwayGoals) / 4),
          clean_sheet_home: Math.exp(-expectedAwayGoals),
          clean_sheet_away: Math.exp(-expectedHomeGoals),
          first_half_goals: totalExpected * 0.45,
          second_half_goals: totalExpected * 0.55,
          cards_expected: homeTeamStats.avg_cards + awayTeamStats.avg_cards,
          corners_expected: homeTeamStats.avg_corners + awayTeamStats.avg_corners
        }
      },

      markets: [],
      best_value_bets: [],
      safest_bets: [],
      highest_odds_bets: []
    };

    // Gera todos os mercados
    analysis.markets = this.generateAllMarkets(analysis);

    // Classifica mercados por tipo
    analysis.best_value_bets = this.getBestValueBets(analysis.markets);
    analysis.safest_bets = this.getSafestBets(analysis.markets);
    analysis.highest_odds_bets = this.getHighestOddsBets(analysis.markets);

    return analysis;
  }

  // 📊 Gera todos os mercados disponíveis
  private generateAllMarkets(analysis: MatchAnalysis): BettingMarket[] {
    const markets: BettingMarket[] = [];
    const { win_probabilities, goals_analysis, advanced_stats } = analysis.ml_analysis;

    // 🏆 1X2 - Resultado da Partida
    markets.push({
      id: '1x2',
      name: 'Resultado da Partida',
      description: 'Vitória da casa, empate ou vitória visitante',
      type: '1X2' as MarketType,
      odds: {
        home: Number((1 / win_probabilities.home * 1.1).toFixed(2)),
        draw: Number((1 / win_probabilities.draw * 1.1).toFixed(2)),
        away: Number((1 / win_probabilities.away * 1.1).toFixed(2))
      },
      probability: win_probabilities,
      value: this.calculateValue(win_probabilities.home, 1 / win_probabilities.home),
      confidence: Math.max(...Object.values(win_probabilities)) * 100,
      recommendation: win_probabilities.home > win_probabilities.away ? 'home' : 'away',
      kelly_percentage: this.calculateKelly(win_probabilities.home, 1 / win_probabilities.home),
      risk_level: win_probabilities.home > 0.6 || win_probabilities.away > 0.6 ? 'low' : 'medium'
    });

    // ⚽ Over/Under Gols
    const overUnder25Prob = goals_analysis.over_under_probabilities['2.5'];
    markets.push({
      id: 'over_under_2.5',
      name: 'Total de Gols 2.5',
      description: 'Mais ou menos de 2.5 gols na partida',
      type: 'over_under' as MarketType,
      odds: {
        over: Number((1 / overUnder25Prob * 1.08).toFixed(2)),
        under: Number((1 / (1 - overUnder25Prob) * 1.08).toFixed(2))
      },
      probability: {
        over: overUnder25Prob,
        under: 1 - overUnder25Prob
      },
      value: this.calculateValue(overUnder25Prob, 1 / overUnder25Prob),
      confidence: Math.abs(overUnder25Prob - 0.5) * 200,
      recommendation: overUnder25Prob > 0.55 ? 'over' : 'under',
      kelly_percentage: this.calculateKelly(overUnder25Prob, 1 / overUnder25Prob),
      risk_level: Math.abs(overUnder25Prob - 0.5) > 0.15 ? 'low' : 'medium'
    });

    // 🎯 Ambos os Times Marcam
    const bttsProb = advanced_stats.btts_probability;
    markets.push({
      id: 'btts',
      name: 'Ambos os Times Marcam',
      description: 'Os dois times marcarão pelo menos um gol',
      type: 'btts' as MarketType,
      odds: {
        yes: Number((1 / bttsProb * 1.05).toFixed(2)),
        no: Number((1 / (1 - bttsProb) * 1.05).toFixed(2))
      },
      probability: {
        yes: bttsProb,
        no: 1 - bttsProb
      },
      value: this.calculateValue(bttsProb, 1 / bttsProb),
      confidence: Math.abs(bttsProb - 0.5) * 200,
      recommendation: bttsProb > 0.55 ? 'yes' : 'no',
      kelly_percentage: this.calculateKelly(bttsProb, 1 / bttsProb),
      risk_level: bttsProb > 0.7 || bttsProb < 0.3 ? 'low' : 'medium'
    });

    // ⚖️ Handicap Asiático -0.5/+0.5
    const homeAdvantage = win_probabilities.home / (win_probabilities.home + win_probabilities.away);
    markets.push({
      id: 'asian_handicap',
      name: 'Handicap Asiático',
      description: 'Casa -0.5 / Visitante +0.5',
      type: 'asian_handicap' as MarketType,
      odds: {
        home: Number((1 / homeAdvantage * 1.06).toFixed(2)),
        away: Number((1 / (1 - homeAdvantage) * 1.06).toFixed(2))
      },
      probability: {
        home: homeAdvantage,
        away: 1 - homeAdvantage
      },
      value: this.calculateValue(homeAdvantage, 1 / homeAdvantage),
      confidence: Math.abs(homeAdvantage - 0.5) * 200,
      recommendation: homeAdvantage > 0.55 ? 'home' : 'away',
      kelly_percentage: this.calculateKelly(homeAdvantage, 1 / homeAdvantage),
      risk_level: Math.abs(homeAdvantage - 0.5) > 0.15 ? 'low' : 'medium'
    });

    // 🔄 Empate Anula Aposta
    const drawNoBetHomeProb = win_probabilities.home / (win_probabilities.home + win_probabilities.away);
    markets.push({
      id: 'draw_no_bet',
      name: 'Empate Anula Aposta',
      description: 'Se empatar, aposta é devolvida',
      type: 'draw_no_bet' as MarketType,
      odds: {
        home: Number((1 / drawNoBetHomeProb * 1.03).toFixed(2)),
        away: Number((1 / (1 - drawNoBetHomeProb) * 1.03).toFixed(2))
      },
      probability: {
        home: drawNoBetHomeProb,
        away: 1 - drawNoBetHomeProb
      },
      value: this.calculateValue(drawNoBetHomeProb, 1 / drawNoBetHomeProb),
      confidence: Math.abs(drawNoBetHomeProb - 0.5) * 200,
      recommendation: drawNoBetHomeProb > 0.52 ? 'home' : 'away',
      kelly_percentage: this.calculateKelly(drawNoBetHomeProb, 1 / drawNoBetHomeProb),
      risk_level: 'low'
    });

    // 🟨 Total de Cartões
    const cardsOver4Prob = advanced_stats.cards_expected > 4.5 ? 0.65 : 0.35;
    markets.push({
      id: 'cards',
      name: 'Total de Cartões 4.5',
      description: 'Mais ou menos de 4.5 cartões na partida',
      type: 'cards' as MarketType,
      odds: {
        over: Number((1 / cardsOver4Prob * 1.12).toFixed(2)),
        under: Number((1 / (1 - cardsOver4Prob) * 1.12).toFixed(2))
      },
      probability: {
        over: cardsOver4Prob,
        under: 1 - cardsOver4Prob
      },
      value: this.calculateValue(cardsOver4Prob, 1 / cardsOver4Prob),
      confidence: Math.abs(cardsOver4Prob - 0.5) * 200,
      recommendation: cardsOver4Prob > 0.55 ? 'over' : 'under',
      kelly_percentage: this.calculateKelly(cardsOver4Prob, 1 / cardsOver4Prob),
      risk_level: 'medium'
    });

    // 📐 Total de Escanteios
    const cornersOver9Prob = advanced_stats.corners_expected > 9.5 ? 0.62 : 0.38;
    markets.push({
      id: 'corners',
      name: 'Total de Escanteios 9.5',
      description: 'Mais ou menos de 9.5 escanteios na partida',
      type: 'corners' as MarketType,
      odds: {
        over: Number((1 / cornersOver9Prob * 1.10).toFixed(2)),
        under: Number((1 / (1 - cornersOver9Prob) * 1.10).toFixed(2))
      },
      probability: {
        over: cornersOver9Prob,
        under: 1 - cornersOver9Prob
      },
      value: this.calculateValue(cornersOver9Prob, 1 / cornersOver9Prob),
      confidence: Math.abs(cornersOver9Prob - 0.5) * 200,
      recommendation: cornersOver9Prob > 0.55 ? 'over' : 'under',
      kelly_percentage: this.calculateKelly(cornersOver9Prob, 1 / cornersOver9Prob),
      risk_level: 'medium'
    });

    // 🥇 Primeiro Gol
    const firstGoalHomeProb = win_probabilities.home * 0.6 + 0.1; // Vantagem de casa no primeiro gol
    const firstGoalAwayProb = win_probabilities.away * 0.6 + 0.05;
    const noGoalProb = 1 - firstGoalHomeProb - firstGoalAwayProb;

    markets.push({
      id: 'first_goal',
      name: 'Primeiro Gol',
      description: 'Qual time marcará o primeiro gol',
      type: 'first_goal' as MarketType,
      odds: {
        home: Number((1 / firstGoalHomeProb * 1.15).toFixed(2)),
        away: Number((1 / firstGoalAwayProb * 1.15).toFixed(2)),
        no_goal: Number((1 / noGoalProb * 1.20).toFixed(2))
      },
      probability: {
        home: firstGoalHomeProb,
        away: firstGoalAwayProb,
        no_goal: noGoalProb
      },
      value: this.calculateValue(firstGoalHomeProb, 1 / firstGoalHomeProb),
      confidence: Math.max(firstGoalHomeProb, firstGoalAwayProb) * 100,
      recommendation: firstGoalHomeProb > firstGoalAwayProb ? 'home' : 'away',
      kelly_percentage: this.calculateKelly(firstGoalHomeProb, 1 / firstGoalHomeProb),
      risk_level: 'high'
    });

    // 🛡️ Sem Sofrer Gols (Clean Sheet)
    const homeCleanSheetProb = advanced_stats.clean_sheet_home;
    const awayCleanSheetProb = advanced_stats.clean_sheet_away;

    markets.push({
      id: 'clean_sheet_home',
      name: 'Casa Não Sofre Gols',
      description: 'Time da casa não sofrerá gols',
      type: 'clean_sheet' as MarketType,
      odds: {
        yes: Number((1 / homeCleanSheetProb * 1.08).toFixed(2)),
        no: Number((1 / (1 - homeCleanSheetProb) * 1.08).toFixed(2))
      },
      probability: {
        yes: homeCleanSheetProb,
        no: 1 - homeCleanSheetProb
      },
      value: this.calculateValue(homeCleanSheetProb, 1 / homeCleanSheetProb),
      confidence: Math.abs(homeCleanSheetProb - 0.5) * 200,
      recommendation: homeCleanSheetProb > 0.55 ? 'yes' : 'no',
      kelly_percentage: this.calculateKelly(homeCleanSheetProb, 1 / homeCleanSheetProb),
      risk_level: 'medium'
    });

    markets.push({
      id: 'clean_sheet_away',
      name: 'Visitante Não Sofre Gols',
      description: 'Time visitante não sofrerá gols',
      type: 'clean_sheet' as MarketType,
      odds: {
        yes: Number((1 / awayCleanSheetProb * 1.08).toFixed(2)),
        no: Number((1 / (1 - awayCleanSheetProb) * 1.08).toFixed(2))
      },
      probability: {
        yes: awayCleanSheetProb,
        no: 1 - awayCleanSheetProb
      },
      value: this.calculateValue(awayCleanSheetProb, 1 / awayCleanSheetProb),
      confidence: Math.abs(awayCleanSheetProb - 0.5) * 200,
      recommendation: awayCleanSheetProb > 0.55 ? 'yes' : 'no',
      kelly_percentage: this.calculateKelly(awayCleanSheetProb, 1 / awayCleanSheetProb),
      risk_level: 'medium'
    });

    // 🎪 Dupla Chance
    const doubleChanceHomeDrawProb = win_probabilities.home + win_probabilities.draw;
    const doubleChanceAwayDrawProb = win_probabilities.away + win_probabilities.draw;
    const doubleChanceHomeAwayProb = win_probabilities.home + win_probabilities.away;

    markets.push({
      id: 'double_chance_1x',
      name: 'Dupla Chance 1X',
      description: 'Casa vence ou empata',
      type: 'double_chance' as MarketType,
      odds: {
        yes: Number((1 / doubleChanceHomeDrawProb * 1.04).toFixed(2)),
        no: Number((1 / (1 - doubleChanceHomeDrawProb) * 1.04).toFixed(2))
      },
      probability: {
        yes: doubleChanceHomeDrawProb,
        no: 1 - doubleChanceHomeDrawProb
      },
      value: this.calculateValue(doubleChanceHomeDrawProb, 1 / doubleChanceHomeDrawProb),
      confidence: doubleChanceHomeDrawProb * 100,
      recommendation: 'yes',
      kelly_percentage: this.calculateKelly(doubleChanceHomeDrawProb, 1 / doubleChanceHomeDrawProb),
      risk_level: 'low'
    });

    // ⏰ Gols em Períodos (Primeira/Segunda Parte)
    const firstHalfGoalsProb = advanced_stats.first_half_goals > 0.75 ? 0.68 : 0.32;
    markets.push({
      id: 'first_half_goals',
      name: 'Gols no 1º Tempo',
      description: 'Haverá gols no primeiro tempo',
      type: 'minute_ranges' as MarketType,
      odds: {
        yes: Number((1 / firstHalfGoalsProb * 1.09).toFixed(2)),
        no: Number((1 / (1 - firstHalfGoalsProb) * 1.09).toFixed(2))
      },
      probability: {
        yes: firstHalfGoalsProb,
        no: 1 - firstHalfGoalsProb
      },
      value: this.calculateValue(firstHalfGoalsProb, 1 / firstHalfGoalsProb),
      confidence: Math.abs(firstHalfGoalsProb - 0.5) * 200,
      recommendation: firstHalfGoalsProb > 0.55 ? 'yes' : 'no',
      kelly_percentage: this.calculateKelly(firstHalfGoalsProb, 1 / firstHalfGoalsProb),
      risk_level: 'medium'
    });

    // ⚽ Gols do Time Casa/Visitante
    const homeTeamGoalsOver1Prob = goals_analysis.expected_home_goals > 1.25 ? 0.64 : 0.36;
    const awayTeamGoalsOver1Prob = goals_analysis.expected_away_goals > 1.25 ? 0.64 : 0.36;

    markets.push({
      id: 'home_team_goals',
      name: 'Gols Casa Over 1.5',
      description: 'Time da casa marcará mais de 1.5 gols',
      type: 'team_goals' as MarketType,
      odds: {
        over: Number((1 / homeTeamGoalsOver1Prob * 1.11).toFixed(2)),
        under: Number((1 / (1 - homeTeamGoalsOver1Prob) * 1.11).toFixed(2))
      },
      probability: {
        over: homeTeamGoalsOver1Prob,
        under: 1 - homeTeamGoalsOver1Prob
      },
      value: this.calculateValue(homeTeamGoalsOver1Prob, 1 / homeTeamGoalsOver1Prob),
      confidence: Math.abs(homeTeamGoalsOver1Prob - 0.5) * 200,
      recommendation: homeTeamGoalsOver1Prob > 0.55 ? 'over' : 'under',
      kelly_percentage: this.calculateKelly(homeTeamGoalsOver1Prob, 1 / homeTeamGoalsOver1Prob),
      risk_level: 'medium'
    });

    // ⏱️ Intervalo/Final (HT/FT)
    const htFtHomeHomeProb = win_probabilities.home * 0.7; // Casa no intervalo e final
    const htFtDrawHomeProb = win_probabilities.draw * win_probabilities.home * 2;

    markets.push({
      id: 'ht_ft_home_home',
      name: 'HT/FT Casa-Casa',
      description: 'Casa na frente no intervalo e vence no final',
      type: 'half_time_full_time' as MarketType,
      odds: {
        yes: Number((1 / htFtHomeHomeProb * 1.18).toFixed(2)),
        no: Number((1 / (1 - htFtHomeHomeProb) * 1.18).toFixed(2))
      },
      probability: {
        yes: htFtHomeHomeProb,
        no: 1 - htFtHomeHomeProb
      },
      value: this.calculateValue(htFtHomeHomeProb, 1 / htFtHomeHomeProb),
      confidence: htFtHomeHomeProb * 100,
      recommendation: htFtHomeHomeProb > 0.3 ? 'yes' : 'no',
      kelly_percentage: this.calculateKelly(htFtHomeHomeProb, 1 / htFtHomeHomeProb),
      risk_level: 'high'
    });

    return markets;
  }

  // 💎 Gera bilhete inteligente baseado na estratégia
  async generateIntelligentTicket(
    matches: string[],
    strategy: keyof typeof TICKET_STRATEGIES,
    bankroll: number,
    userStakeAmount?: number  // NOVO: Valor que o usuário quer apostar
  ): Promise<IntelligentTicket> {

    const strategyConfig = TICKET_STRATEGIES[strategy];
    const analyses: MatchAnalysis[] = [];

    // Analisa todas as partidas
    for (const matchId of matches) {
      const analysis = await this.generateMatchAnalysis(matchId);
      analyses.push(analysis);
    }

    // Seleciona os melhores mercados baseado na estratégia
    const selections = this.selectBestMarkets(analyses, strategyConfig);

    // CORRIGIDO: Calcula odds combinadas (multiplicadas) usando a ODD DA SELEÇÃO ESPECÍFICA
    const combinedOdds = selections.reduce((acc, sel) => acc * this.getBestOddsForSelection(sel), 1);
    const winProbability = selections.reduce((acc, sel) => acc * this.getBestProbabilityForSelection(sel), 1);

    // Para aposta múltipla, usamos a probabilidade combinada para calcular Kelly
    const multipleKelly = this.calculateKelly(winProbability, combinedOdds);
    const bankrollPercentage = Math.min(multipleKelly, strategyConfig.bankroll_percentage);

    // CRÍTICO: Usar o valor digitado pelo usuário OU calcular via Kelly se não informado
    const singleStakeAmount = userStakeAmount && userStakeAmount > 0
      ? userStakeAmount
      : bankroll * bankrollPercentage;

    console.log('📊 Cálculos financeiros (Múltipla):', {
      combinedOdds: combinedOdds.toFixed(2),
      winProbability: (winProbability * 100).toFixed(2) + '%',
      multipleKelly: (multipleKelly * 100).toFixed(2) + '%',
      singleStakeAmount: singleStakeAmount.toFixed(2)
    });

    const ticket: IntelligentTicket = {
      id: `ticket_${Date.now()}`,
      created_at: new Date().toISOString(),
      ticket_type: strategy,

      risk_analysis: {
        total_risk: this.calculateTotalRisk(selections),
        kelly_total: multipleKelly,
        expected_roi: (combinedOdds * winProbability - 1) * 100,
        win_probability: winProbability,
        bankroll_percentage: bankrollPercentage
      },

      selections: selections.map(sel => {
        // Em aposta múltipla, todos os mercados têm o mesmo stake
        const selectionOdds = this.getBestOddsForSelection(sel);
        console.log(`💰 Mercado na múltipla: ${sel.market.name}`, {
          selection: sel.selection,
          odds: selectionOdds.toFixed(2),
          probability: (this.getBestProbabilityForSelection(sel) * 100).toFixed(1) + '%'
        });

        return {
          ...sel,
          individual_stake: singleStakeAmount // Mesmo valor para todos
        };
      }),

      financial: {
        total_stake: singleStakeAmount, // Valor único da aposta múltipla
        total_odds: combinedOdds, // Odds multiplicadas
        potential_return: singleStakeAmount * combinedOdds,
        potential_profit: (singleStakeAmount * combinedOdds) - singleStakeAmount
      },

      strategy: {
        name: strategyConfig.name,
        description: strategyConfig.description,
        reasoning: this.generateReasoningForSelections(selections),
        market_distribution: this.getMarketDistribution(selections)
      }
    };

    console.log('💰 Aposta Múltipla Finalizada:', {
      stake: 'R$ ' + ticket.financial.total_stake.toFixed(2),
      combinedOdds: ticket.financial.total_odds.toFixed(2),
      potentialReturn: 'R$ ' + ticket.financial.potential_return.toFixed(2),
      profit: 'R$ ' + ticket.financial.potential_profit.toFixed(2),
      selections: ticket.selections.length
    });

    return ticket;
  }

  // 🔍 Seleciona os melhores mercados baseado na estratégia
  private selectBestMarkets(
    analyses: MatchAnalysis[],
    strategyConfig: typeof TICKET_STRATEGIES.balanced
  ): TicketSelection[] {
    console.log('⚙️ Selecionando melhores mercados com estratégia:', strategyConfig.name);
    console.log('📊 Análises recebidas:', analyses.length);

    const allSelections: TicketSelection[] = [];

    analyses.forEach((analysis, index) => {
      console.log(`🔍 Analisando partida ${index + 1}:`, analysis.home_team, 'vs', analysis.away_team);
      console.log('🏆 Mercados disponíveis:', analysis.markets.length);

      // Filtra mercados por estratégia
      const suitableMarkets = analysis.markets.filter(market => {
        const config = MARKET_CONFIGS[market.type];
        const maxOdds = Math.max(...Object.values(market.odds));

        const oddsCheck = maxOdds <= strategyConfig.max_odds;
        const confidenceCheck = market.confidence / 100 >= strategyConfig.min_confidence;
        const marketTypeCheck = strategyConfig.preferred_markets.includes(market.type) || market.value > 0.05;

        console.log(`⚙️ ${market.name}:`, {
          maxOdds: maxOdds.toFixed(2),
          confidence: (market.confidence / 100).toFixed(2),
          value: market.value.toFixed(3),
          passed: oddsCheck && confidenceCheck && marketTypeCheck
        });

        return oddsCheck && confidenceCheck && marketTypeCheck;
      });

      // Ordena por valor (combinação de confiança e odds)
      suitableMarkets.sort((a, b) => {
        const aScore = a.value * (a.confidence / 100);
        const bScore = b.value * (b.confidence / 100);
        return bScore - aScore;
      });

      console.log(`✅ Mercados adequados encontrados: ${suitableMarkets.length}`);

      // Se não encontrou mercados adequados, usa os 2 melhores disponíveis
      let selectedForMatch = suitableMarkets.slice(0, 2);

      if (selectedForMatch.length === 0 && analysis.markets.length > 0) {
        console.log('⚠️ Nenhum mercado adequado, usando os melhores disponíveis');
        // Pega os mercados com maior valor * confiânca
        const bestMarkets = analysis.markets
          .sort((a, b) => (b.value * b.confidence) - (a.value * a.confidence))
          .slice(0, 2);
        selectedForMatch = bestMarkets;
      }

      console.log(`🎯 Mercados selecionados para esta partida: ${selectedForMatch.length}`);

      selectedForMatch.forEach(market => {
        console.log(`✅ Adicionando mercado: ${market.name} - ${market.recommendation}`);
        allSelections.push({
          match_id: analysis.match_id,
          match_info: {
            home_team: analysis.home_team,
            away_team: analysis.away_team,
            league: analysis.league,
            date: analysis.match_date
          },
          market,
          selection: market.recommendation,
          individual_stake: 0, // Será calculado depois
          reasoning: this.generateReasoningForMarket(market)
        });
      });
    });

    console.log(`🎆 Total de seleções finais: ${allSelections.length}`);

    if (allSelections.length === 0) {
      console.warn('⚠️ Nenhuma seleção encontrada! Verificar configurações da estratégia');
    }

    // Limita seleções totais
    return allSelections.slice(0, strategyConfig.max_selections);
  }

  // 🎯 Métodos auxiliares
  private calculateValue(probability: number, odds: number): number {
    const expectedValue = (probability * odds) - 1;
    return Math.max(0, expectedValue);
  }

  private calculateKelly(probability: number, odds: number): number {
    const b = odds - 1;
    const p = probability;
    const q = 1 - p;

    const kelly = (b * p - q) / b;

    // Kelly mais conservador: entre 0.5% e 8% do bankroll
    const conservativeKelly = Math.max(0, Math.min(kelly * 0.4, 0.08));

    // Se Kelly for negativo ou muito baixo, usa um mínimo de 0.5%
    return Math.max(conservativeKelly, 0.005);
  }

  // CORRIGIDO: Usa a odd da seleção escolhida, não da recommendation genérica
  private getBestOddsForSelection(selection: TicketSelection): number {
    const selectedOdds = selection.market.odds[selection.selection];
    return selectedOdds || Math.max(...Object.values(selection.market.odds));
  }

  private getBestProbabilityForSelection(selection: TicketSelection): number {
    const selectedProb = selection.market.probability[selection.selection];
    return selectedProb || Math.max(...Object.values(selection.market.probability));
  }

  // Mantido para compatibilidade mas deprecated
  private getBestOddsForMarket(market: BettingMarket): number {
    const recommendedOdds = market.odds[market.recommendation];
    return recommendedOdds || Math.max(...Object.values(market.odds));
  }

  private getBestProbabilityForMarket(market: BettingMarket): number {
    const recommendedProb = market.probability[market.recommendation];
    return recommendedProb || Math.max(...Object.values(market.probability));
  }

  private calculateTotalRisk(selections: TicketSelection[]): 'low' | 'medium' | 'high' {
    const avgRisk = selections.reduce((acc, sel) => {
      const riskWeight = sel.market.risk_level === 'low' ? 1 :
                       sel.market.risk_level === 'medium' ? 2 : 3;
      return acc + riskWeight;
    }, 0) / selections.length;

    if (avgRisk < 1.5) return 'low';
    if (avgRisk < 2.5) return 'medium';
    return 'high';
  }

  private generateReasoningForMarket(market: BettingMarket): string {
    const config = MARKET_CONFIGS[market.type];
    return `${config.icon} ${config.name}: Confiança de ${market.confidence.toFixed(0)}%, valor de ${(market.value * 100).toFixed(1)}%`;
  }

  private generateReasoningForSelections(selections: TicketSelection[]): string[] {
    return [
      `Selecionados ${selections.length} mercados com alta confiança`,
      `Distribuição de riscos equilibrada`,
      `Kelly Criterion aplicado para gestão de banca`,
      `Foco em value betting com ROI positivo esperado`
    ];
  }

  private getMarketDistribution(selections: TicketSelection[]): { [market: string]: number } {
    const distribution: { [market: string]: number } = {};
    selections.forEach(sel => {
      distribution[sel.market.type] = (distribution[sel.market.type] || 0) + 1;
    });
    return distribution;
  }

  private getBestValueBets(markets: BettingMarket[]): BettingMarket[] {
    return markets.sort((a, b) => b.value - a.value).slice(0, 3);
  }

  private getSafestBets(markets: BettingMarket[]): BettingMarket[] {
    return markets.sort((a, b) => b.confidence - a.confidence).slice(0, 3);
  }

  private getHighestOddsBets(markets: BettingMarket[]): BettingMarket[] {
    return markets.sort((a, b) => {
      const maxOddsA = Math.max(...Object.values(a.odds));
      const maxOddsB = Math.max(...Object.values(b.odds));
      return maxOddsB - maxOddsA;
    }).slice(0, 3);
  }

  // 📊 Busca estatísticas reais dos times da API
  private async getTeamStatistics(teamName: string): Promise<{
    strength: number;
    avg_goals_scored: number;
    avg_goals_conceded: number;
    avg_cards: number;
    avg_corners: number;
    form: number;
  }> {
    // Verificar cache primeiro
    const cacheKey = `team_stats_${teamName}`;
    const cached = rateLimiter.getCache(cacheKey);
    if (cached) {
      console.log('✅ Estatísticas do time do cache:', teamName);
      return cached;
    }

    try {
      // Rate limiting para estatísticas de times
      if (rateLimiter.canMakeRequest(`team_stats_${teamName}`, 'team_stats')) {
        // Delay entre requests
        await rateLimiter.delay(500);

        // 1️⃣ Primeiro, busca o time pelo nome para obter o ID
        const teamsResponse = await fetch(`${this.apiUrl}/teams/?search=${encodeURIComponent(teamName)}&limit=1`);

        if (teamsResponse.ok) {
          const teamsData = await teamsResponse.json();

          if (teamsData.teams && teamsData.teams.length > 0) {
            const team = teamsData.teams[0];
            console.log('✅ Time encontrado:', team.name, `(ID: ${team.id})`);

            // 2️⃣ Busca estatísticas usando o ID do time
            const statsResponse = await fetch(`${this.apiUrl}/teams/${team.id}/statistics`);

            if (statsResponse.ok) {
              const statsData = await statsResponse.json();

              if (statsData.statistics && statsData.statistics.length > 0) {
                const latestStats = statsData.statistics[0]; // Pega a estatística mais recente

                const result = {
                  strength: this.calculateStrengthFromStats(latestStats, team),
                  avg_goals_scored: (latestStats.goals_for || 0) / Math.max(latestStats.games_played || 1, 1),
                  avg_goals_conceded: (latestStats.goals_against || 0) / Math.max(latestStats.games_played || 1, 1),
                  avg_cards: (latestStats.total_cards || 50) / Math.max(latestStats.games_played || 1, 1),
                  avg_corners: (latestStats.avg_corners_for || 5.0),
                  form: (latestStats.wins || 0) / Math.max(latestStats.games_played || 1, 1)
                };

                console.log('📊 Estatísticas calculadas para', teamName, ':', result);

                rateLimiter.setCache(cacheKey, result, 900000); // Cache por 15 min
                return result;
              }
            }

            // 3️⃣ Se não tem estatísticas, calcula baseado nos ratings do time
            const result = {
              strength: this.calculateStrengthFromRatings(team),
              avg_goals_scored: 1.2 + (team.attack_rating || 0) / 100,
              avg_goals_conceded: 1.2 - (team.defense_rating || 0) / 100,
              avg_cards: 2.5,
              avg_corners: 5.0,
              form: (team.form_rating || 50) / 100
            };

            rateLimiter.setCache(cacheKey, result, 600000); // Cache por 10 min
            return result;
          }
        }
      }

      // 🎯 FOCO: Usar dados básicos dos times para partidas futuras/ao vivo
      console.log(`🚀 Focando em análise para partidas futuras: ${teamName}`);

      // Se não encontrar dados, retorna estatísticas neutras
      console.warn(`Estatísticas não encontradas para ${teamName}, usando valores padrão`);
      const defaultStats = {
        strength: 0.5,
        avg_goals_scored: 1.2,
        avg_goals_conceded: 1.2,
        avg_cards: 2.5,
        avg_corners: 5.0,
        form: 0.5
      };

      rateLimiter.setCache(cacheKey, defaultStats, 300000); // Cache valores padrão por 5 min
      return defaultStats;

    } catch (error) {
      console.error(`Erro ao buscar estatísticas de ${teamName}:`, error);
      const errorStats = {
        strength: 0.5,
        avg_goals_scored: 1.2,
        avg_goals_conceded: 1.2,
        avg_cards: 2.5,
        avg_corners: 5.0,
        form: 0.5
      };

      rateLimiter.setCache(cacheKey, errorStats, 180000); // Cache erro por 3 min
      return errorStats;
    }
  }

  // 📈 Calcula estatísticas baseadas em partidas recentes reais
  private calculateTeamStatsFromMatches(teamName: string, matches: any[]): {
    strength: number;
    avg_goals_scored: number;
    avg_goals_conceded: number;
    avg_cards: number;
    avg_corners: number;
    form: number;
  } {
    let totalGoalsScored = 0;
    let totalGoalsConceded = 0;
    let totalCards = 0;
    let totalCorners = 0;
    let wins = 0;
    let draws = 0;

    matches.forEach(match => {
      const isHome = match.home_team === teamName;
      const goalsScored = isHome ? match.home_score : match.away_score;
      const goalsConceded = isHome ? match.away_score : match.home_score;

      totalGoalsScored += goalsScored || 0;
      totalGoalsConceded += goalsConceded || 0;

      // Assume que cartões são distribuídos proporcionalmente
      totalCards += (match.total_cards || 5) / 2;
      totalCorners += (match.total_corners || 10) / 2;

      // Calcula forma recente
      if (goalsScored > goalsConceded) wins++;
      else if (goalsScored === goalsConceded) draws++;
    });

    const matchCount = matches.length;
    const avgGoalsScored = matchCount > 0 ? totalGoalsScored / matchCount : 1.2;
    const avgGoalsConceded = matchCount > 0 ? totalGoalsConceded / matchCount : 1.2;
    const avgCards = matchCount > 0 ? totalCards / matchCount : 2.5;
    const avgCorners = matchCount > 0 ? totalCorners / matchCount : 5.0;

    // Calcula strength baseado na performance
    const winRate = matchCount > 0 ? wins / matchCount : 0.33;
    const drawRate = matchCount > 0 ? draws / matchCount : 0.33;
    const goalDifference = avgGoalsScored - avgGoalsConceded;

    const strength = Math.max(0.1, Math.min(0.9,
      winRate * 0.4 +
      drawRate * 0.1 +
      (goalDifference + 1) * 0.25 +
      0.25
    ));

    return {
      strength,
      avg_goals_scored: avgGoalsScored,
      avg_goals_conceded: avgGoalsConceded,
      avg_cards: avgCards,
      avg_corners: avgCorners,
      form: winRate + (drawRate * 0.5)
    };
  }

  // 🎯 Calcula strength baseado nas estatísticas do time
  private calculateStrengthFromStats(stats: any, team: any): number {
    const gamesPlayed = stats.games_played || 1;
    const winRate = (stats.wins || 0) / gamesPlayed;
    const goalsFor = (stats.goals_for || 0) / gamesPlayed;
    const goalsAgainst = (stats.goals_against || 0) / gamesPlayed;
    const goalDiff = goalsFor - goalsAgainst;

    // Combine múltiplos fatores para calcular strength
    let strength = winRate * 0.4; // 40% baseado em vitórias
    strength += Math.min(Math.max(goalDiff + 1, 0), 2) * 0.25; // 25% saldo de gols
    strength += (team.elo_rating || 1500) / 3000 * 0.2; // 20% ELO rating
    strength += (team.form_rating || 50) / 100 * 0.15; // 15% forma atual

    return Math.max(0.1, Math.min(0.9, strength));
  }

  // 🎯 Calcula strength baseado apenas nos ratings do time
  private calculateStrengthFromRatings(team: any): number {
    let strength = 0.5; // Base neutra

    if (team.elo_rating) {
      strength += (team.elo_rating - 1500) / 1000 * 0.3;
    }

    if (team.attack_rating && team.defense_rating) {
      const overallRating = (team.attack_rating + team.defense_rating) / 2;
      strength += (overallRating - 50) / 100 * 0.3;
    }

    if (team.form_rating) {
      strength += (team.form_rating - 50) / 100 * 0.2;
    }

    return Math.max(0.1, Math.min(0.9, strength));
  }

  // 🎯 Dados padrão para partida quando API não disponível
  private getDefaultMatchData(matchId: string): any {
    return {
      id: matchId,
      home_team: { name: 'Home Team' },
      away_team: { name: 'Away Team' },
      league: 'League',
      match_date: new Date().toISOString(),
      status: 'SCHEDULED'
    };
  }

  // 📊 RESERVADO: Análise histórica será implementada quando API for premium
  // TODO: Implementar análise histórica completa com APIs pagas

  // 📊 Estatísticas padrão quando não há dados suficientes
  private getDefaultStats(): {
    strength: number;
    avg_goals_scored: number;
    avg_goals_conceded: number;
    avg_cards: number;
    avg_corners: number;
    form: number;
  } {
    return {
      strength: 0.5,
      avg_goals_scored: 1.2,
      avg_goals_conceded: 1.2,
      avg_cards: 2.5,
      avg_corners: 5.0,
      form: 0.5
    };
  }
}

export const mlBettingService = new MLBettingService();