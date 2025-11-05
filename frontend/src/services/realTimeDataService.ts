import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

// Interfaces for synchronized data
export interface SyncMatch {
  id: number;
  external_id: string;
  home_team: {
    id: number;
    name: string;
    short_name: string;
    logo: string;
  };
  away_team: {
    id: number;
    name: string;
    short_name: string;
    logo: string;
  };
  league: string;
  match_date: string;
  status: 'SCHEDULED' | 'LIVE' | 'FINISHED' | 'POSTPONED' | 'CANCELLED';
  minute?: number;
  home_score?: number;
  away_score?: number;
  venue?: string;
  referee?: string;
  is_predicted: boolean;
  confidence_score?: number;
  odds?: {
    home_win: number;
    draw: number;
    away_win: number;
  };
  prediction?: {
    home_win_prob: number;
    draw_prob: number;
    away_win_prob: number;
    predicted_score_home: number;
    predicted_score_away: number;
  };
}

export interface SyncStatus {
  sync_status: {
    last_full_sync: string | null;
    last_quick_sync: string | null;
  };
  scheduler: {
    status: 'running' | 'stopped';
    jobs: Array<{
      id: string;
      name: string;
      next_run: string | null;
      trigger: string;
    }>;
    total_jobs: number;
  };
  timestamp: string;
}

export interface HealthStatus {
  timestamp: string;
  services: {
    football_data: {
      status: 'healthy' | 'unhealthy';
      response_time?: string;
      error?: string;
    };
    odds_api: {
      status: 'healthy' | 'unhealthy';
      response_time?: string;
      error?: string;
    };
    redis: {
      status: 'healthy' | 'unhealthy';
      error?: string;
    };
  };
  overall_status: 'healthy' | 'degraded' | 'unhealthy';
}

class RealTimeDataService {
  private eventSource: EventSource | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 5000;

  // ===== Match Data Methods =====

  async getTodayMatches(): Promise<{ matches: SyncMatch[]; count: number; source: string }> {
    try {
      console.log('🔄 Fetching today\'s matches from synchronized database...');

      const response = await axios.get(`${API_BASE_URL}/matches/today`, {
        timeout: 10000
      });

      console.log(`✅ Loaded ${response.data.count} matches from ${response.data.source}`);
      return response.data;

    } catch (error) {
      console.error('❌ Error fetching today\'s matches:', error);
      throw new Error('Failed to load synchronized match data');
    }
  }

  async getMatches(filters: {
    skip?: number;
    limit?: number;
    date_from?: string;
    date_to?: string;
    league?: string;
    status?: string;
  } = {}): Promise<{ matches: SyncMatch[]; count: number }> {
    try {
      const params = new URLSearchParams();

      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined) {
          params.append(key, value.toString());
        }
      });

      const response = await axios.get(`${API_BASE_URL}/matches?${params}`, {
        timeout: 10000
      });

      return response.data;

    } catch (error) {
      console.error('❌ Error fetching matches:', error);
      throw new Error('Failed to load match data');
    }
  }

  async getMatchDetails(matchId: number): Promise<SyncMatch> {
    try {
      const response = await axios.get(`${API_BASE_URL}/matches/${matchId}`, {
        timeout: 10000
      });

      return response.data;

    } catch (error) {
      console.error(`❌ Error fetching match ${matchId}:`, error);
      throw new Error('Failed to load match details');
    }
  }

  // ===== Synchronization Control Methods =====

  async triggerSync(syncType: 'full' | 'quick' | 'matches' | 'odds' | 'predictions' = 'quick'): Promise<{
    message: string;
    status?: string;
    results?: any;
    timestamp: string;
  }> {
    try {
      console.log(`🔄 Triggering ${syncType} sync...`);

      const response = await axios.post(`${API_BASE_URL}/sync/${syncType}`, {}, {
        timeout: 30000
      });

      console.log(`✅ ${syncType} sync completed:`, response.data);
      return response.data;

    } catch (error) {
      console.error(`❌ Error triggering ${syncType} sync:`, error);
      throw new Error(`Failed to trigger ${syncType} synchronization`);
    }
  }

  async getSyncStatus(): Promise<SyncStatus> {
    try {
      const response = await axios.get(`${API_BASE_URL}/sync/status`, {
        timeout: 5000
      });

      return response.data;

    } catch (error) {
      console.error('❌ Error fetching sync status:', error);
      throw new Error('Failed to get synchronization status');
    }
  }

  async getHealthStatus(): Promise<HealthStatus> {
    try {
      const response = await axios.get(`${API_BASE_URL}/sync/health`, {
        timeout: 10000
      });

      return response.data;

    } catch (error) {
      console.error('❌ Error fetching health status:', error);
      throw new Error('Failed to get system health status');
    }
  }

  // ===== Scheduler Control Methods =====

  async startScheduler(): Promise<{ message: string; status: string; timestamp: string }> {
    try {
      const response = await axios.post(`${API_BASE_URL}/sync/scheduler/start`, {}, {
        timeout: 10000
      });

      console.log('✅ Scheduler started');
      return response.data;

    } catch (error) {
      console.error('❌ Error starting scheduler:', error);
      throw new Error('Failed to start scheduler');
    }
  }

  async stopScheduler(): Promise<{ message: string; status: string; timestamp: string }> {
    try {
      const response = await axios.post(`${API_BASE_URL}/sync/scheduler/stop`, {}, {
        timeout: 10000
      });

      console.log('⏹️ Scheduler stopped');
      return response.data;

    } catch (error) {
      console.error('❌ Error stopping scheduler:', error);
      throw new Error('Failed to stop scheduler');
    }
  }

  async getSchedulerStatus(): Promise<{
    status: 'running' | 'stopped';
    jobs: Array<{
      id: string;
      name: string;
      next_run: string | null;
      trigger: string;
    }>;
    total_jobs: number;
  }> {
    try {
      const response = await axios.get(`${API_BASE_URL}/sync/scheduler/status`, {
        timeout: 5000
      });

      return response.data;

    } catch (error) {
      console.error('❌ Error fetching scheduler status:', error);
      throw new Error('Failed to get scheduler status');
    }
  }

  // ===== Real-time Updates via WebSocket/SSE =====

  startLiveUpdates(onUpdate: (data: any) => void, onError?: (error: any) => void): void {
    // For now, we'll use polling. Later can be upgraded to WebSocket/SSE
    this.stopLiveUpdates(); // Stop any existing updates

    const pollInterval = setInterval(async () => {
      try {
        // Quick sync to get latest data
        const result = await this.triggerSync('quick');

        // Get updated matches
        const matches = await this.getTodayMatches();

        onUpdate({
          type: 'matches_update',
          data: matches,
          sync_result: result,
          timestamp: new Date().toISOString()
        });

      } catch (error) {
        console.error('❌ Error in live updates:', error);
        if (onError) {
          onError(error);
        }
      }
    }, 30000); // Poll every 30 seconds

    // Store interval ID for cleanup
    (this as any).pollInterval = pollInterval;

    console.log('🔴 Live updates started (polling every 30s)');
  }

  stopLiveUpdates(): void {
    if ((this as any).pollInterval) {
      clearInterval((this as any).pollInterval);
      (this as any).pollInterval = null;
      console.log('⏹️ Live updates stopped');
    }

    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
  }

  // ===== Data Processing Helpers =====

  processMatchForDisplay(match: SyncMatch): {
    id: number;
    homeTeam: string;
    awayTeam: string;
    homeScore: number | null;
    awayScore: number | null;
    status: string;
    minute?: number;
    league: string;
    time: string;
    date: string;
    isLive: boolean;
    isFinished: boolean;
    prediction?: {
      homeWinProb: number;
      drawProb: number;
      awayWinProb: number;
      predictedScore: string;
    };
    odds?: {
      home: number;
      draw: number;
      away: number;
    };
  } {
    const matchDate = new Date(match.match_date);

    return {
      id: match.id,
      homeTeam: match.home_team.name,
      awayTeam: match.away_team.name,
      homeScore: match.home_score ?? null,
      awayScore: match.away_score ?? null,
      status: match.status,
      minute: match.minute,
      league: match.league,
      time: matchDate.toTimeString().substring(0, 5),
      date: matchDate.toISOString().split('T')[0],
      isLive: match.status === 'LIVE',
      isFinished: match.status === 'FINISHED',
      prediction: match.prediction ? {
        homeWinProb: Math.round(match.prediction.home_win_prob * 100),
        drawProb: Math.round(match.prediction.draw_prob * 100),
        awayWinProb: Math.round(match.prediction.away_win_prob * 100),
        predictedScore: `${match.prediction.predicted_score_home}-${match.prediction.predicted_score_away}`
      } : undefined,
      odds: match.odds ? {
        home: match.odds.home_win,
        draw: match.odds.draw,
        away: match.odds.away_win
      } : undefined
    };
  }

  // ===== Cache Management =====

  private cache = new Map<string, { data: any; timestamp: number }>();
  private cacheExpiry = 2 * 60 * 1000; // 2 minutes

  private getCachedData(key: string): any | null {
    const cached = this.cache.get(key);
    if (cached && (Date.now() - cached.timestamp) < this.cacheExpiry) {
      return cached.data;
    }
    return null;
  }

  private setCachedData(key: string, data: any): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });
  }

  clearCache(): void {
    this.cache.clear();
    console.log('🗑️ Cache cleared');
  }

  getCacheStats(): { size: number; keys: string[] } {
    return {
      size: this.cache.size,
      keys: Array.from(this.cache.keys())
    };
  }
}

export const realTimeDataService = new RealTimeDataService();
export default realTimeDataService;