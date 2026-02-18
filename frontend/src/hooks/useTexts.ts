import { useQuery } from '@tanstack/react-query';
import { fetchTexts, fetchText, fetchSection, fetchBlock } from '../services/api';

// Fetch all texts
export function useTexts() {
  return useQuery({
    queryKey: ['texts'],
    queryFn: fetchTexts,
    staleTime: 1000 * 60 * 60, // 1 hour - text data rarely changes
  });
}

// Fetch a single text by slug
export function useText(slug: string) {
  return useQuery({
    queryKey: ['text', slug],
    queryFn: () => fetchText(slug),
    enabled: !!slug,
    staleTime: 1000 * 60 * 60,
  });
}

// Fetch a section with all its blocks
export function useSection(textSlug: string, sectionSlug: string) {
  return useQuery({
    queryKey: ['section', textSlug, sectionSlug],
    queryFn: () => fetchSection(textSlug, sectionSlug),
    enabled: !!textSlug && !!sectionSlug,
    staleTime: 1000 * 60 * 60,
  });
}

// Fetch a single block by ID
export function useBlock(textSlug: string, blockId: number) {
  return useQuery({
    queryKey: ['block', textSlug, blockId],
    queryFn: () => fetchBlock(textSlug, blockId),
    enabled: !!textSlug && !!blockId,
    staleTime: 1000 * 60 * 60,
  });
}
