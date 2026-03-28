"""Dictionary and Sanskrit analysis routes for Yoga Sutras API.

Provides REST endpoints for dictionary lookups, sandhi splitting,
and morphological analysis using the unified sanskrit_analyzer.
"""

from flask import Blueprint, jsonify, request
from app.services.dictionary_service import DictionaryService
from app.services.sanskrit_adapter import get_sanskrit_adapter

dict_bp = Blueprint('dictionary', __name__, url_prefix='/api')
dict_service = DictionaryService()
sanskrit_adapter = get_sanskrit_adapter()


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
    Split a Sanskrit compound word into components using sanskrit_analyzer.

    Accepts input in Devanagari, IAST, or SLP1 encoding.
    Returns splits with both Devanagari and IAST representations.

    Args:
        compound: Sanskrit compound word or phrase

    Returns:
        JSON with:
            - splits: List of token objects with text and lemma in multiple scripts
            - original: Original input with converted forms
            - engine_available: Whether analyzer is initialized
    """
    result = sanskrit_adapter.split(compound)

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
    status = sanskrit_adapter.get_status()

    return jsonify({
        "success": True,
        "data": status
    })


@dict_bp.route('/morphology/<path:word>', methods=['GET'])
def get_morphology(word):
    """
    Get morphological analysis for a Sanskrit word using sanskrit_analyzer.

    Accepts word in Devanagari or IAST encoding.
    Returns grammatical analysis including lemma, case, gender, number.

    Args:
        word: Sanskrit word to analyze

    Returns:
        JSON with morphological analysis:
            - lemma: Base/dictionary form
            - unsandhied: Form after sandhi splitting
            - tag: Morphological tags (Case=X|Gender=Y|Number=Z)
            - case, gender, number: Parsed tag components
            - meanings: English meanings
            - is_verb: Whether the word is a verb form
            - dhatu: Verb root (if applicable)
            - gana: Verb class 1-10 (if applicable)
    """
    analysis = sanskrit_adapter.get_morphology_sync(word)

    if analysis is None:
        # Return empty analysis if word not recognized or service unavailable
        return jsonify({
            "success": True,
            "data": None,
            "query": {
                "word": word,
                "service_available": sanskrit_adapter.is_available()
            }
        })

    return jsonify({
        "success": True,
        "data": analysis,
        "query": {
            "word": word,
            "service_available": True
        }
    })


@dict_bp.route('/morphology/status', methods=['GET'])
def morphology_status():
    """
    Get status of the morphology analysis service.

    Returns availability of sanskrit_analyzer.
    """
    return jsonify({
        "success": True,
        "data": {
            "available": sanskrit_adapter.is_available(),
            "service": "sanskrit_analyzer"
        }
    })
