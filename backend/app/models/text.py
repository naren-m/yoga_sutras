from sqlalchemy import Column, String, Integer, Text as SQLText, JSON
from sqlalchemy.orm import relationship
from app.models.base import Base, pk, foreign_key

class Text(Base):
    """Represents a complete work (e.g., 'Yoga Sutras', 'Ramayana')."""
    __tablename__ = 'texts'
    
    id = pk()
    slug = Column(String, unique=True, index=True, nullable=False) # e.g. "yoga-sutras"
    title = Column(String, nullable=False)
    description = Column(SQLText)
    
    sections = relationship("TextSection", backref="text", cascade="delete")

    def to_dict(self):
        return {
            "id": self.id,
            "slug": self.slug,
            "title": self.title,
            "description": self.description,
            "sections": [s.to_dict() for s in self.sections]
        }

class TextSection(Base):
    """A division within a text (e.g., 'Pada', 'Kanda', 'Chapter')."""
    __tablename__ = 'text_sections'
    
    id = pk()
    text_id = foreign_key("texts.id")
    slug = Column(String, nullable=False) # e.g. "1", "samadhi-pada"
    title = Column(String, nullable=False)
    order_in_text = Column(Integer, nullable=False)
    
    blocks = relationship("TextBlock", backref="section", cascade="delete")

    def to_dict(self):
         return {
            "id": self.id,
            "slug": self.slug,
            "title": self.title,
            "order": self.order_in_text
        }

class TextBlock(Base):
    """The atomic unit of content (e.g., a single Sutra, Sloka, or Verse)."""
    __tablename__ = 'text_blocks'
    
    id = pk()
    text_id = foreign_key("texts.id")
    section_id = foreign_key("text_sections.id")
    
    slug = Column(String, nullable=False) # e.g. "1.2"
    order_in_section = Column(Integer, nullable=False)
    
    # Core Content
    content = Column(SQLText, nullable=False)         # Devanagari
    content_transliteration = Column(SQLText)         # IAST
    content_meaning = Column(SQLText)                 # English Translation
    
    # Analysis & Metadata
    commentary = Column(SQLText)                      # Optional commentary
    word_analysis = Column(JSON)                   # {"words": [...], "sandhi": ...}
    validations = Column(JSON)                     # {"meter": "anushtubh", ...}

    def to_dict(self):
        return {
            "id": self.id,
            "slug": self.slug,
             "order": self.order_in_section,
            "content": self.content,
            "transliteration": self.content_transliteration,
            "meaning": self.content_meaning,
            "commentary": self.commentary,
            "word_analysis": self.word_analysis
        }
