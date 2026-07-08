import axios from 'axios';
import type { ApiResponse, Text, TextSection, TextBlock, DictionaryEntry, SandhiSplitResponse, SearchResult, MorphologyAnalysis, MorphologyResponse } from '../types';

// Backend API base URL - configurable via environment variable.
// Defaults to same-origin '/api' so production (behind the ingress that routes
// /api -> backend) never points a visitor's browser at localhost. Dev uses the
// Vite proxy (see vite.config.ts) so relative '/api' works there too.
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

// Text APIs
export async function fetchTexts(): Promise<Text[]> {
  const response = await api.get<ApiResponse<Text[]>>('/texts');
  if (!response.data.success) {
    throw new Error(response.data.error || 'Failed to fetch texts');
  }
  return response.data.data;
}

export async function fetchText(slug: string): Promise<Text> {
  const response = await api.get<ApiResponse<Text>>(`/texts/${slug}`);
  if (!response.data.success) {
    throw new Error(response.data.error || 'Failed to fetch text');
  }
  return response.data.data;
}

export async function fetchSection(textSlug: string, sectionSlug: string): Promise<TextSection> {
  const response = await api.get<ApiResponse<TextSection>>(`/texts/${textSlug}/section/${sectionSlug}`);
  if (!response.data.success) {
    throw new Error(response.data.error || 'Failed to fetch section');
  }
  return response.data.data;
}

export async function fetchBlock(textSlug: string, blockId: number): Promise<TextBlock> {
  const response = await api.get<ApiResponse<TextBlock>>(`/texts/${textSlug}/block/${blockId}`);
  if (!response.data.success) {
    throw new Error(response.data.error || 'Failed to fetch block');
  }
  return response.data.data;
}

// Dictionary APIs
export async function lookupWord(word: string, fuzzy: boolean = false): Promise<DictionaryEntry[]> {
  const response = await api.get<ApiResponse<DictionaryEntry[]>>(`/dictionary/${encodeURIComponent(word)}`, {
    params: fuzzy ? { fuzzy: 'true' } : undefined,
  });
  if (!response.data.success) {
    throw new Error(response.data.error || 'Failed to lookup word');
  }
  return response.data.data;
}

// Sandhi splitting APIs
export async function splitWord(compound: string): Promise<SandhiSplitResponse> {
  const response = await api.get<ApiResponse<SandhiSplitResponse>>(`/split/${encodeURIComponent(compound)}`);
  if (!response.data.success) {
    throw new Error(response.data.error || 'Failed to split word');
  }
  return response.data.data;
}

// Morphology APIs
export async function fetchMorphology(word: string): Promise<MorphologyAnalysis | null> {
  const response = await api.get<MorphologyResponse>(`/morphology/${encodeURIComponent(word)}`);
  return response.data.data;
}

// Search API
export async function searchSutras(query: string, limit?: number): Promise<{ data: SearchResult[]; query: string; count: number }> {
  const response = await api.get<ApiResponse<SearchResult[]> & { query: string; count: number }>('/search', {
    params: { q: query, ...(limit ? { limit } : {}) },
  });
  if (!response.data.success) {
    throw new Error(response.data.error || 'Search failed');
  }
  return {
    data: response.data.data,
    query: response.data.query,
    count: response.data.count,
  };
}

export default api;
