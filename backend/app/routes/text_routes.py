from flask import Blueprint, jsonify, request
from app.services.text_service import TextService
from app.services.search_service import get_search_service

text_bp = Blueprint('texts', __name__, url_prefix='/api')
service = TextService()


@text_bp.route('/texts', methods=['GET'])
def get_texts():
    """GET /api/texts - Returns list of all texts with metadata."""
    texts = service.get_all_texts()
    # Return texts without sections for list view (performance)
    return jsonify({
        "success": True,
        "data": [{
            "id": t.id,
            "slug": t.slug,
            "title": t.title,
            "description": t.description
        } for t in texts]
    })


@text_bp.route('/texts/<slug>', methods=['GET'])
def get_text(slug):
    """GET /api/texts/{slug} - Returns full text with sections (without blocks for performance)."""
    text = service.get_text_by_slug(slug)
    if not text:
        return jsonify({"success": False, "error": "Text not found"}), 404

    # Include sections but NOT blocks (for performance)
    sections = service.get_sections_by_text(text.id)
    return jsonify({
        "success": True,
        "data": {
            "id": text.id,
            "slug": text.slug,
            "title": text.title,
            "description": text.description,
            "sections": [s.to_dict() for s in sections]
        }
    })


@text_bp.route('/texts/<slug>/section/<section_slug>', methods=['GET'])
def get_section(slug, section_slug):
    """GET /api/texts/{slug}/section/{section_slug} - Returns section with all blocks."""
    text = service.get_text_by_slug(slug)
    if not text:
        return jsonify({"success": False, "error": "Text not found"}), 404

    section = service.get_section_by_slug(text.id, section_slug)
    if not section:
        return jsonify({"success": False, "error": "Section not found"}), 404

    blocks = service.get_blocks_by_section(section.id)
    return jsonify({
        "success": True,
        "data": {
            "id": section.id,
            "slug": section.slug,
            "title": section.title,
            "order": section.order_in_text,
            "blocks": [b.to_dict() for b in blocks]
        }
    })


@text_bp.route('/texts/<slug>/block/<int:block_id>', methods=['GET'])
def get_block(slug, block_id):
    """GET /api/texts/{slug}/block/{block_id} - Returns single block with full details."""
    text = service.get_text_by_slug(slug)
    if not text:
        return jsonify({"success": False, "error": "Text not found"}), 404

    block = service.get_block_by_id(block_id)
    if not block or block.text_id != text.id:
        return jsonify({"success": False, "error": "Block not found"}), 404

    return jsonify({
        "success": True,
        "data": block.to_dict()
    })


@text_bp.route('/search', methods=['GET'])
def search():
    """GET /api/search?q={query} - Full-text search across all sutras.

    Query params:
        q: Search query string (required)
        limit: Maximum results (default 20)
    """
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({
            "success": True,
            "data": [],
            "query": ""
        })

    limit = request.args.get('limit', 20, type=int)
    limit = min(max(1, limit), 50)  # Clamp between 1 and 50

    search_service = get_search_service()
    results = search_service.search(query, limit=limit)

    return jsonify({
        "success": True,
        "data": results,
        "query": query,
        "count": len(results)
    })
