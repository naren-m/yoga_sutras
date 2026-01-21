import { useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useSection } from '../hooks/useTexts';
import { PADAS } from '../types';
import ClickableText from '../components/ClickableText';
import BookmarkButton from '../components/BookmarkButton';
import { useScriptPreference } from '../hooks/useScriptPreference';

export default function SutraPage() {
  const { padaSlug, sutraNumber } = useParams<{ padaSlug: string; sutraNumber: string }>();
  const navigate = useNavigate();
  const { data: section, isLoading, error } = useSection('yoga-sutras', padaSlug || '');
  const [commentaryOpen, setCommentaryOpen] = useState(false);
  const { showDevanagari, showIast } = useScriptPreference();

  const padaIndex = PADAS.findIndex((p) => p.slug === padaSlug);
  const sutraNum = parseInt(sutraNumber || '1', 10);

  // Find current sutra in the section
  const currentSutra = section?.blocks?.find((b) => b.order === sutraNum);
  const sutraIndex = section?.blocks?.findIndex((b) => b.order === sutraNum) ?? -1;

  // Navigation
  const prevSutra = sutraIndex > 0 ? section?.blocks?.[sutraIndex - 1] : null;
  const nextSutra = section?.blocks && sutraIndex < section.blocks.length - 1
    ? section.blocks[sutraIndex + 1]
    : null;

  // Find previous and next pada
  const prevPada = padaIndex > 0 ? PADAS[padaIndex - 1] : null;
  const nextPada = padaIndex < PADAS.length - 1 ? PADAS[padaIndex + 1] : null;

  // Keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowLeft' && prevSutra) {
      navigate(`/pada/${padaSlug}/sutra/${prevSutra.order}`);
    } else if (e.key === 'ArrowRight' && nextSutra) {
      navigate(`/pada/${padaSlug}/sutra/${nextSutra.order}`);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-amber-600">Loading sutra...</div>
      </div>
    );
  }

  if (error || !section || !currentSutra) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
        <p className="text-red-700">Sutra not found.</p>
        <Link to={`/pada/${padaSlug}`} className="text-amber-600 hover:underline mt-2 inline-block">
          ← Back to {PADAS[padaIndex]?.title || 'Pada'}
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6" onKeyDown={handleKeyDown} tabIndex={0}>
      {/* Breadcrumb */}
      <nav className="text-sm text-amber-600">
        <Link to="/" className="hover:underline">Home</Link>
        {' / '}
        <Link to={`/pada/${padaSlug}`} className="hover:underline">
          {section.title}
        </Link>
        {' / '}
        <span className="text-amber-800">Sutra {padaIndex + 1}.{sutraNum}</span>
      </nav>

      {/* Sutra content */}
      <article className="bg-white rounded-xl shadow-sm overflow-hidden">
        {/* Header */}
        <div className="bg-amber-100 px-6 py-4 flex items-start justify-between">
          <div>
            <h2 className="text-lg font-medium text-amber-900">
              Sutra {padaIndex + 1}.{sutraNum}
            </h2>
            <p className="text-amber-700 text-sm">{section.title}</p>
          </div>
          <BookmarkButton
            blockId={currentSutra.id}
            sectionSlug={padaSlug || ''}
            sectionTitle={section.title}
            sutraNumber={sutraNum}
            padaIndex={padaIndex}
            content={currentSutra.content}
          />
        </div>

        {/* Sanskrit text */}
        <div className="p-6 space-y-6">
          {/* Devanagari - with clickable words */}
          {showDevanagari && (
            <div>
              <p className="text-3xl md:text-4xl font-serif text-amber-900 leading-relaxed">
                <ClickableText text={currentSutra.content} />
              </p>
              <p className="text-xs text-gray-400 mt-2">
                Click any word to look it up in the dictionary
              </p>
            </div>
          )}

          {/* Transliteration (IAST) */}
          {showIast && (
            <div>
              <p className={`text-amber-700 italic ${showDevanagari ? 'text-xl' : 'text-2xl md:text-3xl'}`}>
                {currentSutra.content_transliteration}
              </p>
            </div>
          )}

          {/* Meaning */}
          <div className="pt-4 border-t border-amber-100">
            <h3 className="text-sm font-medium text-amber-600 uppercase tracking-wide mb-2">
              Meaning
            </h3>
            <p className="text-gray-700 leading-relaxed">
              {currentSutra.content_meaning}
            </p>
          </div>

          {/* Commentary (collapsible) */}
          {currentSutra.commentary && (
            <div className="pt-4 border-t border-amber-100">
              <button
                onClick={() => setCommentaryOpen(!commentaryOpen)}
                className="flex items-center gap-2 text-sm font-medium text-amber-600 uppercase tracking-wide hover:text-amber-800 transition-colors w-full text-left"
              >
                <svg
                  className={`w-4 h-4 transition-transform ${commentaryOpen ? 'rotate-90' : ''}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
                Commentary
              </button>
              {commentaryOpen && (
                <p className="text-gray-600 leading-relaxed mt-3 pl-6">
                  {currentSutra.commentary}
                </p>
              )}
            </div>
          )}
        </div>
      </article>

      {/* Navigation buttons */}
      <div className="flex items-center justify-between gap-4">
        {/* Previous */}
        <div className="flex-1">
          {prevSutra ? (
            <Link
              to={`/pada/${padaSlug}/sutra/${prevSutra.order}`}
              className="flex items-center gap-2 text-amber-600 hover:text-amber-800 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              <div className="text-left">
                <div className="text-sm">Previous</div>
                <div className="text-xs text-amber-500">{padaIndex + 1}.{prevSutra.order}</div>
              </div>
            </Link>
          ) : prevPada ? (
            <Link
              to={`/pada/${prevPada.slug}`}
              className="flex items-center gap-2 text-amber-600 hover:text-amber-800 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              <div className="text-left">
                <div className="text-sm">Previous Pada</div>
                <div className="text-xs text-amber-500">{prevPada.title}</div>
              </div>
            </Link>
          ) : (
            <div />
          )}
        </div>

        {/* Back to list */}
        <Link
          to={`/pada/${padaSlug}`}
          className="px-4 py-2 bg-amber-100 text-amber-700 rounded-lg hover:bg-amber-200 transition-colors text-sm"
        >
          All Sutras
        </Link>

        {/* Next */}
        <div className="flex-1 flex justify-end">
          {nextSutra ? (
            <Link
              to={`/pada/${padaSlug}/sutra/${nextSutra.order}`}
              className="flex items-center gap-2 text-amber-600 hover:text-amber-800 transition-colors"
            >
              <div className="text-right">
                <div className="text-sm">Next</div>
                <div className="text-xs text-amber-500">{padaIndex + 1}.{nextSutra.order}</div>
              </div>
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          ) : nextPada ? (
            <Link
              to={`/pada/${nextPada.slug}`}
              className="flex items-center gap-2 text-amber-600 hover:text-amber-800 transition-colors"
            >
              <div className="text-right">
                <div className="text-sm">Next Pada</div>
                <div className="text-xs text-amber-500">{nextPada.title}</div>
              </div>
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          ) : (
            <div />
          )}
        </div>
      </div>

      {/* Keyboard hint */}
      <p className="text-center text-gray-400 text-xs">
        Use ← → arrow keys to navigate between sutras
      </p>
    </div>
  );
}
