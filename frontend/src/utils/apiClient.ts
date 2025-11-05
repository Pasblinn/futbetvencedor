/**
 * API Client com logging integrado para debug e monitoramento
 */
import { logger } from './logger';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

interface ApiClientOptions extends RequestInit {
  params?: Record<string, any>;
}

/**
 * Cliente HTTP com logging automático
 */
export const apiClient = {
  /**
   * GET request
   */
  async get<T>(endpoint: string, options?: ApiClientOptions): Promise<T> {
    const url = buildUrl(endpoint, options?.params);

    logger.api('GET', endpoint, options?.params);
    logger.time(`GET ${endpoint}`);

    try {
      const response = await fetch(url, {
        ...options,
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
      });

      logger.timeEnd(`GET ${endpoint}`);

      if (!response.ok) {
        logger.error('apiClient', `GET ${endpoint} failed:`, response.status, response.statusText);
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      logger.success('apiClient', `GET ${endpoint} success`, data);

      return data;
    } catch (error) {
      logger.timeEnd(`GET ${endpoint}`);
      logger.error('apiClient', `GET ${endpoint} error:`, error);
      throw error;
    }
  },

  /**
   * POST request
   */
  async post<T>(endpoint: string, body?: any, options?: ApiClientOptions): Promise<T> {
    const url = buildUrl(endpoint, options?.params);

    logger.api('POST', endpoint, body);
    logger.time(`POST ${endpoint}`);

    try {
      const response = await fetch(url, {
        ...options,
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
        body: body ? JSON.stringify(body) : undefined,
      });

      logger.timeEnd(`POST ${endpoint}`);

      if (!response.ok) {
        logger.error('apiClient', `POST ${endpoint} failed:`, response.status, response.statusText);
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      logger.success('apiClient', `POST ${endpoint} success`, data);

      return data;
    } catch (error) {
      logger.timeEnd(`POST ${endpoint}`);
      logger.error('apiClient', `POST ${endpoint} error:`, error);
      throw error;
    }
  },

  /**
   * PUT request
   */
  async put<T>(endpoint: string, body?: any, options?: ApiClientOptions): Promise<T> {
    const url = buildUrl(endpoint, options?.params);

    logger.api('PUT', endpoint, body);
    logger.time(`PUT ${endpoint}`);

    try {
      const response = await fetch(url, {
        ...options,
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
        body: body ? JSON.stringify(body) : undefined,
      });

      logger.timeEnd(`PUT ${endpoint}`);

      if (!response.ok) {
        logger.error('apiClient', `PUT ${endpoint} failed:`, response.status, response.statusText);
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      logger.success('apiClient', `PUT ${endpoint} success`, data);

      return data;
    } catch (error) {
      logger.timeEnd(`PUT ${endpoint}`);
      logger.error('apiClient', `PUT ${endpoint} error:`, error);
      throw error;
    }
  },

  /**
   * DELETE request
   */
  async delete<T>(endpoint: string, options?: ApiClientOptions): Promise<T> {
    const url = buildUrl(endpoint, options?.params);

    logger.api('DELETE', endpoint);
    logger.time(`DELETE ${endpoint}`);

    try {
      const response = await fetch(url, {
        ...options,
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
      });

      logger.timeEnd(`DELETE ${endpoint}`);

      if (!response.ok) {
        logger.error('apiClient', `DELETE ${endpoint} failed:`, response.status, response.statusText);
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      logger.success('apiClient', `DELETE ${endpoint} success`, data);

      return data;
    } catch (error) {
      logger.timeEnd(`DELETE ${endpoint}`);
      logger.error('apiClient', `DELETE ${endpoint} error:`, error);
      throw error;
    }
  },
};

/**
 * Constrói URL com query parameters
 */
function buildUrl(endpoint: string, params?: Record<string, any>): string {
  const url = new URL(`${API_BASE_URL}${endpoint}`);

  if (params) {
    Object.keys(params).forEach(key => {
      const value = params[key];
      if (value !== undefined && value !== null) {
        url.searchParams.append(key, String(value));
      }
    });
  }

  return url.toString();
}

/**
 * Endpoints tipados para autocompletar
 */
export const endpoints = {
  // Predictions
  predictions: {
    upcoming: '/predictions/upcoming',
    featured: '/predictions/featured',
    byId: (id: number) => `/predictions/${id}`,
    allMarkets: (matchId: number) => `/predictions/${matchId}/all-markets`,
  },

  // Matches
  matches: {
    live: '/live-matches/live',
    today: '/live-matches/today',
    upcoming: '/live-matches/upcoming',
    stats: '/live-matches/stats',
  },

  // Modes
  modes: {
    automatic: '/predictions-modes/automatic',
    assisted: (matchId: number) => `/predictions-modes/assisted/${matchId}`,
    expert: '/predictions-modes/expert',
  },
};

/**
 * Exemplo de uso:
 *
 * // Buscar predictions
 * const predictions = await apiClient.get(endpoints.predictions.upcoming);
 *
 * // Buscar todos os mercados de um jogo
 * const markets = await apiClient.get(endpoints.predictions.allMarkets(123), {
 *   params: { last_n_games: 10 }
 * });
 *
 * // Criar prediction
 * const newPrediction = await apiClient.post(endpoints.modes.expert, {
 *   match_id: 123,
 *   predicted_outcome: '1',
 *   confidence_score: 0.85
 * });
 */
