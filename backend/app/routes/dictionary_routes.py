from flask import Blueprint, jsonify, request
from app.services.dictionary_service import DictionaryService
from app.services.sandhi_service import SandhiService

dict_bp = Blueprint('dictionary', __name__, url_prefix='/api')
dict_service = DictionaryService()
sandhi_service = SandhiService()

@dict_bp.route('/dictionary/<word>', methods=['GET'])
def lookup_word(word):
    """
    Lookup a word in all dictionaries. 
    Word should be provided in SLP1 or handled via transliteration service (todo).
    For now assuming SLP1 or matching key.
    """
    definitions = dict_service.get_definitions(word)
    return jsonify({"success": True, "data": definitions})

@dict_bp.route('/sandhi/split/<path:text>', methods=['GET'])
def split_sandhi(text):
    result = sandhi_service.split(text)
    if "error" in result:
         return jsonify({"success": False, "error": result["error"]}), 500
    return jsonify({"success": True, "data": result})
