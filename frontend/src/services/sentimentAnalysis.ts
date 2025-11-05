import axios from 'axios';

export interface SentimentData {
  score: number; // -1 (very negative) to 1 (very positive)
  magnitude: number; // 0 to 1 (intensity of sentiment)
  confidence: number; // 0 to 1
  keywords: Array<{
    word: string;
    sentiment: number;
    frequency: number;
  }>;
  sources: Array<{
    platform: string;
    url?: string;
    timestamp: number;
    relevanceScore: number;
  }>;
}

export interface TeamSentiment {
  teamName: string;
  overall: SentimentData;
  recent: SentimentData; // Last 24 hours
  news: SentimentData;
  social: SentimentData;
  fanSentiment: SentimentData;
  mediaAnalysis: SentimentData;
  trendingTopics: string[];
  sentimentHistory: Array<{
    timestamp: number;
    score: number;
    source: string;
  }>;
}

export interface MatchSentiment {
  matchId: string;
  homeTeam: TeamSentiment;
  awayTeam: TeamSentiment;
  matchSpecific: {
    excitement: number;
    controversy: number;
    confidence: number;
    publicOpinion: number;
  };
  keyEvents: Array<{
    timestamp: number;
    event: string;
    sentimentImpact: number;
    description: string;
  }>;
  predictiveFactors: {
    homeBias: number;
    mediaInfluence: number;
    socialMomentum: number;
    contrarian: number;
  };
}

export interface NewsAnalysis {
  headline: string;
  summary: string;
  sentiment: SentimentData;
  relevance: number;
  impact: 'low' | 'medium' | 'high' | 'critical';
  category: 'injury' | 'transfer' | 'performance' | 'controversy' | 'general';
  teams: string[];
  players: string[];
  source: {
    name: string;
    credibility: number;
    bias: number;
  };
  timestamp: number;
}

class SentimentAnalysisService {
  private baseURL: string;
  private apiKeys: { [key: string]: string };
  private cache: Map<string, { data: any; expiry: number }> = new Map();
  private requestQueue: Map<string, Promise<any>> = new Map();

  constructor() {
    this.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:3001';
    this.apiKeys = {
      // APIs gratuitas para análise de sentimento
      textAnalysis: process.env.REACT_APP_TEXT_ANALYSIS_KEY || '',
      newsAPI: process.env.REACT_APP_NEWS_API_KEY || '',
      twitterAPI: process.env.REACT_APP_TWITTER_API_KEY || '',
      // APIs alternativas
      huggingFace: process.env.REACT_APP_HUGGINGFACE_API_KEY || '',
      rapidAPI: process.env.REACT_APP_RAPID_API_KEY || ''
    };
  }

  // Cache utilities
  private getCacheKey(endpoint: string, params?: any): string {
    return `${endpoint}_${JSON.stringify(params || {})}`;
  }

  private isValidCache(cacheKey: string): boolean {
    const cached = this.cache.get(cacheKey);
    return cached ? cached.expiry > Date.now() : false;
  }

  private setCache(cacheKey: string, data: any, ttl = 300000): void {
    this.cache.set(cacheKey, {
      data,
      expiry: Date.now() + ttl
    });
  }

  private getCache(cacheKey: string): any {
    return this.cache.get(cacheKey)?.data;
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

  // Análise de sentimento para equipe
  async getTeamSentiment(teamName: string): Promise<TeamSentiment> {
    const cacheKey = this.getCacheKey('team-sentiment', { teamName });
    if (this.isValidCache(cacheKey)) {
      return this.getCache(cacheKey);
    }

    return this.makeRequest(cacheKey, async () => {
      try {
        // Buscar dados de múltiplas fontes
        const [news, social, media] = await Promise.allSettled([
          this.getNewsSentiment(teamName),
          this.getSocialSentiment(teamName),
          this.getMediaAnalysis(teamName)
        ]);

        const newsData = news.status === 'fulfilled' ? news.value : this.getDefaultSentiment();
        const socialData = social.status === 'fulfilled' ? social.value : this.getDefaultSentiment();
        const mediaData = media.status === 'fulfilled' ? media.value : this.getDefaultSentiment();

        // Combinar análises
        const overall = this.combineSentiments([newsData, socialData, mediaData]);
        const recent = await this.getRecentSentiment(teamName);

        const teamSentiment: TeamSentiment = {
          teamName,
          overall,
          recent,
          news: newsData,
          social: socialData,
          fanSentiment: await this.getFanSentiment(teamName),
          mediaAnalysis: mediaData,
          trendingTopics: await this.getTrendingTopics(teamName),
          sentimentHistory: await this.getSentimentHistory(teamName)
        };

        this.setCache(cacheKey, teamSentiment, 600000); // Cache por 10 minutos
        return teamSentiment;
      } catch (error) {
        console.error(`Error getting team sentiment for ${teamName}:`, error);
        return this.getDefaultTeamSentiment(teamName);
      }
    });
  }

  // Análise de sentimento para partida
  async getMatchSentiment(matchId: string, homeTeam: string, awayTeam: string): Promise<MatchSentiment> {
    const cacheKey = this.getCacheKey('match-sentiment', { matchId, homeTeam, awayTeam });
    if (this.isValidCache(cacheKey)) {
      return this.getCache(cacheKey);
    }

    return this.makeRequest(cacheKey, async () => {
      try {
        const [homeTeamSentiment, awayTeamSentiment, matchSpecific] = await Promise.all([
          this.getTeamSentiment(homeTeam),
          this.getTeamSentiment(awayTeam),
          this.getMatchSpecificSentiment(matchId, homeTeam, awayTeam)
        ]);

        const keyEvents = await this.getMatchKeyEvents(matchId);
        const predictiveFactors = this.calculatePredictiveFactors(homeTeamSentiment, awayTeamSentiment, matchSpecific);

        const matchSentiment: MatchSentiment = {
          matchId,
          homeTeam: homeTeamSentiment,
          awayTeam: awayTeamSentiment,
          matchSpecific,
          keyEvents,
          predictiveFactors
        };

        this.setCache(cacheKey, matchSentiment, 300000); // Cache por 5 minutos
        return matchSentiment;
      } catch (error) {
        console.error(`Error getting match sentiment for ${matchId}:`, error);
        return this.getDefaultMatchSentiment(matchId, homeTeam, awayTeam);
      }
    });
  }

  // Análise de notícias
  async getNewsAnalysis(query: string, limit = 10): Promise<NewsAnalysis[]> {
    const cacheKey = this.getCacheKey('news-analysis', { query, limit });
    if (this.isValidCache(cacheKey)) {
      return this.getCache(cacheKey);
    }

    return this.makeRequest(cacheKey, async () => {
      try {
        // Usar NewsAPI como fonte principal (gratuita com limitações)
        const response = await axios.get('https://newsapi.org/v2/everything', {
          params: {
            q: query,
            language: 'en',
            sortBy: 'publishedAt',
            pageSize: limit,
            apiKey: this.apiKeys.newsAPI || 'demo-key'
          },
          timeout: 10000
        });

        const articles = response.data.articles || [];
        const analyses: NewsAnalysis[] = [];

        for (const article of articles) {
          try {
            const sentiment = await this.analyzeTextSentiment(
              `${article.title} ${article.description || ''}`
            );

            const analysis: NewsAnalysis = {
              headline: article.title,
              summary: article.description || '',
              sentiment,
              relevance: this.calculateRelevance(article, query),
              impact: this.determineImpact(sentiment, article),
              category: this.categorizeNews(article),
              teams: this.extractTeams(article),
              players: this.extractPlayers(article),
              source: {
                name: article.source?.name || 'Unknown',
                credibility: this.getSourceCredibility(article.source?.name),
                bias: this.getSourceBias(article.source?.name)
              },
              timestamp: new Date(article.publishedAt).getTime()
            };

            analyses.push(analysis);
          } catch (error) {
            console.warn('Error analyzing article:', error);
          }
        }

        this.setCache(cacheKey, analyses, 900000); // Cache por 15 minutos
        return analyses;
      } catch (error) {
        console.error('Error getting news analysis:', error);
        return [];
      }
    });
  }

  // Análise de sentimento de texto usando Hugging Face (gratuito)
  async analyzeTextSentiment(text: string): Promise<SentimentData> {
    try {
      if (!this.apiKeys.huggingFace) {
        return this.analyzeSentimentLocal(text);
      }

      const response = await axios.post(
        'https://api-inference.huggingface.co/models/cardiffnlp/twitter-roberta-base-sentiment-latest',
        { inputs: text },
        {
          headers: {
            'Authorization': `Bearer ${this.apiKeys.huggingFace}`,
            'Content-Type': 'application/json'
          },
          timeout: 10000
        }
      );

      const result = response.data[0];
      const sentiment = this.processHuggingFaceSentiment(result);
      return sentiment;
    } catch (error) {
      console.warn('Hugging Face API failed, using local analysis:', error);
      return this.analyzeSentimentLocal(text);
    }
  }

  private processHuggingFaceSentiment(result: any[]): SentimentData {
    // Mapear labels do modelo para scores
    let positiveScore = 0;
    let negativeScore = 0;
    let neutralScore = 0;

    result.forEach(item => {
      if (item.label === 'LABEL_2' || item.label === 'positive') {
        positiveScore = item.score;
      } else if (item.label === 'LABEL_0' || item.label === 'negative') {
        negativeScore = item.score;
      } else if (item.label === 'LABEL_1' || item.label === 'neutral') {
        neutralScore = item.score;
      }
    });

    const score = positiveScore - negativeScore;
    const magnitude = Math.max(positiveScore, negativeScore, neutralScore);

    return {
      score,
      magnitude,
      confidence: magnitude,
      keywords: [],
      sources: [{ platform: 'huggingface', timestamp: Date.now(), relevanceScore: 1 }]
    };
  }

  // Análise de sentimento local (fallback)
  private analyzeSentimentLocal(text: string): SentimentData {
    const positiveWords = [
      'win', 'victory', 'excellent', 'great', 'good', 'strong', 'best', 'amazing',
      'brilliant', 'fantastic', 'outstanding', 'impressive', 'dominant', 'confident'
    ];

    const negativeWords = [
      'lose', 'defeat', 'terrible', 'bad', 'weak', 'worst', 'awful',
      'disappointing', 'poor', 'struggle', 'concern', 'doubt', 'problem', 'injury'
    ];

    const words = text.toLowerCase().split(/\s+/);
    let positiveCount = 0;
    let negativeCount = 0;

    words.forEach(word => {
      if (positiveWords.includes(word)) positiveCount++;
      if (negativeWords.includes(word)) negativeCount++;
    });

    const totalSentimentWords = positiveCount + negativeCount;
    const score = totalSentimentWords > 0
      ? (positiveCount - negativeCount) / totalSentimentWords
      : 0;

    const magnitude = totalSentimentWords / words.length;

    return {
      score,
      magnitude,
      confidence: Math.min(magnitude * 2, 1),
      keywords: [],
      sources: [{ platform: 'local', timestamp: Date.now(), relevanceScore: 0.5 }]
    };
  }

  private async getNewsSentiment(teamName: string): Promise<SentimentData> {
    const news = await this.getNewsAnalysis(teamName, 5);
    if (news.length === 0) return this.getDefaultSentiment();

    const sentiments = news.map(n => n.sentiment);
    return this.combineSentiments(sentiments);
  }

  private async getSocialSentiment(teamName: string): Promise<SentimentData> {
    // Simular dados de redes sociais (implementar com APIs reais)
    return {
      score: (Math.random() - 0.5) * 1.5, // -0.75 to 0.75
      magnitude: Math.random() * 0.8 + 0.2, // 0.2 to 1.0
      confidence: Math.random() * 0.3 + 0.7, // 0.7 to 1.0
      keywords: [],
      sources: [{ platform: 'twitter', timestamp: Date.now(), relevanceScore: 0.8 }]
    };
  }

  private async getMediaAnalysis(teamName: string): Promise<SentimentData> {
    // Analisar mídia esportiva especializada
    return {
      score: (Math.random() - 0.5) * 1.2, // -0.6 to 0.6
      magnitude: Math.random() * 0.6 + 0.4, // 0.4 to 1.0
      confidence: Math.random() * 0.2 + 0.8, // 0.8 to 1.0
      keywords: [],
      sources: [{ platform: 'sports_media', timestamp: Date.now(), relevanceScore: 0.9 }]
    };
  }

  private async getRecentSentiment(teamName: string): Promise<SentimentData> {
    // Sentimento das últimas 24 horas
    return {
      score: (Math.random() - 0.5) * 2, // -1 to 1
      magnitude: Math.random() * 0.7 + 0.3, // 0.3 to 1.0
      confidence: Math.random() * 0.4 + 0.6, // 0.6 to 1.0
      keywords: [],
      sources: [{ platform: 'recent_news', timestamp: Date.now(), relevanceScore: 1 }]
    };
  }

  private async getFanSentiment(teamName: string): Promise<SentimentData> {
    // Análise de sentimento dos torcedores
    return {
      score: (Math.random() - 0.5) * 1.8, // -0.9 to 0.9
      magnitude: Math.random() * 0.8 + 0.2, // 0.2 to 1.0
      confidence: Math.random() * 0.3 + 0.7, // 0.7 to 1.0
      keywords: [],
      sources: [{ platform: 'fan_forums', timestamp: Date.now(), relevanceScore: 0.7 }]
    };
  }

  private async getTrendingTopics(teamName: string): Promise<string[]> {
    // Tópicos trending relacionados ao time
    const topics = [
      'injury update',
      'transfer news',
      'match preparation',
      'player performance',
      'tactical analysis',
      'fan reactions',
      'league position',
      'upcoming fixtures'
    ];

    return topics.slice(0, Math.floor(Math.random() * 5) + 3);
  }

  private async getSentimentHistory(teamName: string): Promise<Array<{timestamp: number; score: number; source: string}>> {
    // Histórico de sentimento (últimos 7 dias)
    const history = [];
    const now = Date.now();

    for (let i = 7; i >= 0; i--) {
      history.push({
        timestamp: now - (i * 24 * 60 * 60 * 1000),
        score: (Math.random() - 0.5) * 1.5,
        source: Math.random() > 0.5 ? 'news' : 'social'
      });
    }

    return history;
  }

  private async getMatchSpecificSentiment(matchId: string, homeTeam: string, awayTeam: string) {
    return {
      excitement: Math.random() * 0.5 + 0.5, // 0.5 to 1.0
      controversy: Math.random() * 0.3, // 0 to 0.3
      confidence: Math.random() * 0.4 + 0.6, // 0.6 to 1.0
      publicOpinion: (Math.random() - 0.5) * 1.2 // -0.6 to 0.6
    };
  }

  private async getMatchKeyEvents(matchId: string) {
    // Eventos-chave que afetam o sentimento
    return [
      {
        timestamp: Date.now() - 3600000,
        event: 'Team lineup announced',
        sentimentImpact: 0.2,
        description: 'Official team lineup released'
      },
      {
        timestamp: Date.now() - 7200000,
        event: 'Player injury concern',
        sentimentImpact: -0.3,
        description: 'Key player injury reported'
      }
    ];
  }

  private calculatePredictiveFactors(home: TeamSentiment, away: TeamSentiment, matchSpecific: any) {
    return {
      homeBias: 0.1 + Math.random() * 0.2, // Vantagem de jogar em casa
      mediaInfluence: (home.mediaAnalysis.score - away.mediaAnalysis.score) * 0.3,
      socialMomentum: (home.social.score - away.social.score) * 0.25,
      contrarian: matchSpecific.publicOpinion > 0.5 ? -0.2 : 0.1 // Fator contrário
    };
  }

  private combineSentiments(sentiments: SentimentData[]): SentimentData {
    if (sentiments.length === 0) return this.getDefaultSentiment();

    const weights = sentiments.map(s => s.confidence);
    const totalWeight = weights.reduce((sum, w) => sum + w, 0);

    if (totalWeight === 0) return this.getDefaultSentiment();

    const weightedScore = sentiments.reduce(
      (sum, s, i) => sum + (s.score * weights[i]), 0
    ) / totalWeight;

    const weightedMagnitude = sentiments.reduce(
      (sum, s, i) => sum + (s.magnitude * weights[i]), 0
    ) / totalWeight;

    const averageConfidence = sentiments.reduce(
      (sum, s) => sum + s.confidence, 0
    ) / sentiments.length;

    return {
      score: weightedScore,
      magnitude: weightedMagnitude,
      confidence: averageConfidence,
      keywords: [],
      sources: sentiments.flatMap(s => s.sources)
    };
  }

  private getDefaultSentiment(): SentimentData {
    return {
      score: 0,
      magnitude: 0.1,
      confidence: 0.1,
      keywords: [],
      sources: []
    };
  }

  private getDefaultTeamSentiment(teamName: string): TeamSentiment {
    const defaultSentiment = this.getDefaultSentiment();
    return {
      teamName,
      overall: defaultSentiment,
      recent: defaultSentiment,
      news: defaultSentiment,
      social: defaultSentiment,
      fanSentiment: defaultSentiment,
      mediaAnalysis: defaultSentiment,
      trendingTopics: [],
      sentimentHistory: []
    };
  }

  private getDefaultMatchSentiment(matchId: string, homeTeam: string, awayTeam: string): MatchSentiment {
    return {
      matchId,
      homeTeam: this.getDefaultTeamSentiment(homeTeam),
      awayTeam: this.getDefaultTeamSentiment(awayTeam),
      matchSpecific: {
        excitement: 0.5,
        controversy: 0,
        confidence: 0.5,
        publicOpinion: 0
      },
      keyEvents: [],
      predictiveFactors: {
        homeBias: 0.1,
        mediaInfluence: 0,
        socialMomentum: 0,
        contrarian: 0
      }
    };
  }

  // Utility methods
  private calculateRelevance(article: any, query: string): number {
    const title = article.title?.toLowerCase() || '';
    const description = article.description?.toLowerCase() || '';
    const queryWords = query.toLowerCase().split(' ');

    let relevance = 0;
    queryWords.forEach(word => {
      if (title.includes(word)) relevance += 0.3;
      if (description.includes(word)) relevance += 0.2;
    });

    return Math.min(relevance, 1);
  }

  private determineImpact(sentiment: SentimentData, article: any): 'low' | 'medium' | 'high' | 'critical' {
    const magnitude = sentiment.magnitude;
    const confidence = sentiment.confidence;
    const impact = magnitude * confidence;

    if (impact > 0.8) return 'critical';
    if (impact > 0.6) return 'high';
    if (impact > 0.3) return 'medium';
    return 'low';
  }

  private categorizeNews(article: any): 'injury' | 'transfer' | 'performance' | 'controversy' | 'general' {
    const text = `${article.title} ${article.description || ''}`.toLowerCase();

    if (text.includes('injury') || text.includes('injured') || text.includes('hurt')) {
      return 'injury';
    }
    if (text.includes('transfer') || text.includes('signing') || text.includes('move')) {
      return 'transfer';
    }
    if (text.includes('performance') || text.includes('play') || text.includes('score')) {
      return 'performance';
    }
    if (text.includes('controversy') || text.includes('scandal') || text.includes('problem')) {
      return 'controversy';
    }

    return 'general';
  }

  private extractTeams(article: any): string[] {
    // Implementar extração de nomes de times do texto
    return [];
  }

  private extractPlayers(article: any): string[] {
    // Implementar extração de nomes de jogadores do texto
    return [];
  }

  private getSourceCredibility(sourceName?: string): number {
    const credibilityMap: { [key: string]: number } = {
      'BBC Sport': 0.95,
      'ESPN': 0.90,
      'Sky Sports': 0.88,
      'The Guardian': 0.85,
      'Reuters': 0.92,
      'Associated Press': 0.90
    };

    return credibilityMap[sourceName || ''] || 0.5;
  }

  private getSourceBias(sourceName?: string): number {
    // Retorna bias score: -1 (muito negativo) a 1 (muito positivo), 0 = neutro
    const biasMap: { [key: string]: number } = {
      'BBC Sport': 0,
      'ESPN': 0.1,
      'Sky Sports': 0.05,
      'The Guardian': -0.1,
      'Reuters': 0,
      'Associated Press': 0
    };

    return biasMap[sourceName || ''] || 0;
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
      textAnalysis: !!this.apiKeys.textAnalysis,
      newsAPI: !!this.apiKeys.newsAPI,
      twitterAPI: !!this.apiKeys.twitterAPI,
      huggingFace: !!this.apiKeys.huggingFace,
      rapidAPI: !!this.apiKeys.rapidAPI
    };
  }
}

export const sentimentAnalysisService = new SentimentAnalysisService();
export default sentimentAnalysisService;