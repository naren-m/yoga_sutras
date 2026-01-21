import { Outlet, NavLink, Link } from 'react-router-dom';
import { useState, useRef, useEffect } from 'react';
import { PADAS } from '../types';
import DictionaryPanel from './DictionaryPanel';
import SearchInput from './SearchInput';
import SearchResults from './SearchResults';
import { useSearch } from '../hooks/useSearch';

export default function Layout() {
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const { query, setQuery, results, isLoading, isEmpty } = useSearch();
  const searchContainerRef = useRef<HTMLDivElement>(null);

  // Close search dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchContainerRef.current && !searchContainerRef.current.contains(event.target as Node)) {
        setIsSearchOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Close search dropdown on Escape
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsSearchOpen(false);
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, []);

  const handleResultClick = () => {
    setIsSearchOpen(false);
    setQuery('');
  };

  return (
    <div className="min-h-screen bg-amber-50">
      {/* Header */}
      <header className="bg-gradient-to-r from-amber-800 to-amber-900 text-amber-50 shadow-lg">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
            <Link to="/" className="block">
              <h1 className="text-2xl md:text-3xl font-serif">Yoga Sutras of Patanjali</h1>
              <p className="text-amber-200 text-sm mt-1">Sanskrit Reading Platform</p>
            </Link>

            {/* Search input */}
            <div ref={searchContainerRef} className="relative w-full md:w-72">
              <SearchInput
                value={query}
                onChange={setQuery}
                onFocus={() => setIsSearchOpen(true)}
                placeholder="Search sutras..."
              />

              {/* Search results dropdown */}
              {isSearchOpen && (query.length > 0 || isLoading) && (
                <div className="absolute top-full left-0 right-0 mt-1 bg-white rounded-lg shadow-xl border border-amber-200 max-h-96 overflow-y-auto z-50">
                  <SearchResults
                    results={results}
                    query={query}
                    isLoading={isLoading}
                    isEmpty={isEmpty}
                    onResultClick={handleResultClick}
                  />
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Navigation tabs */}
        <nav className="max-w-6xl mx-auto px-4">
          <ul className="flex overflow-x-auto gap-1 pb-1 -mb-px">
            <li>
              <NavLink
                to="/"
                end
                className={({ isActive }) =>
                  `block px-4 py-2 rounded-t-lg text-sm font-medium transition-colors whitespace-nowrap ${
                    isActive
                      ? 'bg-amber-50 text-amber-900'
                      : 'text-amber-200 hover:text-amber-50 hover:bg-amber-700/50'
                  }`
                }
              >
                Home
              </NavLink>
            </li>
            {PADAS.map((pada) => (
              <li key={pada.slug}>
                <NavLink
                  to={`/pada/${pada.slug}`}
                  className={({ isActive }) =>
                    `block px-4 py-2 rounded-t-lg text-sm font-medium transition-colors whitespace-nowrap ${
                      isActive
                        ? 'bg-amber-50 text-amber-900'
                        : 'text-amber-200 hover:text-amber-50 hover:bg-amber-700/50'
                    }`
                  }
                >
                  {pada.title.replace(' Pada', '')}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
      </header>

      {/* Main content */}
      <main className="max-w-6xl mx-auto px-4 py-6">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="bg-amber-900 text-amber-200 py-6 mt-8">
        <div className="max-w-6xl mx-auto px-4 text-center text-sm">
          <p>योगश्चित्तवृत्तिनिरोधः</p>
          <p className="mt-1 text-amber-400">Yoga is the cessation of the fluctuations of the mind</p>
        </div>
      </footer>

      {/* Dictionary panel - slides in when a word is selected */}
      <DictionaryPanel />
    </div>
  );
}
