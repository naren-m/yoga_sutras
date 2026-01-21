import { useEffect } from 'react';
import { useWordSelection } from '../hooks/useWordSelection';
import { useDictionary } from '../hooks/useDictionary';
import type { DictionaryEntry } from '../types';

/**
 * Dictionary panel that slides in from the right on desktop,
 * and appears as a bottom sheet on mobile.
 * Shows definitions from Monier-Williams and Apte dictionaries.
 */
export default function DictionaryPanel() {
  const { selectedWord, clearSelection } = useWordSelection();
  const { data: entries, isLoading, error } = useDictionary(selectedWord?.word ?? null);

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        clearSelection();
      }
    };

    if (selectedWord) {
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [selectedWord, clearSelection]);

  // Don't render if no word selected
  if (!selectedWord) {
    return null;
  }

  // Group entries by dictionary
  const mwEntries = entries?.filter((e) => e.dictionary_code === 'mw') ?? [];
  const apteEntries = entries?.filter((e) => e.dictionary_code === 'apte') ?? [];

  return (
    <>
      {/* Backdrop for mobile */}
      <div
        className="fixed inset-0 bg-black/30 z-40 md:hidden"
        onClick={clearSelection}
        aria-hidden="true"
      />

      {/* Panel */}
      <aside
        className={`
          fixed z-50 bg-white shadow-xl overflow-hidden
          transition-transform duration-300 ease-out

          /* Mobile: bottom sheet */
          inset-x-0 bottom-0 h-[70vh] rounded-t-2xl
          transform ${selectedWord ? 'translate-y-0' : 'translate-y-full'}

          /* Desktop: right sidebar */
          md:inset-y-0 md:right-0 md:left-auto md:bottom-auto
          md:w-96 md:h-full md:rounded-none md:rounded-l-xl
          md:transform md:${selectedWord ? 'translate-x-0' : 'translate-x-full'}
        `}
        role="complementary"
        aria-label="Dictionary definitions"
      >
        {/* Header */}
        <header className="bg-amber-100 px-4 py-3 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-serif text-amber-900">
              {selectedWord.word}
            </h2>
            <p className="text-sm text-amber-600">Dictionary Lookup</p>
          </div>
          <button
            onClick={clearSelection}
            className="p-2 hover:bg-amber-200 rounded-full transition-colors"
            aria-label="Close dictionary panel"
          >
            <svg className="w-6 h-6 text-amber-800" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </header>

        {/* Content */}
        <div className="p-4 overflow-y-auto h-[calc(100%-4rem)]">
          {/* Loading state */}
          {isLoading && (
            <div className="flex items-center justify-center py-12">
              <div className="flex items-center gap-3 text-amber-600">
                <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                <span>Looking up word...</span>
              </div>
            </div>
          )}

          {/* Error state */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
              <p>Failed to look up word. Please try again.</p>
            </div>
          )}

          {/* Not found state */}
          {!isLoading && !error && entries && entries.length === 0 && (
            <div className="text-center py-12">
              <svg className="w-12 h-12 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
              <p className="text-gray-500 mb-2">No definition found for</p>
              <p className="text-xl font-serif text-gray-700">{selectedWord.word}</p>
              <p className="text-sm text-gray-400 mt-4">
                Try clicking on a different word or the word may be a compound.
              </p>
            </div>
          )}

          {/* Dictionary entries */}
          {!isLoading && !error && entries && entries.length > 0 && (
            <div className="space-y-6">
              {/* Monier-Williams */}
              {mwEntries.length > 0 && (
                <DictionarySection
                  title="Monier-Williams"
                  subtitle="Sanskrit-English Dictionary"
                  entries={mwEntries}
                />
              )}

              {/* Apte */}
              {apteEntries.length > 0 && (
                <DictionarySection
                  title="Apte"
                  subtitle="Practical Sanskrit-English Dictionary"
                  entries={apteEntries}
                />
              )}
            </div>
          )}
        </div>

        {/* Mobile drag handle indicator */}
        <div className="absolute top-2 left-1/2 -translate-x-1/2 w-12 h-1 bg-gray-300 rounded-full md:hidden" />
      </aside>
    </>
  );
}

/**
 * Section component for displaying entries from a single dictionary.
 */
function DictionarySection({
  title,
  subtitle,
  entries,
}: {
  title: string;
  subtitle: string;
  entries: DictionaryEntry[];
}) {
  return (
    <section>
      <div className="mb-3">
        <h3 className="text-sm font-semibold text-amber-700 uppercase tracking-wide">
          {title}
        </h3>
        <p className="text-xs text-gray-400">{subtitle}</p>
      </div>
      <div className="space-y-3">
        {entries.map((entry, index) => (
          <DefinitionEntry key={`${entry.dictionary_code}-${entry.key}-${index}`} entry={entry} />
        ))}
      </div>
    </section>
  );
}

/**
 * Individual definition entry with formatted content.
 * Shows key in IAST and definition as plain text.
 */
function DefinitionEntry({ entry }: { entry: DictionaryEntry }) {
  return (
    <div className="bg-amber-50/50 rounded-lg p-3 border border-amber-100">
      <div className="flex items-baseline gap-2 mb-1">
        <span className="text-sm font-serif text-amber-800">{entry.key_devanagari}</span>
        <span className="text-xs text-gray-400 font-mono">{entry.key_iast}</span>
        {entry.is_fuzzy_match && (
          <span className="text-xs bg-amber-200 text-amber-700 px-1.5 rounded">fuzzy</span>
        )}
      </div>
      <p className="text-gray-700 text-sm leading-relaxed whitespace-pre-wrap">
        {entry.definition}
      </p>
    </div>
  );
}
