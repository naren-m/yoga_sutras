import { useState, useCallback, useEffect, useMemo, type ReactNode } from 'react';
import { ScriptPreferenceContext, type ScriptPreference } from './scriptPreferenceTypes';

const STORAGE_KEY = 'yoga-sutras-script-preference';
const DEFAULT_PREFERENCE: ScriptPreference = 'both';

function loadPreference(): ScriptPreference {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored && ['devanagari', 'iast', 'both'].includes(stored)) {
      return stored as ScriptPreference;
    }
  } catch (e) {
    console.error('Failed to load script preference from localStorage:', e);
  }
  return DEFAULT_PREFERENCE;
}

function savePreference(preference: ScriptPreference): void {
  try {
    localStorage.setItem(STORAGE_KEY, preference);
  } catch (e) {
    console.error('Failed to save script preference to localStorage:', e);
  }
}

export function ScriptPreferenceProvider({ children }: { children: ReactNode }) {
  const [preference, setPreferenceState] = useState<ScriptPreference>(() => loadPreference());

  // Persist preference to localStorage whenever it changes
  useEffect(() => {
    savePreference(preference);
  }, [preference]);

  const setPreference = useCallback((newPreference: ScriptPreference) => {
    setPreferenceState(newPreference);
  }, []);

  // Compute convenience booleans
  const showDevanagari = useMemo(() => preference === 'devanagari' || preference === 'both', [preference]);
  const showIast = useMemo(() => preference === 'iast' || preference === 'both', [preference]);

  return (
    <ScriptPreferenceContext.Provider
      value={{
        preference,
        setPreference,
        showDevanagari,
        showIast,
      }}
    >
      {children}
    </ScriptPreferenceContext.Provider>
  );
}
