import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Home,
  Calendar,
  Target,
  TrendingUp,
  Zap,
  Settings,
  HelpCircle,
  X,
  Activity,
  Trophy,
} from 'lucide-react';
import { useAppStore } from '../../store';
import { useDashboardOverview } from '../../hooks/useDashboardOverview';
import { useTranslation } from '../../contexts/I18nContext';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

const navigationItems = [
  {
    nameKey: 'nav.dashboard',
    href: '/dashboard',
    icon: Home,
    current: true,
  },
  {
    nameKey: 'nav.bankroll',
    href: '/bankroll',
    icon: TrendingUp,
    current: false,
  },
  {
    nameKey: 'nav.tickets',
    href: '/tickets',
    icon: Calendar,
    current: false,
  },
  {
    nameKey: 'nav.live',
    href: '/live-matches',
    icon: Activity,
    current: false,
    highlight: true,
  },
  {
    nameKey: 'nav.predictions',
    href: '/predictions',
    icon: Target,
    current: false,
  },
  {
    nameKey: 'nav.news',
    href: '/news-injuries',
    icon: Zap,
    current: false,
  },
  {
    nameKey: 'nav.history',
    href: '/history',
    icon: Calendar,
    current: false,
  },
];

const userStatsItems = [
  {
    nameKey: 'nav.greenred',
    href: '/green-red',
    icon: Trophy,
    current: false,
    highlight: true,
  },
];

const secondaryItems = [
  {
    nameKey: 'nav.settings',
    href: '/settings',
    icon: Settings,
  },
  {
    nameKey: 'nav.help',
    href: '/help',
    icon: HelpCircle,
  },
];

const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const currentPage = useAppStore((state) => state.currentPage);
  const setCurrentPage = useAppStore((state) => state.setCurrentPage);
  const { data: overview, isLoading, error } = useDashboardOverview();

  const handleNavigation = (href: string) => {
    navigate(href);
    const page = href.replace('/', '');
    setCurrentPage(page);
    onClose(); // Close mobile sidebar
  };

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black bg-opacity-50 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed inset-y-0 left-0 z-50 w-64 bg-white dark:bg-bg-card border-r border-slate-200 dark:border-border-subtle transform transition-transform duration-300 ease-in-out lg:translate-x-0
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="flex flex-col h-full">
          {/* Header - Mobile */}
          <div className="flex items-center justify-between p-4 border-b border-slate-200 dark:border-border-subtle lg:hidden">
            <div className="flex items-center space-x-2">
              <div className="w-9 h-9 bg-gradient-to-br from-green-500 to-green-700 rounded-xl flex items-center justify-center shadow-lg">
                <span className="text-white font-black text-xs tracking-tight">FBV</span>
              </div>
              <span className="text-base font-black text-slate-900 dark:text-text-primary tracking-tight" style={{ fontFamily: 'Poppins, sans-serif' }}>
                FUT BET VENCEDOR
              </span>
            </div>
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-bg-tertiary"
            >
              <X className="w-5 h-5 text-slate-600 dark:text-text-secondary" />
            </button>
          </div>

          {/* Header - Desktop */}
          <div className="hidden lg:flex items-center p-4 border-b border-slate-200 dark:border-border-subtle">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-green-700 rounded-xl flex items-center justify-center shadow-lg">
                <span className="text-white font-black text-sm tracking-tight">FBV</span>
              </div>
              <div>
                <h1 className="text-base font-black text-slate-900 dark:text-text-primary tracking-tight leading-tight" style={{ fontFamily: 'Poppins, sans-serif' }}>
                  FUT BET<br />VENCEDOR
                </h1>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-1">
            <div className="space-y-1">
              {navigationItems.map((item) => {
                const isActive = currentPage === item.href.replace('/', '');
                return (
                  <button
                    key={item.nameKey}
                    onClick={() => handleNavigation(item.href)}
                    className={`
                      w-full flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors relative
                      ${isActive
                        ? 'bg-primary-50 text-primary-700 border-r-2 border-primary-600'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                      }
                      ${(item as any).highlight ? 'bg-green-50 hover:bg-green-100 border border-green-200' : ''}
                    `}
                  >
                    <item.icon className={`
                      mr-3 w-5 h-5
                      ${isActive ? 'text-primary-600' : (item as any).highlight ? 'text-green-600' : 'text-slate-400'}
                    `} />
                    <span className={(item as any).highlight ? 'text-green-700 font-semibold' : ''}>
                      {t(item.nameKey)}
                    </span>
                    {(item as any).highlight && (
                      <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full flex items-center justify-center">
                        <span className="text-white text-xs font-bold">🇧🇷</span>
                      </div>
                    )}
                  </button>
                );
              })}
            </div>

            {/* Divider */}
            <div className="my-6 border-t border-slate-200 dark:border-border-subtle" />

            {/* User Stats Section */}
            <div className="space-y-1">
              <div className="px-3 py-2 text-xs font-semibold text-slate-500 dark:text-text-tertiary uppercase tracking-wider">
                📊 {t('sidebar.stats_title')}
              </div>
              {userStatsItems.map((item) => {
                const isActive = currentPage === item.href.replace('/', '');
                return (
                  <button
                    key={item.nameKey}
                    onClick={() => handleNavigation(item.href)}
                    className={`
                      w-full flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors relative
                      ${isActive
                        ? 'bg-blue-50 text-blue-700 border-r-2 border-blue-600'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                      }
                      ${(item as any).highlight ? 'bg-blue-50 hover:bg-blue-100 border border-blue-200' : ''}
                    `}
                  >
                    <item.icon className={`
                      mr-3 w-5 h-5
                      ${isActive ? 'text-blue-600' : (item as any).highlight ? 'text-blue-600' : 'text-slate-400'}
                    `} />
                    <span className={(item as any).highlight ? 'text-blue-700 font-semibold' : ''}>
                      {t(item.nameKey)}
                    </span>
                    {(item as any).highlight && (
                      <div className="absolute -top-1 -right-1 w-3 h-3 bg-blue-500 rounded-full flex items-center justify-center">
                        <span className="text-white text-xs font-bold">🌍</span>
                      </div>
                    )}
                  </button>
                );
              })}
            </div>

            {/* Divider */}
            <div className="my-6 border-t border-slate-200 dark:border-border-subtle" />

            {/* Quick Stats */}
            <div className="bg-slate-50 dark:bg-bg-tertiary rounded-lg p-4">
              <h3 className="text-sm font-medium text-slate-900 mb-3">{t('sidebar.today_overview')}</h3>
              {isLoading ? (
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-slate-600">{t('sidebar.loading')}</span>
                    <div className="w-6 h-4 bg-slate-200 rounded animate-pulse"></div>
                  </div>
                </div>
              ) : error ? (
                <div className="text-xs text-red-600">{t('sidebar.failed_load')}</div>
              ) : (
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-slate-600">{t('sidebar.matches')}</span>
                    <span className="text-sm font-medium text-slate-900">{overview?.today_matches || 0}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-slate-600">{t('sidebar.predictions')}</span>
                    <span className="text-sm font-medium text-primary-600">{overview?.predictions_made || 0}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-slate-600">{t('sidebar.alerts')}</span>
                    <span className="text-sm font-medium text-success-600">{overview?.active_alerts || 0}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-slate-600">{t('sidebar.accuracy')}</span>
                    <span className="text-sm font-medium text-warning-600">{overview?.accuracy_rate || 0}%</span>
                  </div>
                </div>
              )}
            </div>

            {/* Divider */}
            <div className="my-6 border-t border-slate-200" />

            {/* Secondary navigation */}
            <div className="space-y-1">
              {secondaryItems.map((item) => (
                <button
                  key={item.nameKey}
                  onClick={() => handleNavigation(item.href)}
                  className="w-full flex items-center px-3 py-2 text-sm font-medium text-slate-600 dark:text-text-secondary rounded-lg hover:text-slate-900 dark:hover:text-text-primary hover:bg-slate-50 dark:hover:bg-bg-tertiary transition-colors"
                >
                  <item.icon className="mr-3 w-5 h-5 text-slate-400" />
                  {t(item.nameKey)}
                </button>
              ))}
            </div>
          </nav>

          {/* Footer */}
          <div className="p-4 border-t border-slate-200">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-success-100 rounded-full flex items-center justify-center">
                <Trophy className="w-4 h-4 text-success-600" />
              </div>
              <div className="flex-1 min-w-0">
                {overview ? (
                  <>
                    <p className="text-sm font-medium text-slate-900 truncate">
                      {overview.accuracy_rate}% {t('sidebar.accuracy')}
                    </p>
                    <p className="text-xs text-slate-500 truncate">
                      {t('sidebar.system_performance')}
                    </p>
                  </>
                ) : (
                  <>
                    <p className="text-sm font-medium text-slate-900 truncate">
                      {t('sidebar.system_ready')}
                    </p>
                    <p className="text-xs text-slate-500 truncate">
                      {t('sidebar.loading_data')}
                    </p>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Sidebar;