import { useQuery } from '@tanstack/react-query';

interface LiveMatch {
  id: number;
  home_team: string;
  away_team: string;
  status: string;
  minute?: number;
  score?: {
    home: number;
    away: number;
  };
  live_prediction?: {
    home_win: number;
    draw: number;
    away_win: number;
  };
}

interface LiveMatchesResponse {
  matches: LiveMatch[];
  total: number;
}

const fetchLiveMatches = async (): Promise<LiveMatchesResponse> => {
  const response = await fetch('http://localhost:8000/api/v1/matches/live');
  if (!response.ok) {
    throw new Error('Failed to fetch live matches');
  }
  return response.json();
};

export const useLiveMatches = () => {
  return useQuery({
    queryKey: ['live-matches'],
    queryFn: fetchLiveMatches,
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 60 * 1000, // Refetch every minute for live data
    retry: 2,
  });
};