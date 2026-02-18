import { useState, useCallback, useEffect, type ReactNode } from 'react';
import { BookmarksContext, type Bookmark } from './bookmarksTypes';

const STORAGE_KEY = 'yoga-sutras-bookmarks';

function loadBookmarks(): Bookmark[] {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      return JSON.parse(stored);
    }
  } catch (e) {
    console.error('Failed to load bookmarks from localStorage:', e);
  }
  return [];
}

function saveBookmarks(bookmarks: Bookmark[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(bookmarks));
  } catch (e) {
    console.error('Failed to save bookmarks to localStorage:', e);
  }
}

export function BookmarksProvider({ children }: { children: ReactNode }) {
  const [bookmarks, setBookmarks] = useState<Bookmark[]>(() => loadBookmarks());

  // Persist bookmarks to localStorage whenever they change
  useEffect(() => {
    saveBookmarks(bookmarks);
  }, [bookmarks]);

  const isBookmarked = useCallback(
    (blockId: number) => bookmarks.some((b) => b.blockId === blockId),
    [bookmarks]
  );

  const addBookmark = useCallback((bookmark: Omit<Bookmark, 'createdAt'>) => {
    setBookmarks((prev) => {
      // Don't add duplicate
      if (prev.some((b) => b.blockId === bookmark.blockId)) {
        return prev;
      }
      return [...prev, { ...bookmark, createdAt: Date.now() }];
    });
  }, []);

  const removeBookmark = useCallback((blockId: number) => {
    setBookmarks((prev) => prev.filter((b) => b.blockId !== blockId));
  }, []);

  const toggleBookmark = useCallback(
    (bookmark: Omit<Bookmark, 'createdAt'>) => {
      if (isBookmarked(bookmark.blockId)) {
        removeBookmark(bookmark.blockId);
      } else {
        addBookmark(bookmark);
      }
    },
    [isBookmarked, removeBookmark, addBookmark]
  );

  const exportBookmarks = useCallback(() => {
    return JSON.stringify(bookmarks, null, 2);
  }, [bookmarks]);

  return (
    <BookmarksContext.Provider
      value={{
        bookmarks,
        bookmarkCount: bookmarks.length,
        isBookmarked,
        addBookmark,
        removeBookmark,
        toggleBookmark,
        exportBookmarks,
      }}
    >
      {children}
    </BookmarksContext.Provider>
  );
}
