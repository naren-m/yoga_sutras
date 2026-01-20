from app.models.dictionary import Dictionary, DictionaryEntry
from app import db 
from typing import List, Dict, Any

class DictionaryService:
    def get_definitions(self, word_slp1: str) -> List[Dict[str, Any]]:
        """
        Lookup a word (SLP1) across all dictionaries.
        """
        results = db.session.query(DictionaryEntry, Dictionary).\
            join(Dictionary, DictionaryEntry.dictionary_id == Dictionary.id).\
            filter(DictionaryEntry.key == word_slp1).all()
            
        definitions = []
        for entry, dictionary in results:
            definitions.append({
                "dictionary_id": dictionary.id,
                "dictionary_title": dictionary.title,
                "dictionary_slug": dictionary.slug,
                "entry_id": entry.id,
                "key": entry.key,
                "value": entry.value # Expected to be HTML/XML payload
            })
            
        return definitions

    def get_dictionaries(self):
        return Dictionary.query.all()
