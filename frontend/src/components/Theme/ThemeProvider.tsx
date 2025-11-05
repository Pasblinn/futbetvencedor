import React, { useEffect } from 'react';
import { useTheme, useAppStore } from '../../store';

interface ThemeProviderProps {
  children: React.ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  const theme = useTheme();
  const setTheme = useAppStore((state) => state.setTheme);

  useEffect(() => {
    // Get stored theme from localStorage or detect system preference
    const storedTheme = localStorage.getItem('theme');
    let initialTheme: 'light' | 'dark' = 'dark';

    if (storedTheme === 'light' || storedTheme === 'dark') {
      initialTheme = storedTheme;
    } else if (typeof window !== 'undefined' && window.matchMedia) {
      // Use system preference if no stored theme
      initialTheme = window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
    }

    // Set initial theme
    if (theme !== initialTheme) {
      setTheme(initialTheme);
    }

    // Apply theme to document
    const root = document.documentElement;
    root.classList.remove('light', 'dark');
    root.classList.add(initialTheme);

    // Listen for system theme changes
    const mediaQuery = window.matchMedia('(prefers-color-scheme: light)');
    const handleSystemThemeChange = (e: MediaQueryListEvent) => {
      if (!localStorage.getItem('theme')) {
        const newTheme = e.matches ? 'light' : 'dark';
        setTheme(newTheme);
        root.classList.remove('light', 'dark');
        root.classList.add(newTheme);
      }
    };

    mediaQuery.addListener(handleSystemThemeChange);

    return () => {
      mediaQuery.removeListener(handleSystemThemeChange);
    };
  }, []);

  // Apply theme changes
  useEffect(() => {
    const root = document.documentElement;
    root.classList.remove('light', 'dark');
    root.classList.add(theme);

    // Update meta theme-color
    const metaThemeColor = document.querySelector('meta[name="theme-color"]');
    if (metaThemeColor) {
      metaThemeColor.setAttribute('content', theme === 'dark' ? '#0a0e1a' : '#f8fafc');
    }

    // Store in localStorage
    localStorage.setItem('theme', theme);
  }, [theme]);

  return <>{children}</>;
};

export default ThemeProvider;