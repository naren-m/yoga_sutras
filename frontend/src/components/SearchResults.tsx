import { Link } from 'react-router-dom';
import type { SearchResult } from '../types';

interface SearchResultsProps {
  results: SearchResult[];
  query: string;
  isLoading: boolean;
  isEmpty: boolean;
  onResultClick?: () => void;
}

export default function SearchResults({
  results,
  query,
  isLoading,
  isEmpty,
  onResultClick,
}: SearchResultsProps) {
  if (isLoading) {
    return (
      <div className="p-4 text-center text-amber-700">
        <div className="animate-pulse">Searching...</div>
      </div>
    );
  }

  if (isEmpty) {
    return (
      <div className="p-4 text-center text-amber-700">
        <p className="text-sm">No results found for "{query}"</p>
        <p className="text-xs mt-1 text-amber-500">Try searching in Sanskrit (Devanagari/IAST) or English</p>
      </div>
    );
  }

  if (results.length === 0) {
    return null;
  }

  // Helper to highlight matching text
  const highlightMatch = (text: string, searchQuery: string) => {
    if (!searchQuery) return text;

    // Simple case-insensitive highlight
    const regex = new RegExp(`(${searchQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    const parts = text.split(regex);

    return parts.map((part, i) =>
      regex.test(part) ? (
        <mark key={i} className="bg-amber-300 text-amber-900 rounded px-0.5">
          {part}
        </mark>
      ) : (
        part
      )
    );
  };

  // Get field label
  const getFieldLabel = (field: string) => {
    switch (field) {
      case 'devanagari':
        return 'Sanskrit';
      case 'iast':
        return 'Transliteration';
      case 'english':
        return 'Translation';
      default:
        return field;
    }
  };

  return (
    <div className="divide-y divide-amber-200">
      {results.map((result) => (
        <Link
          key={result.block_id}
          to={`/pada/${result.section_slug}/sutra/${result.sutra_number.split('.')[1]}`}
          onClick={onResultClick}
          className="block p-3 hover:bg-amber-100 transition-colors"
        >
          <div className="flex items-start gap-3">
            {/* Sutra number badge */}
            <span className="flex-shrink-0 px-2 py-1 text-xs font-semibold bg-amber-200 text-amber-800 rounded">
              {result.sutra_number}
            </span>

            <div className="flex-1 min-w-0">
              {/* Section title */}
              <p className="text-xs text-amber-600 mb-1">{result.section_title}</p>

              {/* Match context with highlight */}
              <p className="text-sm text-amber-900">
                {highlightMatch(result.match_text, query)}
              </p>

              {/* Match field indicator */}
              <p className="text-xs text-amber-500 mt-1">
                Matched in: {getFieldLabel(result.match_field)}
              </p>

              {/* Preview of Devanagari if match was in English */}
              {result.match_field === 'english' && result.content && (
                <p className="text-sm font-serif text-amber-700 mt-1 truncate">
                  {result.content}
                </p>
              )}
            </div>
          </div>
        </Link>
      ))}
    </div>
  );
}
