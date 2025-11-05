import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Bell,
  Palette,
  Shield,
  Download,
  Upload,
  User,
  Mail,
  Phone,
  Moon,
  Sun,
  Monitor,
  Save,
  RotateCcw,
  AlertTriangle,
  Check,
  Eye,
  EyeOff,
  Lock,
  Key,
  Database,
  Trash2
} from 'lucide-react';
import { useTranslation } from '../contexts/I18nContext';

interface NotificationSettings {
  email: boolean;
  push: boolean;
  sms: boolean;
  inApp: boolean;
  sound: boolean;
  categories: {
    injuries: boolean;
    transfers: boolean;
    matches: boolean;
    odds: boolean;
    alerts: boolean;
  };
}

interface AppearanceSettings {
  theme: 'dark' | 'light' | 'auto';
  primaryColor: string;
  accentColor: string;
  fontSize: 'small' | 'medium' | 'large';
  animations: boolean;
  compactMode: boolean;
}

interface SecuritySettings {
  twoFactor: boolean;
  sessionTimeout: number;
  dataSharing: boolean;
  analytics: boolean;
  crashReports: boolean;
}

interface BettingLimits {
  dailyLimit: number;
  weeklyLimit: number;
  monthlyLimit: number;
  maxBetAmount: number;
  kellyMaxPercent: number;
  alertOnLimit: boolean;
}

interface UserProfile {
  name: string;
  email: string;
  phone: string;
  timezone: string;
  language: string;
  currency: string;
}

const Settings: React.FC = () => {
  const { language, setLanguage, t } = useTranslation();
  const [activeTab, setActiveTab] = useState<'profile' | 'notifications' | 'appearance' | 'security' | 'limits' | 'data'>('profile');
  const [showSuccess, setShowSuccess] = useState(false);
  const [isModified, setIsModified] = useState(false);

  // Estados para cada seção
  const [profile, setProfile] = useState<UserProfile>({
    name: 'João Silva',
    email: 'joao@email.com',
    phone: '+55 11 99999-9999',
    timezone: 'America/Sao_Paulo',
    language: language, // Use language from i18n context
    currency: 'BRL'
  });

  // Sync profile language with i18n context
  useEffect(() => {
    setProfile(prev => ({ ...prev, language }));
  }, [language]);

  const [notifications, setNotifications] = useState<NotificationSettings>({
    email: true,
    push: true,
    sms: false,
    inApp: true,
    sound: true,
    categories: {
      injuries: true,
      transfers: true,
      matches: true,
      odds: true,
      alerts: true
    }
  });

  const [appearance, setAppearance] = useState<AppearanceSettings>({
    theme: 'dark',
    primaryColor: '#10b981',
    accentColor: '#f59e0b',
    fontSize: 'medium',
    animations: true,
    compactMode: false
  });

  const [security, setSecurity] = useState<SecuritySettings>({
    twoFactor: false,
    sessionTimeout: 60,
    dataSharing: false,
    analytics: true,
    crashReports: true
  });

  const [limits, setLimits] = useState<BettingLimits>({
    dailyLimit: 100,
    weeklyLimit: 500,
    monthlyLimit: 2000,
    maxBetAmount: 50,
    kellyMaxPercent: 5,
    alertOnLimit: true
  });

  const [showPassword, setShowPassword] = useState(false);

  const handleSave = () => {
    // Simular salvamento
    setShowSuccess(true);
    setIsModified(false);
    setTimeout(() => setShowSuccess(false), 3000);
  };

  const handleReset = () => {
    // Resetar para valores padrão
    setIsModified(false);
  };

  const ColorPicker: React.FC<{ value: string; onChange: (color: string) => void; label: string }> = ({
    value,
    onChange,
    label
  }) => {
    const colors = [
      '#10b981', '#3b82f6', '#8b5cf6', '#f59e0b',
      '#ef4444', '#06b6d4', '#84cc16', '#f97316'
    ];

    return (
      <div>
        <label className="block text-sm font-medium text-text-secondary mb-2">
          {label}
        </label>
        <div className="flex gap-2">
          {colors.map((color) => (
            <button
              key={color}
              onClick={() => {
                onChange(color);
                setIsModified(true);
              }}
              className={`w-8 h-8 rounded-full border-2 transition-all ${
                value === color
                  ? 'border-white shadow-lg scale-110'
                  : 'border-border-subtle hover:scale-105'
              }`}
              style={{ backgroundColor: color }}
            />
          ))}
        </div>
        <div className="mt-2 text-xs text-text-tertiary font-mono">
          {value}
        </div>
      </div>
    );
  };

  const Toggle: React.FC<{
    checked: boolean;
    onChange: (checked: boolean) => void;
    label: string;
    description?: string;
  }> = ({ checked, onChange, label, description }) => (
    <div className="flex items-center justify-between p-3 bg-bg-tertiary rounded-lg border border-border-subtle">
      <div>
        <div className="text-text-primary font-medium">{label}</div>
        {description && (
          <div className="text-sm text-text-secondary">{description}</div>
        )}
      </div>
      <label className="relative inline-flex items-center cursor-pointer">
        <input
          type="checkbox"
          checked={checked}
          onChange={(e) => {
            onChange(e.target.checked);
            setIsModified(true);
          }}
          className="sr-only peer"
        />
        <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
      </label>
    </div>
  );

  const InputField: React.FC<{
    label: string;
    value: string | number;
    onChange: (value: string) => void;
    type?: string;
    placeholder?: string;
    icon?: React.ReactNode;
  }> = ({ label, value, onChange, type = 'text', placeholder, icon }) => (
    <div>
      <label className="block text-sm font-medium text-text-secondary mb-2">
        {label}
      </label>
      <div className="relative">
        {icon && (
          <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-tertiary">
            {icon}
          </div>
        )}
        <input
          type={type}
          value={value}
          onChange={(e) => {
            onChange(e.target.value);
            setIsModified(true);
          }}
          placeholder={placeholder}
          className={`w-full ${
            icon ? 'pl-10' : 'pl-4'
          } pr-4 py-2 bg-bg-tertiary border border-border-subtle rounded-lg text-text-primary placeholder:text-text-tertiary focus:outline-none focus:border-primary-500`}
        />
      </div>
    </div>
  );

  const SelectField: React.FC<{
    label: string;
    value: string;
    onChange: (value: string) => void;
    options: { value: string; label: string }[];
  }> = ({ label, value, onChange, options }) => (
    <div>
      <label className="block text-sm font-medium text-text-secondary mb-2">
        {label}
      </label>
      <select
        value={value}
        onChange={(e) => {
          onChange(e.target.value);
          setIsModified(true);
        }}
        className="w-full px-4 py-2 bg-bg-tertiary border border-border-subtle rounded-lg text-text-primary focus:outline-none focus:border-primary-500"
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">{t('settings.title')}</h1>
          <p className="text-text-secondary">
            {t('settings.subtitle')}
          </p>
        </div>

        {isModified && (
          <div className="flex gap-2 w-full sm:w-auto">
            <button
              onClick={handleReset}
              className="flex-1 sm:flex-none px-4 py-2 text-text-secondary hover:text-text-primary transition-colors flex items-center justify-center gap-2"
            >
              <RotateCcw className="w-4 h-4" />
              <span className="hidden sm:inline">{t('settings.discard')}</span>
            </button>
            <button
              onClick={handleSave}
              className="flex-1 sm:flex-none bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition-colors flex items-center justify-center gap-2"
            >
              <Save className="w-4 h-4" />
              <span className="hidden sm:inline">{t('settings.save_changes')}</span>
            </button>
          </div>
        )}
      </div>

      {/* Success Message */}
      <AnimatePresence>
        {showSuccess && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="bg-green-900/20 border border-green-500/30 rounded-lg p-4 flex items-center gap-2"
          >
            <Check className="w-5 h-5 text-green-400" />
            <span className="text-green-400">{t('settings.success')}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Tabs */}
      <div className="bg-bg-card rounded-lg border border-border-subtle p-1">
        <div className="flex space-x-1 overflow-x-auto scrollbar-hide pb-1">
          {[
            { id: 'profile', labelKey: 'settings.tabs.profile', icon: User },
            { id: 'notifications', labelKey: 'settings.tabs.notifications', icon: Bell },
            { id: 'appearance', labelKey: 'settings.tabs.appearance', icon: Palette },
            { id: 'security', labelKey: 'settings.tabs.security', icon: Shield },
            { id: 'limits', labelKey: 'settings.tabs.limits', icon: AlertTriangle },
            { id: 'data', labelKey: 'settings.tabs.data', icon: Database }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-4 py-2 rounded-md transition-all whitespace-nowrap ${
                activeTab === tab.id
                  ? 'bg-primary-600 text-white'
                  : 'text-text-secondary hover:text-text-primary hover:bg-bg-tertiary'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {t(tab.labelKey)}
            </button>
          ))}
        </div>
      </div>

      {/* Content based on active tab */}
      <AnimatePresence mode="wait">
        {activeTab === 'profile' && (
          <motion.div
            key="profile"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="grid grid-cols-1 lg:grid-cols-2 gap-6"
          >
            <div className="bg-bg-card rounded-lg border border-border-subtle p-6">
              <h3 className="text-lg font-semibold text-text-primary mb-6">
                {t('settings.profile.personal')}
              </h3>

              <div className="space-y-4">
                <InputField
                  label={t('settings.profile.name')}
                  value={profile.name}
                  onChange={(value) => setProfile(prev => ({ ...prev, name: value }))}
                  icon={<User className="w-4 h-4" />}
                />

                <InputField
                  label={t('settings.profile.email')}
                  value={profile.email}
                  onChange={(value) => setProfile(prev => ({ ...prev, email: value }))}
                  type="email"
                  icon={<Mail className="w-4 h-4" />}
                />

                <InputField
                  label={t('settings.profile.phone')}
                  value={profile.phone}
                  onChange={(value) => setProfile(prev => ({ ...prev, phone: value }))}
                  type="tel"
                  icon={<Phone className="w-4 h-4" />}
                />
              </div>
            </div>

            <div className="bg-bg-card rounded-lg border border-border-subtle p-6">
              <h3 className="text-lg font-semibold text-text-primary mb-6">
                {t('settings.profile.location')}
              </h3>

              <div className="space-y-4">
                <SelectField
                  label={t('settings.profile.timezone')}
                  value={profile.timezone}
                  onChange={(value) => setProfile(prev => ({ ...prev, timezone: value }))}
                  options={[
                    { value: 'America/Sao_Paulo', label: 'São Paulo (GMT-3)' },
                    { value: 'America/New_York', label: 'New York (GMT-5)' },
                    { value: 'Europe/London', label: 'London (GMT+0)' },
                    { value: 'Europe/Madrid', label: 'Madrid (GMT+1)' }
                  ]}
                />

                <SelectField
                  label={t('settings.profile.language')}
                  value={profile.language}
                  onChange={(value) => {
                    setProfile(prev => ({ ...prev, language: value }));
                    setLanguage(value as 'pt' | 'en' | 'es'); // Update i18n context
                    setIsModified(true);
                  }}
                  options={[
                    { value: 'pt', label: 'Português' },
                    { value: 'en', label: 'English' },
                    { value: 'es', label: 'Español' }
                  ]}
                />

                <SelectField
                  label={t('settings.profile.currency')}
                  value={profile.currency}
                  onChange={(value) => setProfile(prev => ({ ...prev, currency: value }))}
                  options={[
                    { value: 'BRL', label: 'Real Brasileiro (R$)' },
                    { value: 'USD', label: 'US Dollar ($)' },
                    { value: 'EUR', label: 'Euro (€)' },
                    { value: 'GBP', label: 'British Pound (£)' }
                  ]}
                />
              </div>
            </div>
          </motion.div>
        )}

        {activeTab === 'notifications' && (
          <motion.div
            key="notifications"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-6"
          >
            <div className="bg-bg-card rounded-lg border border-border-subtle p-6">
              <h3 className="text-lg font-semibold text-text-primary mb-6">
                {t('settings.notifications.methods')}
              </h3>

              <div className="space-y-4">
                <Toggle
                  checked={notifications.email}
                  onChange={(checked) => setNotifications(prev => ({ ...prev, email: checked }))}
                  label={t('settings.notifications.email')}
                  description={t('settings.notifications.email_desc')}
                />

                <Toggle
                  checked={notifications.push}
                  onChange={(checked) => setNotifications(prev => ({ ...prev, push: checked }))}
                  label={t('settings.notifications.push')}
                  description={t('settings.notifications.push_desc')}
                />

                <Toggle
                  checked={notifications.sms}
                  onChange={(checked) => setNotifications(prev => ({ ...prev, sms: checked }))}
                  label={t('settings.notifications.sms')}
                  description={t('settings.notifications.sms_desc')}
                />

                <Toggle
                  checked={notifications.inApp}
                  onChange={(checked) => setNotifications(prev => ({ ...prev, inApp: checked }))}
                  label={t('settings.notifications.inapp')}
                  description={t('settings.notifications.inapp_desc')}
                />

                <Toggle
                  checked={notifications.sound}
                  onChange={(checked) => setNotifications(prev => ({ ...prev, sound: checked }))}
                  label={t('settings.notifications.sound')}
                  description={t('settings.notifications.sound_desc')}
                />
              </div>
            </div>

            <div className="bg-bg-card rounded-lg border border-border-subtle p-6">
              <h3 className="text-lg font-semibold text-text-primary mb-6">
                {t('settings.notifications.categories')}
              </h3>

              <div className="space-y-4">
                <Toggle
                  checked={notifications.categories.injuries}
                  onChange={(checked) => setNotifications(prev => ({
                    ...prev,
                    categories: { ...prev.categories, injuries: checked }
                  }))}
                  label={t('settings.notifications.injuries')}
                  description={t('settings.notifications.injuries_desc')}
                />

                <Toggle
                  checked={notifications.categories.transfers}
                  onChange={(checked) => setNotifications(prev => ({
                    ...prev,
                    categories: { ...prev.categories, transfers: checked }
                  }))}
                  label={t('settings.notifications.transfers')}
                  description={t('settings.notifications.transfers_desc')}
                />

                <Toggle
                  checked={notifications.categories.matches}
                  onChange={(checked) => setNotifications(prev => ({
                    ...prev,
                    categories: { ...prev.categories, matches: checked }
                  }))}
                  label={t('settings.notifications.matches')}
                  description={t('settings.notifications.matches_desc')}
                />

                <Toggle
                  checked={notifications.categories.odds}
                  onChange={(checked) => setNotifications(prev => ({
                    ...prev,
                    categories: { ...prev.categories, odds: checked }
                  }))}
                  label={t('settings.notifications.odds')}
                  description={t('settings.notifications.odds_desc')}
                />

                <Toggle
                  checked={notifications.categories.alerts}
                  onChange={(checked) => setNotifications(prev => ({
                    ...prev,
                    categories: { ...prev.categories, alerts: checked }
                  }))}
                  label={t('settings.notifications.alerts')}
                  description={t('settings.notifications.alerts_desc')}
                />
              </div>
            </div>
          </motion.div>
        )}

        {activeTab === 'appearance' && (
          <motion.div
            key="appearance"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-6"
          >
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-bg-card rounded-lg border border-border-subtle p-6">
                <h3 className="text-lg font-semibold text-text-primary mb-6">
                  {t('settings.appearance.theme')}
                </h3>

                <div className="space-y-6">
                  <div>
                    <label className="block text-sm font-medium text-text-secondary mb-3">
                      {t('settings.appearance.theme_label')}
                    </label>
                    <div className="grid grid-cols-3 gap-3">
                      {[
                        { value: 'dark', labelKey: 'settings.appearance.dark', icon: Moon },
                        { value: 'light', labelKey: 'settings.appearance.light', icon: Sun },
                        { value: 'auto', labelKey: 'settings.appearance.auto', icon: Monitor }
                      ].map(({ value, labelKey, icon: Icon }) => (
                        <button
                          key={value}
                          onClick={() => {
                            setAppearance(prev => ({ ...prev, theme: value as any }));
                            setIsModified(true);
                          }}
                          className={`flex flex-col items-center gap-2 p-4 rounded-lg border transition-all ${
                            appearance.theme === value
                              ? 'border-primary-500 bg-primary-600/20'
                              : 'border-border-subtle bg-bg-tertiary hover:border-border-primary'
                          }`}
                        >
                          <Icon className="w-6 h-6" />
                          <span className="text-sm">{t(labelKey)}</span>
                        </button>
                      ))}
                    </div>
                  </div>

                  <ColorPicker
                    label={t('settings.appearance.primary_color')}
                    value={appearance.primaryColor}
                    onChange={(color) => setAppearance(prev => ({ ...prev, primaryColor: color }))}
                  />

                  <ColorPicker
                    label={t('settings.appearance.accent_color')}
                    value={appearance.accentColor}
                    onChange={(color) => setAppearance(prev => ({ ...prev, accentColor: color }))}
                  />
                </div>
              </div>

              <div className="bg-bg-card rounded-lg border border-border-subtle p-6">
                <h3 className="text-lg font-semibold text-text-primary mb-6">
                  {t('settings.appearance.interface')}
                </h3>

                <div className="space-y-4">
                  <SelectField
                    label={t('settings.appearance.font_size')}
                    value={appearance.fontSize}
                    onChange={(value) => setAppearance(prev => ({ ...prev, fontSize: value as any }))}
                    options={[
                      { value: 'small', label: t('settings.appearance.font_small') },
                      { value: 'medium', label: t('settings.appearance.font_medium') },
                      { value: 'large', label: t('settings.appearance.font_large') }
                    ]}
                  />

                  <Toggle
                    checked={appearance.animations}
                    onChange={(checked) => setAppearance(prev => ({ ...prev, animations: checked }))}
                    label={t('settings.appearance.animations')}
                    description={t('settings.appearance.animations_desc')}
                  />

                  <Toggle
                    checked={appearance.compactMode}
                    onChange={(checked) => setAppearance(prev => ({ ...prev, compactMode: checked }))}
                    label={t('settings.appearance.compact')}
                    description={t('settings.appearance.compact_desc')}
                  />
                </div>
              </div>
            </div>

            {/* Preview */}
            <div className="bg-bg-card rounded-lg border border-border-subtle p-6">
              <h3 className="text-lg font-semibold text-text-primary mb-6">
                {t('settings.appearance.preview')}
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div
                  className="p-4 rounded-lg border border-border-subtle"
                  style={{ backgroundColor: appearance.primaryColor + '20' }}
                >
                  <div
                    className="w-full h-2 rounded mb-3"
                    style={{ backgroundColor: appearance.primaryColor }}
                  />
                  <div className="text-text-primary font-medium mb-2">{t('settings.appearance.preview_main')}</div>
                  <div className="text-text-secondary text-sm">
                    {t('settings.appearance.preview_main_desc')}
                  </div>
                </div>

                <div
                  className="p-4 rounded-lg border border-border-subtle"
                  style={{ backgroundColor: appearance.accentColor + '20' }}
                >
                  <div
                    className="w-full h-2 rounded mb-3"
                    style={{ backgroundColor: appearance.accentColor }}
                  />
                  <div className="text-text-primary font-medium mb-2">{t('settings.appearance.preview_accent')}</div>
                  <div className="text-text-secondary text-sm">
                    {t('settings.appearance.preview_accent_desc')}
                  </div>
                </div>

                <div className="p-4 rounded-lg border border-border-subtle bg-bg-tertiary">
                  <div className="w-full h-2 rounded mb-3 bg-gray-500" />
                  <div className="text-text-primary font-medium mb-2">{t('settings.appearance.preview_neutral')}</div>
                  <div className="text-text-secondary text-sm">
                    {t('settings.appearance.preview_neutral_desc')}
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {activeTab === 'security' && (
          <motion.div
            key="security"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-6"
          >
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-bg-card rounded-lg border border-border-subtle p-6">
                <h3 className="text-lg font-semibold text-text-primary mb-6">
                  {t('settings.security.auth')}
                </h3>

                <div className="space-y-4">
                  <Toggle
                    checked={security.twoFactor}
                    onChange={(checked) => setSecurity(prev => ({ ...prev, twoFactor: checked }))}
                    label={t('settings.security.2fa')}
                    description={t('settings.security.2fa_desc')}
                  />

                  <div>
                    <label className="block text-sm font-medium text-text-secondary mb-2">
                      {t('settings.security.session_timeout')}
                    </label>
                    <select
                      value={security.sessionTimeout}
                      onChange={(e) => {
                        setSecurity(prev => ({ ...prev, sessionTimeout: Number(e.target.value) }));
                        setIsModified(true);
                      }}
                      className="w-full px-4 py-2 bg-bg-tertiary border border-border-subtle rounded-lg text-text-primary focus:outline-none focus:border-primary-500"
                    >
                      <option value={15}>15 minutos</option>
                      <option value={30}>30 minutos</option>
                      <option value={60}>1 hora</option>
                      <option value={120}>2 horas</option>
                      <option value={480}>8 horas</option>
                    </select>
                  </div>

                  <div className="pt-4 border-t border-border-subtle">
                    <h4 className="text-text-primary font-medium mb-3">{t('settings.security.change_password')}</h4>
                    <div className="space-y-3">
                      <div className="relative">
                        <input
                          type={showPassword ? 'text' : 'password'}
                          placeholder={t('settings.security.current_password')}
                          className="w-full pl-10 pr-10 py-2 bg-bg-tertiary border border-border-subtle rounded-lg text-text-primary placeholder:text-text-tertiary focus:outline-none focus:border-primary-500"
                        />
                        <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-text-tertiary" />
                        <button
                          type="button"
                          onClick={() => setShowPassword(!showPassword)}
                          className="absolute right-3 top-1/2 transform -translate-y-1/2 text-text-tertiary hover:text-text-primary"
                        >
                          {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                        </button>
                      </div>

                      <input
                        type="password"
                        placeholder={t('settings.security.new_password')}
                        className="w-full pl-10 py-2 bg-bg-tertiary border border-border-subtle rounded-lg text-text-primary placeholder:text-text-tertiary focus:outline-none focus:border-primary-500"
                      />

                      <input
                        type="password"
                        placeholder={t('settings.security.confirm_password')}
                        className="w-full pl-10 py-2 bg-bg-tertiary border border-border-subtle rounded-lg text-text-primary placeholder:text-text-tertiary focus:outline-none focus:border-primary-500"
                      />

                      <button className="w-full bg-primary-600 text-white py-2 rounded-lg hover:bg-primary-700 transition-colors flex items-center justify-center gap-2">
                        <Key className="w-4 h-4" />
                        {t('settings.security.change_password')}
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-bg-card rounded-lg border border-border-subtle p-6">
                <h3 className="text-lg font-semibold text-text-primary mb-6">
                  {t('settings.security.privacy')}
                </h3>

                <div className="space-y-4">
                  <Toggle
                    checked={security.dataSharing}
                    onChange={(checked) => setSecurity(prev => ({ ...prev, dataSharing: checked }))}
                    label={t('settings.security.data_sharing')}
                    description={t('settings.security.data_sharing_desc')}
                  />

                  <Toggle
                    checked={security.analytics}
                    onChange={(checked) => setSecurity(prev => ({ ...prev, analytics: checked }))}
                    label={t('settings.security.analytics')}
                    description={t('settings.security.analytics_desc')}
                  />

                  <Toggle
                    checked={security.crashReports}
                    onChange={(checked) => setSecurity(prev => ({ ...prev, crashReports: checked }))}
                    label={t('settings.security.crash_reports')}
                    description={t('settings.security.crash_reports_desc')}
                  />

                  <div className="pt-4 border-t border-border-subtle">
                    <h4 className="text-text-primary font-medium mb-3">{t('settings.security.active_sessions')}</h4>
                    <div className="space-y-2">
                      {[
                        { device: 'Chrome - Windows', location: 'São Paulo, BR', current: true },
                        { device: 'Safari - iPhone', location: 'São Paulo, BR', current: false },
                        { device: 'Chrome - Android', location: 'Rio de Janeiro, BR', current: false }
                      ].map((session, index) => (
                        <div key={index} className="flex items-center justify-between p-3 bg-bg-tertiary rounded border border-border-subtle">
                          <div>
                            <div className="text-text-primary text-sm">{session.device}</div>
                            <div className="text-text-tertiary text-xs">{session.location}</div>
                          </div>
                          <div className="flex items-center gap-2">
                            {session.current && (
                              <span className="px-2 py-1 bg-green-900/20 text-green-400 rounded text-xs">
                                {t('settings.security.current_session')}
                              </span>
                            )}
                            {!session.current && (
                              <button className="text-red-400 hover:text-red-300 text-xs">
                                {t('settings.security.revoke')}
                              </button>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {activeTab === 'limits' && (
          <motion.div
            key="limits"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-6"
          >
            <div className="bg-accent-900/20 border border-accent-500/30 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className="w-5 h-5 text-accent-400" />
                <span className="text-accent-400 font-medium">{t('settings.limits.responsible')}</span>
              </div>
              <p className="text-text-secondary text-sm">
                {t('settings.limits.responsible_desc')}
              </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-bg-card rounded-lg border border-border-subtle p-6">
                <h3 className="text-lg font-semibold text-text-primary mb-6">
                  {t('settings.limits.time')}
                </h3>

                <div className="space-y-4">
                  <InputField
                    label={t('settings.limits.daily')}
                    value={limits.dailyLimit}
                    onChange={(value) => setLimits(prev => ({ ...prev, dailyLimit: Number(value) }))}
                    type="number"
                  />

                  <InputField
                    label={t('settings.limits.weekly')}
                    value={limits.weeklyLimit}
                    onChange={(value) => setLimits(prev => ({ ...prev, weeklyLimit: Number(value) }))}
                    type="number"
                  />

                  <InputField
                    label={t('settings.limits.monthly')}
                    value={limits.monthlyLimit}
                    onChange={(value) => setLimits(prev => ({ ...prev, monthlyLimit: Number(value) }))}
                    type="number"
                  />

                  <div className="pt-4 border-t border-border-subtle">
                    <div className="text-text-primary font-medium mb-2">{t('settings.limits.current_usage')}</div>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-text-tertiary">{t('settings.limits.today')}</span>
                        <span className="text-text-primary">R$ 45,00 / R$ {limits.dailyLimit}</span>
                      </div>
                      <div className="bg-bg-tertiary rounded-full h-2">
                        <div className="bg-primary-400 h-2 rounded-full" style={{ width: '45%' }} />
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-bg-card rounded-lg border border-border-subtle p-6">
                <h3 className="text-lg font-semibold text-text-primary mb-6">
                  {t('settings.limits.per_bet')}
                </h3>

                <div className="space-y-4">
                  <InputField
                    label={t('settings.limits.max_bet')}
                    value={limits.maxBetAmount}
                    onChange={(value) => setLimits(prev => ({ ...prev, maxBetAmount: Number(value) }))}
                    type="number"
                  />

                  <InputField
                    label={t('settings.limits.kelly_max')}
                    value={limits.kellyMaxPercent}
                    onChange={(value) => setLimits(prev => ({ ...prev, kellyMaxPercent: Number(value) }))}
                    type="number"
                  />

                  <Toggle
                    checked={limits.alertOnLimit}
                    onChange={(checked) => setLimits(prev => ({ ...prev, alertOnLimit: checked }))}
                    label={t('settings.limits.alerts')}
                    description={t('settings.limits.alerts_desc')}
                  />

                  <div className="pt-4 border-t border-border-subtle">
                    <h4 className="text-text-primary font-medium mb-3">{t('settings.limits.self_exclusion')}</h4>
                    <p className="text-text-secondary text-sm mb-3">
                      {t('settings.limits.self_exclusion_desc')}
                    </p>
                    <div className="space-y-2">
                      {['24 horas', '7 dias', '30 dias', '6 meses'].map((period) => (
                        <button
                          key={period}
                          className="w-full p-2 text-left text-text-secondary hover:text-text-primary hover:bg-bg-tertiary rounded border border-border-subtle transition-colors"
                        >
                          {t('settings.limits.self_exclusion_period')} {period}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {activeTab === 'data' && (
          <motion.div
            key="data"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-6"
          >
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-bg-card rounded-lg border border-border-subtle p-6">
                <h3 className="text-lg font-semibold text-text-primary mb-6">
                  {t('settings.data.backup')}
                </h3>

                <div className="space-y-4">
                  <button className="w-full p-4 bg-bg-tertiary border border-border-subtle rounded-lg hover:border-primary-500/30 transition-colors flex items-center gap-3">
                    <Download className="w-5 h-5 text-primary-400" />
                    <div className="text-left">
                      <div className="text-text-primary font-medium">{t('settings.data.export')}</div>
                      <div className="text-text-tertiary text-sm">
                        {t('settings.data.export_desc')}
                      </div>
                    </div>
                  </button>

                  <button className="w-full p-4 bg-bg-tertiary border border-border-subtle rounded-lg hover:border-primary-500/30 transition-colors flex items-center gap-3">
                    <Upload className="w-5 h-5 text-accent-400" />
                    <div className="text-left">
                      <div className="text-text-primary font-medium">{t('settings.data.import')}</div>
                      <div className="text-text-tertiary text-sm">
                        {t('settings.data.import_desc')}
                      </div>
                    </div>
                  </button>

                  <div className="pt-4 border-t border-border-subtle">
                    <h4 className="text-text-primary font-medium mb-3">{t('settings.data.auto_backup')}</h4>
                    <Toggle
                      checked={true}
                      onChange={() => {}}
                      label={t('settings.data.weekly_backup')}
                      description={t('settings.data.weekly_backup_desc')}
                    />
                  </div>
                </div>
              </div>

              <div className="bg-bg-card rounded-lg border border-border-subtle p-6">
                <h3 className="text-lg font-semibold text-text-primary mb-6">
                  {t('settings.data.storage')}
                </h3>

                <div className="space-y-4">
                  <div className="p-4 bg-bg-tertiary rounded border border-border-subtle">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-text-primary">{t('settings.data.cache')}</span>
                      <span className="text-text-secondary">2.3 MB</span>
                    </div>
                    <div className="bg-bg-primary rounded-full h-2">
                      <div className="bg-primary-400 h-2 rounded-full" style={{ width: '23%' }} />
                    </div>
                  </div>

                  <div className="p-4 bg-bg-tertiary rounded border border-border-subtle">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-text-primary">{t('settings.data.offline')}</span>
                      <span className="text-text-secondary">856 KB</span>
                    </div>
                    <div className="bg-bg-primary rounded-full h-2">
                      <div className="bg-accent-400 h-2 rounded-full" style={{ width: '8%' }} />
                    </div>
                  </div>

                  <button className="w-full p-3 bg-red-900/20 border border-red-500/30 text-red-400 rounded-lg hover:bg-red-900/30 transition-colors flex items-center justify-center gap-2">
                    <Trash2 className="w-4 h-4" />
                    {t('settings.data.clear_cache')}
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Footer educativo */}
      <div className="bg-bg-card rounded-lg border border-border-subtle p-4 text-center">
        <p className="text-text-tertiary text-sm">
          <strong className="text-text-primary">{t('footer.educational')}</strong> {t('footer.educational_desc')}
        </p>
      </div>
    </div>
  );
};

export default Settings;