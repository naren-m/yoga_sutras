import { useContext } from 'react';
import { BookmarksContext, type BookmarksContextType } from '../contexts/bookmarksTypes';

export function useBookmarks(): BookmarksContextType {
  const context = useContext(BookmarksContext);
  if (context === undefined) {
    throw new Error('useBookmarks must be used within a BookmarksProvider');
  }
  return context;
}
