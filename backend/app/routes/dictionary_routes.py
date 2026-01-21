from flask import Blueprint, jsonify, request
from app.services.dictionary_service import DictionaryService
from app.services.sandhi_service import SandhiService

dict_bp = Blueprint('dictionary', __name__, url_prefix='/api')
dict_service = DictionaryService()
sandhi_service = SandhiService()


@dict_bp.route('/dictionary/<path:word>', methods=['GET'])
def lookup_word(word):
    """
    Lookup a word in all dictionaries.

    Accepts word in Devanagari, IAST, or SLP1 encoding.
    Returns definitions from all dictionaries (MW, Apte).

    Query params:
        fuzzy (bool): Enable fuzzy matching (default: true)

    Returns empty array (not error) when word not found.
    """
    # Parse query params
    fuzzy = request.args.get('fuzzy', 'true').lower() != 'false'

    # Get definitions (returns empty list if not found)
    definitions = dict_service.get_definitions(word, fuzzy=fuzzy)

    return jsonify({
        "success": True,
        "data": definitions,
        "query": {
            "word": word,
            "fuzzy_enabled": fuzzy
        }
    })


@dict_bp.route('/split/<path:compound>', methods=['GET'])
def split_compound(compound):
    """
    Split a Sanskrit compound word into components using Vidyut Cheda.

    Accepts input in Devanagari, IAST, or SLP1 encoding.
    Returns splits with both Devanagari and IAST representations.

    Args:
        compound: Sanskrit compound word or phrase

    Returns:
        JSON with:
            - splits: List of token objects with text and lemma in multiple scripts
            - original: Original input with converted forms
            - engine_available: Whether Vidyut engine is initialized
    """
    result = sandhi_service.split(compound)

    return jsonify({
        "success": True,
        "data": result
    })


@dict_bp.route('/split/status', methods=['GET'])
def split_status():
    """
    Get status of the sandhi splitting service.

    Returns availability and any initialization errors.
    """
    status = sandhi_service.get_status()

    return jsonify({
        "success": True,
        "data": status
    })
