import React, { useState, useRef, useEffect } from 'react';
import { Bell, Search, Menu, Sun, Moon, Settings, LogOut, User, ChevronDown } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAppStore, useNotifications, useTheme } from '../../store';
import { useAuth } from '../../contexts/AuthContext';
import LanguageSelector from './LanguageSelector';

interface HeaderProps {
  onMenuToggle: () => void;
}

const Header: React.FC<HeaderProps> = ({ onMenuToggle }) => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const theme = useTheme();
  const setTheme = useAppStore((state) => state.setTheme);
  const markNotificationRead = useAppStore((state) => state.markNotificationRead);
  const notifications = useNotifications();

  const [showUserDropdown, setShowUserDropdown] = useState(false);
  const [showNotificationsDropdown, setShowNotificationsDropdown] = useState(false);

  const userDropdownRef = useRef<HTMLDivElement>(null);
  const notificationsDropdownRef = useRef<HTMLDivElement>(null);

  const unreadCount = notifications.filter(n => !n.read).length;

  const toggleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light');
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
    setShowUserDropdown(false);
  };

  const markAsRead = (id: string) => {
    markNotificationRead(id);
  };

  const markAllAsRead = () => {
    notifications.forEach(n => {
      if (!n.read) {
        markNotificationRead(n.id);
      }
    });
  };

  // Click outside handler
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (userDropdownRef.current && !userDropdownRef.current.contains(event.target as Node)) {
        setShowUserDropdown(false);
      }
      if (notificationsDropdownRef.current && !notificationsDropdownRef.current.contains(event.target as Node)) {
        setShowNotificationsDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  return (
    <header className="fixed top-0 left-0 right-0 z-40 bg-white dark:bg-bg-secondary border-b border-slate-200 dark:border-border-subtle px-4 py-3 lg:pl-64">
      <div className="flex items-center justify-between">
        {/* Left side */}
        <div className="flex items-center space-x-4">
          {/* Mobile menu button */}
          <button
            onClick={onMenuToggle}
            className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-bg-tertiary lg:hidden"
          >
            <Menu className="w-5 h-5 text-slate-600 dark:text-text-secondary" />
          </button>

          {/* Logo - Only show on mobile, hidden on desktop where sidebar shows it */}
          <div className="flex items-center space-x-3 lg:hidden">
            <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-green-700 rounded-xl flex items-center justify-center shadow-lg">
              <span className="text-white font-black text-sm tracking-tight">FBV</span>
            </div>
            <div>
              <h1 className="text-xl font-black text-slate-900 dark:text-text-primary tracking-tight" style={{ fontFamily: 'Poppins, sans-serif' }}>
                FUT BET VENCEDOR
              </h1>
              <p className="text-xs text-slate-500 dark:text-text-tertiary font-medium">Sistema de Análise e Predictions</p>
            </div>
          </div>
        </div>

        {/* Center - Search */}
        <div className="hidden md:flex flex-1 max-w-md mx-8">
          <div className="relative w-full">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search className="h-4 w-4 text-slate-400 dark:text-text-tertiary" />
            </div>
            <input
              type="text"
              placeholder="Search matches, teams..."
              className="block w-full pl-10 pr-3 py-2 border border-slate-300 dark:border-border-primary rounded-lg leading-5 bg-white dark:bg-bg-tertiary placeholder-slate-500 dark:placeholder-text-tertiary text-slate-900 dark:text-text-primary focus:outline-none focus:placeholder-slate-400 focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
        </div>

        {/* Right side */}
        <div className="flex items-center space-x-2">
          {/* Language Selector */}
          <LanguageSelector />

          {/* Theme toggle */}
          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-bg-tertiary transition-colors"
            title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
          >
            {theme === 'light' ? (
              <Moon className="w-5 h-5 text-slate-600 dark:text-text-secondary" />
            ) : (
              <Sun className="w-5 h-5 text-accent-500 dark:text-accent-400" />
            )}
          </button>

          {/* Notifications */}
          <div className="relative" ref={notificationsDropdownRef}>
            <button
              onClick={() => setShowNotificationsDropdown(!showNotificationsDropdown)}
              className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-bg-tertiary transition-colors"
            >
              <Bell className="w-5 h-5 text-slate-600 dark:text-text-secondary" />
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 w-5 h-5 bg-danger-500 text-white text-xs rounded-full flex items-center justify-center">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </button>

            {/* Notification dropdown */}
            {showNotificationsDropdown && (
              <div className="absolute right-0 mt-2 w-80 bg-white dark:bg-bg-secondary rounded-lg shadow-lg border border-slate-200 dark:border-border-primary py-2 z-50">
                <div className="flex items-center justify-between px-4 py-2 border-b border-slate-200 dark:border-border-subtle">
                  <h3 className="text-sm font-semibold text-slate-900 dark:text-text-primary">Notificações</h3>
                  {unreadCount > 0 && (
                    <button
                      onClick={markAllAsRead}
                      className="text-xs text-primary-600 dark:text-primary-400 hover:underline"
                    >
                      Marcar todas como lida
                    </button>
                  )}
                </div>
                <div className="max-h-96 overflow-y-auto">
                  {notifications.length > 0 ? (
                    notifications.slice(0, 10).map((notification) => (
                      <div
                        key={notification.id}
                        onClick={() => markAsRead(notification.id)}
                        className={`px-4 py-3 hover:bg-slate-50 dark:hover:bg-bg-tertiary cursor-pointer border-b border-slate-100 dark:border-border-subtle ${
                          !notification.read ? 'bg-primary-50/50 dark:bg-primary-900/10' : ''
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          <div className={`w-2 h-2 rounded-full mt-2 ${
                            notification.type === 'success' ? 'bg-green-500' :
                            notification.type === 'error' ? 'bg-red-500' :
                            notification.type === 'warning' ? 'bg-yellow-500' :
                            'bg-blue-500'
                          }`} />
                          <div className="flex-1">
                            <p className="text-sm font-medium text-slate-900 dark:text-text-primary">
                              {notification.title}
                            </p>
                            <p className="text-xs text-slate-600 dark:text-text-secondary mt-1">
                              {notification.message}
                            </p>
                            <p className="text-xs text-slate-400 dark:text-text-tertiary mt-1">
                              {new Date(notification.timestamp).toLocaleString('pt-BR')}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="px-4 py-8 text-center text-slate-500 dark:text-text-tertiary text-sm">
                      Nenhuma notificação
                    </div>
                  )}
                </div>
                {notifications.length > 10 && (
                  <div className="px-4 py-2 border-t border-slate-200 dark:border-border-subtle">
                    <button className="text-xs text-primary-600 dark:text-primary-400 hover:underline w-full text-center">
                      Ver todas as notificações
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Settings */}
          <button
            onClick={() => navigate('/settings')}
            className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-bg-tertiary transition-colors"
            title="Configurações"
          >
            <Settings className="w-5 h-5 text-slate-600 dark:text-text-secondary" />
          </button>

          {/* User menu */}
          <div className="relative" ref={userDropdownRef}>
            <button
              onClick={() => setShowUserDropdown(!showUserDropdown)}
              className="flex items-center space-x-3 pl-3 border-l border-slate-200 dark:border-border-subtle hover:bg-slate-100 dark:hover:bg-bg-tertiary rounded-lg py-2 px-3 transition-colors"
            >
              <div className="hidden sm:block text-right">
                <p className="text-sm font-medium text-slate-900 dark:text-text-primary">
                  {user?.username || 'Usuário'}
                </p>
                <p className="text-xs text-slate-500 dark:text-text-tertiary">
                  {user?.email || 'Premium Account'}
                </p>
              </div>
              <div className="w-8 h-8 bg-primary-100 dark:bg-primary-900 rounded-full flex items-center justify-center">
                <span className="text-primary-600 dark:text-primary-300 font-medium text-sm">
                  {user?.username ? user.username.substring(0, 2).toUpperCase() : 'AU'}
                </span>
              </div>
              <ChevronDown className="w-4 h-4 text-slate-600 dark:text-text-secondary" />
            </button>

            {/* User dropdown */}
            {showUserDropdown && (
              <div className="absolute right-0 mt-2 w-56 bg-white dark:bg-bg-secondary rounded-lg shadow-lg border border-slate-200 dark:border-border-primary py-2 z-50">
                <div className="px-4 py-3 border-b border-slate-200 dark:border-border-subtle">
                  <p className="text-sm font-medium text-slate-900 dark:text-text-primary">
                    {user?.username || 'Usuário'}
                  </p>
                  <p className="text-xs text-slate-500 dark:text-text-tertiary mt-1">
                    {user?.email || 'user@example.com'}
                  </p>
                </div>
                <div className="py-1">
                  <button
                    onClick={() => {
                      navigate('/profile');
                      setShowUserDropdown(false);
                    }}
                    className="flex items-center gap-3 w-full px-4 py-2 text-sm text-slate-700 dark:text-text-secondary hover:bg-slate-100 dark:hover:bg-bg-tertiary"
                  >
                    <User className="w-4 h-4" />
                    <span>Meu Perfil</span>
                  </button>
                  <button
                    onClick={() => {
                      navigate('/settings');
                      setShowUserDropdown(false);
                    }}
                    className="flex items-center gap-3 w-full px-4 py-2 text-sm text-slate-700 dark:text-text-secondary hover:bg-slate-100 dark:hover:bg-bg-tertiary"
                  >
                    <Settings className="w-4 h-4" />
                    <span>Configurações</span>
                  </button>
                </div>
                <div className="border-t border-slate-200 dark:border-border-subtle py-1">
                  <button
                    onClick={handleLogout}
                    className="flex items-center gap-3 w-full px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
                  >
                    <LogOut className="w-4 h-4" />
                    <span>Sair</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Mobile search */}
      <div className="md:hidden mt-3">
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-4 w-4 text-slate-400" />
          </div>
          <input
            type="text"
            placeholder="Search matches, teams..."
            className="block w-full pl-10 pr-3 py-2 border border-slate-300 rounded-lg leading-5 bg-white placeholder-slate-500 focus:outline-none focus:placeholder-slate-400 focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
          />
        </div>
      </div>
    </header>
  );
};

export default Header;