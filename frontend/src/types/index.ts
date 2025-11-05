// API Response Types
export interface APIResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

// Team Types
export interface Team {
  id: number;
  external_id: string;
  name: string;
  short_name?: string;
  country?: string;
  league?: string;
  founded?: number;
  venue?: string;
  logo_url?: string;
  elo_rating: number;
  form_rating: number;
  attack_rating: number;
  defense_rating: number;
}

// Match Types
export interface Match {
  id: number;
  external_id: string;
  home_team: Team;
  away_team: Team;
  league: string;
  season?: string;
  matchday?: number;
  match_date: string;
  venue?: string;
  referee?: string;
  status: 'SCHEDULED' | 'LIVE' | 'FINISHED' | 'POSTPONED';
  minute?: number;
  home_score?: number;
  away_score?: number;
  home_score_ht?: number;
  away_score_ht?: number;
  temperature?: number;
  humidity?: number;
  wind_speed?: number;
  weather_condition?: string;
  importance_factor?: number;
  motivation_home?: number;
  motivation_away?: number;
  is_predicted: boolean;
  confidence_score?: number;
  statistics?: MatchStatistics;
}

// Statistics Types
export interface MatchStatistics {
  possession_home?: number;
  possession_away?: number;
  shots_home?: number;
  shots_away?: number;
  shots_on_target_home?: number;
  shots_on_target_away?: number;
  corners_home?: number;
  corners_away?: number;
  fouls_home?: number;
  fouls_away?: number;
  yellow_cards_home?: number;
  yellow_cards_away?: number;
  red_cards_home?: number;
  red_cards_away?: number;
  xg_home?: number;
  xg_away?: number;
  xga_home?: number;
  xga_away?: number;
  passes_home?: number;
  passes_away?: number;
  pass_accuracy_home?: number;
  pass_accuracy_away?: number;
}

// Form Analysis Types
export interface FormAnalysis {
  matches_analyzed: number;
  wins: number;
  draws: number;
  losses: number;
  goals_for: number;
  goals_against: number;
  clean_sheets: number;
  win_rate: number;
  points: number;
  points_per_game: number;
  goals_per_game: number;
  goals_conceded_per_game: number;
  goal_difference: number;
  clean_sheet_rate: number;
  form_trend: number;
  form_string: string;
  matches: FormMatch[];
}

export interface FormMatch {
  date: string;
  opponent_id: number;
  is_home: boolean;
  result: 'W' | 'D' | 'L';
  score: string;
  team_score: number;
  opponent_score: number;
}

// Prediction Types
export interface MatchOutcomePrediction {
  home_win_probability: number;
  draw_probability: number;
  away_win_probability: number;
  home_win_odds: number;
  draw_odds: number;
  away_win_odds: number;
  predicted_outcome: '1' | 'X' | '2';
  confidence: number;
  factors_considered: {
    form_adjustment: number;
    h2h_adjustment: number;
    xg_adjustment: number;
    weather_adjustment: number;
    injury_adjustment: number;
  };
}

export interface GoalsPrediction {
  expected_home_goals: number;
  expected_away_goals: number;
  expected_total_goals: number;
  over_1_5_probability: number;
  under_1_5_probability: number;
  over_2_5_probability: number;
  under_2_5_probability: number;
  over_3_5_probability: number;
  under_3_5_probability: number;
  over_1_5_odds: number;
  under_1_5_odds: number;
  over_2_5_odds: number;
  under_2_5_odds: number;
}

export interface BTTSPrediction {
  btts_yes_probability: number;
  btts_no_probability: number;
  btts_yes_odds: number;
  btts_no_odds: number;
  predicted_outcome: 'Yes' | 'No';
  confidence: number;
}

export interface CornersPrediction {
  expected_total_corners: number;
  over_8_5_probability: number;
  under_8_5_probability: number;
  over_9_5_probability: number;
  under_9_5_probability: number;
  over_10_5_probability: number;
  under_10_5_probability: number;
  over_8_5_odds: number;
  over_9_5_odds: number;
  over_10_5_odds: number;
}

export interface MatchPrediction {
  match_id: number;
  home_team: string;
  away_team: string;
  match_date: string;
  analysis_timestamp: string;
  match_outcome: MatchOutcomePrediction;
  goals_prediction: GoalsPrediction;
  btts_prediction: BTTSPrediction;
  corners_prediction: CornersPrediction;
  form_analysis: {
    home: FormAnalysis;
    away: FormAnalysis;
  };
  h2h_analysis: HeadToHeadAnalysis;
  weather_impact: WeatherImpact;
  injury_impact: InjuryImpact;
  overall_confidence: number;
  key_factors: string[];
  risk_assessment: RiskAssessment;
}

// Head to Head Types
export interface HeadToHeadAnalysis {
  matches_analyzed: number;
  team1_wins: number;
  draws: number;
  team2_wins: number;
  team1_goals: number;
  team2_goals: number;
  team1_win_rate: number;
  team2_win_rate: number;
  draw_rate: number;
  avg_goals_per_match: number;
  over_2_5_rate: number;
  btts_rate: number;
  matches: HeadToHeadMatch[];
}

export interface HeadToHeadMatch {
  date: string;
  team1_is_home: boolean;
  score: string;
  team1_score: number;
  team2_score: number;
}

// Weather Types
export interface WeatherImpact {
  temperature?: number;
  humidity?: number;
  wind_speed?: number;
  weather_condition?: string;
  impact_assessment?: {
    overall_score: number;
    factors: Record<string, number>;
    recommendations: string[];
    style_prediction: string;
    betting_implications: string[];
  };
}

// Injury Types
export interface InjuryImpact {
  home_injuries_count: number;
  away_injuries_count: number;
  home_impact: number;
  away_impact: number;
  net_impact: number;
  injury_details: {
    home: InjuryDetail[];
    away: InjuryDetail[];
  };
}

export interface InjuryDetail {
  player_name: string;
  injury_type: string;
  severity: string;
  impact: number;
}

// Risk Assessment Types
export interface RiskAssessment {
  risk_score: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  risk_factors: string[];
}

// Betting Combination Types
export interface BetSelection {
  match_id: number;
  match_name: string;
  market: string;
  selection: string;
  odds: number;
  probability: number;
}

export interface BetCombination {
  id: string;
  type: 'single' | 'double' | 'treble' | 'multiple';
  selections: BetSelection[];
  combined_odds: number;
  combined_probability: number;
  combined_confidence: number;
  expected_value: number;
  kelly_percentage: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  correlation_check?: {
    risk: 'LOW' | 'MEDIUM' | 'HIGH';
    note: string;
  };
  diversification_score?: number;
}

export interface DailyCombinations {
  date: string;
  total_matches: number;
  total_selections: number;
  high_confidence_selections: number;
  combinations: {
    doubles: BetCombination[];
    trebles: BetCombination[];
    multiples: BetCombination[];
  };
  single_bets: BetCombination[];
  analysis: {
    avg_confidence: number;
    market_distribution: Record<string, { count: number; percentage: number }>;
    risk_assessment: {
      overall_risk: 'LOW' | 'MEDIUM' | 'HIGH';
      risk_score: number;
      factors: string[];
      avg_confidence: number;
      selection_count: number;
      market_concentration: string;
    };
  };
}

// Odds Types
export interface Odds {
  id: number;
  match_id: number;
  bookmaker: string;
  market: string;
  home_win?: number;
  draw?: number;
  away_win?: number;
  over_2_5?: number;
  under_2_5?: number;
  btts_yes?: number;
  btts_no?: number;
  corners_over_9_5?: number;
  corners_under_9_5?: number;
  odds_timestamp: string;
  is_active: boolean;
}

// Filter Types
export interface MatchFilters {
  date_from?: string;
  date_to?: string;
  league?: string;
  status?: string;
  skip?: number;
  limit?: number;
}

export interface CombinationFilters {
  min_odds: number;
  max_odds: number;
  min_confidence: number;
}

// UI State Types
export interface LoadingState {
  isLoading: boolean;
  error?: string;
}

export interface PaginationState {
  page: number;
  limit: number;
  total: number;
}

// Chart Data Types
export interface ChartDataPoint {
  x: string | number;
  y: number;
  label?: string;
}

export interface FormChartData {
  date: string;
  result: 'W' | 'D' | 'L';
  points: number;
  goals_for: number;
  goals_against: number;
}

// Theme Types
export type Theme = 'light' | 'dark';

// Navigation Types
export interface NavItem {
  name: string;
  href: string;
  icon?: React.ComponentType;
  current: boolean;
}