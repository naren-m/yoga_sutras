"""Search service for full-text search across sutras.

Uses rapidfuzz for fuzzy matching across Devanagari, IAST, and English content.
"""

from rapidfuzz import fuzz, process
from app.models.text import TextBlock, TextSection
from app import db


class SearchService:
    """Service for searching across text blocks (sutras)."""

    def __init__(self):
        self._cache = None  # Cache for search corpus

    def _build_search_corpus(self):
        """Build search corpus from all text blocks.

        Returns list of tuples: (block, searchable_text, field)
        """
        if self._cache is not None:
            return self._cache

        corpus = []
        blocks = db.session.query(TextBlock).join(TextSection).all()

        for block in blocks:
            # Add Devanagari content
            if block.content:
                corpus.append({
                    'block': block,
                    'section': block.section,
                    'text': block.content,
                    'field': 'devanagari'
                })

            # Add IAST transliteration
            if block.content_transliteration:
                corpus.append({
                    'block': block,
                    'section': block.section,
                    'text': block.content_transliteration,
                    'field': 'iast'
                })

            # Add English meaning
            if block.content_meaning:
                corpus.append({
                    'block': block,
                    'section': block.section,
                    'text': block.content_meaning,
                    'field': 'english'
                })

        self._cache = corpus
        return corpus

    def search(self, query: str, limit: int = 20, min_score: int = 50) -> list:
        """Search across all text blocks.

        Args:
            query: Search query string
            limit: Maximum number of results to return
            min_score: Minimum fuzzy match score (0-100)

        Returns:
            List of search results with matched text and context
        """
        if not query or len(query.strip()) < 1:
            return []

        query = query.strip()
        corpus = self._build_search_corpus()

        # Extract searchable texts for rapidfuzz
        texts = [item['text'] for item in corpus]

        # Use rapidfuzz to find matches
        # partial_ratio is good for finding query as substring
        matches = process.extract(
            query,
            texts,
            scorer=fuzz.partial_ratio,
            limit=limit * 3,  # Get more candidates to filter later
            score_cutoff=min_score
        )

        # Build results, deduplicating by block ID
        seen_blocks = set()
        results = []

        for match_text, score, index in matches:
            item = corpus[index]
            block = item['block']

            # Skip if we've already seen this block
            if block.id in seen_blocks:
                continue
            seen_blocks.add(block.id)

            # Find match position for highlighting
            match_start = self._find_match_position(match_text.lower(), query.lower())

            # Extract context around match (for highlighting)
            context_start = max(0, match_start - 30)
            context_end = min(len(match_text), match_start + len(query) + 30)

            # Adjust to word boundaries
            if context_start > 0:
                # Find previous space
                space_pos = match_text.rfind(' ', 0, context_start)
                if space_pos != -1:
                    context_start = space_pos + 1

            if context_end < len(match_text):
                # Find next space
                space_pos = match_text.find(' ', context_end)
                if space_pos != -1:
                    context_end = space_pos

            context = match_text[context_start:context_end]
            if context_start > 0:
                context = '...' + context
            if context_end < len(match_text):
                context = context + '...'

            results.append({
                'block_id': block.id,
                'sutra_number': block.slug,  # e.g., "1.2"
                'section_slug': item['section'].slug,
                'section_title': item['section'].title,
                'match_field': item['field'],
                'match_text': context,
                'match_score': score,
                'content': block.content,
                'transliteration': block.content_transliteration,
                'meaning': block.content_meaning[:150] + '...' if block.content_meaning and len(block.content_meaning) > 150 else block.content_meaning
            })

            if len(results) >= limit:
                break

        return results

    def _find_match_position(self, text: str, query: str) -> int:
        """Find the approximate position of query in text."""
        # Direct substring search first
        pos = text.find(query)
        if pos != -1:
            return pos

        # If not found directly, find best partial match position
        # Simple approach: find the start of the most similar substring
        best_pos = 0
        best_score = 0

        for i in range(len(text) - len(query) + 1):
            substring = text[i:i + len(query)]
            score = fuzz.ratio(substring, query)
            if score > best_score:
                best_score = score
                best_pos = i

        return best_pos

    def clear_cache(self):
        """Clear the search corpus cache."""
        self._cache = None


# Singleton instance
_search_service = None


def get_search_service() -> SearchService:
    """Get or create the search service singleton."""
    global _search_service
    if _search_service is None:
        _search_service = SearchService()
    return _search_service
