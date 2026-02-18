import { useParams, Link } from 'react-router-dom';
import { useSection } from '../hooks/useTexts';
import { PADAS } from '../types';

export default function PadaPage() {
  const { padaSlug } = useParams<{ padaSlug: string }>();
  const { data: section, isLoading, error } = useSection('yoga-sutras', padaSlug || '');

  const padaInfo = PADAS.find((p) => p.slug === padaSlug);
  const padaIndex = PADAS.findIndex((p) => p.slug === padaSlug);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-amber-600">Loading sutras...</div>
      </div>
    );
  }

  if (error || !section) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
        <p className="text-red-700">Failed to load section. Please try again.</p>
        <p className="text-red-500 text-sm mt-2">{error?.message}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl p-6 shadow-sm">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-full bg-amber-100 flex items-center justify-center text-amber-800 font-serif text-2xl flex-shrink-0">
            {padaIndex + 1}
          </div>
          <div>
            <h2 className="text-2xl font-serif text-amber-900">{section.title}</h2>
            {padaInfo && (
              <p className="text-gray-600 mt-1">{padaInfo.description}</p>
            )}
          </div>
        </div>
      </div>

      {/* Sutras list */}
      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <div className="divide-y divide-amber-100">
          {section.blocks?.map((block) => (
            <Link
              key={block.id}
              to={`/pada/${padaSlug}/sutra/${block.order}`}
              className="block p-4 hover:bg-amber-50 transition-colors"
            >
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center text-amber-700 font-medium flex-shrink-0">
                  {padaIndex + 1}.{block.order}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-lg font-serif text-amber-900 truncate">
                    {block.content}
                  </p>
                  <p className="text-sm text-amber-600 truncate mt-1">
                    {block.content_transliteration}
                  </p>
                  <p className="text-sm text-gray-500 truncate mt-1">
                    {block.content_meaning}
                  </p>
                </div>
                <div className="text-amber-400 flex-shrink-0">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Pagination info */}
      <div className="text-center text-amber-600 text-sm">
        {section.blocks?.length || 0} sutras in {section.title}
      </div>
    </div>
  );
}
