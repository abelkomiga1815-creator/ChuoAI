'use client';

import { useCallback, useEffect, useState } from 'react';

export type Language = 'auto' | 'en' | 'sw';

const STORAGE_KEY = 'chuoai-language';

function getInitialLanguage(): Language {
  if (typeof window === 'undefined') return 'auto';
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === 'en' || stored === 'sw' || stored === 'auto') return stored;
  return 'auto';
}

export function usePreferences() {
  const [language, setLanguage] = useState<Language>(getInitialLanguage);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, language);
  }, [language]);

  const cycleLanguage = useCallback(() => {
    setLanguage((l) => (l === 'en' ? 'sw' : l === 'sw' ? 'auto' : 'en'));
  }, []);

  return { language, setLanguage, cycleLanguage };
}