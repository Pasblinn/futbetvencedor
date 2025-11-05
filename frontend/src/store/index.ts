import React from 'react';
import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import {
  Match,
  Team,
  MatchPrediction,
  DailyCombinations,
  LoadingState,
  Theme,
  CombinationFilters,
  MatchFilters
} from '../types';

// App State Interface
interface AppState {
  // Theme
  theme: Theme;
  setTheme: (theme: Theme) => void;

  // Navigation
  currentPage: string;
  setCurrentPage: (page: string) => void;

  // Loading States
  loading: {
    matches: LoadingState;
    predictions: LoadingState;
    combinations: LoadingState;
    analytics: LoadingState;
  };
  setLoading: (key: keyof AppState['loading'], state: LoadingState) => void;

  // Data States
  matches: {
    today: Match[];
    selected: Match | null;
    filters: MatchFilters;
  };
  setMatches: (matches: Match[]) => void;
  setSelectedMatch: (match: Match | null) => void;
  setMatchFilters: (filters: MatchFilters) => void;

  teams: {
    list: Team[];
    selected: Team | null;
    leagues: string[];
    countries: string[];
  };
  setTeams: (teams: Team[]) => void;
  setSelectedTeam: (team: Team | null) => void;
  setLeagues: (leagues: string[]) => void;
  setCountries: (countries: string[]) => void;

  predictions: {
    current: MatchPrediction | null;
    performance: any | null;
  };
  setCurrentPrediction: (prediction: MatchPrediction | null) => void;
  setPredictionPerformance: (performance: any) => void;

  combinations: {
    daily: DailyCombinations | null;
    filters: CombinationFilters;
  };
  setDailyCombinations: (combinations: DailyCombinations | null) => void;
  setCombinationFilters: (filters: CombinationFilters) => void;

  // Favorites and Settings
  favorites: {
    teams: number[];
    matches: number[];
  };
  addFavoriteTeam: (teamId: number) => void;
  removeFavoriteTeam: (teamId: number) => void;
  addFavoriteMatch: (matchId: number) => void;
  removeFavoriteMatch: (matchId: number) => void;

  // Notifications
  notifications: Array<{
    id: string;
    type: 'info' | 'success' | 'warning' | 'error';
    title: string;
    message: string;
    timestamp: number;
    read: boolean;
  }>;
  addNotification: (notification: Omit<AppState['notifications'][0], 'id' | 'timestamp' | 'read'>) => void;
  markNotificationRead: (id: string) => void;
  clearNotifications: () => void;

  // User Preferences
  preferences: {
    defaultFilters: CombinationFilters;
    dashboardLayout: 'grid' | 'list';
    autoRefresh: boolean;
    refreshInterval: number; // in seconds
  };
  updatePreferences: (preferences: Partial<AppState['preferences']>) => void;

  // Cache Management
  cache: {
    lastUpdated: Record<string, number>;
    expiryTime: number; // in milliseconds
  };
  updateCacheTimestamp: (key: string) => void;
  isCacheValid: (key: string) => boolean;
}

// Create the store
export const useAppStore = create<AppState>()(
  subscribeWithSelector((set, get) => ({
    // Theme
    theme: (localStorage.getItem('theme') as Theme) || 'dark',
    setTheme: (theme) => {
      localStorage.setItem('theme', theme);
      set({ theme });
    },

    // Navigation
    currentPage: 'dashboard',
    setCurrentPage: (page) => set({ currentPage: page }),

    // Loading States
    loading: {
      matches: { isLoading: false },
      predictions: { isLoading: false },
      combinations: { isLoading: false },
      analytics: { isLoading: false },
    },
    setLoading: (key, state) =>
      set((prev) => ({
        loading: {
          ...prev.loading,
          [key]: state,
        },
      })),

    // Data States
    matches: {
      today: [],
      selected: null,
      filters: {
        skip: 0,
        limit: 50,
      },
    },
    setMatches: (matches) =>
      set((prev) => ({
        matches: { ...prev.matches, today: matches },
      })),
    setSelectedMatch: (match) =>
      set((prev) => ({
        matches: { ...prev.matches, selected: match },
      })),
    setMatchFilters: (filters) =>
      set((prev) => ({
        matches: { ...prev.matches, filters },
      })),

    teams: {
      list: [],
      selected: null,
      leagues: [],
      countries: [],
    },
    setTeams: (teams) =>
      set((prev) => ({
        teams: { ...prev.teams, list: teams },
      })),
    setSelectedTeam: (team) =>
      set((prev) => ({
        teams: { ...prev.teams, selected: team },
      })),
    setLeagues: (leagues) =>
      set((prev) => ({
        teams: { ...prev.teams, leagues },
      })),
    setCountries: (countries) =>
      set((prev) => ({
        teams: { ...prev.teams, countries },
      })),

    predictions: {
      current: null,
      performance: null,
    },
    setCurrentPrediction: (prediction) =>
      set((prev) => ({
        predictions: { ...prev.predictions, current: prediction },
      })),
    setPredictionPerformance: (performance) =>
      set((prev) => ({
        predictions: { ...prev.predictions, performance },
      })),

    combinations: {
      daily: null,
      filters: {
        min_odds: 1.5,
        max_odds: 2.0,
        min_confidence: 0.65,
      },
    },
    setDailyCombinations: (combinations) =>
      set((prev) => ({
        combinations: { ...prev.combinations, daily: combinations },
      })),
    setCombinationFilters: (filters) =>
      set((prev) => ({
        combinations: { ...prev.combinations, filters },
      })),

    // Favorites
    favorites: {
      teams: JSON.parse(localStorage.getItem('favoriteTeams') || '[]'),
      matches: JSON.parse(localStorage.getItem('favoriteMatches') || '[]'),
    },
    addFavoriteTeam: (teamId) => {
      const favorites = get().favorites.teams;
      if (!favorites.includes(teamId)) {
        const newFavorites = [...favorites, teamId];
        localStorage.setItem('favoriteTeams', JSON.stringify(newFavorites));
        set((prev) => ({
          favorites: { ...prev.favorites, teams: newFavorites },
        }));
      }
    },
    removeFavoriteTeam: (teamId) => {
      const favorites = get().favorites.teams;
      const newFavorites = favorites.filter((id) => id !== teamId);
      localStorage.setItem('favoriteTeams', JSON.stringify(newFavorites));
      set((prev) => ({
        favorites: { ...prev.favorites, teams: newFavorites },
      }));
    },
    addFavoriteMatch: (matchId) => {
      const favorites = get().favorites.matches;
      if (!favorites.includes(matchId)) {
        const newFavorites = [...favorites, matchId];
        localStorage.setItem('favoriteMatches', JSON.stringify(newFavorites));
        set((prev) => ({
          favorites: { ...prev.favorites, matches: newFavorites },
        }));
      }
    },
    removeFavoriteMatch: (matchId) => {
      const favorites = get().favorites.matches;
      const newFavorites = favorites.filter((id) => id !== matchId);
      localStorage.setItem('favoriteMatches', JSON.stringify(newFavorites));
      set((prev) => ({
        favorites: { ...prev.favorites, matches: newFavorites },
      }));
    },

    // Notifications
    notifications: [],
    addNotification: (notification) => {
      const id = Date.now().toString();
      const newNotification = {
        ...notification,
        id,
        timestamp: Date.now(),
        read: false,
      };
      set((prev) => ({
        notifications: [newNotification, ...prev.notifications].slice(0, 50), // Keep only last 50
      }));
    },
    markNotificationRead: (id) =>
      set((prev) => ({
        notifications: prev.notifications.map((n) =>
          n.id === id ? { ...n, read: true } : n
        ),
      })),
    clearNotifications: () => set({ notifications: [] }),

    // User Preferences
    preferences: {
      defaultFilters: {
        min_odds: 1.5,
        max_odds: 2.0,
        min_confidence: 0.65,
      },
      dashboardLayout: 'grid',
      autoRefresh: true,
      refreshInterval: 300, // 5 minutes
      ...JSON.parse(localStorage.getItem('userPreferences') || '{}'),
    },
    updatePreferences: (preferences) => {
      const newPreferences = { ...get().preferences, ...preferences };
      localStorage.setItem('userPreferences', JSON.stringify(newPreferences));
      set({ preferences: newPreferences });
    },

    // Cache Management
    cache: {
      lastUpdated: {},
      expiryTime: 5 * 60 * 1000, // 5 minutes
    },
    updateCacheTimestamp: (key) =>
      set((prev) => ({
        cache: {
          ...prev.cache,
          lastUpdated: {
            ...prev.cache.lastUpdated,
            [key]: Date.now(),
          },
        },
      })),
    isCacheValid: (key) => {
      const state = get();
      const lastUpdated = state.cache.lastUpdated[key];
      if (!lastUpdated) return false;
      return Date.now() - lastUpdated < state.cache.expiryTime;
    },
  }))
);

// Selectors for common state combinations
export const useMatchesData = () => useAppStore((state) => state.matches);
export const useTeamsData = () => useAppStore((state) => state.teams);
export const usePredictionsData = () => useAppStore((state) => state.predictions);
export const useCombinationsData = () => useAppStore((state) => state.combinations);
export const useLoadingStates = () => useAppStore((state) => state.loading);
export const useFavorites = () => useAppStore((state) => state.favorites);
export const useNotifications = () => useAppStore((state) => state.notifications);
export const usePreferences = () => useAppStore((state) => state.preferences);
export const useTheme = () => useAppStore((state) => state.theme);

// Theme effect hook (to be used in components with React import)
export const useThemeEffect = () => {
  const theme = useTheme();

  // Ensure theme is applied to document root on initial load
  React.useEffect(() => {
    const root = window.document.documentElement;
    root.classList.remove('light', 'dark');
    root.classList.add(theme);

    // Store theme in localStorage
    localStorage.setItem('theme', theme);
  }, [theme]);

  return theme;
};

// Export default
export default useAppStore;