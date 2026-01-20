try:
    from vidyut.cheda import Cheda
except ImportError:
    Cheda = None

class SandhiService:
    def __init__(self, data_path: str = "data/vidyut-data"):
        self.cheda = None
        if Cheda:
            try:
                self.cheda = Cheda(data_path)
            except Exception as e:
                print(f"Failed to initialize Vidyut Cheda: {e}")
    
    def split(self, text: str):
        """
        Split a sandhied string into components.
        """
        if not self.cheda:
            return {"error": "Sandhi engine not initialized"}
        
        # Hypothetical API for verify: cheda.split(text) -> list of results
        try:
            results = self.cheda.split(text)
            return {"splits": results}
        except Exception as e:
            return {"error": str(e)}
