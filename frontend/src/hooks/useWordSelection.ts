import { useContext } from 'react';
import { WordSelectionContext, type WordSelectionContextType } from '../contexts/wordSelectionTypes';

export function useWordSelection(): WordSelectionContextType {
  const context = useContext(WordSelectionContext);
  if (context === undefined) {
    throw new Error('useWordSelection must be used within a WordSelectionProvider');
  }
  return context;
}
