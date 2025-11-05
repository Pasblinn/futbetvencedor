import axios, { AxiosResponse } from 'axios';
import {
  Match,
  Team,
  MatchPrediction,
  DailyCombinations,
  FormAnalysis,
  HeadToHeadAnalysis,
  MatchFilters,
  CombinationFilters,
  Odds,
  APIResponse
} from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

// Retry configuration
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // 1 second

// Sleep utility for retry delay
const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth token if needed
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for handling errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Utility function to handle API responses
const handleResponse = <T>(response: AxiosResponse<T>): T => {
  return response.data;
};

// Utility function to handle API errors
const handleError = (error: any): never => {
  if (error.response) {
    // Server responded with error status
    throw new Error(error.response.data?.detail || error.response.data?.message || 'Server error');
  } else if (error.request) {
    // Request was made but no response received
    throw new Error('Network error - please check your connection');
  } else {
    // Something else happened
    throw new Error(error.message || 'An unexpected error occurred');
  }
};

// API Service Class
export class APIService {
  // Matches API
  static async getMatches(filters?: MatchFilters) {
    try {
      const response = await api.get<{ matches: Match[]; count: number }>('/matches', {
        params: filters,
      });
      return handleResponse(response);
    } catch (error) {
      handleError(error);
    }
  }

  static async getTodayMatches() {
    try {
      const response = await api.get<{ matches: Match[]; count: number }>('/matches/today');
      return handleResponse(response);
    } catch (error) {
      handleError(error);
    }
  }

  static async getMatchDetails(matchId: number) {
    try {
      const response = await api.get<Match>(`/matches/${matchId}`);
      return handleResponse(response);
    } catch (error) {
      handleError(error);
    }
  }

  static async getMatchHeadToHead(matchId: number) {
    try {
      const response = await api.get<{
        match_id: number;
        home_team: string;
        away_team: string;
        head_to_head: HeadToHeadAnalysis;
      }>(`/matches/${matchId}/head-to-head`);
      return handleResponse(response);
    } catch (error) {
      handleError(error);
    }
  }

  // Teams API
  static async getTeams(filters?: { skip?: number; limit?: number; league?: string; country?: string; search?: string }) {
    try {
      const response = await api.get<{ teams: Team[]; count: number }>('/teams', {
        params: filters,
      });
      return handleResponse(response);
    } catch (error) {
      handleError(error);
    }
  }

  static async getTeamDetails(teamId: number) {
    try {
      const response = await api.get<Team>(`/teams/${teamId}`);
      return handleResponse(response);
    } catch (error) {
      handleError(error);
    }
  }

  static async getTeamRecentMatches(teamId: number, limit?: number) {
    try {
      const response = await api.get<{
        team_id: number;
        team_name: string;
        recent_matches: Array<{
          id: number;
          date: string;
          home_team: string;
          away_team: string;
          score: string;
          status: string;
          league: string;
          venue?: string;
          is_home: boolean;
          result?: 'W' | 'D' | 'L';
        }>;
      }>(`/teams/${teamId}/recent-matches`, {
        params: { limit },
      });
      return handleResponse(response);
    } catch (error) {
      handleError(error);
    }
  }

  static async getLeagues() {
    try {
      const response = await api.get<{ leagues: string[] }>('/teams/leagues');
      return handleResponse(response);
    } catch (error) {
      handleError(error);
    }
  }

  static async getCountries() {
    try {
      const response = await api.get<{ countries: string[] }>('/teams/countries');
      return handleResponse(response);
    } catch (error) {
      handleError(error);
    }
  }

  // Analytics API
  static async getTeamForm(teamId: number, matchesCount?: number) {
    try {
      const response = await api.get<{
        team_id: number;
        team_name: string;
        form_analysis: FormAnalysis;
      }>(`/analytics/team/${teamId}/form`, {
        params: { matches_count: matchesCount },
      });
      return handleResponse(response);
    } catch (error) {
      handleError(error);
    }
  }

  static async getTeamXGMetrics(teamId: number, matchesCount?: number) {
    try {
      const response = await api.get<{
        team_id: number;
        team_name: string;
        xg_metrics: any;
      }>(`/analytics/team/${teamId}/xg-metrics`, {
        params: { matches_count: matchesCount },
      });
      return handleResponse(response);
    } catch (error) {
      handleError(error);
    }
  }

  static async getTeamCornersAnalysis(teamId: number, matchesCount?: number) {
    try {
      const response = await api.get<{
        team_id: number;
        team_name: string;
        corners_analysis: any;
      }>(`/analytics/team/${teamId}/corners`, {
        params: { matches_count: matchesCount },
      });
      return handleResponse(response);
    } catch (error) {
      handleError(error);
    }
  }

  static async getHeadToHeadAnalysis(team1Id: number, team2Id: number, matchesCount?: number) {
    try {
      const response = await api.get<{
        team1: { id: number; name: string };
        team2: { id: number; name: string };
        head_to_head: HeadToHeadAnalysis;
      }>(`/analytics/head-to-head/${team1Id}/${team2Id}`, {
        params: { matches_count: matchesCount },
      });
      return handleResponse(response);
    } catch (error) {
      handleError(error);
    }
  }

  static async getComprehensiveMatchAnalysis(matchId: number) {
    try {
      const response = await api.get<{
        match: {
          id: number;
          home_team: string;
          away_team: string;
          match_date: string;
          league: string;
          venue?: string;
        };
        analysis: any;
        summary: any;
      }>(`/analytics/match/${matchId}/comprehensive`);
      return handleResponse(response);
    } catch (error) {
      handleError(error);
    }
  }

  // Predictions API
  static async getUpcomingPredictions(daysAhead: number = 7, limit: number = 50) {
    try {
      const response = await api.get<{
        success: boolean;
        period: { from: string; to: string; days: number };
        matches: Array<{
          match_id: number;
          match_date: string;
          status: string;
          home_team: { id: number; name: string };
          away_team: { id: number; name: string };
          league: { name: string };
          venue: string | null;
          prediction: {
            predicted_outcome: string;
            confidence_score: number;
            probabilities: { home: number; draw: number; away: number };
            analysis: string;
            recommendation: string;
            model_version: string;
            predicted_at: string;
          } | null;
        }>;
        total: number;
      }>('/predictions/upcoming', {
        params: { days_ahead: daysAhead, limit },
      });
      return handleResponse(response);
    } catch (error) {
      handleError(error);
    }
  }

  static async getMLEnhancedPrediction(matchId: number) {
    try {
      const response = await api.get<{
        success: boolean;
        match: {
          id: number;
          date: string;
          status: string;
          home_team: { id: number; name: string };
          away_team: { id: number; name: string };
          league: { name: string };
          venue: string | null;
        };
        prediction: {
          predicted_outcome: { code: string; description: string };
          probabilities: {
            home_win: { probability: number; percentage: string; odds_implied: number };
            draw: { probability: number; percentage: string; odds_implied: number };
            away_win: { probability: number; percentage: string; odds_implied: number };
          };
          confidence_score: number;
          analysis: string;
          recommendation: string;
          model: {
            version: string;
            features: string[];
            accuracy: string;
            trained_on: string;
          };
        };
        metadata: { predicted_at: string; last_updated: string | null };
      }>(`/predictions/ml-enhanced/${matchId}`);
      return handleResponse(response);
    } catch (error) {
      handleError(error);
    }
  }

  static async getStatisticsOverview() {
    try {
      const response = await api.get<{
        success: boolean;
        data_collection: {
          total_matches: number;
          total_teams: number;
          total_statistics: number;
          coverage_percentage: number;
          leagues: Array<{ league: string; matches: number }>;
        };
        predictions: {
          total_generated: number;
          upcoming_matches_covered: number;
          model_version: string;
          model_accuracy: string;
          trained_on_matches: number;
        };
        system_health: {
          data_quality: string;
          prediction_coverage: number;
          status: string;
        };
      }>('/predictions/statistics/overview');
      return handleResponse(response);
    } catch (error) {
      handleError(error);
    }
  }

  static async generateMatchPrediction(matchId: number) {
    try {
      const response = await api.post<MatchPrediction>(`/predictions/${matchId}`);
      return handleResponse(response);
    } catch (error) {
      handleError(error);
    }
  }

  static async getTodayCombinations(filters?: CombinationFilters) {
    try {
      const response = await api.get<DailyCombinations>('/predictions/combinations/today', {
        params: filters,
      });
      return handleResponse(response);
    } catch (error) {
      handleError(error);
    }
  }

  static async getDateCombinations(targetDate: string, filters?: CombinationFilters) {
    try {
      const response = await api.get<DailyCombinations>(`/predictions/combinations/${targetDate}`, {
        params: filters,
      });
      return handleResponse(response);
    } catch (error) {
      handleError(error);
    }
  }

  static async getMatchPrediction(matchId: number) {
    try {
      const response = await api.get<{
        id: number;
        match_id: number;
        prediction_type: string;
        market_type: string;
        predicted_outcome: string;
        predicted_probability: number;
        recommended_odds: number;
        actual_odds: number;
        confidence_score: number;
        value_score: number;
        kelly_percentage: number;
        analysis_summary: string;
        key_factors: any;
        is_validated: boolean;
        validation_score: number;
        final_recommendation: string;
        predicted_at: string;
        expires_at: string;
      }>(`/predictions/${matchId}`);
      return handleResponse(response);
    } catch (error) {
      handleError(error);
    }
  }

  static async getPredictionPerformance(filters?: {
    date_from?: string;
    date_to?: string;
    market_type?: string;
  }) {
    try {
      const response = await api.get<{
        period: { from: string; to: string };
        overall_stats: {
          total_predictions: number;
          winners: number;
          win_rate: number;
          total_profit_loss: number;
          avg_confidence: number;
          avg_value_score: number;
          roi: number;
        };
        recommended_bets: {
          total_bets: number;
          winners: number;
          win_rate: number;
          profit_loss: number;
          roi: number;
        };
        market_breakdown: Record<string, {
          total: number;
          winners: number;
          win_rate: number;
          profit_loss: number;
          roi: number;
        }>;
      }>('/predictions/performance/stats', {
        params: filters,
      });
      return handleResponse(response);
    } catch (error) {
      handleError(error);
    }
  }

  // Odds API
  static async getAvailableSports() {
    try {
      const response = await api.get<{ sports: any[] }>('/odds/sports');
      return handleResponse(response);
    } catch (error) {
      handleError(error);
    }
  }

  static async getCurrentOdds(sport?: string, regions?: string, markets?: string) {
    try {
      const response = await api.get<{ sport: string; odds: any[]; count: number }>('/odds/current/' + (sport || 'soccer_epl'), {
        params: { regions, markets },
      });
      return handleResponse(response);
    } catch (error) {
      handleError(error);
    }
  }

  static async getMatchOdds(matchExternalId: string) {
    try {
      const response = await api.get<{ match_id: string; odds: any }>(`/odds/match/${matchExternalId}`);
      return handleResponse(response);
    } catch (error) {
      handleError(error);
    }
  }

  static async getOddsComparison(matchExternalId: string) {
    try {
      const response = await api.get<any>(`/odds/match/${matchExternalId}/comparison`);
      return handleResponse(response);
    } catch (error) {
      handleError(error);
    }
  }

  static async getOddsMovement(matchExternalId: string) {
    try {
      const response = await api.get<{
        match_id: string;
        movement_history: any[];
        data_points: number;
      }>(`/odds/match/${matchExternalId}/movement`);
      return handleResponse(response);
    } catch (error) {
      handleError(error);
    }
  }

  static async calculateValueBets(matchExternalId: string, predictedProbabilities: Record<string, number>) {
    try {
      const response = await api.post<{
        match_id: string;
        predicted_probabilities: Record<string, number>;
        value_bets: any[];
        value_bet_count: number;
      }>(`/odds/match/${matchExternalId}/value-bets`, predictedProbabilities);
      return handleResponse(response);
    } catch (error) {
      handleError(error);
    }
  }

  static async getStoredOdds(matchId: number, bookmaker?: string, market?: string) {
    try {
      const response = await api.get<{
        match_id: number;
        match: {
          home_team: string;
          away_team: string;
          match_date: string;
          status: string;
        };
        odds: Odds[];
        count: number;
      }>(`/odds/database/match/${matchId}`, {
        params: { bookmaker, market },
      });
      return handleResponse(response);
    } catch (error) {
      handleError(error);
    }
  }

  static async getBookmakers() {
    try {
      const response = await api.get<{ bookmakers: string[] }>('/odds/database/bookmakers');
      return handleResponse(response);
    } catch (error) {
      handleError(error);
    }
  }

  static async getMarkets() {
    try {
      const response = await api.get<{ markets: string[] }>('/odds/database/markets');
      return handleResponse(response);
    } catch (error) {
      handleError(error);
    }
  }

  static async findArbitrageOpportunities(matchExternalId: string) {
    try {
      const response = await api.get<{
        match_id: string;
        arbitrage_opportunities: any[];
        opportunity_count: number;
        total_profit_potential: number;
      }>(`/odds/arbitrage/${matchExternalId}`);
      return handleResponse(response);
    } catch (error) {
      handleError(error);
    }
  }

  // ML Real API endpoints
  static async getMLSystemStatus() {
    try {
      const response = await api.get<{
        status: string;
        system: {
          models_loaded: boolean;
          models_available: boolean;
          models_count: number;
          encoders_available: boolean;
          models_dir: string;
          supported_teams: string[];
        };
      }>('/ml-real/system/status');
      return handleResponse(response);
    } catch (error) {
      handleError(error);
    }
  }

  static async getSupportedTeams() {
    try {
      const response = await api.get<{
        status: string;
        teams: Array<{
          name: string;
          api_code: string;
          supported: boolean;
        }>;
        total_teams: number;
      }>('/ml-real/teams/supported');
      return handleResponse(response);
    } catch (error) {
      handleError(error);
    }
  }

  static async getBrasileraoMatchPrediction(homeTeam: string, awayTeam: string) {
    try {
      const response = await api.get<{
        status: string;
        prediction: {
          home_team: string;
          away_team: string;
          ensemble_prediction: string;
          confidence: number;
          individual_predictions: {
            random_forest: string;
            random_forest_proba: { away_win: number; draw: number; home_win: number };
            gradient_boosting: string;
            gradient_boosting_proba: { away_win: number; draw: number; home_win: number };
            logistic_regression: string;
            logistic_regression_proba: { away_win: number; draw: number; home_win: number };
          };
          models_used: string[];
          prediction_timestamp: string;
        };
        model_info: {
          source: string;
          training_samples: number;
          models: string[];
        };
      }>(`/ml-real/brasileirao/predict/${homeTeam}/${awayTeam}`);
      return handleResponse(response);
    } catch (error) {
      handleError(error);
    }
  }

  static async reloadMLModels() {
    try {
      const response = await api.post<{
        status: string;
        message: string;
        models_reloaded: number;
        timestamp: string;
      }>('/ml-real/system/reload-models');
      return handleResponse(response);
    } catch (error) {
      handleError(error);
    }
  }

  // Add method to get ML models info
  static async getMLModelsInfo() {
    try {
      const response = await api.get<{
        models: Array<{
          name: string;
          accuracy: number;
          precision: number;
          recall: number;
          f1_score: number;
          trained_at: string;
          samples_count: number;
        }>;
        status: string;
      }>('/ml/models/info');
      return handleResponse(response);
    } catch (error) {
      handleError(error);
    }
  }

  // Add method to get prediction performance
  static async getMLPredictionStats() {
    try {
      const response = await api.get<{
        total_predictions: number;
        accuracy: number;
        by_model: Record<string, any>;
        recent_predictions: Array<{
          home_team: string;
          away_team: string;
          prediction: string;
          confidence: number;
          date: string;
        }>;
      }>('/predictions/performance/stats');
      return handleResponse(response);
    } catch (error) {
      handleError(error);
    }
  }

  // Prediction History API
  static async getPredictionHistory(params?: {
    limit?: number;
    date_from?: string;
    date_to?: string;
    league?: string;
    status?: string;
  }) {
    try {
      const response = await api.get<{
        entries: Array<{
          id: string;
          type: string;
          title: string;
          description: string;
          timestamp: string;
          status: 'won' | 'lost' | 'pending' | 'void';
          confidence: number;
          odds: number;
          stake: number;
          potential_return: number;
          actual_return: number;
          profit: number;
          league: string;
          teams: string[];
          strategy: string;
          kelly_percentage: number;
          tags: string[];
          market_type: string;
          notes: string;
        }>;
        metrics: {
          total_bets: number;
          win_rate: number;
          total_profit: number;
          total_stake: number;
          roi: number;
          avg_odds: number;
          avg_stake: number;
          best_win: number;
          worst_loss: number;
          current_streak: number;
          profit_by_month: Array<{ month: string; profit: number }>;
        };
        count: number;
      }>('/predictions/history/performance', {
        params,
      });
      return handleResponse(response);
    } catch (error) {
      handleError(error);
    }
  }

  // News API
  static async getNewsFromRSS(league: string = 'all', limit: number = 50) {
    try {
      const response = await api.get<{
        success: boolean;
        items: Array<{
          id: string;
          title: string;
          description: string;
          url: string;
          source: { id: string; name: string };
          author?: string;
          publishedAt: string;
          urlToImage?: string;
          category: string;
          language: string;
        }>;
        total: number;
        sources: string[];
      }>('/news/rss', {
        params: { league, limit },
      });
      return handleResponse(response);
    } catch (error) {
      handleError(error);
    }
  }

  static async searchNews(query: string, language: string = 'pt', limit: number = 20) {
    try {
      const response = await api.get<{
        success: boolean;
        items: Array<{
          id: string;
          title: string;
          description: string;
          url: string;
          source: { id: string; name: string };
          author?: string;
          publishedAt: string;
          urlToImage?: string;
          category: string;
          language: string;
        }>;
        total: number;
        sources: string[];
      }>('/news/search', {
        params: { query, language, limit },
      });
      return handleResponse(response);
    } catch (error) {
      handleError(error);
    }
  }

  static async getOfficialNews(league: string = 'brasileirao') {
    try {
      const response = await api.get<{
        success: boolean;
        items: Array<{
          id: string;
          title: string;
          description: string;
          url: string;
          source: { id: string; name: string };
          author?: string;
          publishedAt: string;
          urlToImage?: string;
          category: string;
          language: string;
        }>;
        total: number;
        sources: string[];
      }>('/news/official', {
        params: { league },
      });
      return handleResponse(response);
    } catch (error) {
      handleError(error);
    }
  }

  static async getInjuries(filters?: { league?: string; team_id?: number; status?: string }) {
    try {
      const response = await api.get<{
        success: boolean;
        injuries: Array<{
          id: number;
          player_name: string;
          team_name: string;
          team_id: number;
          position?: string;
          injury_type: string;
          severity: string;
          status: string;
          description: string;
          expected_return?: string;
          reported_at: string;
        }>;
        total: number;
      }>('/news/injuries', {
        params: filters,
      });
      return handleResponse(response);
    } catch (error) {
      handleError(error);
    }
  }
}

export default APIService;