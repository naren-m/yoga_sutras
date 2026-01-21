import { createContext } from 'react';

/**
 * Available script display options:
 * - 'devanagari': Show only Devanagari script
 * - 'iast': Show only IAST (Roman) transliteration
 * - 'both': Show both Devanagari and IAST (default)
 */
export type ScriptPreference = 'devanagari' | 'iast' | 'both';

export interface ScriptPreferenceContextType {
  /** Current script preference */
  preference: ScriptPreference;
  /** Update the script preference */
  setPreference: (preference: ScriptPreference) => void;
  /** Convenience boolean for checking if Devanagari should be shown */
  showDevanagari: boolean;
  /** Convenience boolean for checking if IAST should be shown */
  showIast: boolean;
}

export const ScriptPreferenceContext = createContext<ScriptPreferenceContextType | undefined>(undefined);
