import type { MorphologyAnalysis } from '../types';

interface DhatuSectionProps {
  morphology: MorphologyAnalysis | null;
  onDhatuClick: (dhatu: string) => void;
}

// Gana names in Sanskrit tradition
const GANA_NAMES: Record<number, string> = {
  1: 'Bhvādi (1st)',
  2: 'Adādi (2nd)',
  3: 'Juhotyādi (3rd)',
  4: 'Divādi (4th)',
  5: 'Svādi (5th)',
  6: 'Tudādi (6th)',
  7: 'Rudhādi (7th)',
  8: 'Tanādi (8th)',
  9: 'Kryādi (9th)',
  10: 'Curādi (10th)',
};

/**
 * Displays verb root (dhatu) information with clickable link to dictionary.
 * Only shown for verb forms.
 */
export default function DhatuSection({ morphology, onDhatuClick }: DhatuSectionProps) {
  // Only show for verbs with dhatu
  if (!morphology || !morphology.is_verb || !morphology.dhatu) {
    return null;
  }

  const ganaName = morphology.gana ? GANA_NAMES[morphology.gana] : null;

  return (
    <section className="mb-4 pb-4 border-b border-gray-200">
      <div className="flex items-center gap-2 mb-3">
        <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
        <h3 className="text-sm font-semibold text-blue-700 uppercase tracking-wide">
          Verb Root
        </h3>
      </div>

      <div className="bg-blue-50/50 rounded-lg p-3 border border-blue-100">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs text-gray-500 mb-1">Dhatu (Root)</p>
            <button
              onClick={() => onDhatuClick(morphology.dhatu!)}
              className="text-lg font-serif text-blue-700 hover:text-blue-900 hover:underline cursor-pointer flex items-center gap-1 transition-colors"
              title="Look up in dictionary"
            >
              {morphology.dhatu}
              <svg className="w-3.5 h-3.5 opacity-60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
            </button>
          </div>

          {ganaName && (
            <div className="text-right">
              <p className="text-xs text-gray-500 mb-1">Verb Class</p>
              <p className="text-sm text-blue-800 font-medium">{ganaName}</p>
            </div>
          )}
        </div>

        {/* Show meanings from Dharmamitra if available */}
        {morphology.meanings && morphology.meanings.length > 0 && (
          <div className="mt-2 pt-2 border-t border-blue-100">
            <p className="text-xs text-gray-500 mb-1">Root Meaning</p>
            <p className="text-sm text-gray-700">
              {morphology.meanings.slice(0, 2).join('; ')}
            </p>
          </div>
        )}
      </div>
    </section>
  );
}
