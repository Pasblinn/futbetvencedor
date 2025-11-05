import axios from 'axios';
import { sentimentAnalysisService, SentimentData } from './sentimentAnalysis';

export interface SocialMediaPost {
  id: string;
  platform: 'twitter' | 'reddit' | 'instagram' | 'facebook' | 'youtube' | 'tiktok';
  author: {
    id: string;
    username: string;
    displayName: string;
    verified: boolean;
    followers: number;
    influence: number; // 0-1 scale
  };
  content: {
    text: string;
    hashtags: string[];
    mentions: string[];
    media?: Array<{
      type: 'image' | 'video' | 'gif';
      url: string;
      description?: string;
    }>;
  };
  engagement: {
    likes: number;
    shares: number;
    comments: number;
    views?: number;
    reactions?: { [key: string]: number };
  };
  metadata: {
    timestamp: number;
    language: string;
    location?: string;
    isRetweet?: boolean;
    isReply?: boolean;
    parentPostId?: string;
  };
  analysis: {
    sentiment: SentimentData;
    relevance: number; // 0-1 scale
    virality: number; // 0-1 scale
    credibility: number; // 0-1 scale
    topics: string[];
    entities: Array<{
      type: 'team' | 'player' | 'match' | 'league' | 'injury' | 'transfer';
      name: string;
      confidence: number;
    }>;
  };
}

export interface TrendingTopic {
  keyword: string;
  volume: number;
  growth: number; // Percentage growth
  sentiment: SentimentData;
  relatedTerms: string[];
  platforms: Array<{
    platform: string;
    volume: number;
    trending: boolean;
  }>;
  timespan: {
    start: number;
    peak: number;
    current: number;
  };
  categories: string[];
  influencers: Array<{
    username: string;
    platform: string;
    followers: number;
    engagement: number;
  }>;
}

export interface TeamSocialProfile {
  teamName: string;
  handles: {
    twitter?: string;
    instagram?: string;
    facebook?: string;
    youtube?: string;
    tiktok?: string;
  };
  metrics: {
    totalFollowers: number;
    totalEngagement: number;
    weeklyGrowth: number;
    sentimentScore: number;
    virality: number;
  };
  recentActivity: SocialMediaPost[];
  fanEngagement: {
    positiveHashtags: string[];
    negativeHashtags: string[];
    topInfluencers: Array<{
      username: string;
      platform: string;
      influence: number;
      sentiment: number;
    }>;
  };
  competitorComparison: {
    engagementRank: number;
    sentimentRank: number;
    growthRank: number;
    totalTeamsCompared: number;
  };
}

export interface MatchSocialBuzz {
  matchId: string;
  homeTeam: string;
  awayTeam: string;
  preMatchBuzz: {
    volume: number;
    sentiment: SentimentData;
    keyTopics: string[];
    predictions: Array<{
      prediction: string;
      confidence: number;
      volume: number;
    }>;
  };
  liveUpdates: Array<{
    timestamp: number;
    event: string;
    socialSpike: number;
    sentiment: SentimentData;
    topPosts: SocialMediaPost[];
  }>;
  postMatchAnalysis: {
    overallReaction: SentimentData;
    controversies: Array<{
      topic: string;
      sentiment: SentimentData;
      volume: number;
    }>;
    playerPerformanceReactions: Array<{
      playerName: string;
      sentiment: SentimentData;
      mentionVolume: number;
    }>;
  };
  viralMoments: Array<{
    timestamp: number;
    description: string;
    posts: SocialMediaPost[];
    reach: number;
    engagement: number;
  }>;
}

export interface InfluencerAlert {
  id: string;
  influencer: {
    username: string;
    platform: string;
    followers: number;
    engagement: number;
    credibility: number;
  };
  post: SocialMediaPost;
  impact: {
    potentialReach: number;
    sentimentImpact: number;
    relevance: number;
    urgency: 'low' | 'medium' | 'high' | 'critical';
  };
  recommendations: string[];
  relatedMatches: string[];
  timestamp: number;
}

export interface SocialMediaAlert {
  id: string;
  type: 'viral_content' | 'negative_sentiment' | 'injury_rumor' | 'transfer_news' | 'controversy' | 'trending_topic';
  title: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  confidence: number;
  source: {
    platform: string;
    username?: string;
    credibility: number;
  };
  content: {
    posts: SocialMediaPost[];
    summary: string;
    keyPoints: string[];
  };
  impact: {
    affectedTeams: string[];
    affectedPlayers: string[];
    affectedMatches: string[];
    marketImpact: number; // Expected odds change
    publicOpinion: number; // -1 to 1
  };
  timeline: Array<{
    timestamp: number;
    event: string;
    volume: number;
  }>;
  recommendations: Array<{
    action: string;
    priority: number;
    reasoning: string;
  }>;
  timestamp: number;
  resolved: boolean;
}

class SocialMediaMonitoringService {
  private baseURL: string;
  private apiKeys: { [key: string]: string };
  private cache: Map<string, { data: any; expiry: number }> = new Map();
  private trendingTopics: Map<string, TrendingTopic> = new Map();
  private activeAlerts: SocialMediaAlert[] = [];
  private teamProfiles: Map<string, TeamSocialProfile> = new Map();
  private monitoringChannels: Set<string> = new Set();
  private webhookSubscriptions: Map<string, any> = new Map();

  // Rate limiting
  private rateLimits: Map<string, { requests: number; resetTime: number }> = new Map();
  private requestQueues: Map<string, Promise<any>[]> = new Map();

  constructor() {
    this.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:3001';
    this.apiKeys = {
      // Twitter API v2 (Essential - Free)
      twitterBearer: process.env.REACT_APP_TWITTER_BEARER_TOKEN || '',
      twitterApiKey: process.env.REACT_APP_TWITTER_API_KEY || '',
      twitterApiSecret: process.env.REACT_APP_TWITTER_API_SECRET || '',

      // Reddit API (Free)
      redditClientId: process.env.REACT_APP_REDDIT_CLIENT_ID || '',
      redditClientSecret: process.env.REACT_APP_REDDIT_CLIENT_SECRET || '',

      // YouTube API (Free with quotas)
      youtubeApiKey: process.env.REACT_APP_YOUTUBE_API_KEY || '',

      // Alternative aggregation services
      rapidApi: process.env.REACT_APP_RAPID_API_KEY || '',
      socialMention: process.env.REACT_APP_SOCIAL_MENTION_KEY || '',
      brandwatch: process.env.REACT_APP_BRANDWATCH_KEY || ''
    };

    this.initializeMonitoring();
  }

  private initializeMonitoring() {
    // Setup default monitoring channels
    this.monitoringChannels.add('football');
    this.monitoringChannels.add('soccer');
    this.monitoringChannels.add('epl');
    this.monitoringChannels.add('premierleague');
    this.monitoringChannels.add('championsleague');
    this.monitoringChannels.add('uefa');
    this.monitoringChannels.add('fifa');

    // Start periodic monitoring
    this.startPeriodicMonitoring();
  }

  // Main monitoring methods
  async monitorTeamMentions(teamName: string, options?: {
    platforms?: string[];
    timeframe?: number;
    includeReplies?: boolean;
    minFollowers?: number;
  }): Promise<SocialMediaPost[]> {
    const cacheKey = `team-mentions-${teamName}-${JSON.stringify(options)}`;

    if (this.cache.has(cacheKey)) {
      const cached = this.cache.get(cacheKey);
      if (cached && cached.expiry > Date.now()) {
        return cached.data;
      }
    }

    try {
      const platforms = options?.platforms || ['twitter', 'reddit', 'youtube'];
      const timeframe = options?.timeframe || 86400000; // 24 hours
      const mentions: SocialMediaPost[] = [];

      // Search across platforms
      for (const platform of platforms) {
        try {
          const platformMentions = await this.searchPlatform(platform, teamName, {
            since: Date.now() - timeframe,
            includeReplies: options?.includeReplies || false,
            minFollowers: options?.minFollowers || 0
          });
          mentions.push(...platformMentions);
        } catch (error) {
          console.warn(`Error searching ${platform} for ${teamName}:`, error);
        }
      }

      // Sort by relevance and engagement
      mentions.sort((a, b) => {
        const scoreA = this.calculatePostScore(a);
        const scoreB = this.calculatePostScore(b);
        return scoreB - scoreA;
      });

      // Cache results
      this.cache.set(cacheKey, {
        data: mentions,
        expiry: Date.now() + 300000 // 5 minutes
      });

      return mentions;
    } catch (error) {
      console.error(`Error monitoring team mentions for ${teamName}:`, error);
      return [];
    }
  }

  async getTrendingTopics(category?: string): Promise<TrendingTopic[]> {
    const cacheKey = `trending-topics-${category || 'all'}`;

    if (this.cache.has(cacheKey)) {
      const cached = this.cache.get(cacheKey);
      if (cached && cached.expiry > Date.now()) {
        return cached.data;
      }
    }

    try {
      const topics: TrendingTopic[] = [];

      // Aggregate from multiple sources
      const [twitterTrends, redditTrends, youtubeTrends] = await Promise.allSettled([
        this.getTwitterTrends(category),
        this.getRedditTrends(category),
        this.getYouTubeTrends(category)
      ]);

      // Combine and deduplicate trends
      const allTrends = [
        ...(twitterTrends.status === 'fulfilled' ? twitterTrends.value : []),
        ...(redditTrends.status === 'fulfilled' ? redditTrends.value : []),
        ...(youtubeTrends.status === 'fulfilled' ? youtubeTrends.value : [])
      ];

      // Merge similar topics
      const mergedTopics = this.mergeSimilarTopics(allTrends);

      // Cache results
      this.cache.set(cacheKey, {
        data: mergedTopics,
        expiry: Date.now() + 600000 // 10 minutes
      });

      return mergedTopics;
    } catch (error) {
      console.error('Error getting trending topics:', error);
      return [];
    }
  }

  async analyzeMatchBuzz(matchId: string, homeTeam: string, awayTeam: string): Promise<MatchSocialBuzz> {
    const cacheKey = `match-buzz-${matchId}`;

    if (this.cache.has(cacheKey)) {
      const cached = this.cache.get(cacheKey);
      if (cached && cached.expiry > Date.now()) {
        return cached.data;
      }
    }

    try {
      const searchTerms = [
        homeTeam,
        awayTeam,
        `${homeTeam} vs ${awayTeam}`,
        `${homeTeam}vs${awayTeam}`,
        `#${homeTeam.replace(/\s+/g, '')}`,
        `#${awayTeam.replace(/\s+/g, '')}`
      ];

      // Get posts from multiple platforms
      const allPosts: SocialMediaPost[] = [];
      for (const term of searchTerms) {
        const posts = await this.monitorTeamMentions(term, {
          platforms: ['twitter', 'reddit'],
          timeframe: 86400000, // 24 hours
          includeReplies: false,
          minFollowers: 100
        });
        allPosts.push(...posts);
      }

      // Deduplicate posts
      const uniquePosts = this.deduplicatePosts(allPosts);

      // Analyze buzz
      const buzz = this.analyzeMatchSocialData(matchId, homeTeam, awayTeam, uniquePosts);

      // Cache results
      this.cache.set(cacheKey, {
        data: buzz,
        expiry: Date.now() + 300000 // 5 minutes
      });

      return buzz;
    } catch (error) {
      console.error(`Error analyzing match buzz for ${matchId}:`, error);
      return this.getDefaultMatchBuzz(matchId, homeTeam, awayTeam);
    }
  }

  async getTeamSocialProfile(teamName: string): Promise<TeamSocialProfile> {
    const cacheKey = `team-profile-${teamName}`;

    if (this.cache.has(cacheKey)) {
      const cached = this.cache.get(cacheKey);
      if (cached && cached.expiry > Date.now()) {
        return cached.data;
      }
    }

    try {
      // Get team handles and basic info
      const handles = await this.getTeamSocialHandles(teamName);

      // Get recent activity
      const recentActivity = await this.monitorTeamMentions(teamName, {
        timeframe: 604800000, // 7 days
        minFollowers: 500
      });

      // Calculate metrics
      const metrics = this.calculateTeamMetrics(recentActivity);

      // Analyze fan engagement
      const fanEngagement = this.analyzeFanEngagement(recentActivity);

      const profile: TeamSocialProfile = {
        teamName,
        handles,
        metrics,
        recentActivity: recentActivity.slice(0, 50), // Top 50 posts
        fanEngagement,
        competitorComparison: await this.getCompetitorComparison(teamName)
      };

      // Cache results
      this.cache.set(cacheKey, {
        data: profile,
        expiry: Date.now() + 1800000 // 30 minutes
      });

      return profile;
    } catch (error) {
      console.error(`Error getting team social profile for ${teamName}:`, error);
      return this.getDefaultTeamProfile(teamName);
    }
  }

  // Platform-specific search methods
  private async searchPlatform(platform: string, query: string, options: any): Promise<SocialMediaPost[]> {
    switch (platform) {
      case 'twitter':
        return this.searchTwitter(query, options);
      case 'reddit':
        return this.searchReddit(query, options);
      case 'youtube':
        return this.searchYouTube(query, options);
      default:
        console.warn(`Unsupported platform: ${platform}`);
        return [];
    }
  }

  private async searchTwitter(query: string, options: any): Promise<SocialMediaPost[]> {
    if (!this.apiKeys.twitterBearer) {
      return this.simulateTwitterPosts(query);
    }

    try {
      await this.checkRateLimit('twitter');

      const response = await axios.get('https://api.twitter.com/2/tweets/search/recent', {
        headers: {
          'Authorization': `Bearer ${this.apiKeys.twitterBearer}`
        },
        params: {
          query: `${query} -is:retweet`,
          max_results: 100,
          'tweet.fields': 'created_at,author_id,context_annotations,conversation_id,public_metrics,referenced_tweets,reply_settings,source,lang,possibly_sensitive',
          'user.fields': 'created_at,description,entities,location,name,pinned_tweet_id,profile_image_url,protected,public_metrics,url,username,verified',
          'expansions': 'author_id,referenced_tweets.id,referenced_tweets.id.author_id'
        },
        timeout: 10000
      });

      return this.processTwitterResponse(response.data);
    } catch (error) {
      console.error('Error searching Twitter:', error);
      return this.simulateTwitterPosts(query);
    }
  }

  private async searchReddit(query: string, options: any): Promise<SocialMediaPost[]> {
    try {
      // Use Reddit's JSON API (no auth required for search)
      const response = await axios.get(`https://www.reddit.com/search.json`, {
        params: {
          q: query,
          sort: 'hot',
          limit: 50,
          type: 'link',
          t: 'day'
        },
        timeout: 10000
      });

      return this.processRedditResponse(response.data, query);
    } catch (error) {
      console.error('Error searching Reddit:', error);
      return this.simulateRedditPosts(query);
    }
  }

  private async searchYouTube(query: string, options: any): Promise<SocialMediaPost[]> {
    if (!this.apiKeys.youtubeApiKey) {
      return this.simulateYouTubePosts(query);
    }

    try {
      const response = await axios.get('https://www.googleapis.com/youtube/v3/search', {
        params: {
          key: this.apiKeys.youtubeApiKey,
          q: query,
          part: 'snippet',
          type: 'video',
          maxResults: 25,
          order: 'relevance',
          publishedAfter: new Date(Date.now() - options.since).toISOString()
        },
        timeout: 10000
      });

      return this.processYouTubeResponse(response.data);
    } catch (error) {
      console.error('Error searching YouTube:', error);
      return this.simulateYouTubePosts(query);
    }
  }

  // Response processors
  private processTwitterResponse(data: any): SocialMediaPost[] {
    const posts: SocialMediaPost[] = [];
    const tweets = data.data || [];
    const includes = data.includes || {};
    const users = includes.users || [];

    tweets.forEach((tweet: any) => {
      const author = users.find((user: any) => user.id === tweet.author_id);
      if (!author) return;

      const post: SocialMediaPost = {
        id: tweet.id,
        platform: 'twitter',
        author: {
          id: author.id,
          username: author.username,
          displayName: author.name,
          verified: author.verified || false,
          followers: author.public_metrics?.followers_count || 0,
          influence: this.calculateInfluenceScore(author)
        },
        content: {
          text: tweet.text,
          hashtags: this.extractHashtags(tweet.text),
          mentions: this.extractMentions(tweet.text),
          media: []
        },
        engagement: {
          likes: tweet.public_metrics?.like_count || 0,
          shares: tweet.public_metrics?.retweet_count || 0,
          comments: tweet.public_metrics?.reply_count || 0,
          views: tweet.public_metrics?.impression_count || 0
        },
        metadata: {
          timestamp: new Date(tweet.created_at).getTime(),
          language: tweet.lang || 'en',
          isRetweet: false,
          isReply: !!tweet.in_reply_to_user_id
        },
        analysis: {
          sentiment: { score: 0, magnitude: 0, confidence: 0, keywords: [], sources: [] },
          relevance: 0,
          virality: 0,
          credibility: 0,
          topics: [],
          entities: []
        }
      };

      // Analyze post
      this.analyzePost(post);
      posts.push(post);
    });

    return posts;
  }

  private processRedditResponse(data: any, query: string): SocialMediaPost[] {
    const posts: SocialMediaPost[] = [];
    const submissions = data.data?.children || [];

    submissions.forEach((item: any) => {
      const submission = item.data;

      const post: SocialMediaPost = {
        id: submission.id,
        platform: 'reddit',
        author: {
          id: submission.author,
          username: submission.author,
          displayName: submission.author,
          verified: false,
          followers: 0, // Reddit doesn't expose follower counts
          influence: this.calculateRedditInfluence(submission)
        },
        content: {
          text: `${submission.title}\n${submission.selftext || ''}`,
          hashtags: [],
          mentions: [],
          media: submission.url ? [{ type: 'image', url: submission.url }] : []
        },
        engagement: {
          likes: submission.ups || 0,
          shares: submission.num_crossposts || 0,
          comments: submission.num_comments || 0
        },
        metadata: {
          timestamp: (submission.created_utc || 0) * 1000,
          language: 'en'
        },
        analysis: {
          sentiment: { score: 0, magnitude: 0, confidence: 0, keywords: [], sources: [] },
          relevance: 0,
          virality: 0,
          credibility: 0,
          topics: [],
          entities: []
        }
      };

      this.analyzePost(post);
      posts.push(post);
    });

    return posts;
  }

  private processYouTubeResponse(data: any): SocialMediaPost[] {
    const posts: SocialMediaPost[] = [];
    const videos = data.items || [];

    videos.forEach((video: any) => {
      const snippet = video.snippet;

      const post: SocialMediaPost = {
        id: video.id.videoId,
        platform: 'youtube',
        author: {
          id: snippet.channelId,
          username: snippet.channelTitle,
          displayName: snippet.channelTitle,
          verified: false,
          followers: 0, // Would need additional API call
          influence: 0.5 // Default value
        },
        content: {
          text: `${snippet.title}\n${snippet.description}`,
          hashtags: this.extractHashtags(snippet.description),
          mentions: [],
          media: [{
            type: 'video',
            url: `https://www.youtube.com/watch?v=${video.id.videoId}`,
            description: snippet.description
          }]
        },
        engagement: {
          likes: 0, // Would need additional API call
          shares: 0,
          comments: 0,
          views: 0
        },
        metadata: {
          timestamp: new Date(snippet.publishedAt).getTime(),
          language: snippet.defaultLanguage || 'en'
        },
        analysis: {
          sentiment: { score: 0, magnitude: 0, confidence: 0, keywords: [], sources: [] },
          relevance: 0,
          virality: 0,
          credibility: 0,
          topics: [],
          entities: []
        }
      };

      this.analyzePost(post);
      posts.push(post);
    });

    return posts;
  }

  // Post analysis
  private async analyzePost(post: SocialMediaPost): Promise<void> {
    try {
      // Sentiment analysis
      post.analysis.sentiment = await sentimentAnalysisService.analyzeTextSentiment(post.content.text);

      // Relevance scoring
      post.analysis.relevance = this.calculateRelevanceScore(post);

      // Virality potential
      post.analysis.virality = this.calculateViralityScore(post);

      // Credibility assessment
      post.analysis.credibility = this.calculateCredibilityScore(post);

      // Topic extraction
      post.analysis.topics = this.extractTopics(post.content.text);

      // Entity recognition
      post.analysis.entities = this.extractEntities(post.content.text);
    } catch (error) {
      console.warn('Error analyzing post:', error);
    }
  }

  // Scoring algorithms
  private calculatePostScore(post: SocialMediaPost): number {
    const engagement = (post.engagement.likes + post.engagement.shares * 2 + post.engagement.comments * 1.5) / 10;
    const authorInfluence = post.author.influence * 100;
    const recency = Math.max(0, 1 - (Date.now() - post.metadata.timestamp) / 86400000); // Decay over 24 hours

    return (engagement * 0.4) + (authorInfluence * 0.3) + (recency * 0.2) + (post.analysis.relevance * 100 * 0.1);
  }

  private calculateInfluenceScore(author: any): number {
    const followers = author.public_metrics?.followers_count || 0;
    const following = author.public_metrics?.following_count || 1;
    const tweets = author.public_metrics?.tweet_count || 1;

    // Influence based on follower ratio, engagement, and activity
    const followerRatio = Math.min(followers / (following + 1), 10);
    const activityScore = Math.min(tweets / 1000, 1);
    const verifiedBonus = author.verified ? 0.2 : 0;

    return Math.min((followerRatio * 0.1 + activityScore * 0.3 + verifiedBonus), 1);
  }

  private calculateRedditInfluence(submission: any): number {
    const karma = submission.ups || 0;
    const comments = submission.num_comments || 0;
    const ratio = submission.upvote_ratio || 0.5;

    return Math.min((karma * ratio + comments * 2) / 1000, 1);
  }

  private calculateRelevanceScore(post: SocialMediaPost): number {
    const footballTerms = [
      'football', 'soccer', 'match', 'game', 'goal', 'team', 'player', 'league',
      'premier', 'champions', 'uefa', 'fifa', 'world cup', 'euro', 'transfer',
      'injury', 'coach', 'manager', 'stadium', 'fixture', 'table', 'season'
    ];

    const text = post.content.text.toLowerCase();
    let relevanceScore = 0;

    footballTerms.forEach(term => {
      if (text.includes(term)) {
        relevanceScore += 0.1;
      }
    });

    // Boost for hashtags
    post.content.hashtags.forEach(hashtag => {
      if (footballTerms.some(term => hashtag.toLowerCase().includes(term))) {
        relevanceScore += 0.15;
      }
    });

    return Math.min(relevanceScore, 1);
  }

  private calculateViralityScore(post: SocialMediaPost): number {
    const engagement = post.engagement.likes + post.engagement.shares + post.engagement.comments;
    const timeHours = (Date.now() - post.metadata.timestamp) / 3600000;

    if (timeHours === 0) return 0;

    const engagementRate = engagement / Math.max(timeHours, 1);
    const authorBonus = post.author.influence * 0.3;

    return Math.min((engagementRate / 100) + authorBonus, 1);
  }

  private calculateCredibilityScore(post: SocialMediaPost): number {
    let credibility = 0.5; // Base score

    // Author factors
    if (post.author.verified) credibility += 0.3;
    if (post.author.followers > 10000) credibility += 0.1;
    if (post.author.followers > 100000) credibility += 0.1;

    // Content factors
    if (post.content.text.length > 100) credibility += 0.05;
    if (post.content.media && post.content.media.length > 0) credibility += 0.05;

    // Platform factors
    if (post.platform === 'youtube') credibility += 0.1; // Video content generally more credible
    if (post.platform === 'reddit') credibility -= 0.05; // Anonymous nature

    return Math.min(Math.max(credibility, 0), 1);
  }

  // Utility methods
  private extractHashtags(text: string): string[] {
    const hashtags = text.match(/#\w+/g) || [];
    return hashtags.map(tag => tag.slice(1)); // Remove # symbol
  }

  private extractMentions(text: string): string[] {
    const mentions = text.match(/@\w+/g) || [];
    return mentions.map(mention => mention.slice(1)); // Remove @ symbol
  }

  private extractTopics(text: string): string[] {
    const footballTopics = [
      'transfer', 'injury', 'goal', 'penalty', 'red card', 'yellow card',
      'substitute', 'lineup', 'formation', 'tactics', 'referee', 'var',
      'champions league', 'premier league', 'world cup', 'euros'
    ];

    const lowerText = text.toLowerCase();
    return footballTopics.filter(topic => lowerText.includes(topic));
  }

  private extractEntities(text: string): Array<{type: 'team' | 'player' | 'match' | 'league' | 'injury' | 'transfer'; name: string; confidence: number}> {
    // Simple entity extraction - in production, use proper NER
    const entities: Array<{type: 'team' | 'player' | 'match' | 'league' | 'injury' | 'transfer'; name: string; confidence: number}> = [];
    const lowerText = text.toLowerCase();

    // Common team names (simplified)
    const teams = ['arsenal', 'chelsea', 'liverpool', 'manchester united', 'manchester city', 'tottenham'];
    teams.forEach(team => {
      if (lowerText.includes(team)) {
        entities.push({
          type: 'team',
          name: team,
          confidence: 0.8
        });
      }
    });

    return entities;
  }

  // Simulation methods for testing without API keys
  private simulateTwitterPosts(query: string): SocialMediaPost[] {
    const posts: SocialMediaPost[] = [];
    const numPosts = Math.floor(Math.random() * 20) + 10;

    for (let i = 0; i < numPosts; i++) {
      const post: SocialMediaPost = {
        id: `twitter_${Date.now()}_${i}`,
        platform: 'twitter',
        author: {
          id: `user_${i}`,
          username: `user${i}`,
          displayName: `User ${i}`,
          verified: Math.random() > 0.8,
          followers: Math.floor(Math.random() * 50000),
          influence: Math.random()
        },
        content: {
          text: `Simulated tweet about ${query} - this is post number ${i}`,
          hashtags: [`${query.replace(/\s+/g, '')}`],
          mentions: [],
          media: []
        },
        engagement: {
          likes: Math.floor(Math.random() * 1000),
          shares: Math.floor(Math.random() * 200),
          comments: Math.floor(Math.random() * 100)
        },
        metadata: {
          timestamp: Date.now() - Math.random() * 86400000,
          language: 'en'
        },
        analysis: {
          sentiment: { score: (Math.random() - 0.5) * 2, magnitude: Math.random(), confidence: Math.random(), keywords: [], sources: [] },
          relevance: Math.random(),
          virality: Math.random(),
          credibility: Math.random(),
          topics: [query],
          entities: []
        }
      };

      posts.push(post);
    }

    return posts;
  }

  private simulateRedditPosts(query: string): SocialMediaPost[] {
    return []; // Simplified for brevity
  }

  private simulateYouTubePosts(query: string): SocialMediaPost[] {
    return []; // Simplified for brevity
  }

  // Additional utility methods
  private async checkRateLimit(platform: string): Promise<void> {
    const now = Date.now();
    const limit = this.rateLimits.get(platform);

    if (limit && now < limit.resetTime) {
      if (limit.requests >= this.getRateLimitMax(platform)) {
        const waitTime = limit.resetTime - now;
        throw new Error(`Rate limit exceeded for ${platform}. Wait ${waitTime}ms`);
      }
      limit.requests++;
    } else {
      this.rateLimits.set(platform, {
        requests: 1,
        resetTime: now + this.getRateLimitWindow(platform)
      });
    }
  }

  private getRateLimitMax(platform: string): number {
    const limits = {
      twitter: 100, // per 15 minutes
      reddit: 60,   // per minute
      youtube: 100  // per day
    };
    return limits[platform as keyof typeof limits] || 60;
  }

  private getRateLimitWindow(platform: string): number {
    const windows = {
      twitter: 15 * 60 * 1000, // 15 minutes
      reddit: 60 * 1000,       // 1 minute
      youtube: 24 * 60 * 60 * 1000 // 24 hours
    };
    return windows[platform as keyof typeof windows] || 60 * 1000;
  }

  private deduplicatePosts(posts: SocialMediaPost[]): SocialMediaPost[] {
    const seen = new Set<string>();
    return posts.filter(post => {
      const key = `${post.platform}-${post.content.text.slice(0, 50)}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }

  private mergeSimilarTopics(topics: TrendingTopic[]): TrendingTopic[] {
    // Simple implementation - in production, use proper topic clustering
    const merged = new Map<string, TrendingTopic>();

    topics.forEach(topic => {
      const key = topic.keyword.toLowerCase();
      if (merged.has(key)) {
        const existing = merged.get(key)!;
        existing.volume += topic.volume;
        existing.platforms.push(...topic.platforms);
      } else {
        merged.set(key, { ...topic });
      }
    });

    return Array.from(merged.values()).sort((a, b) => b.volume - a.volume);
  }

  private analyzeMatchSocialData(matchId: string, homeTeam: string, awayTeam: string, posts: SocialMediaPost[]): MatchSocialBuzz {
    // Implement match buzz analysis
    return this.getDefaultMatchBuzz(matchId, homeTeam, awayTeam);
  }

  private calculateTeamMetrics(posts: SocialMediaPost[]) {
    const totalEngagement = posts.reduce((sum, post) =>
      sum + post.engagement.likes + post.engagement.shares + post.engagement.comments, 0);

    const totalFollowers = posts.reduce((sum, post) => sum + post.author.followers, 0);

    const avgSentiment = posts.reduce((sum, post) => sum + post.analysis.sentiment.score, 0) / posts.length;

    return {
      totalFollowers,
      totalEngagement,
      weeklyGrowth: Math.random() * 10 - 5, // Simulated
      sentimentScore: avgSentiment,
      virality: posts.reduce((sum, post) => sum + post.analysis.virality, 0) / posts.length
    };
  }

  private analyzeFanEngagement(posts: SocialMediaPost[]) {
    const positiveHashtags = posts
      .filter(post => post.analysis.sentiment.score > 0.3)
      .flatMap(post => post.content.hashtags)
      .slice(0, 10);

    const negativeHashtags = posts
      .filter(post => post.analysis.sentiment.score < -0.3)
      .flatMap(post => post.content.hashtags)
      .slice(0, 10);

    return {
      positiveHashtags,
      negativeHashtags,
      topInfluencers: posts
        .filter(post => post.author.influence > 0.7)
        .slice(0, 5)
        .map(post => ({
          username: post.author.username,
          platform: post.platform,
          influence: post.author.influence,
          sentiment: post.analysis.sentiment.score
        }))
    };
  }

  private async getCompetitorComparison(teamName: string) {
    return {
      engagementRank: Math.floor(Math.random() * 20) + 1,
      sentimentRank: Math.floor(Math.random() * 20) + 1,
      growthRank: Math.floor(Math.random() * 20) + 1,
      totalTeamsCompared: 20
    };
  }

  private async getTeamSocialHandles(teamName: string) {
    // In production, maintain a database of team social handles
    return {
      twitter: `@${teamName.toLowerCase().replace(/\s+/g, '')}`,
      instagram: teamName.toLowerCase().replace(/\s+/g, ''),
      facebook: teamName.toLowerCase().replace(/\s+/g, ''),
      youtube: teamName,
      tiktok: teamName.toLowerCase().replace(/\s+/g, '')
    };
  }

  private async getTwitterTrends(category?: string): Promise<TrendingTopic[]> {
    // Implement Twitter trends fetching
    return [];
  }

  private async getRedditTrends(category?: string): Promise<TrendingTopic[]> {
    // Implement Reddit trends fetching
    return [];
  }

  private async getYouTubeTrends(category?: string): Promise<TrendingTopic[]> {
    // Implement YouTube trends fetching
    return [];
  }

  private getDefaultMatchBuzz(matchId: string, homeTeam: string, awayTeam: string): MatchSocialBuzz {
    return {
      matchId,
      homeTeam,
      awayTeam,
      preMatchBuzz: {
        volume: Math.floor(Math.random() * 10000),
        sentiment: { score: (Math.random() - 0.5) * 2, magnitude: Math.random(), confidence: Math.random(), keywords: [], sources: [] },
        keyTopics: ['prediction', 'lineup', 'form'],
        predictions: []
      },
      liveUpdates: [],
      postMatchAnalysis: {
        overallReaction: { score: (Math.random() - 0.5) * 2, magnitude: Math.random(), confidence: Math.random(), keywords: [], sources: [] },
        controversies: [],
        playerPerformanceReactions: []
      },
      viralMoments: []
    };
  }

  private getDefaultTeamProfile(teamName: string): TeamSocialProfile {
    return {
      teamName,
      handles: {},
      metrics: {
        totalFollowers: 0,
        totalEngagement: 0,
        weeklyGrowth: 0,
        sentimentScore: 0,
        virality: 0
      },
      recentActivity: [],
      fanEngagement: {
        positiveHashtags: [],
        negativeHashtags: [],
        topInfluencers: []
      },
      competitorComparison: {
        engagementRank: 0,
        sentimentRank: 0,
        growthRank: 0,
        totalTeamsCompared: 0
      }
    };
  }

  private startPeriodicMonitoring(): void {
    // Start monitoring every 5 minutes
    setInterval(() => {
      this.performPeriodicChecks();
    }, 300000);
  }

  private async performPeriodicChecks(): Promise<void> {
    try {
      // Check for trending topics
      const trending = await this.getTrendingTopics('football');

      // Generate alerts for significant trends
      trending.forEach(topic => {
        if (topic.volume > 10000 && topic.growth > 50) {
          this.generateTrendingAlert(topic);
        }
      });

    } catch (error) {
      console.error('Error in periodic monitoring:', error);
    }
  }

  private generateTrendingAlert(topic: TrendingTopic): void {
    const alert: SocialMediaAlert = {
      id: `trending_${Date.now()}`,
      type: 'trending_topic',
      title: `Trending: ${topic.keyword}`,
      description: `${topic.keyword} is trending with ${topic.volume} mentions (${topic.growth}% growth)`,
      severity: topic.growth > 100 ? 'high' : 'medium',
      confidence: Math.min(topic.growth / 100, 1),
      source: {
        platform: 'multiple',
        credibility: 0.8
      },
      content: {
        posts: [],
        summary: `${topic.keyword} is trending across social media platforms`,
        keyPoints: topic.relatedTerms
      },
      impact: {
        affectedTeams: [],
        affectedPlayers: [],
        affectedMatches: [],
        marketImpact: topic.sentiment.score * 0.1,
        publicOpinion: topic.sentiment.score
      },
      timeline: [{
        timestamp: topic.timespan.current,
        event: 'Topic started trending',
        volume: topic.volume
      }],
      recommendations: [{
        action: 'Monitor topic development',
        priority: 1,
        reasoning: 'High volume trending topic may impact betting markets'
      }],
      timestamp: Date.now(),
      resolved: false
    };

    this.activeAlerts.unshift(alert);
    if (this.activeAlerts.length > 100) {
      this.activeAlerts = this.activeAlerts.slice(0, 100);
    }
  }

  // Public API methods
  getActiveAlerts(): SocialMediaAlert[] {
    return this.activeAlerts.filter(alert => !alert.resolved);
  }

  resolveAlert(alertId: string): boolean {
    const alert = this.activeAlerts.find(a => a.id === alertId);
    if (alert) {
      alert.resolved = true;
      return true;
    }
    return false;
  }

  clearCache(): void {
    this.cache.clear();
  }

  getCacheSize(): number {
    return this.cache.size;
  }

  getApiStatus(): { [key: string]: boolean } {
    return {
      twitterBearer: !!this.apiKeys.twitterBearer,
      redditApi: true, // No auth required for search
      youtubeApi: !!this.apiKeys.youtubeApiKey,
      rapidApi: !!this.apiKeys.rapidApi
    };
  }
}

export const socialMediaMonitoringService = new SocialMediaMonitoringService();
export default socialMediaMonitoringService;