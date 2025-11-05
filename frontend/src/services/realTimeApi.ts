import axios from 'axios';

// Interfaces para APIs de dados esportivos
export interface LiveOddsData {
  matchId: string;
  homeTeam: string;
  awayTeam: string;
  odds: {
    '1': number; // Home win
    'X': number; // Draw
    '2': number; // Away win
    'BTTS_Yes': number; // Both teams to score - Yes
    'BTTS_No': number; // Both teams to score - No
    'O2.5': number; // Over 2.5 goals
    'U2.5': number; // Under 2.5 goals
  };
  lastUpdated: number;
  bookmaker: string;
}

export interface LiveMatchData {
  matchId: string;
  homeTeam: string;
  awayTeam: string;
  league: string;
  status: 'pre-match' | 'live' | 'finished' | 'postponed';
  minute?: number;
  score: {
    home: number;
    away: number;
  };
  events: Array<{
    type: 'goal' | 'card' | 'substitution' | 'corner';
    minute: number;
    player?: string;
    team: 'home' | 'away';
    details?: string;
  }>;
  statistics?: {
    possession: { home: number; away: number };
    shots: { home: number; away: number };
    shotsOnTarget: { home: number; away: number };
    corners: { home: number; away: number };
    fouls: { home: number; away: number };
    yellowCards: { home: number; away: number };
    redCards: { home: number; away: number };
  };
  lastUpdated: number;
}

export interface WeatherData {
  location: string;
  temperature: number;
  humidity: number;
  windSpeed: number;
  conditions: string;
  precipitation: number;
}

export interface NewsAlert {
  id: string;
  title: string;
  content: string;
  source: string;
  timestamp: number;
  relevantMatches: string[];
  category: 'injury' | 'lineup' | 'transfer' | 'suspension' | 'general';
  priority: 'low' | 'medium' | 'high' | 'critical';
}

class RealTimeAPIService {
  private baseURL: string;
  private apiKeys: { [key: string]: string };
  private cache: Map<string, { data: any; expiry: number }> = new Map();
  private requestQueue: Map<string, Promise<any>> = new Map();

  constructor() {
    this.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:3001';
    this.apiKeys = {
      // APIs públicas e gratuitas
      footballAPI: process.env.REACT_APP_FOOTBALL_API_KEY || '',
      weatherAPI: process.env.REACT_APP_WEATHER_API_KEY || '',
      newsAPI: process.env.REACT_APP_NEWS_API_KEY || '',
      // APIs alternativas
      apiSports: process.env.REACT_APP_API_SPORTS_KEY || '',
      rapidAPI: process.env.REACT_APP_RAPID_API_KEY || ''
    };
  }

  // Cache utility methods
  private getCacheKey(url: string, params?: any): string {
    return `${url}_${JSON.stringify(params || {})}`;
  }

  private isValidCache(cacheKey: string): boolean {
    const cached = this.cache.get(cacheKey);
    return cached ? cached.expiry > Date.now() : false;
  }

  private setCache(cacheKey: string, data: any, ttl = 60000): void {
    this.cache.set(cacheKey, {
      data,
      expiry: Date.now() + ttl
    });
  }

  private getCache(cacheKey: string): any {
    const cached = this.cache.get(cacheKey);
    return cached?.data;
  }

  // Request deduplication
  private async makeRequest<T>(key: string, requestFn: () => Promise<T>): Promise<T> {
    if (this.requestQueue.has(key)) {
      return this.requestQueue.get(key) as Promise<T>;
    }

    const promise = requestFn().finally(() => {
      this.requestQueue.delete(key);
    });

    this.requestQueue.set(key, promise);
    return promise;
  }

  // API Methods

  // 1. Live Odds (usando API gratuita do football-data.org)
  async getLiveOdds(matchIds: string[]): Promise<LiveOddsData[]> {
    const cacheKey = this.getCacheKey('live-odds', { matchIds });
    if (this.isValidCache(cacheKey)) {
      return this.getCache(cacheKey);
    }

    return this.makeRequest(cacheKey, async () => {
      try {
        // Usando football-data.org (gratuito com limitações)
        const odds: LiveOddsData[] = [];

        for (const matchId of matchIds) {
          try {
            const response = await axios.get(
              `https://api.football-data.org/v4/matches/${matchId}`,
              {
                headers: {
                  'X-Auth-Token': this.apiKeys.footballAPI || 'demo-key'
                },
                timeout: 5000
              }
            );

            const match = response.data;

            // Simular odds se não disponíveis (para demo)
            const simulatedOdds: LiveOddsData = {
              matchId,
              homeTeam: match.homeTeam?.name || 'Home Team',
              awayTeam: match.awayTeam?.name || 'Away Team',
              odds: {
                '1': 2.10 + Math.random() * 0.5,
                'X': 3.20 + Math.random() * 0.8,
                '2': 3.50 + Math.random() * 0.7,
                'BTTS_Yes': 1.85 + Math.random() * 0.3,
                'BTTS_No': 1.95 + Math.random() * 0.3,
                'O2.5': 1.75 + Math.random() * 0.4,
                'U2.5': 2.05 + Math.random() * 0.4
              },
              lastUpdated: Date.now(),
              bookmaker: 'demo'
            };

            odds.push(simulatedOdds);
          } catch (error) {
            console.warn(`Failed to fetch odds for match ${matchId}:`, error);
          }
        }

        this.setCache(cacheKey, odds, 30000); // Cache por 30 segundos
        return odds;
      } catch (error) {
        console.error('Error fetching live odds:', error);
        return [];
      }
    });
  }

  // 2. Live Match Data
  async getLiveMatchData(matchIds: string[]): Promise<LiveMatchData[]> {
    const cacheKey = this.getCacheKey('live-matches', { matchIds });
    if (this.isValidCache(cacheKey)) {
      return this.getCache(cacheKey);
    }

    return this.makeRequest(cacheKey, async () => {
      try {
        const matches: LiveMatchData[] = [];

        for (const matchId of matchIds) {
          try {
            // Tentar múltiplas APIs
            let matchData = await this.fetchFromFootballAPI(matchId);

            if (!matchData) {
              matchData = await this.fetchFromAPIFootball(matchId);
            }

            if (!matchData) {
              matchData = this.generateDemoMatchData(matchId);
            }

            matches.push(matchData);
          } catch (error) {
            console.warn(`Failed to fetch match data for ${matchId}:`, error);
          }
        }

        this.setCache(cacheKey, matches, 15000); // Cache por 15 segundos
        return matches;
      } catch (error) {
        console.error('Error fetching live match data:', error);
        return [];
      }
    });
  }

  // Football-data.org API
  private async fetchFromFootballAPI(matchId: string): Promise<LiveMatchData | null> {
    try {
      const response = await axios.get(
        `https://api.football-data.org/v4/matches/${matchId}`,
        {
          headers: {
            'X-Auth-Token': this.apiKeys.footballAPI || 'demo-key'
          },
          timeout: 5000
        }
      );

      const match = response.data;

      return {
        matchId,
        homeTeam: match.homeTeam?.name || 'Home Team',
        awayTeam: match.awayTeam?.name || 'Away Team',
        league: match.competition?.name || 'Unknown League',
        status: this.mapMatchStatus(match.status),
        minute: match.minute,
        score: {
          home: match.score?.fullTime?.home || 0,
          away: match.score?.fullTime?.away || 0
        },
        events: [], // football-data.org tem limitações nos eventos
        statistics: match.statistics ? {
          possession: { home: 50, away: 50 },
          shots: { home: 0, away: 0 },
          shotsOnTarget: { home: 0, away: 0 },
          corners: { home: 0, away: 0 },
          fouls: { home: 0, away: 0 },
          yellowCards: { home: 0, away: 0 },
          redCards: { home: 0, away: 0 }
        } : undefined,
        lastUpdated: Date.now()
      };
    } catch (error) {
      console.warn('Football API failed:', error);
      return null;
    }
  }

  // API-Football (RapidAPI)
  private async fetchFromAPIFootball(matchId: string): Promise<LiveMatchData | null> {
    try {
      if (!this.apiKeys.rapidAPI) return null;

      const response = await axios.get(
        `https://api-football-v1.p.rapidapi.com/v3/fixtures`,
        {
          params: { id: matchId },
          headers: {
            'X-RapidAPI-Key': this.apiKeys.rapidAPI,
            'X-RapidAPI-Host': 'api-football-v1.p.rapidapi.com'
          },
          timeout: 5000
        }
      );

      const fixture = response.data.response[0];
      if (!fixture) return null;

      return {
        matchId,
        homeTeam: fixture.teams.home.name,
        awayTeam: fixture.teams.away.name,
        league: fixture.league.name,
        status: this.mapMatchStatus(fixture.fixture.status.short),
        minute: fixture.fixture.status.elapsed,
        score: {
          home: fixture.goals.home || 0,
          away: fixture.goals.away || 0
        },
        events: fixture.events?.map((event: any) => ({
          type: this.mapEventType(event.type),
          minute: event.time.elapsed,
          player: event.player?.name,
          team: event.team.id === fixture.teams.home.id ? 'home' : 'away',
          details: event.detail
        })) || [],
        statistics: fixture.statistics ? {
          possession: this.extractStatistic(fixture.statistics, 'Ball Possession'),
          shots: this.extractStatistic(fixture.statistics, 'Total Shots'),
          shotsOnTarget: this.extractStatistic(fixture.statistics, 'Shots on Goal'),
          corners: this.extractStatistic(fixture.statistics, 'Corner Kicks'),
          fouls: this.extractStatistic(fixture.statistics, 'Fouls'),
          yellowCards: this.extractStatistic(fixture.statistics, 'Yellow Cards'),
          redCards: this.extractStatistic(fixture.statistics, 'Red Cards')
        } : undefined,
        lastUpdated: Date.now()
      };
    } catch (error) {
      console.warn('API-Football failed:', error);
      return null;
    }
  }

  // Generate demo data for testing
  private generateDemoMatchData(matchId: string): LiveMatchData {
    const teams = [
      'Arsenal', 'Chelsea', 'Liverpool', 'Manchester City', 'Manchester United',
      'Barcelona', 'Real Madrid', 'Bayern Munich', 'PSG', 'Juventus'
    ];

    const homeTeam = teams[Math.floor(Math.random() * teams.length)];
    const awayTeam = teams.filter(t => t !== homeTeam)[Math.floor(Math.random() * (teams.length - 1))];

    return {
      matchId,
      homeTeam,
      awayTeam,
      league: 'Demo League',
      status: 'live',
      minute: Math.floor(Math.random() * 90) + 1,
      score: {
        home: Math.floor(Math.random() * 4),
        away: Math.floor(Math.random() * 4)
      },
      events: [],
      statistics: {
        possession: {
          home: 40 + Math.random() * 20,
          away: 40 + Math.random() * 20
        },
        shots: {
          home: Math.floor(Math.random() * 15),
          away: Math.floor(Math.random() * 15)
        },
        shotsOnTarget: {
          home: Math.floor(Math.random() * 8),
          away: Math.floor(Math.random() * 8)
        },
        corners: {
          home: Math.floor(Math.random() * 10),
          away: Math.floor(Math.random() * 10)
        },
        fouls: {
          home: Math.floor(Math.random() * 20),
          away: Math.floor(Math.random() * 20)
        },
        yellowCards: {
          home: Math.floor(Math.random() * 5),
          away: Math.floor(Math.random() * 5)
        },
        redCards: {
          home: Math.floor(Math.random() * 2),
          away: Math.floor(Math.random() * 2)
        }
      },
      lastUpdated: Date.now()
    };
  }

  // 3. Weather Data
  async getWeatherData(city: string): Promise<WeatherData | null> {
    const cacheKey = this.getCacheKey('weather', { city });
    if (this.isValidCache(cacheKey)) {
      return this.getCache(cacheKey);
    }

    return this.makeRequest(cacheKey, async () => {
      try {
        // OpenWeatherMap API (gratuita)
        const response = await axios.get(
          `https://api.openweathermap.org/data/2.5/weather`,
          {
            params: {
              q: city,
              appid: this.apiKeys.weatherAPI || 'demo-key',
              units: 'metric'
            },
            timeout: 5000
          }
        );

        const data = response.data;

        const weatherData: WeatherData = {
          location: data.name,
          temperature: data.main.temp,
          humidity: data.main.humidity,
          windSpeed: data.wind.speed,
          conditions: data.weather[0].description,
          precipitation: data.rain?.['1h'] || 0
        };

        this.setCache(cacheKey, weatherData, 300000); // Cache por 5 minutos
        return weatherData;
      } catch (error) {
        console.error('Error fetching weather data:', error);

        // Retornar dados simulados em caso de erro
        return {
          location: city,
          temperature: 15 + Math.random() * 20,
          humidity: 40 + Math.random() * 40,
          windSpeed: Math.random() * 15,
          conditions: 'Clear',
          precipitation: 0
        };
      }
    });
  }

  // 4. News Alerts
  async getNewsAlerts(teams: string[]): Promise<NewsAlert[]> {
    const cacheKey = this.getCacheKey('news', { teams });
    if (this.isValidCache(cacheKey)) {
      return this.getCache(cacheKey);
    }

    return this.makeRequest(cacheKey, async () => {
      try {
        // Simular dados de notícias para demo
        const alerts: NewsAlert[] = teams.flatMap(team => [
          {
            id: `news_${team}_${Date.now()}`,
            title: `${team} injury update`,
            content: `Latest injury report for ${team}`,
            source: 'Demo Sports News',
            timestamp: Date.now() - Math.random() * 3600000,
            relevantMatches: [`match_${team}`],
            category: 'injury',
            priority: 'medium'
          }
        ]);

        this.setCache(cacheKey, alerts, 180000); // Cache por 3 minutos
        return alerts;
      } catch (error) {
        console.error('Error fetching news alerts:', error);
        return [];
      }
    });
  }

  // Utility methods
  private mapMatchStatus(status: string): 'pre-match' | 'live' | 'finished' | 'postponed' {
    const liveStatuses = ['1H', '2H', 'HT', 'LIVE', 'IN_PLAY'];
    const finishedStatuses = ['FT', 'FINISHED'];
    const postponedStatuses = ['POSTPONED', 'CANCELLED'];

    if (liveStatuses.includes(status)) return 'live';
    if (finishedStatuses.includes(status)) return 'finished';
    if (postponedStatuses.includes(status)) return 'postponed';
    return 'pre-match';
  }

  private mapEventType(type: string): 'goal' | 'card' | 'substitution' | 'corner' {
    if (type.toLowerCase().includes('goal')) return 'goal';
    if (type.toLowerCase().includes('card')) return 'card';
    if (type.toLowerCase().includes('substitution')) return 'substitution';
    return 'corner';
  }

  private extractStatistic(statistics: any[], statName: string): { home: number; away: number } {
    const stat = statistics.find(s => s.type === statName);
    if (!stat) return { home: 0, away: 0 };

    return {
      home: parseInt(stat.home) || 0,
      away: parseInt(stat.away) || 0
    };
  }

  // Public utility methods
  clearCache(): void {
    this.cache.clear();
  }

  getCacheSize(): number {
    return this.cache.size;
  }

  getApiStatus(): { [key: string]: boolean } {
    return {
      footballAPI: !!this.apiKeys.footballAPI,
      weatherAPI: !!this.apiKeys.weatherAPI,
      newsAPI: !!this.apiKeys.newsAPI,
      apiSports: !!this.apiKeys.apiSports,
      rapidAPI: !!this.apiKeys.rapidAPI
    };
  }

  // Health check endpoint
  async healthCheck(): Promise<{
    status: 'healthy' | 'degraded' | 'unhealthy';
    services: { [key: string]: boolean };
    latency: number;
  }> {
    const startTime = Date.now();
    const services: { [key: string]: boolean } = {};

    // Test each service
    try {
      await axios.get('https://api.football-data.org/v4/competitions', {
        headers: { 'X-Auth-Token': this.apiKeys.footballAPI || 'demo-key' },
        timeout: 3000
      });
      services.footballAPI = true;
    } catch {
      services.footballAPI = false;
    }

    try {
      await axios.get('https://api.openweathermap.org/data/2.5/weather', {
        params: { q: 'London', appid: this.apiKeys.weatherAPI || 'demo-key' },
        timeout: 3000
      });
      services.weatherAPI = true;
    } catch {
      services.weatherAPI = false;
    }

    const latency = Date.now() - startTime;
    const healthyServices = Object.values(services).filter(Boolean).length;
    const totalServices = Object.keys(services).length;

    let status: 'healthy' | 'degraded' | 'unhealthy' = 'healthy';
    if (healthyServices === 0) {
      status = 'unhealthy';
    } else if (healthyServices < totalServices) {
      status = 'degraded';
    }

    return { status, services, latency };
  }
}

export const realTimeAPIService = new RealTimeAPIService();
export default realTimeAPIService;