import React, { createContext, useContext, useState, useEffect } from 'react';

export type Language = 'pt' | 'en' | 'es';

interface I18nContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string;
}

const I18nContext = createContext<I18nContextType | undefined>(undefined);

interface I18nProviderProps {
  children: React.ReactNode;
}

export const I18nProvider: React.FC<I18nProviderProps> = ({ children }) => {
  const [language, setLanguageState] = useState<Language>(() => {
    // Carregar idioma salvo ou usar o do navegador
    const saved = localStorage.getItem('language') as Language;
    if (saved && ['pt', 'en', 'es'].includes(saved)) {
      return saved;
    }

    // Detectar idioma do navegador
    const browserLang = navigator.language.toLowerCase();
    if (browserLang.startsWith('pt')) return 'pt';
    if (browserLang.startsWith('es')) return 'es';
    return 'en'; // Default
  });

  const [translations, setTranslations] = useState<Record<string, string>>({});

  useEffect(() => {
    // Carregar traduções dinamicamente
    console.log('📚 I18n: Loading translations for:', language);
    import(`../locales/${language}.ts`)
      .then((module) => {
        console.log(`✅ I18n: Translations loaded for ${language}:`, Object.keys(module.default).length, 'keys');
        setTranslations(module.default);
      })
      .catch((error) => {
        console.error(`❌ I18n: Failed to load translations for ${language}:`, error);
      });
  }, [language]);

  const setLanguage = (lang: Language) => {
    console.log('🌍 I18n: Changing language to:', lang);
    setLanguageState(lang);
    localStorage.setItem('language', lang);
    console.log('✅ I18n: Language changed and saved to localStorage');
  };

  const t = (key: string): string => {
    return translations[key] || key;
  };

  return (
    <I18nContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </I18nContext.Provider>
  );
};

export const useTranslation = () => {
  const context = useContext(I18nContext);
  if (!context) {
    throw new Error('useTranslation must be used within I18nProvider');
  }
  return context;
};
