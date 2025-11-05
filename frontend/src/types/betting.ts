// 🎯 Tipos Completos para Sistema de Apostas Inteligente

export interface BettingMarket {
  id: string;
  name: string;
  description: string;
  type: MarketType;
  odds: { [key: string]: number };
  probability: { [key: string]: number };
  value: number;
  confidence: number;
  recommendation: string;
  kelly_percentage: number;
  risk_level: 'low' | 'medium' | 'high';
}

export type MarketType =
  | '1X2' // Vencedor da Partida
  | 'asian_handicap' // Handicap Asiático
  | 'over_under' // Over/Under Gols
  | 'btts' // Both Teams to Score
  | 'correct_score' // Resultado Correto
  | 'half_time_full_time' // Intervalo/Final
  | 'draw_no_bet' // Empate Anula Aposta
  | 'cards' // Total de Cartões
  | 'corners' // Total de Escanteios
  | 'first_goal' // Primeiro Gol
  | 'clean_sheet' // Sem Sofrer Gols
  | 'double_chance' // Dupla Chance
  | 'goal_scorer' // Marcador de Gol
  | 'team_goals' // Gols do Time
  | 'minute_ranges'; // Gols em Períodos

export interface MatchAnalysis {
  match_id: string;
  home_team: string;
  away_team: string;
  league: string;
  match_date: string;

  // Análise ML Avançada
  ml_analysis: {
    win_probabilities: {
      home: number;
      draw: number;
      away: number;
    };
    goals_analysis: {
      expected_home_goals: number;
      expected_away_goals: number;
      total_expected: number;
      over_under_probabilities: { [threshold: string]: number };
    };
    advanced_stats: {
      btts_probability: number;
      clean_sheet_home: number;
      clean_sheet_away: number;
      first_half_goals: number;
      second_half_goals: number;
      cards_expected: number;
      corners_expected: number;
    };
  };

  // Mercados Disponíveis
  markets: BettingMarket[];

  // Recomendações
  best_value_bets: BettingMarket[];
  safest_bets: BettingMarket[];
  highest_odds_bets: BettingMarket[];
}

export interface IntelligentTicket {
  id: string;
  created_at: string;
  ticket_type: 'conservative' | 'balanced' | 'aggressive' | 'value' | 'combo';

  // Análise de Risco
  risk_analysis: {
    total_risk: 'low' | 'medium' | 'high';
    kelly_total: number;
    expected_roi: number;
    win_probability: number;
    bankroll_percentage: number;
  };

  // Seleções
  selections: TicketSelection[];

  // Financeiro
  financial: {
    total_stake: number;
    total_odds: number;
    potential_return: number;
    potential_profit: number;
  };

  // Estratégia
  strategy: {
    name: string;
    description: string;
    reasoning: string[];
    market_distribution: { [market: string]: number };
  };
}

export interface TicketSelection {
  match_id: string;
  match_info: {
    home_team: string;
    away_team: string;
    league: string;
    date: string;
  };
  market: BettingMarket;
  selection: string;
  individual_stake: number;
  reasoning: string;
}

// 🎯 Configurações de Mercado
export const MARKET_CONFIGS: { [key in MarketType]: {
  name: string;
  description: string;
  icon: string;
  risk_factor: number;
  min_confidence: number;
} } = {
  '1X2': {
    name: 'Vencedor da Partida',
    description: 'Aposta no resultado final: vitória da casa, empate ou vitória do visitante',
    icon: '🏆',
    risk_factor: 1.0,
    min_confidence: 0.6
  },
  'asian_handicap': {
    name: 'Handicap Asiático',
    description: 'Handicap que elimina o empate, oferecendo vantagem/desvantagem',
    icon: '⚖️',
    risk_factor: 0.8,
    min_confidence: 0.65
  },
  'over_under': {
    name: 'Total de Gols',
    description: 'Aposta se o total de gols será maior ou menor que um valor',
    icon: '⚽',
    risk_factor: 0.7,
    min_confidence: 0.7
  },
  'btts': {
    name: 'Ambos Marcam',
    description: 'Aposta se ambos os times marcarão pelo menos um gol',
    icon: '🎯',
    risk_factor: 0.6,
    min_confidence: 0.65
  },
  'correct_score': {
    name: 'Resultado Correto',
    description: 'Aposta no placar exato da partida',
    icon: '🎲',
    risk_factor: 2.0,
    min_confidence: 0.8
  },
  'half_time_full_time': {
    name: 'Intervalo/Final',
    description: 'Resultado no intervalo e no final do jogo',
    icon: '⏱️',
    risk_factor: 1.5,
    min_confidence: 0.75
  },
  'draw_no_bet': {
    name: 'Empate Anula',
    description: 'Se empatar, o valor da aposta é devolvido',
    icon: '🔄',
    risk_factor: 0.5,
    min_confidence: 0.6
  },
  'cards': {
    name: 'Total de Cartões',
    description: 'Aposta no número total de cartões mostrados',
    icon: '🟨',
    risk_factor: 0.9,
    min_confidence: 0.7
  },
  'corners': {
    name: 'Total de Escanteios',
    description: 'Aposta no número total de escanteios',
    icon: '📐',
    risk_factor: 0.8,
    min_confidence: 0.7
  },
  'first_goal': {
    name: 'Primeiro Gol',
    description: 'Qual time marcará o primeiro gol',
    icon: '🥇',
    risk_factor: 1.2,
    min_confidence: 0.65
  },
  'clean_sheet': {
    name: 'Sem Sofrer Gols',
    description: 'Se um time não sofrerá gols na partida',
    icon: '🛡️',
    risk_factor: 1.1,
    min_confidence: 0.7
  },
  'double_chance': {
    name: 'Dupla Chance',
    description: 'Cobre duas das três possibilidades de resultado',
    icon: '🎪',
    risk_factor: 0.4,
    min_confidence: 0.5
  },
  'goal_scorer': {
    name: 'Marcador de Gol',
    description: 'Qual jogador marcará um gol',
    icon: '👤',
    risk_factor: 1.8,
    min_confidence: 0.8
  },
  'team_goals': {
    name: 'Gols do Time',
    description: 'Quantos gols um time específico marcará',
    icon: '⚽',
    risk_factor: 1.0,
    min_confidence: 0.65
  },
  'minute_ranges': {
    name: 'Períodos de Gol',
    description: 'Em que período da partida haverá gols',
    icon: '⏰',
    risk_factor: 1.3,
    min_confidence: 0.7
  }
};

// 🎯 Estratégias de Ticket
export const TICKET_STRATEGIES = {
  conservative: {
    name: 'Conservador',
    description: 'Apostas seguras com odds baixas e alta probabilidade',
    max_odds: 2.5,
    min_confidence: 0.75,
    max_selections: 3,
    preferred_markets: ['draw_no_bet', 'double_chance', 'btts'],
    bankroll_percentage: 0.05
  },
  balanced: {
    name: 'Equilibrado',
    description: 'Mix de segurança e valor, odds moderadas',
    max_odds: 4.0,
    min_confidence: 0.65,
    max_selections: 4,
    preferred_markets: ['1X2', 'over_under', 'btts', 'asian_handicap'],
    bankroll_percentage: 0.03
  },
  aggressive: {
    name: 'Agressivo',
    description: 'Busca por odds altas e maior retorno potencial',
    max_odds: 8.0,
    min_confidence: 0.55,
    max_selections: 6,
    preferred_markets: ['correct_score', 'first_goal', 'goal_scorer'],
    bankroll_percentage: 0.02
  },
  value: {
    name: 'Value Betting',
    description: 'Foca em apostas com valor positivo',
    max_odds: 6.0,
    min_confidence: 0.6,
    max_selections: 5,
    preferred_markets: ['1X2', 'over_under', 'asian_handicap'],
    bankroll_percentage: 0.025
  },
  combo: {
    name: 'Combo Builder',
    description: 'Combinações inteligentes no mesmo jogo',
    max_odds: 10.0,
    min_confidence: 0.6,
    max_selections: 4,
    preferred_markets: ['1X2', 'btts', 'over_under', 'cards'],
    bankroll_percentage: 0.015
  }
};