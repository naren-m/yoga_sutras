from app.models.text import Text, TextSection, TextBlock
from app import db

class TextService:
    """Service for querying Text, TextSection, and TextBlock models.

    Uses Flask-SQLAlchemy v3 query style: db.session.query(Model) instead of Model.query
    """

    def get_all_texts(self):
        """Returns all texts with metadata (without loading sections for performance)."""
        return db.session.query(Text).all()

    def get_text_by_slug(self, slug: str):
        """Returns a single text by slug, or None if not found."""
        return db.session.query(Text).filter_by(slug=slug).first()

    def get_sections_by_text(self, text_id: int):
        """Returns all sections for a text, ordered by order_in_text."""
        return db.session.query(TextSection).filter_by(text_id=text_id).order_by(TextSection.order_in_text).all()

    def get_section_by_slug(self, text_id: int, section_slug: str):
        """Returns a single section by text_id and section_slug, or None if not found."""
        return db.session.query(TextSection).filter_by(text_id=text_id, slug=section_slug).first()

    def get_blocks_by_section(self, section_id: int):
        """Returns all blocks for a section, ordered by order_in_section."""
        return db.session.query(TextBlock).filter_by(section_id=section_id).order_by(TextBlock.order_in_section).all()

    def get_block_by_id(self, block_id: int):
        """Returns a single block by ID, or None if not found."""
        return db.session.query(TextBlock).filter_by(id=block_id).first()

    def get_block_by_slug(self, slug: str):
        """Returns a single block by slug (e.g., '1.2'), or None if not found."""
        return db.session.query(TextBlock).filter_by(slug=slug).first()
