import { Link } from 'react-router-dom';
import { useBookmarks } from '../hooks/useBookmarks';

export default function BookmarksPage() {
  const { bookmarks, removeBookmark, exportBookmarks, bookmarkCount } = useBookmarks();

  // Sort by createdAt (most recent first)
  const sortedBookmarks = [...bookmarks].sort((a, b) => b.createdAt - a.createdAt);

  const handleExport = () => {
    const data = exportBookmarks();
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'yoga-sutras-bookmarks.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (bookmarkCount === 0) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-serif text-amber-900">Bookmarks</h1>

        <div className="bg-white rounded-xl shadow-sm p-8 text-center">
          <svg
            className="w-16 h-16 mx-auto text-gray-300 mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"
            />
          </svg>
          <h2 className="text-lg font-medium text-gray-600 mb-2">No bookmarks yet</h2>
          <p className="text-gray-500 mb-4">
            Click the bookmark icon on any sutra to save it for later.
          </p>
          <Link
            to="/"
            className="inline-block px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition-colors"
          >
            Browse Sutras
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-serif text-amber-900">
          Bookmarks ({bookmarkCount})
        </h1>

        <button
          onClick={handleExport}
          className="flex items-center gap-2 px-3 py-2 text-sm text-amber-700 hover:text-amber-900 hover:bg-amber-100 rounded-lg transition-colors"
          title="Export bookmarks as JSON"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
            />
          </svg>
          Export
        </button>
      </div>

      <div className="space-y-4">
        {sortedBookmarks.map((bookmark) => (
          <div
            key={bookmark.blockId}
            className="bg-white rounded-xl shadow-sm overflow-hidden"
          >
            <div className="p-4 flex items-start gap-4">
              <div className="flex-1 min-w-0">
                <Link
                  to={`/pada/${bookmark.sectionSlug}/sutra/${bookmark.sutraNumber}`}
                  className="block hover:opacity-80 transition-opacity"
                >
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-sm font-medium text-amber-600">
                      {bookmark.padaIndex + 1}.{bookmark.sutraNumber}
                    </span>
                    <span className="text-sm text-gray-500">
                      {bookmark.sectionTitle}
                    </span>
                  </div>
                  <p className="text-xl font-serif text-amber-900 truncate">
                    {bookmark.content}
                  </p>
                </Link>
              </div>

              <button
                onClick={() => removeBookmark(bookmark.blockId)}
                className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                title="Remove bookmark"
                aria-label="Remove bookmark"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>

            <div className="px-4 pb-4 pt-0">
              <p className="text-xs text-gray-400">
                Saved {new Date(bookmark.createdAt).toLocaleDateString()}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
