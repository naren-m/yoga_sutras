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

@dict_bp.route('/sandhi/split/<path:text>', methods=['GET'])
def split_sandhi(text):
    result = sandhi_service.split(text)
    if "error" in result:
         return jsonify({"success": False, "error": result["error"]}), 500
    return jsonify({"success": True, "data": result})
