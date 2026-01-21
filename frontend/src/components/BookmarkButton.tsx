import { useBookmarks } from '../hooks/useBookmarks';
import type { Bookmark } from '../contexts/bookmarksTypes';

interface BookmarkButtonProps {
  blockId: number;
  sectionSlug: string;
  sectionTitle: string;
  sutraNumber: number;
  padaIndex: number;
  content: string;
}

export default function BookmarkButton({
  blockId,
  sectionSlug,
  sectionTitle,
  sutraNumber,
  padaIndex,
  content,
}: BookmarkButtonProps) {
  const { isBookmarked, toggleBookmark } = useBookmarks();
  const bookmarked = isBookmarked(blockId);

  const handleClick = () => {
    const bookmark: Omit<Bookmark, 'createdAt'> = {
      blockId,
      sectionSlug,
      sectionTitle,
      sutraNumber,
      padaIndex,
      content,
    };
    toggleBookmark(bookmark);
  };

  return (
    <button
      onClick={handleClick}
      className={`p-2 rounded-lg transition-colors ${
        bookmarked
          ? 'text-amber-600 hover:text-amber-700 bg-amber-100 hover:bg-amber-200'
          : 'text-gray-400 hover:text-amber-600 hover:bg-amber-50'
      }`}
      title={bookmarked ? 'Remove bookmark' : 'Add bookmark'}
      aria-label={bookmarked ? 'Remove bookmark' : 'Add bookmark'}
    >
      {bookmarked ? (
        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
          <path d="M5 5c0-1.1.9-2 2-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
        </svg>
      ) : (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"
          />
        </svg>
      )}
    </button>
  );
}
