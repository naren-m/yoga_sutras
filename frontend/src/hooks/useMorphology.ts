import { useQuery } from '@tanstack/react-query';
import { fetchMorphology } from '../services/api';

/**
 * Hook for fetching morphological analysis for a Sanskrit word.
 * Uses Dharmamitra ByT5 model for grammar analysis.
 *
 * Returns lemma, case, gender, number, meanings, and verb info (dhatu, gana).
 */
export function useMorphology(word: string | null) {
  return useQuery({
    queryKey: ['morphology', word],
    queryFn: () => fetchMorphology(word!),
    enabled: !!word,
    staleTime: 1000 * 60 * 60, // 1 hour - morphology doesn't change
    retry: 1,
  });
}
