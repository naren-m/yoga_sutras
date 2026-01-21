import { useQuery } from '@tanstack/react-query';
import { useState, useEffect } from 'react';
import { searchSutras } from '../services/api';

/**
 * Hook for debounced search across sutras.
 *
 * @param initialQuery - Initial search query
 * @param debounceMs - Debounce delay in milliseconds (default 300ms)
 */
export function useSearch(initialQuery: string = '', debounceMs: number = 300) {
  const [query, setQuery] = useState(initialQuery);
  const [debouncedQuery, setDebouncedQuery] = useState(initialQuery);

  // Debounce the query
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(query);
    }, debounceMs);

    return () => clearTimeout(timer);
  }, [query, debounceMs]);

  // React Query for search results
  const {
    data,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['search', debouncedQuery],
    queryFn: () => searchSutras(debouncedQuery),
    enabled: debouncedQuery.length > 0,
    staleTime: 60000, // Cache for 1 minute
  });

  return {
    query,
    setQuery,
    debouncedQuery,
    results: data?.data ?? [],
    count: data?.count ?? 0,
    isLoading: isLoading && debouncedQuery.length > 0,
    isError,
    error,
    isEmpty: debouncedQuery.length > 0 && !isLoading && data?.data.length === 0,
  };
}
