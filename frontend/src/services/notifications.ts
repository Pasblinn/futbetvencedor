import { EventEmitter } from 'events';

export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info' | 'odds_change' | 'match_update' | 'prediction_ready';
  title: string;
  message: string;
  timestamp: number;
  read: boolean;
  persistent?: boolean;
  actions?: NotificationAction[];
  metadata?: any;
  expiresAt?: number;
}

export interface NotificationAction {
  label: string;
  action: () => void;
  style?: 'primary' | 'secondary' | 'danger';
}

export interface NotificationSettings {
  enabled: boolean;
  types: {
    odds_changes: boolean;
    match_updates: boolean;
    predictions: boolean;
    system_alerts: boolean;
    news_alerts: boolean;
  };
  channels: {
    browser: boolean;
    sound: boolean;
    desktop: boolean;
  };
  filters: {
    minOddsChange: number;
    favoriteTeams: string[];
    importantLeagues: string[];
  };
}

class NotificationService extends EventEmitter {
  private notifications: Notification[] = [];
  private settings: NotificationSettings;
  private maxNotifications = 100;
  private soundEnabled = true;
  private permission: NotificationPermission = 'default';

  constructor() {
    super();
    this.settings = this.loadSettings();
    this.requestPermission();
  }

  // Load settings from localStorage
  private loadSettings(): NotificationSettings {
    const defaultSettings: NotificationSettings = {
      enabled: true,
      types: {
        odds_changes: true,
        match_updates: true,
        predictions: true,
        system_alerts: true,
        news_alerts: true
      },
      channels: {
        browser: true,
        sound: true,
        desktop: true
      },
      filters: {
        minOddsChange: 0.1,
        favoriteTeams: [],
        importantLeagues: ['Premier League', 'La Liga', 'Bundesliga', 'Serie A', 'Ligue 1']
      }
    };

    try {
      const saved = localStorage.getItem('notification_settings');
      return saved ? { ...defaultSettings, ...JSON.parse(saved) } : defaultSettings;
    } catch {
      return defaultSettings;
    }
  }

  // Save settings to localStorage
  private saveSettings(): void {
    try {
      localStorage.setItem('notification_settings', JSON.stringify(this.settings));
    } catch (error) {
      console.error('Failed to save notification settings:', error);
    }
  }

  // Request browser notification permission
  async requestPermission(): Promise<NotificationPermission> {
    if (!('Notification' in window)) {
      console.warn('This browser does not support notifications');
      return 'denied';
    }

    if (Notification.permission === 'granted') {
      this.permission = 'granted';
      return 'granted';
    }

    if (Notification.permission !== 'denied') {
      const permission = await Notification.requestPermission();
      this.permission = permission;
      return permission;
    }

    this.permission = 'denied';
    return 'denied';
  }

  // Add notification
  addNotification(notification: Omit<Notification, 'id' | 'timestamp' | 'read'>): string {
    if (!this.settings.enabled) {
      return '';
    }

    // Check if notification type is enabled
    if (!this.isNotificationTypeEnabled(notification.type)) {
      return '';
    }

    // Apply filters
    if (!this.passesFilters(notification)) {
      return '';
    }

    const id = `notification_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;
    const fullNotification: Notification = {
      id,
      timestamp: Date.now(),
      read: false,
      ...notification
    };

    // Add to array (newest first)
    this.notifications.unshift(fullNotification);

    // Limit array size
    if (this.notifications.length > this.maxNotifications) {
      this.notifications = this.notifications.slice(0, this.maxNotifications);
    }

    // Emit event
    this.emit('notification', fullNotification);

    // Show browser notification if enabled
    if (this.settings.channels.browser && this.permission === 'granted') {
      this.showBrowserNotification(fullNotification);
    }

    // Play sound if enabled
    if (this.settings.channels.sound && this.soundEnabled) {
      this.playNotificationSound(notification.type);
    }

    return id;
  }

  // Check if notification type is enabled
  private isNotificationTypeEnabled(type: string): boolean {
    switch (type) {
      case 'odds_change': return this.settings.types.odds_changes;
      case 'match_update': return this.settings.types.match_updates;
      case 'prediction_ready': return this.settings.types.predictions;
      case 'error':
      case 'warning': return this.settings.types.system_alerts;
      case 'info': return this.settings.types.news_alerts;
      default: return true;
    }
  }

  // Apply notification filters
  private passesFilters(notification: Omit<Notification, 'id' | 'timestamp' | 'read'>): boolean {
    const { metadata } = notification;

    // Odds change filter
    if (notification.type === 'odds_change' && metadata?.oddsChange) {
      if (Math.abs(metadata.oddsChange) < this.settings.filters.minOddsChange) {
        return false;
      }
    }

    // Favorite teams filter
    if (metadata?.teams && this.settings.filters.favoriteTeams.length > 0) {
      const hasfavoriteTeam = metadata.teams.some((team: string) =>
        this.settings.filters.favoriteTeams.includes(team)
      );
      if (!hasfavoriteTeam && notification.type !== 'error' && notification.type !== 'warning') {
        return false;
      }
    }

    // Important leagues filter
    if (metadata?.league && !this.settings.filters.importantLeagues.includes(metadata.league)) {
      if (notification.type === 'match_update' || notification.type === 'odds_change') {
        return false;
      }
    }

    return true;
  }

  // Show browser notification
  private showBrowserNotification(notification: Notification): void {
    if (!this.settings.channels.desktop) return;

    try {
      const browserNotification = new Notification(notification.title, {
        body: notification.message,
        icon: '/favicon.ico',
        badge: '/favicon.ico',
        tag: notification.type,
        requireInteraction: notification.persistent || false,
        timestamp: notification.timestamp
      });

      browserNotification.onclick = () => {
        window.focus();
        this.markAsRead(notification.id);
        browserNotification.close();
      };

      // Auto close after 5 seconds unless persistent
      if (!notification.persistent) {
        setTimeout(() => browserNotification.close(), 5000);
      }
    } catch (error) {
      console.error('Failed to show browser notification:', error);
    }
  }

  // Play notification sound
  private playNotificationSound(type: string): void {
    try {
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();

      // Different sounds for different types
      const frequencies: { [key: string]: number } = {
        success: 800,
        error: 400,
        warning: 600,
        info: 500,
        odds_change: 700,
        match_update: 650,
        prediction_ready: 750
      };

      const frequency = frequencies[type] || 500;

      // Create sound
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);

      oscillator.frequency.setValueAtTime(frequency, audioContext.currentTime);
      oscillator.type = 'sine';

      gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);

      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.2);
    } catch (error) {
      console.warn('Could not play notification sound:', error);
    }
  }

  // Mark notification as read
  markAsRead(id: string): boolean {
    const notification = this.notifications.find(n => n.id === id);
    if (notification && !notification.read) {
      notification.read = true;
      this.emit('notificationRead', notification);
      return true;
    }
    return false;
  }

  // Mark all notifications as read
  markAllAsRead(): void {
    let changed = false;
    this.notifications.forEach(notification => {
      if (!notification.read) {
        notification.read = true;
        changed = true;
      }
    });

    if (changed) {
      this.emit('allNotificationsRead');
    }
  }

  // Remove notification
  removeNotification(id: string): boolean {
    const index = this.notifications.findIndex(n => n.id === id);
    if (index !== -1) {
      const notification = this.notifications.splice(index, 1)[0];
      this.emit('notificationRemoved', notification);
      return true;
    }
    return false;
  }

  // Clear all notifications
  clearAll(): void {
    const count = this.notifications.length;
    this.notifications = [];
    this.emit('notificationsCleared', count);
  }

  // Clear expired notifications
  clearExpired(): void {
    const now = Date.now();
    const initialCount = this.notifications.length;

    this.notifications = this.notifications.filter(notification => {
      return !notification.expiresAt || notification.expiresAt > now;
    });

    const removedCount = initialCount - this.notifications.length;
    if (removedCount > 0) {
      this.emit('expiredNotificationsCleared', removedCount);
    }
  }

  // Get notifications
  getNotifications(filter?: {
    unreadOnly?: boolean;
    type?: string;
    limit?: number;
  }): Notification[] {
    let notifications = [...this.notifications];

    if (filter?.unreadOnly) {
      notifications = notifications.filter(n => !n.read);
    }

    if (filter?.type) {
      notifications = notifications.filter(n => n.type === filter.type);
    }

    if (filter?.limit) {
      notifications = notifications.slice(0, filter.limit);
    }

    return notifications;
  }

  // Get unread count
  getUnreadCount(): number {
    return this.notifications.filter(n => !n.read).length;
  }

  // Settings management
  updateSettings(updates: Partial<NotificationSettings>): void {
    this.settings = { ...this.settings, ...updates };
    this.saveSettings();
    this.emit('settingsUpdated', this.settings);
  }

  getSettings(): NotificationSettings {
    return { ...this.settings };
  }

  // Sound control
  setSoundEnabled(enabled: boolean): void {
    this.soundEnabled = enabled;
  }

  isSoundEnabled(): boolean {
    return this.soundEnabled;
  }

  // Utility methods for common notifications
  notifyOddsChange(matchId: string, homeTeam: string, awayTeam: string, oldOdds: number, newOdds: number): void {
    const change = newOdds - oldOdds;
    const changePercent = ((change / oldOdds) * 100).toFixed(1);

    this.addNotification({
      type: 'odds_change',
      title: 'Odds Changed',
      message: `${homeTeam} vs ${awayTeam}: ${change > 0 ? '+' : ''}${changePercent}%`,
      metadata: {
        matchId,
        teams: [homeTeam, awayTeam],
        oldOdds,
        newOdds,
        oddsChange: change
      }
    });
  }

  notifyMatchUpdate(matchId: string, homeTeam: string, awayTeam: string, event: string): void {
    this.addNotification({
      type: 'match_update',
      title: 'Match Update',
      message: `${homeTeam} vs ${awayTeam}: ${event}`,
      metadata: {
        matchId,
        teams: [homeTeam, awayTeam],
        event
      }
    });
  }

  notifyPredictionReady(matchId: string, homeTeam: string, awayTeam: string, confidence: number): void {
    this.addNotification({
      type: 'prediction_ready',
      title: 'Prediction Ready',
      message: `${homeTeam} vs ${awayTeam} - Confidence: ${(confidence * 100).toFixed(1)}%`,
      persistent: true,
      metadata: {
        matchId,
        teams: [homeTeam, awayTeam],
        confidence
      },
      actions: [
        {
          label: 'View Prediction',
          action: () => {
            window.location.hash = `#/matches/${matchId}`;
          },
          style: 'primary'
        }
      ]
    });
  }

  notifySystemAlert(level: 'info' | 'warning' | 'error', message: string, details?: any): void {
    this.addNotification({
      type: level,
      title: level === 'error' ? 'System Error' : level === 'warning' ? 'System Warning' : 'System Info',
      message,
      persistent: level === 'error',
      metadata: details
    });
  }

  // Bulk notification methods
  notifyBulkOddsUpdate(updates: Array<{
    matchId: string;
    homeTeam: string;
    awayTeam: string;
    changes: number;
  }>): void {
    if (updates.length === 0) return;

    if (updates.length === 1) {
      const update = updates[0];
      this.addNotification({
        type: 'odds_change',
        title: 'Odds Update',
        message: `${update.homeTeam} vs ${update.awayTeam}: ${update.changes} odds changed`,
        metadata: { matchId: update.matchId, teams: [update.homeTeam, update.awayTeam] }
      });
    } else {
      this.addNotification({
        type: 'odds_change',
        title: 'Bulk Odds Update',
        message: `${updates.length} matches have odds updates`,
        metadata: { updates }
      });
    }
  }

  // Schedule notification
  scheduleNotification(
    notification: Omit<Notification, 'id' | 'timestamp' | 'read'>,
    delay: number
  ): string {
    const id = `scheduled_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;

    setTimeout(() => {
      this.addNotification(notification);
    }, delay);

    return id;
  }

  // Get notification statistics
  getStatistics(): {
    total: number;
    unread: number;
    byType: { [key: string]: number };
    last24Hours: number;
  } {
    const now = Date.now();
    const last24Hours = now - (24 * 60 * 60 * 1000);

    const byType: { [key: string]: number } = {};
    let last24HoursCount = 0;

    this.notifications.forEach(notification => {
      byType[notification.type] = (byType[notification.type] || 0) + 1;

      if (notification.timestamp >= last24Hours) {
        last24HoursCount++;
      }
    });

    return {
      total: this.notifications.length,
      unread: this.getUnreadCount(),
      byType,
      last24Hours: last24HoursCount
    };
  }
}

export const notificationService = new NotificationService();
export default notificationService;