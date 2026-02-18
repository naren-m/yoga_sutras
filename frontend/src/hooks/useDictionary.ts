import { useQuery } from '@tanstack/react-query';
import { lookupWord } from '../services/api';

/**
 * Hook for looking up a word in the dictionary.
 * Returns entries from all available dictionaries (MW, Apte).
 */
export function useDictionary(word: string | null, fuzzy: boolean = false) {
  return useQuery({
    queryKey: ['dictionary', word, fuzzy],
    queryFn: () => lookupWord(word!, fuzzy),
    enabled: !!word,
    staleTime: 1000 * 60 * 60, // 1 hour - dictionary entries don't change
    retry: 1,
  });
}
