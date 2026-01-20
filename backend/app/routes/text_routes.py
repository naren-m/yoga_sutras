from flask import Blueprint, jsonify, request
from app.services.text_service import TextService

text_bp = Blueprint('texts', __name__, url_prefix='/api')
service = TextService()

@text_bp.route('/texts', methods=['GET'])
def get_texts():
    texts = service.get_all_texts()
    return jsonify({"success": True, "data": [t.to_dict() for t in texts]})

@text_bp.route('/texts/<slug>', methods=['GET'])
def get_text(slug):
    text = service.get_text_by_slug(slug)
    if not text:
        return jsonify({"success": False, "error": "Text not found"}), 404
    return jsonify({"success": True, "data": text.to_dict()})

@text_bp.route('/texts/<slug>/sections', methods=['GET'])
def get_sections(slug):
    text = service.get_text_by_slug(slug)
    if not text:
        return jsonify({"success": False, "error": "Text not found"}), 404
    sections = service.get_sections_by_text(text.id)
    return jsonify({"success": True, "data": [s.to_dict() for s in sections]})

@text_bp.route('/sections/<int:section_id>/blocks', methods=['GET'])
def get_blocks(section_id):
    blocks = service.get_blocks_by_section(section_id)
    return jsonify({"success": True, "data": [b.to_dict() for b in blocks]})
