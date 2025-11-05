// 🛡️ Rate Limiter para controlar chamadas às APIs
export class RateLimiter {
  private requestCounts: Map<string, { count: number; resetTime: number }> = new Map();
  private cache: Map<string, { data: any; expiry: number }> = new Map();

  private readonly limits = {
    default: { requests: 10, windowMs: 60000 }, // 10 requests per minute
    ml_analysis: { requests: 3, windowMs: 60000 }, // 3 ML requests per minute
    team_stats: { requests: 20, windowMs: 60000 }, // 20 team stats per minute
    matches: { requests: 15, windowMs: 60000 } // 15 match requests per minute
  };

  // 🔍 Verifica se pode fazer a requisição
  canMakeRequest(key: string, type: keyof typeof this.limits = 'default'): boolean {
    const limit = this.limits[type];
    const now = Date.now();
    const entry = this.requestCounts.get(key);

    if (!entry || now > entry.resetTime) {
      this.requestCounts.set(key, { count: 1, resetTime: now + limit.windowMs });
      return true;
    }

    if (entry.count >= limit.requests) {
      console.warn(`Rate limit exceeded for ${key}. Try again in ${Math.ceil((entry.resetTime - now) / 1000)} seconds`);
      return false;
    }

    entry.count++;
    return true;
  }

  // 📦 Cache com TTL
  setCache(key: string, data: any, ttlMs: number = 300000): void { // 5 min default
    this.cache.set(key, { data, expiry: Date.now() + ttlMs });
  }

  getCache(key: string): any | null {
    const entry = this.cache.get(key);
    if (!entry) return null;

    if (Date.now() > entry.expiry) {
      this.cache.delete(key);
      return null;
    }

    return entry.data;
  }

  // ⏰ Delay entre requests para evitar spam
  async delay(ms: number = 1000): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // 🧹 Limpeza automática
  cleanup(): void {
    const now = Date.now();

    // Limpa rate limits expirados
    this.requestCounts.forEach((entry, key) => {
      if (now > entry.resetTime) {
        this.requestCounts.delete(key);
      }
    });

    // Limpa cache expirado
    this.cache.forEach((entry, key) => {
      if (now > entry.expiry) {
        this.cache.delete(key);
      }
    });
  }

  // 📊 Status do rate limiting
  getStatus(key: string, type: keyof typeof this.limits = 'default'): {
    remaining: number;
    resetIn: number;
    canRequest: boolean;
  } {
    const limit = this.limits[type];
    const entry = this.requestCounts.get(key);

    if (!entry || Date.now() > entry.resetTime) {
      return {
        remaining: limit.requests,
        resetIn: 0,
        canRequest: true
      };
    }

    return {
      remaining: Math.max(0, limit.requests - entry.count),
      resetIn: Math.max(0, entry.resetTime - Date.now()),
      canRequest: entry.count < limit.requests
    };
  }
}

export const rateLimiter = new RateLimiter();

// Limpeza automática a cada 5 minutos
setInterval(() => rateLimiter.cleanup(), 300000);