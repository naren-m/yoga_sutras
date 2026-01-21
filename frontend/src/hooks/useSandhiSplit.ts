import { useQuery } from '@tanstack/react-query';
import { splitWord } from '../services/api';

/**
 * Hook for splitting a compound Sanskrit word into its components.
 * Uses Vidyut Cheda for sandhi analysis.
 *
 * Returns the original word and an array of split tokens with:
 * - text (inflected form as it appears)
 * - lemma (base form for dictionary lookup, may be null)
 */
export function useSandhiSplit(word: string | null) {
  return useQuery({
    queryKey: ['sandhiSplit', word],
    queryFn: () => splitWord(word!),
    enabled: !!word,
    staleTime: 1000 * 60 * 60, // 1 hour - splits don't change
    retry: 1,
  });
}
