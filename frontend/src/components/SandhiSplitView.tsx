import { useScriptPreference } from '../hooks/useScriptPreference';
import type { SandhiSplitToken } from '../types';

interface SandhiSplitViewProps {
  /** The original compound word in Devanagari */
  originalDevanagari: string;
  /** The original compound word in IAST */
  originalIast: string;
  /** Array of split tokens */
  splits: SandhiSplitToken[];
  /** Callback when a split component is clicked for dictionary lookup */
  onComponentClick: (word: string) => void;
  /** Callback to view full compound in dictionary (unsplit) */
  onViewFullCompound: () => void;
  /** Whether this is a true compound (more than 1 component) */
  isCompound: boolean;
}

/**
 * Displays sandhi split results with clickable components.
 * Shows the original compound above the split visualization.
 * Respects script preference settings.
 */
export default function SandhiSplitView({
  originalDevanagari,
  originalIast,
  splits,
  onComponentClick,
  onViewFullCompound,
  isCompound,
}: SandhiSplitViewProps) {
  const { showDevanagari, showIast } = useScriptPreference();

  if (!isCompound) {
    // Not a compound - just show the word directly
    return null;
  }

  return (
    <div className="bg-amber-50 rounded-lg p-4 border border-amber-200 mb-4">
      {/* Original compound */}
      <div className="mb-3">
        <p className="text-xs text-amber-600 uppercase tracking-wide mb-1">
          Compound Word
        </p>
        <div className="flex items-baseline gap-2 flex-wrap">
          {showDevanagari && (
            <span className="text-xl font-serif text-amber-900">{originalDevanagari}</span>
          )}
          {showIast && (
            <span className={`text-gray-500 font-mono ${showDevanagari ? 'text-sm' : 'text-lg'}`}>
              {originalIast}
            </span>
          )}
        </div>
      </div>

      {/* Split visualization */}
      <div className="mb-3">
        <p className="text-xs text-amber-600 uppercase tracking-wide mb-2">
          Split Components
        </p>
        <div className="flex flex-wrap items-center gap-1">
          {splits.map((token, index) => (
            <span key={index} className="flex items-center">
              {index > 0 && (
                <span className="text-amber-400 mx-1 font-bold">+</span>
              )}
              <button
                // Use lemma for dictionary lookup if available, otherwise use text
                onClick={() => onComponentClick(token.lemma_devanagari || token.text_devanagari)}
                className="group px-2 py-1 bg-white rounded border border-amber-200 hover:border-amber-400 hover:bg-amber-100 transition-colors"
                title={`Look up "${token.lemma_iast || token.text_iast}" in dictionary`}
              >
                {showDevanagari && (
                  <span className="font-serif text-amber-800 group-hover:text-amber-900">
                    {token.text_devanagari}
                  </span>
                )}
                {showIast && (
                  <span className={`text-gray-400 font-mono ${showDevanagari ? 'text-xs ml-1' : 'text-sm'}`}>
                    {token.text_iast}
                  </span>
                )}
                {showIast && token.lemma_iast && token.lemma_iast !== token.text_iast && (
                  <span className="text-xs text-amber-600 ml-1">
                    ({token.lemma_iast})
                  </span>
                )}
              </button>
              {/* Sandhi type indicator on the right */}
              {token.sandhi_type && (
                <span
                  className="ml-1 px-1.5 py-0.5 text-[10px] bg-purple-100 text-purple-700 rounded border border-purple-200"
                  title={`${token.sandhi_type.description}: ${token.sandhi_type.rule}`}
                >
                  {token.sandhi_type.name}
                </span>
              )}
            </span>
          ))}
        </div>
      </div>

      {/* Hint about clicking */}
      <p className="text-xs text-gray-500 mb-3">
        Click any component above to look it up in the dictionary
      </p>

      {/* View full compound option */}
      <button
        onClick={onViewFullCompound}
        className="text-sm text-amber-700 hover:text-amber-900 underline underline-offset-2"
      >
        View dictionary entry for full compound
      </button>
    </div>
  );
}

/**
 * Indicator badge showing that a word is a compound.
 * Can be used inline with clickable words.
 */
export function CompoundIndicator({ isCompound }: { isCompound: boolean }) {
  if (!isCompound) return null;

  return (
    <span
      className="inline-block w-2 h-2 bg-amber-400 rounded-full ml-1"
      title="This is a compound word - click to see split"
      aria-label="Compound word indicator"
    />
  );
}
