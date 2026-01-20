from app.models.text import Text, TextSection, TextBlock
from app import db # Assuming global db instance for now, will verify run.py later

class TextService:
    def get_all_texts(self):
        return Text.query.all()

    def get_text_by_slug(self, slug: str):
        return Text.query.filter_by(slug=slug).first()

    def get_sections_by_text(self, text_id: int):
        return TextSection.query.filter_by(text_id=text_id).order_by(TextSection.order_in_text).all()

    def get_blocks_by_section(self, section_id: int):
        return TextBlock.query.filter_by(section_id=section_id).order_by(TextBlock.order_in_section).all()

    def get_block_by_slug(self, slug: str):
        return TextBlock.query.filter_by(slug=slug).first()
