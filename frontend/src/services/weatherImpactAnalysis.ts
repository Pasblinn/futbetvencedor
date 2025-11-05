import axios from 'axios';

export interface WeatherConditions {
  temperature: number; // Celsius
  humidity: number; // Percentage
  windSpeed: number; // km/h
  windDirection: number; // Degrees
  precipitation: number; // mm
  visibility: number; // km
  pressure: number; // hPa
  uvIndex: number;
  conditions: string;
  cloudCover: number; // Percentage
  dewPoint: number; // Celsius
  feelsLike: number; // Celsius
}

export interface WeatherForecast {
  timestamp: number;
  conditions: WeatherConditions;
  forecast: {
    kickoffWeather: WeatherConditions;
    halfTimeWeather: WeatherConditions;
    fullTimeWeather: WeatherConditions;
  };
  alerts: Array<{
    type: 'rain' | 'wind' | 'temperature' | 'fog' | 'snow';
    severity: 'low' | 'medium' | 'high' | 'extreme';
    description: string;
    startTime: number;
    endTime: number;
  }>;
  reliability: number; // 0-1 (forecast accuracy)
}

export interface WeatherImpact {
  overall: number; // -1 to 1 (negative to positive impact)
  goalScoring: {
    homeTeamImpact: number;
    awayTeamImpact: number;
    totalGoalsExpected: number;
    under25Probability: number;
    over35Probability: number;
  };
  playingStyle: {
    aerialPlay: number; // Wind and conditions effect
    passAccuracy: number; // Rain, wind effect
    ballControl: number; // Wet conditions
    physicality: number; // Temperature effect
    paceOfPlay: number; // Overall game speed
  };
  positions: {
    goalkeepers: number; // Visibility, wind, wet ball
    defenders: number; // Aerial play, ball control
    midfielders: number; // Pass accuracy, ball control
    forwards: number; // Ball control, movement
  };
  tacticalFactors: {
    longBallEffectiveness: number;
    shortPassingAccuracy: number;
    counterAttackSpeed: number;
    setpieceEffectiveness: number;
    substituionTiming: number;
  };
  historicalPerformance: {
    homeTeamRecord: {
      similarConditions: number;
      wins: number;
      draws: number;
      losses: number;
      goalsFor: number;
      goalsAgainst: number;
    };
    awayTeamRecord: {
      similarConditions: number;
      wins: number;
      draws: number;
      losses: number;
      goalsFor: number;
      goalsAgainst: number;
    };
  };
  recommendations: Array<{
    category: 'betting' | 'tactical' | 'lineup';
    confidence: number;
    description: string;
    impact: 'low' | 'medium' | 'high';
  }>;
}

export interface VenueWeatherProfile {
  venueId: string;
  venueName: string;
  location: {
    latitude: number;
    longitude: number;
    altitude: number;
    timezone: string;
  };
  characteristics: {
    roofType: 'open' | 'retractable' | 'closed';
    windExposure: number; // 0-1
    drainageQuality: number; // 0-1
    pitchType: 'natural' | 'artificial' | 'hybrid';
    orientation: number; // Stadium orientation in degrees
  };
  historicalData: {
    averageConditions: { [month: string]: WeatherConditions };
    extremeConditions: Array<{
      date: string;
      conditions: WeatherConditions;
      matchImpact: string;
    }>;
  };
}

export interface MatchWeatherAnalysis {
  matchId: string;
  venue: VenueWeatherProfile;
  forecast: WeatherForecast;
  impact: WeatherImpact;
  riskFactors: Array<{
    factor: string;
    probability: number;
    impact: string;
    mitigation: string;
  }>;
  comparison: {
    lastSeasonSameFixture?: WeatherConditions;
    averageConditionsForFixture: WeatherConditions;
    optimalConditions: WeatherConditions;
    variance: number;
  };
}

class WeatherImpactAnalysisService {
  private baseURL: string;
  private apiKeys: { [key: string]: string };
  private cache: Map<string, { data: any; expiry: number }> = new Map();
  private venueDatabase: Map<string, VenueWeatherProfile> = new Map();

  // Weather impact coefficients based on research
  private readonly impactCoefficients = {
    temperature: {
      optimal: 18, // Celsius
      coldThreshold: 5,
      hotThreshold: 30,
      goalImpact: 0.05, // Per degree deviation
    },
    wind: {
      lowThreshold: 10, // km/h
      highThreshold: 25,
      aerialImpact: 0.08, // Per km/h above threshold
      passAccuracyImpact: 0.03,
    },
    rain: {
      lightThreshold: 1, // mm
      heavyThreshold: 10,
      ballControlImpact: 0.12,
      goalkeepingImpact: 0.15,
    },
    humidity: {
      optimalRange: [40, 60], // Percentage
      fatigueImpact: 0.02, // Per % above 70%
    },
    visibility: {
      poorThreshold: 5, // km
      criticalThreshold: 1,
      decisionMakingImpact: 0.2,
    }
  };

  constructor() {
    this.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:3001';
    this.apiKeys = {
      openWeatherMap: process.env.REACT_APP_OPENWEATHER_API_KEY || '',
      weatherAPI: process.env.REACT_APP_WEATHER_API_KEY || '',
      accuWeather: process.env.REACT_APP_ACCUWEATHER_API_KEY || '',
      visualCrossing: process.env.REACT_APP_VISUALCROSSING_API_KEY || ''
    };

    this.initializeVenueDatabase();
  }

  private initializeVenueDatabase() {
    // Initialize with major stadiums - in real implementation, load from database
    const majorVenues: VenueWeatherProfile[] = [
      {
        venueId: '1',
        venueName: 'Old Trafford',
        location: { latitude: 53.4631, longitude: -2.2914, altitude: 78, timezone: 'Europe/London' },
        characteristics: {
          roofType: 'open',
          windExposure: 0.7,
          drainageQuality: 0.9,
          pitchType: 'natural',
          orientation: 110
        },
        historicalData: { averageConditions: {}, extremeConditions: [] }
      },
      {
        venueId: '2',
        venueName: 'Emirates Stadium',
        location: { latitude: 51.5549, longitude: -0.1084, altitude: 41, timezone: 'Europe/London' },
        characteristics: {
          roofType: 'open',
          windExposure: 0.6,
          drainageQuality: 0.95,
          pitchType: 'natural',
          orientation: 90
        },
        historicalData: { averageConditions: {}, extremeConditions: [] }
      }
    ];

    majorVenues.forEach(venue => {
      this.venueDatabase.set(venue.venueId, venue);
    });
  }

  // Main analysis method
  async analyzeMatchWeather(
    matchId: string,
    venueId: string,
    matchDateTime: number,
    homeTeam: string,
    awayTeam: string
  ): Promise<MatchWeatherAnalysis> {
    const cacheKey = `weather-analysis-${matchId}-${matchDateTime}`;

    if (this.cache.has(cacheKey)) {
      const cached = this.cache.get(cacheKey);
      if (cached && cached.expiry > Date.now()) {
        return cached.data;
      }
    }

    try {
      const venue = this.getVenueProfile(venueId);
      const forecast = await this.getDetailedForecast(venue, matchDateTime);
      const impact = await this.calculateWeatherImpact(forecast, venue, homeTeam, awayTeam);
      const riskFactors = this.assessRiskFactors(forecast, venue);
      const comparison = await this.getWeatherComparison(venue, matchDateTime, homeTeam, awayTeam);

      const analysis: MatchWeatherAnalysis = {
        matchId,
        venue,
        forecast,
        impact,
        riskFactors,
        comparison
      };

      this.cache.set(cacheKey, {
        data: analysis,
        expiry: Date.now() + 1800000 // 30 minutes cache
      });

      return analysis;
    } catch (error) {
      console.error('Error analyzing match weather:', error);
      return this.getDefaultWeatherAnalysis(matchId, venueId, matchDateTime);
    }
  }

  // Get detailed weather forecast
  private async getDetailedForecast(venue: VenueWeatherProfile, matchDateTime: number): Promise<WeatherForecast> {
    try {
      // Try multiple weather APIs for reliability
      const forecasts = await Promise.allSettled([
        this.getOpenWeatherMapForecast(venue, matchDateTime),
        this.getWeatherAPIForecast(venue, matchDateTime),
        this.getVisualCrossingForecast(venue, matchDateTime)
      ]);

      // Use the most reliable forecast
      const validForecasts = forecasts
        .filter(f => f.status === 'fulfilled')
        .map(f => (f as PromiseFulfilledResult<WeatherForecast>).value);

      if (validForecasts.length === 0) {
        return this.getDefaultForecast(matchDateTime);
      }

      // Combine forecasts with weighted average based on reliability
      return this.combineForecast(validForecasts);
    } catch (error) {
      console.error('Error getting weather forecast:', error);
      return this.getDefaultForecast(matchDateTime);
    }
  }

  private async getOpenWeatherMapForecast(venue: VenueWeatherProfile, matchDateTime: number): Promise<WeatherForecast> {
    if (!this.apiKeys.openWeatherMap) {
      throw new Error('OpenWeatherMap API key not available');
    }

    const response = await axios.get('https://api.openweathermap.org/data/2.5/forecast', {
      params: {
        lat: venue.location.latitude,
        lon: venue.location.longitude,
        appid: this.apiKeys.openWeatherMap,
        units: 'metric'
      },
      timeout: 10000
    });

    return this.processOpenWeatherMapResponse(response.data, matchDateTime);
  }

  private async getWeatherAPIForecast(venue: VenueWeatherProfile, matchDateTime: number): Promise<WeatherForecast> {
    if (!this.apiKeys.weatherAPI) {
      throw new Error('WeatherAPI key not available');
    }

    const date = new Date(matchDateTime).toISOString().split('T')[0];
    const response = await axios.get('http://api.weatherapi.com/v1/forecast.json', {
      params: {
        key: this.apiKeys.weatherAPI,
        q: `${venue.location.latitude},${venue.location.longitude}`,
        dt: date,
        hour: new Date(matchDateTime).getHours()
      },
      timeout: 10000
    });

    return this.processWeatherAPIResponse(response.data, matchDateTime);
  }

  private async getVisualCrossingForecast(venue: VenueWeatherProfile, matchDateTime: number): Promise<WeatherForecast> {
    if (!this.apiKeys.visualCrossing) {
      throw new Error('Visual Crossing API key not available');
    }

    const date = new Date(matchDateTime).toISOString().split('T')[0];
    const response = await axios.get(
      `https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/${venue.location.latitude},${venue.location.longitude}/${date}`,
      {
        params: {
          key: this.apiKeys.visualCrossing,
          unitGroup: 'metric',
          include: 'hours'
        },
        timeout: 10000
      }
    );

    return this.processVisualCrossingResponse(response.data, matchDateTime);
  }

  // Calculate comprehensive weather impact
  private async calculateWeatherImpact(
    forecast: WeatherForecast,
    venue: VenueWeatherProfile,
    homeTeam: string,
    awayTeam: string
  ): Promise<WeatherImpact> {
    const conditions = forecast.forecast.kickoffWeather;

    // Calculate individual impact factors
    const temperatureImpact = this.calculateTemperatureImpact(conditions.temperature);
    const windImpact = this.calculateWindImpact(conditions.windSpeed, venue.characteristics.windExposure);
    const precipitationImpact = this.calculatePrecipitationImpact(conditions.precipitation);
    const humidityImpact = this.calculateHumidityImpact(conditions.humidity);
    const visibilityImpact = this.calculateVisibilityImpact(conditions.visibility);

    // Get historical performance
    const historicalPerformance = await this.getHistoricalWeatherPerformance(
      homeTeam, awayTeam, conditions
    );

    // Calculate position-specific impacts
    const positions = {
      goalkeepers: this.calculateGoalkeeperImpact(conditions, venue),
      defenders: this.calculateDefenderImpact(conditions),
      midfielders: this.calculateMidfielderImpact(conditions),
      forwards: this.calculateForwardImpact(conditions)
    };

    // Calculate tactical factors
    const tacticalFactors = {
      longBallEffectiveness: windImpact.aerialPlay,
      shortPassingAccuracy: precipitationImpact.passAccuracy + windImpact.passAccuracy,
      counterAttackSpeed: temperatureImpact + precipitationImpact.ballControl,
      setpieceEffectiveness: windImpact.setpieces,
      substituionTiming: humidityImpact + temperatureImpact
    };

    // Calculate goal scoring impact
    const goalScoring = {
      homeTeamImpact: this.calculateTeamGoalImpact(conditions, venue, 'home', historicalPerformance.homeTeamRecord),
      awayTeamImpact: this.calculateTeamGoalImpact(conditions, venue, 'away', historicalPerformance.awayTeamRecord),
      totalGoalsExpected: 0,
      under25Probability: 0,
      over35Probability: 0
    };

    goalScoring.totalGoalsExpected = 2.5 + (goalScoring.homeTeamImpact + goalScoring.awayTeamImpact) * 0.5;
    goalScoring.under25Probability = goalScoring.totalGoalsExpected < 2.5 ? 0.6 : 0.4;
    goalScoring.over35Probability = goalScoring.totalGoalsExpected > 3.5 ? 0.6 : 0.3;

    // Calculate playing style impacts
    const playingStyle = {
      aerialPlay: windImpact.aerialPlay,
      passAccuracy: precipitationImpact.passAccuracy + windImpact.passAccuracy,
      ballControl: precipitationImpact.ballControl,
      physicality: temperatureImpact + humidityImpact,
      paceOfPlay: (temperatureImpact + humidityImpact + precipitationImpact.ballControl) / 3
    };

    // Calculate overall impact
    const overall = this.calculateOverallImpact(conditions, venue);

    // Generate recommendations
    const recommendations = this.generateWeatherRecommendations(conditions, venue, {
      goalScoring,
      playingStyle,
      tacticalFactors
    });

    return {
      overall,
      goalScoring,
      playingStyle,
      positions,
      tacticalFactors,
      historicalPerformance,
      recommendations
    };
  }

  // Impact calculation methods
  private calculateTemperatureImpact(temperature: number): number {
    const optimal = this.impactCoefficients.temperature.optimal;
    const deviation = Math.abs(temperature - optimal);

    if (temperature < this.impactCoefficients.temperature.coldThreshold) {
      return -(deviation * this.impactCoefficients.temperature.goalImpact * 1.5);
    } else if (temperature > this.impactCoefficients.temperature.hotThreshold) {
      return -(deviation * this.impactCoefficients.temperature.goalImpact * 1.2);
    }

    return -(deviation * this.impactCoefficients.temperature.goalImpact);
  }

  private calculateWindImpact(windSpeed: number, windExposure: number) {
    const adjustedWindSpeed = windSpeed * windExposure;
    const impact = {
      aerialPlay: 0,
      passAccuracy: 0,
      setpieces: 0
    };

    if (adjustedWindSpeed > this.impactCoefficients.wind.highThreshold) {
      const excess = adjustedWindSpeed - this.impactCoefficients.wind.highThreshold;
      impact.aerialPlay = -(excess * this.impactCoefficients.wind.aerialImpact);
      impact.passAccuracy = -(excess * this.impactCoefficients.wind.passAccuracyImpact);
      impact.setpieces = -(excess * this.impactCoefficients.wind.aerialImpact * 1.2);
    } else if (adjustedWindSpeed > this.impactCoefficients.wind.lowThreshold) {
      const excess = adjustedWindSpeed - this.impactCoefficients.wind.lowThreshold;
      impact.aerialPlay = -(excess * this.impactCoefficients.wind.aerialImpact * 0.5);
      impact.passAccuracy = -(excess * this.impactCoefficients.wind.passAccuracyImpact * 0.5);
    }

    return impact;
  }

  private calculatePrecipitationImpact(precipitation: number) {
    const impact = {
      ballControl: 0,
      passAccuracy: 0,
      goalkeeping: 0
    };

    if (precipitation > this.impactCoefficients.rain.heavyThreshold) {
      impact.ballControl = -(precipitation * this.impactCoefficients.rain.ballControlImpact);
      impact.passAccuracy = -(precipitation * this.impactCoefficients.rain.ballControlImpact * 0.8);
      impact.goalkeeping = -(precipitation * this.impactCoefficients.rain.goalkeepingImpact);
    } else if (precipitation > this.impactCoefficients.rain.lightThreshold) {
      impact.ballControl = -(precipitation * this.impactCoefficients.rain.ballControlImpact * 0.6);
      impact.passAccuracy = -(precipitation * this.impactCoefficients.rain.ballControlImpact * 0.4);
      impact.goalkeeping = -(precipitation * this.impactCoefficients.rain.goalkeepingImpact * 0.6);
    }

    return impact;
  }

  private calculateHumidityImpact(humidity: number): number {
    const [minOptimal, maxOptimal] = this.impactCoefficients.humidity.optimalRange;

    if (humidity < minOptimal) {
      return -((minOptimal - humidity) * 0.01);
    } else if (humidity > maxOptimal) {
      const excess = humidity - maxOptimal;
      if (excess > 10) {
        return -(excess * this.impactCoefficients.humidity.fatigueImpact);
      }
    }

    return 0;
  }

  private calculateVisibilityImpact(visibility: number): number {
    if (visibility < this.impactCoefficients.visibility.criticalThreshold) {
      return -(this.impactCoefficients.visibility.decisionMakingImpact * 2);
    } else if (visibility < this.impactCoefficients.visibility.poorThreshold) {
      const factor = (this.impactCoefficients.visibility.poorThreshold - visibility) /
                    this.impactCoefficients.visibility.poorThreshold;
      return -(factor * this.impactCoefficients.visibility.decisionMakingImpact);
    }

    return 0;
  }

  // Position-specific impact calculations
  private calculateGoalkeeperImpact(conditions: WeatherConditions, venue: VenueWeatherProfile): number {
    let impact = 0;

    // Wind affects distribution and handling
    if (conditions.windSpeed > 15) {
      impact -= (conditions.windSpeed - 15) * 0.02;
    }

    // Rain affects grip and visibility
    if (conditions.precipitation > 1) {
      impact -= conditions.precipitation * 0.03;
    }

    // Visibility
    if (conditions.visibility < 5) {
      impact -= (5 - conditions.visibility) * 0.1;
    }

    return Math.max(impact, -0.5); // Cap at -50%
  }

  private calculateDefenderImpact(conditions: WeatherConditions): number {
    let impact = 0;

    // Aerial duels affected by wind
    if (conditions.windSpeed > 20) {
      impact -= (conditions.windSpeed - 20) * 0.015;
    }

    // Ball control in wet conditions
    if (conditions.precipitation > 2) {
      impact -= conditions.precipitation * 0.02;
    }

    return Math.max(impact, -0.4);
  }

  private calculateMidfielderImpact(conditions: WeatherConditions): number {
    let impact = 0;

    // Passing accuracy most affected
    if (conditions.windSpeed > 15) {
      impact -= (conditions.windSpeed - 15) * 0.025;
    }

    if (conditions.precipitation > 1) {
      impact -= conditions.precipitation * 0.025;
    }

    // Stamina affected by temperature and humidity
    if (conditions.temperature > 28 || conditions.humidity > 75) {
      impact -= 0.02;
    }

    return Math.max(impact, -0.4);
  }

  private calculateForwardImpact(conditions: WeatherConditions): number {
    let impact = 0;

    // Ball control and first touch
    if (conditions.precipitation > 1) {
      impact -= conditions.precipitation * 0.02;
    }

    // Movement and agility in extreme temperatures
    if (conditions.temperature < 5 || conditions.temperature > 30) {
      impact -= 0.03;
    }

    return Math.max(impact, -0.3);
  }

  private calculateTeamGoalImpact(
    conditions: WeatherConditions,
    venue: VenueWeatherProfile,
    homeAway: 'home' | 'away',
    historicalRecord: any
  ): number {
    let impact = 0;

    // Base weather impact on goal scoring
    impact += this.calculateTemperatureImpact(conditions.temperature) * 0.1;

    const windImpact = this.calculateWindImpact(conditions.windSpeed, venue.characteristics.windExposure);
    impact += windImpact.aerialPlay * 0.05;

    const precipitationImpact = this.calculatePrecipitationImpact(conditions.precipitation);
    impact += precipitationImpact.ballControl * 0.08;

    // Home advantage in adverse conditions
    if (homeAway === 'home' && (conditions.precipitation > 5 || conditions.windSpeed > 25)) {
      impact += 0.05; // Home familiarity advantage
    }

    // Historical performance adjustment
    if (historicalRecord.similarConditions > 5) {
      const historicalGoalAverage = historicalRecord.goalsFor / historicalRecord.similarConditions;
      if (historicalGoalAverage > 1.5) {
        impact += 0.03; // Good historical performance in similar conditions
      } else if (historicalGoalAverage < 1.0) {
        impact -= 0.03; // Poor historical performance
      }
    }

    return Math.max(Math.min(impact, 0.2), -0.2); // Cap between -20% and +20%
  }

  private calculateOverallImpact(conditions: WeatherConditions, venue: VenueWeatherProfile): number {
    const factors = [
      this.calculateTemperatureImpact(conditions.temperature),
      this.calculateWindImpact(conditions.windSpeed, venue.characteristics.windExposure).aerialPlay,
      this.calculatePrecipitationImpact(conditions.precipitation).ballControl,
      this.calculateHumidityImpact(conditions.humidity),
      this.calculateVisibilityImpact(conditions.visibility)
    ];

    // Weighted average of all factors
    const weights = [0.2, 0.25, 0.3, 0.15, 0.1];
    const weightedSum = factors.reduce((sum, factor, index) => sum + (factor * weights[index]), 0);

    return Math.max(Math.min(weightedSum, 1), -1);
  }

  // Risk assessment
  private assessRiskFactors(forecast: WeatherForecast, venue: VenueWeatherProfile) {
    const risks = [];
    const conditions = forecast.forecast.kickoffWeather;

    // Postponement risk
    if (conditions.windSpeed > 40 || conditions.precipitation > 20 || conditions.visibility < 0.5) {
      risks.push({
        factor: 'Match Postponement',
        probability: 0.8,
        impact: 'All bets void',
        mitigation: 'Monitor weather updates closely'
      });
    }

    // Significant game disruption
    if (conditions.precipitation > 10 || conditions.windSpeed > 30) {
      risks.push({
        factor: 'Game Disruption',
        probability: 0.6,
        impact: 'Lower scoring, more defensive play',
        mitigation: 'Consider under bets and defensive strategies'
      });
    }

    // Player performance impact
    if (conditions.temperature < 0 || conditions.temperature > 35) {
      risks.push({
        factor: 'Player Performance Impact',
        probability: 0.7,
        impact: 'Reduced technical quality',
        mitigation: 'Focus on more direct playing style bets'
      });
    }

    return risks;
  }

  // Weather comparison
  private async getWeatherComparison(
    venue: VenueWeatherProfile,
    matchDateTime: number,
    homeTeam: string,
    awayTeam: string
  ) {
    const month = new Date(matchDateTime).getMonth();
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const monthKey = monthNames[month];

    return {
      averageConditionsForFixture: venue.historicalData.averageConditions[monthKey] || this.getTypicalConditions(month),
      optimalConditions: this.getOptimalConditions(),
      variance: Math.random() * 0.3 + 0.1 // Placeholder - calculate actual variance
    };
  }

  // Generate recommendations
  private generateWeatherRecommendations(conditions: WeatherConditions, venue: VenueWeatherProfile, impacts: any): Array<{category: 'betting' | 'tactical' | 'lineup'; confidence: number; description: string; impact: 'low' | 'medium' | 'high'}> {
    const recommendations: Array<{category: 'betting' | 'tactical' | 'lineup'; confidence: number; description: string; impact: 'low' | 'medium' | 'high'}> = [];

    // Goal-based recommendations
    if (impacts.goalScoring.totalGoalsExpected < 2.0) {
      recommendations.push({
        category: 'betting',
        confidence: 0.75,
        description: 'Consider under 2.5 goals due to adverse weather conditions',
        impact: 'medium'
      });
    }

    if (impacts.playingStyle.aerialPlay < -0.2) {
      recommendations.push({
        category: 'tactical',
        confidence: 0.8,
        description: 'Wind conditions favor short passing over aerial play',
        impact: 'high'
      });
    }

    if (conditions.precipitation > 5) {
      recommendations.push({
        category: 'lineup',
        confidence: 0.7,
        description: 'Teams may prefer players with better ball control in wet conditions',
        impact: 'medium'
      });
    }

    if (conditions.temperature < 5) {
      recommendations.push({
        category: 'betting',
        confidence: 0.6,
        description: 'Cold weather may lead to more physical play and cards',
        impact: 'low'
      });
    }

    return recommendations;
  }

  // Utility methods
  private getVenueProfile(venueId: string): VenueWeatherProfile {
    return this.venueDatabase.get(venueId) || this.getDefaultVenueProfile(venueId);
  }

  private getDefaultVenueProfile(venueId: string): VenueWeatherProfile {
    return {
      venueId,
      venueName: 'Unknown Venue',
      location: { latitude: 51.5074, longitude: -0.1278, altitude: 11, timezone: 'Europe/London' },
      characteristics: {
        roofType: 'open',
        windExposure: 0.5,
        drainageQuality: 0.7,
        pitchType: 'natural',
        orientation: 90
      },
      historicalData: { averageConditions: {}, extremeConditions: [] }
    };
  }

  private getDefaultForecast(matchDateTime: number): WeatherForecast {
    const defaultConditions: WeatherConditions = {
      temperature: 15,
      humidity: 60,
      windSpeed: 10,
      windDirection: 180,
      precipitation: 0,
      visibility: 10,
      pressure: 1013,
      uvIndex: 3,
      conditions: 'Partly Cloudy',
      cloudCover: 50,
      dewPoint: 8,
      feelsLike: 15
    };

    return {
      timestamp: Date.now(),
      conditions: defaultConditions,
      forecast: {
        kickoffWeather: defaultConditions,
        halfTimeWeather: defaultConditions,
        fullTimeWeather: defaultConditions
      },
      alerts: [],
      reliability: 0.3
    };
  }

  private getDefaultWeatherAnalysis(matchId: string, venueId: string, matchDateTime: number): MatchWeatherAnalysis {
    const venue = this.getVenueProfile(venueId);
    const forecast = this.getDefaultForecast(matchDateTime);

    return {
      matchId,
      venue,
      forecast,
      impact: {
        overall: 0,
        goalScoring: {
          homeTeamImpact: 0,
          awayTeamImpact: 0,
          totalGoalsExpected: 2.5,
          under25Probability: 0.5,
          over35Probability: 0.3
        },
        playingStyle: {
          aerialPlay: 0,
          passAccuracy: 0,
          ballControl: 0,
          physicality: 0,
          paceOfPlay: 0
        },
        positions: {
          goalkeepers: 0,
          defenders: 0,
          midfielders: 0,
          forwards: 0
        },
        tacticalFactors: {
          longBallEffectiveness: 0,
          shortPassingAccuracy: 0,
          counterAttackSpeed: 0,
          setpieceEffectiveness: 0,
          substituionTiming: 0
        },
        historicalPerformance: {
          homeTeamRecord: {
            similarConditions: 0,
            wins: 0,
            draws: 0,
            losses: 0,
            goalsFor: 0,
            goalsAgainst: 0
          },
          awayTeamRecord: {
            similarConditions: 0,
            wins: 0,
            draws: 0,
            losses: 0,
            goalsFor: 0,
            goalsAgainst: 0
          }
        },
        recommendations: []
      },
      riskFactors: [],
      comparison: {
        averageConditionsForFixture: forecast.conditions,
        optimalConditions: this.getOptimalConditions(),
        variance: 0.1
      }
    };
  }

  private getOptimalConditions(): WeatherConditions {
    return {
      temperature: 18,
      humidity: 50,
      windSpeed: 5,
      windDirection: 180,
      precipitation: 0,
      visibility: 20,
      pressure: 1013,
      uvIndex: 4,
      conditions: 'Clear',
      cloudCover: 10,
      dewPoint: 10,
      feelsLike: 18
    };
  }

  private getTypicalConditions(month: number): WeatherConditions {
    // Typical UK weather by month
    const monthlyAverages = [
      { temp: 7, humidity: 75, wind: 15, precip: 2 }, // Jan
      { temp: 8, humidity: 70, wind: 14, precip: 1.8 }, // Feb
      { temp: 11, humidity: 65, wind: 13, precip: 1.5 }, // Mar
      { temp: 14, humidity: 60, wind: 12, precip: 1.2 }, // Apr
      { temp: 17, humidity: 55, wind: 11, precip: 1.0 }, // May
      { temp: 20, humidity: 55, wind: 10, precip: 1.1 }, // Jun
      { temp: 22, humidity: 60, wind: 10, precip: 1.3 }, // Jul
      { temp: 21, humidity: 65, wind: 11, precip: 1.5 }, // Aug
      { temp: 18, humidity: 70, wind: 12, precip: 1.8 }, // Sep
      { temp: 14, humidity: 75, wind: 13, precip: 2.2 }, // Oct
      { temp: 10, humidity: 80, wind: 14, precip: 2.5 }, // Nov
      { temp: 7, humidity: 80, wind: 15, precip: 2.8 }   // Dec
    ];

    const monthData = monthlyAverages[month];
    return {
      temperature: monthData.temp,
      humidity: monthData.humidity,
      windSpeed: monthData.wind,
      windDirection: 225, // SW typical for UK
      precipitation: monthData.precip,
      visibility: 12,
      pressure: 1013,
      uvIndex: month >= 4 && month <= 8 ? 5 : 2,
      conditions: monthData.precip > 2 ? 'Light Rain' : 'Partly Cloudy',
      cloudCover: 60,
      dewPoint: monthData.temp - 5,
      feelsLike: monthData.temp
    };
  }

  // API response processors
  private processOpenWeatherMapResponse(data: any, matchDateTime: number): WeatherForecast {
    // Find closest forecast to match time
    const matchHour = new Date(matchDateTime).getHours();
    const forecast = data.list.find((f: any) => {
      const forecastHour = new Date(f.dt * 1000).getHours();
      return Math.abs(forecastHour - matchHour) <= 3;
    }) || data.list[0];

    const conditions: WeatherConditions = {
      temperature: forecast.main.temp,
      humidity: forecast.main.humidity,
      windSpeed: forecast.wind.speed * 3.6, // Convert m/s to km/h
      windDirection: forecast.wind.deg,
      precipitation: (forecast.rain?.['3h'] || 0) / 3, // Convert 3h to hourly
      visibility: (forecast.visibility || 10000) / 1000, // Convert m to km
      pressure: forecast.main.pressure,
      uvIndex: 0, // Not available in this API
      conditions: forecast.weather[0].description,
      cloudCover: forecast.clouds.all,
      dewPoint: forecast.main.temp - ((100 - forecast.main.humidity) / 5),
      feelsLike: forecast.main.feels_like
    };

    return {
      timestamp: Date.now(),
      conditions,
      forecast: {
        kickoffWeather: conditions,
        halfTimeWeather: conditions,
        fullTimeWeather: conditions
      },
      alerts: [],
      reliability: 0.85
    };
  }

  private processWeatherAPIResponse(data: any, matchDateTime: number): WeatherForecast {
    const forecast = data.forecast.forecastday[0];
    const hour = forecast.hour.find((h: any) => {
      const hourTime = new Date(h.time).getHours();
      const matchHour = new Date(matchDateTime).getHours();
      return Math.abs(hourTime - matchHour) <= 1;
    }) || forecast.hour[12];

    const conditions: WeatherConditions = {
      temperature: hour.temp_c,
      humidity: hour.humidity,
      windSpeed: hour.wind_kph,
      windDirection: hour.wind_degree,
      precipitation: hour.precip_mm,
      visibility: hour.vis_km,
      pressure: hour.pressure_mb,
      uvIndex: hour.uv,
      conditions: hour.condition.text,
      cloudCover: hour.cloud,
      dewPoint: hour.dewpoint_c,
      feelsLike: hour.feelslike_c
    };

    return {
      timestamp: Date.now(),
      conditions,
      forecast: {
        kickoffWeather: conditions,
        halfTimeWeather: conditions,
        fullTimeWeather: conditions
      },
      alerts: [],
      reliability: 0.9
    };
  }

  private processVisualCrossingResponse(data: any, matchDateTime: number): WeatherForecast {
    const day = data.days[0];
    const matchHour = new Date(matchDateTime).getHours();
    const hour = day.hours[matchHour] || day.hours[15]; // Default to 3 PM

    const conditions: WeatherConditions = {
      temperature: hour.temp,
      humidity: hour.humidity,
      windSpeed: hour.windspeed * 1.609, // Convert mph to km/h
      windDirection: hour.winddir,
      precipitation: hour.precip || 0,
      visibility: hour.visibility,
      pressure: hour.pressure,
      uvIndex: hour.uvindex,
      conditions: hour.conditions,
      cloudCover: hour.cloudcover,
      dewPoint: hour.dew,
      feelsLike: hour.feelslike
    };

    return {
      timestamp: Date.now(),
      conditions,
      forecast: {
        kickoffWeather: conditions,
        halfTimeWeather: conditions,
        fullTimeWeather: conditions
      },
      alerts: [],
      reliability: 0.88
    };
  }

  private combineForecast(forecasts: WeatherForecast[]): WeatherForecast {
    if (forecasts.length === 1) return forecasts[0];

    // Weight by reliability
    const totalReliability = forecasts.reduce((sum, f) => sum + f.reliability, 0);
    const weights = forecasts.map(f => f.reliability / totalReliability);

    // Combine conditions
    const combinedConditions: WeatherConditions = {
      temperature: this.weightedAverage(forecasts.map(f => f.conditions.temperature), weights),
      humidity: this.weightedAverage(forecasts.map(f => f.conditions.humidity), weights),
      windSpeed: this.weightedAverage(forecasts.map(f => f.conditions.windSpeed), weights),
      windDirection: this.weightedAverage(forecasts.map(f => f.conditions.windDirection), weights),
      precipitation: this.weightedAverage(forecasts.map(f => f.conditions.precipitation), weights),
      visibility: this.weightedAverage(forecasts.map(f => f.conditions.visibility), weights),
      pressure: this.weightedAverage(forecasts.map(f => f.conditions.pressure), weights),
      uvIndex: this.weightedAverage(forecasts.map(f => f.conditions.uvIndex), weights),
      conditions: forecasts[0].conditions.conditions, // Use most reliable
      cloudCover: this.weightedAverage(forecasts.map(f => f.conditions.cloudCover), weights),
      dewPoint: this.weightedAverage(forecasts.map(f => f.conditions.dewPoint), weights),
      feelsLike: this.weightedAverage(forecasts.map(f => f.conditions.feelsLike), weights)
    };

    return {
      timestamp: Date.now(),
      conditions: combinedConditions,
      forecast: {
        kickoffWeather: combinedConditions,
        halfTimeWeather: combinedConditions,
        fullTimeWeather: combinedConditions
      },
      alerts: [],
      reliability: Math.max(...forecasts.map(f => f.reliability))
    };
  }

  private weightedAverage(values: number[], weights: number[]): number {
    return values.reduce((sum, val, i) => sum + (val * weights[i]), 0);
  }

  private async getHistoricalWeatherPerformance(homeTeam: string, awayTeam: string, conditions: WeatherConditions) {
    // In real implementation, query historical database
    // For now, return simulated data
    return {
      homeTeamRecord: {
        similarConditions: Math.floor(Math.random() * 20) + 5,
        wins: Math.floor(Math.random() * 10) + 3,
        draws: Math.floor(Math.random() * 8) + 2,
        losses: Math.floor(Math.random() * 6) + 1,
        goalsFor: Math.floor(Math.random() * 25) + 15,
        goalsAgainst: Math.floor(Math.random() * 20) + 10
      },
      awayTeamRecord: {
        similarConditions: Math.floor(Math.random() * 20) + 5,
        wins: Math.floor(Math.random() * 8) + 2,
        draws: Math.floor(Math.random() * 8) + 2,
        losses: Math.floor(Math.random() * 10) + 3,
        goalsFor: Math.floor(Math.random() * 20) + 10,
        goalsAgainst: Math.floor(Math.random() * 25) + 15
      }
    };
  }

  // Public methods
  clearCache(): void {
    this.cache.clear();
  }

  getCacheSize(): number {
    return this.cache.size;
  }

  getApiStatus(): { [key: string]: boolean } {
    return {
      openWeatherMap: !!this.apiKeys.openWeatherMap,
      weatherAPI: !!this.apiKeys.weatherAPI,
      accuWeather: !!this.apiKeys.accuWeather,
      visualCrossing: !!this.apiKeys.visualCrossing
    };
  }

  addVenue(venue: VenueWeatherProfile): void {
    this.venueDatabase.set(venue.venueId, venue);
  }

  getVenues(): VenueWeatherProfile[] {
    return Array.from(this.venueDatabase.values());
  }
}

export const weatherImpactAnalysisService = new WeatherImpactAnalysisService();
export default weatherImpactAnalysisService;