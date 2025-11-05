import { useQuery } from '@tanstack/react-query';

interface DashboardOverview {
  today_matches: number;
  predictions_made: number;
  accuracy_rate: number;
  active_alerts: number;
  last_update: string;
}

const fetchDashboardOverview = async (): Promise<DashboardOverview> => {
  const response = await fetch('http://localhost:8000/api/v1/dashboard/overview');
  if (!response.ok) {
    throw new Error('Failed to fetch dashboard overview');
  }
  return response.json();
};

export const useDashboardOverview = () => {
  return useQuery({
    queryKey: ['dashboard-overview'],
    queryFn: fetchDashboardOverview,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 2 * 60 * 1000, // Refetch every 2 minutes
    retry: 2,
  });
};