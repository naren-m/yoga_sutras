import { createContext } from 'react';

export interface Bookmark {
  /** Block ID of the bookmarked sutra */
  blockId: number;
  /** Section slug (e.g., 'samadhi-pada') */
  sectionSlug: string;
  /** Section title (e.g., 'Samadhi Pada') */
  sectionTitle: string;
  /** Sutra number within the section */
  sutraNumber: number;
  /** Pada index (0-based, for display as 1.x, 2.x, etc.) */
  padaIndex: number;
  /** Sutra content in Devanagari */
  content: string;
  /** Timestamp when bookmarked */
  createdAt: number;
}

export interface BookmarksContextType {
  bookmarks: Bookmark[];
  bookmarkCount: number;
  isBookmarked: (blockId: number) => boolean;
  addBookmark: (bookmark: Omit<Bookmark, 'createdAt'>) => void;
  removeBookmark: (blockId: number) => void;
  toggleBookmark: (bookmark: Omit<Bookmark, 'createdAt'>) => void;
  exportBookmarks: () => string;
}

export const BookmarksContext = createContext<BookmarksContextType | undefined>(undefined);
