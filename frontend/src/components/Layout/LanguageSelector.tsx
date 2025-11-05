import React, { useState, useRef, useEffect } from 'react';
import { Globe, Check } from 'lucide-react';
import { useTranslation, Language } from '../../contexts/I18nContext';

const LanguageSelector: React.FC = () => {
  const { language, setLanguage, t } = useTranslation();
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const languages: { code: Language; label: string; flag: string }[] = [
    { code: 'pt', label: 'Português', flag: '🇧🇷' },
    { code: 'en', label: 'English', flag: '🇺🇸' },
    { code: 'es', label: 'Español', flag: '🇪🇸' },
  ];

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleLanguageChange = (lang: Language) => {
    setLanguage(lang);
    setShowDropdown(false);
  };

  const currentLang = languages.find((l) => l.code === language);

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setShowDropdown(!showDropdown)}
        className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-bg-tertiary transition-colors flex items-center gap-2"
        title={t('settings.profile.language')}
      >
        <Globe className="w-5 h-5 text-slate-600 dark:text-text-secondary" />
        <span className="text-xl">{currentLang?.flag}</span>
      </button>

      {showDropdown && (
        <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-bg-secondary rounded-lg shadow-lg border border-slate-200 dark:border-border-primary py-2 z-50">
          <div className="px-4 py-2 border-b border-slate-200 dark:border-border-subtle">
            <h3 className="text-sm font-semibold text-slate-900 dark:text-text-primary">
              {t('settings.profile.language')}
            </h3>
          </div>
          {languages.map((lang) => (
            <button
              key={lang.code}
              onClick={() => handleLanguageChange(lang.code)}
              className={`flex items-center gap-3 w-full px-4 py-2 text-sm hover:bg-slate-50 dark:hover:bg-bg-tertiary transition-colors ${
                language === lang.code
                  ? 'text-primary-600 dark:text-primary-400 bg-primary-50/50 dark:bg-primary-900/10'
                  : 'text-slate-700 dark:text-text-secondary'
              }`}
            >
              <span className="text-xl">{lang.flag}</span>
              <span className="flex-1 text-left">{lang.label}</span>
              {language === lang.code && (
                <Check className="w-4 h-4" />
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default LanguageSelector;
