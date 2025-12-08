
'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { UseCase, getUseCase, getDefaultUseCase } from '@/lib/use-cases';

interface UseCaseContextType {
  currentUseCase: UseCase;
  setUseCase: (useCaseId: string) => void;
}

const UseCaseContext = createContext<UseCaseContextType | undefined>(undefined);

export function UseCaseProvider({ children }: { children: React.ReactNode }) {
  const [currentUseCase, setCurrentUseCase] = useState<UseCase>(getDefaultUseCase());

  // Load from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('selectedUseCase');
    if (saved) {
      const useCase = getUseCase(saved);
      if (useCase) {
        setCurrentUseCase(useCase);
      }
    }
  }, []);

  const setUseCase = (useCaseId: string) => {
    const useCase = getUseCase(useCaseId);
    if (useCase) {
      setCurrentUseCase(useCase);
      localStorage.setItem('selectedUseCase', useCaseId);
    }
  };

  return (
    <UseCaseContext.Provider value={{ currentUseCase, setUseCase }}>
      {children}
    </UseCaseContext.Provider>
  );
}

export function useUseCase() {
  const context = useContext(UseCaseContext);
  if (context === undefined) {
    throw new Error('useUseCase must be used within a UseCaseProvider');
  }
  return context;
}
