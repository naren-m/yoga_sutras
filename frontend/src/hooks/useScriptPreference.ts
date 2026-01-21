import { useContext } from 'react';
import { ScriptPreferenceContext, type ScriptPreferenceContextType } from '../contexts/scriptPreferenceTypes';

export function useScriptPreference(): ScriptPreferenceContextType {
  const context = useContext(ScriptPreferenceContext);
  if (context === undefined) {
    throw new Error('useScriptPreference must be used within a ScriptPreferenceProvider');
  }
  return context;
}
