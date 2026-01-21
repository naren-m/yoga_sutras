// API Response types
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  error?: string;
}

// Text model types
export interface Text {
  id: number;
  slug: string;
  title: string;
  description: string;
  sections?: TextSection[];
}

export interface TextSection {
  id: number;
  slug: string;
  title: string;
  order: number;
  text_id: number;
  blocks?: TextBlock[];
}

export interface TextBlock {
  id: number;
  content: string;
  content_transliteration: string;
  content_meaning: string;
  word_analysis: WordAnalysis | null;
  commentary: string | null;
  order: number;
  section_id: number;
}

export interface WordAnalysis {
  words: WordInfo[];
}

export interface WordInfo {
  original: string;
  base_form: string;
  meaning?: string;
}

// Dictionary types
export interface DictionaryEntry {
  dictionary_code: string;
  dictionary_name: string;
  key: string;
  key_devanagari: string;
  key_iast: string;
  definition: string;
  is_fuzzy_match: boolean;
}

// Sandhi split types
export interface SandhiSplitToken {
  text: string;
  text_devanagari: string;
  text_iast: string;
  lemma: string | null;
  lemma_devanagari: string | null;
  lemma_iast: string | null;
}

export interface SandhiSplitResponse {
  original: string;
  original_devanagari: string;
  original_iast: string;
  original_slp1: string;
  splits: SandhiSplitToken[];
  engine_available: boolean;
  engine_error: string | null;
}

// Navigation types
export interface PadaInfo {
  slug: string;
  title: string;
  description: string;
  sutraCount: number;
}

// Pada metadata
export const PADAS: PadaInfo[] = [
  {
    slug: 'samadhi-pada',
    title: 'Samadhi Pada',
    description: 'The chapter on contemplation, covering the nature and goal of yoga.',
    sutraCount: 51,
  },
  {
    slug: 'sadhana-pada',
    title: 'Sadhana Pada',
    description: 'The chapter on practice, outlining the eight limbs of yoga.',
    sutraCount: 55,
  },
  {
    slug: 'vibhuti-pada',
    title: 'Vibhuti Pada',
    description: 'The chapter on powers, describing the attainments from yoga practice.',
    sutraCount: 56,
  },
  {
    slug: 'kaivalya-pada',
    title: 'Kaivalya Pada',
    description: 'The chapter on liberation, explaining the nature of liberation.',
    sutraCount: 34,
  },
];
