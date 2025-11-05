import { useState, useEffect, useCallback, useRef } from 'react';
import { realTimeDataService, SyncMatch, SyncStatus, HealthStatus } from '../services/realTimeDataService';

interface UseSynchronizedDataReturn {
  // Match data
  matches: SyncMatch[];
  todayMatches: SyncMatch[];
  isLoadingMatches: boolean;
  matchesError: string | null;

  // Sync status
  syncStatus: SyncStatus | null;
  healthStatus: HealthStatus | null;
  isHealthy: boolean;

  // Actions
  refreshMatches: () => Promise<void>;
  triggerSync: (type?: 'full' | 'quick' | 'matches' | 'odds' | 'predictions') => Promise<void>;
  startLiveUpdates: () => void;
  stopLiveUpdates: () => void;

  // Scheduler control
  startScheduler: () => Promise<void>;
  stopScheduler: () => Promise<void>;
  schedulerStatus: 'running' | 'stopped' | 'unknown';

  // States
  isLiveUpdatesActive: boolean;
  lastUpdateTime: Date | null;
  syncInProgress: boolean;
}

export const useSynchronizedData = (): UseSynchronizedDataReturn => {
  // Match data state
  const [matches, setMatches] = useState<SyncMatch[]>([]);
  const [todayMatches, setTodayMatches] = useState<SyncMatch[]>([]);
  const [isLoadingMatches, setIsLoadingMatches] = useState(false);
  const [matchesError, setMatchesError] = useState<string | null>(null);

  // System status state
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null);
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null);
  const [schedulerStatus, setSchedulerStatus] = useState<'running' | 'stopped' | 'unknown'>('unknown');

  // Control state
  const [isLiveUpdatesActive, setIsLiveUpdatesActive] = useState(false);
  const [lastUpdateTime, setLastUpdateTime] = useState<Date | null>(null);
  const [syncInProgress, setSyncInProgress] = useState(false);

  // Refs for cleanup
  const mountedRef = useRef(true);
  const updateIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // ===== Match Data Functions =====

  const loadTodayMatches = useCallback(async () => {
    if (!mountedRef.current) return;

    setIsLoadingMatches(true);
    setMatchesError(null);

    try {
      const result = await realTimeDataService.getTodayMatches();

      if (mountedRef.current) {
        setTodayMatches(result.matches);
        setLastUpdateTime(new Date());

        console.log(`✅ Loaded ${result.count} today's matches from ${result.source}`);
      }
    } catch (error) {
      if (mountedRef.current) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to load matches';
        setMatchesError(errorMessage);
        console.error('❌ Error loading today\'s matches:', error);
      }
    } finally {
      if (mountedRef.current) {
        setIsLoadingMatches(false);
      }
    }
  }, []);

  const loadAllMatches = useCallback(async (filters: {
    date_from?: string;
    date_to?: string;
    league?: string;
    status?: string;
    limit?: number;
  } = {}) => {
    try {
      const result = await realTimeDataService.getMatches(filters);

      if (mountedRef.current) {
        setMatches(result.matches);
        console.log(`✅ Loaded ${result.count} matches`);
      }
    } catch (error) {
      console.error('❌ Error loading matches:', error);
    }
  }, []);

  const refreshMatches = useCallback(async () => {
    await Promise.all([
      loadTodayMatches(),
      loadAllMatches({ limit: 100 })
    ]);
  }, [loadTodayMatches, loadAllMatches]);

  // ===== Sync Functions =====

  const triggerSync = useCallback(async (type: 'full' | 'quick' | 'matches' | 'odds' | 'predictions' = 'quick') => {
    if (syncInProgress) {
      console.log('⚠️ Sync already in progress, skipping...');
      return;
    }

    setSyncInProgress(true);

    try {
      console.log(`🔄 Triggering ${type} sync...`);
      const result = await realTimeDataService.triggerSync(type);

      console.log(`✅ ${type} sync completed:`, result);

      // Refresh matches after sync
      if (type === 'quick' || type === 'matches' || type === 'full') {
        await refreshMatches();
      }

      // Update sync status
      await loadSyncStatus();

    } catch (error) {
      console.error(`❌ ${type} sync failed:`, error);
    } finally {
      setSyncInProgress(false);
    }
  }, [syncInProgress, refreshMatches]);

  // ===== Status Functions =====

  const loadSyncStatus = useCallback(async () => {
    try {
      const status = await realTimeDataService.getSyncStatus();

      if (mountedRef.current) {
        setSyncStatus(status);
        setSchedulerStatus(status.scheduler.status);
      }
    } catch (error) {
      console.error('❌ Error loading sync status:', error);
    }
  }, []);

  const loadHealthStatus = useCallback(async () => {
    try {
      const health = await realTimeDataService.getHealthStatus();

      if (mountedRef.current) {
        setHealthStatus(health);
      }
    } catch (error) {
      console.error('❌ Error loading health status:', error);
    }
  }, []);

  // ===== Scheduler Functions =====

  const startScheduler = useCallback(async () => {
    try {
      await realTimeDataService.startScheduler();
      setSchedulerStatus('running');
      console.log('✅ Scheduler started');
    } catch (error) {
      console.error('❌ Failed to start scheduler:', error);
      throw error;
    }
  }, []);

  const stopScheduler = useCallback(async () => {
    try {
      await realTimeDataService.stopScheduler();
      setSchedulerStatus('stopped');
      console.log('⏹️ Scheduler stopped');
    } catch (error) {
      console.error('❌ Failed to stop scheduler:', error);
      throw error;
    }
  }, []);

  // ===== Live Updates Functions =====

  const startLiveUpdates = useCallback(() => {
    if (isLiveUpdatesActive) {
      console.log('⚠️ Live updates already active');
      return;
    }

    console.log('🔴 Starting live updates...');
    setIsLiveUpdatesActive(true);

    // Start live updates with callback
    realTimeDataService.startLiveUpdates(
      (data) => {
        if (mountedRef.current) {
          console.log('📡 Received live update:', data);

          if (data.type === 'matches_update') {
            setTodayMatches(data.data.matches);
            setLastUpdateTime(new Date());
          }
        }
      },
      (error) => {
        console.error('❌ Live update error:', error);
        if (mountedRef.current) {
          setMatchesError('Live updates failed');
        }
      }
    );

    // Also start periodic status updates
    updateIntervalRef.current = setInterval(async () => {
      if (mountedRef.current) {
        await Promise.all([
          loadSyncStatus(),
          loadHealthStatus()
        ]);
      }
    }, 60000); // Update status every minute

  }, [isLiveUpdatesActive, loadSyncStatus, loadHealthStatus]);

  const stopLiveUpdates = useCallback(() => {
    console.log('⏹️ Stopping live updates...');

    setIsLiveUpdatesActive(false);
    realTimeDataService.stopLiveUpdates();

    if (updateIntervalRef.current) {
      clearInterval(updateIntervalRef.current);
      updateIntervalRef.current = null;
    }
  }, []);

  // ===== Effects =====

  // Initial data load
  useEffect(() => {
    const initializeData = async () => {
      await Promise.all([
        refreshMatches(),
        loadSyncStatus(),
        loadHealthStatus()
      ]);
    };

    initializeData();
  }, [refreshMatches, loadSyncStatus, loadHealthStatus]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      mountedRef.current = false;
      stopLiveUpdates();
    };
  }, [stopLiveUpdates]);

  // Auto-start live updates if scheduler is running
  useEffect(() => {
    if (schedulerStatus === 'running' && !isLiveUpdatesActive) {
      // Auto-start live updates when scheduler is running
      const timer = setTimeout(() => {
        if (mountedRef.current) {
          startLiveUpdates();
        }
      }, 2000); // Small delay to let initial data load

      return () => clearTimeout(timer);
    }
  }, [schedulerStatus, isLiveUpdatesActive, startLiveUpdates]);

  // ===== Computed Values =====

  const isHealthy = healthStatus?.overall_status === 'healthy';

  return {
    // Data
    matches,
    todayMatches,
    isLoadingMatches,
    matchesError,

    // Status
    syncStatus,
    healthStatus,
    isHealthy,

    // Actions
    refreshMatches,
    triggerSync,
    startLiveUpdates,
    stopLiveUpdates,

    // Scheduler
    startScheduler,
    stopScheduler,
    schedulerStatus,

    // State
    isLiveUpdatesActive,
    lastUpdateTime,
    syncInProgress
  };
};