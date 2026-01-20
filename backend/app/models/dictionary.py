from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.models.base import Base, pk, foreign_key

class Dictionary(Base):
    """A dictionary that maps Sanskrit expressions to definitions."""
    __tablename__ = "dictionaries"

    id = pk()
    slug = Column(String, unique=True, nullable=False) # e.g. "mw"
    title = Column(String, nullable=False)             # e.g. "Monier-Williams"

    entries = relationship("DictionaryEntry", backref="dictionary", cascade="delete")

    def to_dict(self):
        return {
            "id": self.id,
            "slug": self.slug,
            "title": self.title
        }

class DictionaryEntry(Base):
    """Dictionary definitions for a specific entry key."""
    __tablename__ = "dictionary_entries"

    id = pk()
    dictionary_id = foreign_key("dictionaries.id")
    key = Column(String, index=True, nullable=False) # Standardized lookup key (SLP1)
    value = Column(String, nullable=False)           # XML/HTML payload

    def to_dict(self):
        return {
            "id": self.id,
            "key": self.key,
            "value": self.value,
            "dictionary_id": self.dictionary_id
        }
