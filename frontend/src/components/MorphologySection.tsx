import type { MorphologyAnalysis } from '../types';

interface MorphologySectionProps {
  morphology: MorphologyAnalysis | null;
  isLoading: boolean;
}

/**
 * Displays grammatical analysis for a Sanskrit word.
 * Shows lemma, case, gender, number, and verb-specific info.
 */
export default function MorphologySection({ morphology, isLoading }: MorphologySectionProps) {
  if (isLoading) {
    return (
      <section className="mb-4 pb-4 border-b border-gray-200">
        <div className="flex items-center gap-2 text-amber-600">
          <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <span className="text-sm">Analyzing grammar...</span>
        </div>
      </section>
    );
  }

  if (!morphology) {
    return null; // Hide section if no analysis available
  }

  // Build list of grammar properties to display
  const grammarItems: { label: string; value: string }[] = [];

  // Always show lemma if different from surface form
  if (morphology.lemma && morphology.lemma !== morphology.surface_form) {
    grammarItems.push({ label: 'Root Form', value: morphology.lemma });
  }

  // Noun/adjective properties
  if (morphology.case) {
    grammarItems.push({ label: 'Case', value: morphology.case });
  }
  if (morphology.gender) {
    grammarItems.push({ label: 'Gender', value: morphology.gender });
  }
  if (morphology.number) {
    grammarItems.push({ label: 'Number', value: morphology.number });
  }

  // Verb properties
  if (morphology.is_verb) {
    if (morphology.person) {
      grammarItems.push({ label: 'Person', value: morphology.person });
    }
    if (morphology.tense) {
      grammarItems.push({ label: 'Tense', value: morphology.tense });
    }
    if (morphology.voice) {
      grammarItems.push({ label: 'Voice', value: morphology.voice });
    }
  }

  // If no grammar items, don't show the section
  if (grammarItems.length === 0) {
    return null;
  }

  return (
    <section className="mb-4 pb-4 border-b border-gray-200">
      <div className="flex items-center gap-2 mb-3">
        <svg className="w-4 h-4 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <h3 className="text-sm font-semibold text-amber-700 uppercase tracking-wide">
          Grammar
        </h3>
        {morphology.is_verb && (
          <span className="text-xs bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded">verb</span>
        )}
      </div>

      <div className="grid grid-cols-2 gap-2">
        {grammarItems.map(({ label, value }) => (
          <div key={label} className="bg-amber-50/50 rounded px-2 py-1.5">
            <span className="text-xs text-gray-500 block">{label}</span>
            <span className="text-sm text-gray-800 font-medium">{value}</span>
          </div>
        ))}
      </div>

      {/* Dharmamitra meanings if available */}
      {morphology.meanings && morphology.meanings.length > 0 && (
        <div className="mt-3 bg-amber-50/50 rounded px-2 py-1.5">
          <span className="text-xs text-gray-500 block mb-1">Meanings</span>
          <p className="text-sm text-gray-800">
            {morphology.meanings.slice(0, 3).join('; ')}
            {morphology.meanings.length > 3 && (
              <span className="text-gray-500"> (+{morphology.meanings.length - 3} more)</span>
            )}
          </p>
        </div>
      )}
    </section>
  );
}
