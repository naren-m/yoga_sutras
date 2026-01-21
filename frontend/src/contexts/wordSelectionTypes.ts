import { createContext } from 'react';

export interface SelectedWord {
  word: string;
  position?: { x: number; y: number };
}

export interface WordSelectionContextType {
  selectedWord: SelectedWord | null;
  selectWord: (word: string, position?: { x: number; y: number }) => void;
  clearSelection: () => void;
}

export const WordSelectionContext = createContext<WordSelectionContextType | undefined>(undefined);
