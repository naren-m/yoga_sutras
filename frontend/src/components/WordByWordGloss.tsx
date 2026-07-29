import type { WordAnalysis, WordInfo } from '../types';
import { useWordSelection } from '../hooks/useWordSelection';
import { useScriptPreference } from '../hooks/useScriptPreference';

interface WordByWordGlossProps {
  analysis: WordAnalysis;
}

/**
 * Inline word-by-word gloss (padaccheda) rendered from the precomputed
 * word_analysis stored on each sutra. Shows each sandhi-resolved word with
 * its lemma, morphology and dictionary meaning — no API calls needed.
 * Clicking a card opens the full dictionary panel for that word.
 */
export default function WordByWordGloss({ analysis }: WordByWordGlossProps) {
  const { selectWord } = useWordSelection();
  const { showDevanagari } = useScriptPreference();

  if (!analysis?.words?.length) return null;

  const handleClick = (word: WordInfo, e: React.MouseEvent) => {
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
    selectWord(word.surface_devanagari || word.surface_form, {
      x: rect.left + rect.width / 2,
      y: rect.bottom,
    });
  };

  return (
    <div className="pt-4 border-t border-amber-100">
      <h3 className="text-sm font-medium text-amber-600 uppercase tracking-wide mb-3">
        Word by Word
      </h3>
      <div className="flex flex-wrap gap-2">
        {analysis.words.map((word, i) => (
          <button
            key={i}
            onClick={(e) => handleClick(word, e)}
            className="text-left bg-amber-50 hover:bg-amber-100 border border-amber-200
                       rounded-lg px-3 py-2 transition-colors max-w-[16rem]
                       focus:outline-none focus:ring-2 focus:ring-amber-400"
            title="Open dictionary"
          >
            <div className="font-serif text-lg text-amber-900 leading-snug">
              {showDevanagari ? word.surface_devanagari : word.surface_form}
            </div>
            <div className="text-xs text-amber-700 italic">
              {word.surface_form}
              {word.lemma && word.lemma !== word.surface_form && (
                <span className="text-amber-500"> → {word.lemma}</span>
              )}
            </div>
            {morphSummary(word) && (
              <div className="text-[11px] text-amber-500 mt-0.5">{morphSummary(word)}</div>
            )}
            {word.meanings?.[0] && (
              <div className="text-xs text-gray-600 mt-1 line-clamp-2">
                {word.meanings[0]}
              </div>
            )}
            {word.dhatu && (
              <div className="text-[11px] text-amber-600 mt-1">
                √{word.dhatu}
                {word.gana != null && <span> · class {word.gana}</span>}
                {word.dhatu_verified && (
                  <span title="Root attested in the Dhatupatha" className="text-green-600"> ✓</span>
                )}
                {word.dhatu_meaning && (
                  <span className="text-gray-500"> “{word.dhatu_meaning}”</span>
                )}
              </div>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}

/** Compact human-readable morphology line, e.g. "noun · nom · sg" or "verb · pres · 3rd". */
function morphSummary(word: WordInfo): string {
  const parts: string[] = [];
  if (word.is_verb) parts.push('verb');
  if (word.case) parts.push(word.case);
  if (word.gender) parts.push(word.gender);
  if (word.number) parts.push(word.number);
  if (word.tense) parts.push(word.tense);
  if (word.person) parts.push(word.person);
  return parts.join(' · ');
}
