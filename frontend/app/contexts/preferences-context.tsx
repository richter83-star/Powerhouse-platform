
'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { Locale } from '@/lib/i18n';

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system';
  locale: Locale;
  reducedMotion: boolean;
  highContrast: boolean;
  fontSize: 'small' | 'medium' | 'large';
  notifications: {
    email: boolean;
    push: boolean;
    slack: boolean;
  };
  dashboardLayout: 'compact' | 'comfortable' | 'spacious';
}

interface PreferencesContextType {
  preferences: UserPreferences;
  updatePreferences: (updates: Partial<UserPreferences>) => void;
  resetPreferences: () => void;
}

const defaultPreferences: UserPreferences = {
  theme: 'system',
  locale: 'en',
  reducedMotion: false,
  highContrast: false,
  fontSize: 'medium',
  notifications: {
    email: true,
    push: true,
    slack: false,
  },
  dashboardLayout: 'comfortable',
};

const PreferencesContext = createContext<PreferencesContextType | undefined>(undefined);

export function PreferencesProvider({ children }: { children: React.ReactNode }) {
  const [preferences, setPreferences] = useState<UserPreferences>(defaultPreferences);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('user-preferences');
      if (saved) {
        try {
          const parsed = JSON.parse(saved);
          setPreferences({ ...defaultPreferences, ...parsed });
        } catch (e) {
          console.error('Failed to parse preferences:', e);
        }
      }
      
      // Apply system preferences
      const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      const prefersHighContrast = window.matchMedia('(prefers-contrast: high)').matches;
      
      if (prefersReducedMotion || prefersHighContrast) {
        setPreferences(prev => ({
          ...prev,
          reducedMotion: prefersReducedMotion,
          highContrast: prefersHighContrast,
        }));
      }
    }
  }, []);

  useEffect(() => {
    if (mounted && typeof window !== 'undefined') {
      localStorage.setItem('user-preferences', JSON.stringify(preferences));
      
      // Apply preferences to DOM
      document.documentElement.setAttribute('data-font-size', preferences.fontSize);
      document.documentElement.setAttribute('data-layout', preferences.dashboardLayout);
      
      if (preferences.reducedMotion) {
        document.documentElement.style.setProperty('--motion-duration', '0.01ms');
      } else {
        document.documentElement.style.removeProperty('--motion-duration');
      }
      
      if (preferences.highContrast) {
        document.documentElement.classList.add('high-contrast');
      } else {
        document.documentElement.classList.remove('high-contrast');
      }
    }
  }, [preferences, mounted]);

  const updatePreferences = (updates: Partial<UserPreferences>) => {
    setPreferences(prev => ({ ...prev, ...updates }));
  };

  const resetPreferences = () => {
    setPreferences(defaultPreferences);
    if (typeof window !== 'undefined') {
      localStorage.removeItem('user-preferences');
    }
  };

  return (
    <PreferencesContext.Provider value={{ preferences, updatePreferences, resetPreferences }}>
      {children}
    </PreferencesContext.Provider>
  );
}

export function usePreferences() {
  const context = useContext(PreferencesContext);
  if (!context) {
    throw new Error('usePreferences must be used within PreferencesProvider');
  }
  return context;
}
