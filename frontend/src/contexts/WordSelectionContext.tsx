import { useState, useCallback, type ReactNode } from 'react';
import { WordSelectionContext, type SelectedWord } from './wordSelectionTypes';

export function WordSelectionProvider({ children }: { children: ReactNode }) {
  const [selectedWord, setSelectedWord] = useState<SelectedWord | null>(null);

  const selectWord = useCallback((word: string, position?: { x: number; y: number }) => {
    setSelectedWord({ word, position });
  }, []);

  const clearSelection = useCallback(() => {
    setSelectedWord(null);
  }, []);

  return (
    <WordSelectionContext.Provider value={{ selectedWord, selectWord, clearSelection }}>
      {children}
    </WordSelectionContext.Provider>
  );
}
