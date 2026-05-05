import re

try:
    import spacy
    nlp = spacy.load("es_core_news_sm")
    print("[LAC] Spacy cargado con éxito para análisis morfológico avanzado.")
except ImportError:
    nlp = None
    print("[LAC] Spacy no instalado. Usando heurística básica.")
except OSError:
    nlp = None
    print("[LAC] Modelo 'es_core_news_sm' no encontrado. Usando heurística básica.")

class LACEngine:
    """
    Motor de Lenguaje Atómico de Compresión (LAC).
    Aplica daño gramatical y compresión semántica por reglas y NLP.
    """
    def __init__(self):
        # Mapeo de conectores lógicos de 1 carácter
        self.connectors = {
            r'\bque\b': '#',
            r'\bporque\b': '>',
            r'\bpor tanto\b': '>',
            r'\bpero\b': '|',
            r'\ben\b': '@',
            r'\ba\b': '@',
            r'\bhacia\b': '@',
            r'\bde\b': '$',
            r'\bmi\b': '$',
            r'\bsu\b': '$',
            r'\bpara\b': '^',
            r'\bsi\b': '?',
            r'\by\b': '&'
        }

        # Palabras a eliminar completamente (artículos)
        self.stop_words = [
            r'\bel\b', r'\bla\b', r'\blos\b', r'\blas\b', 
            r'\bun\b', r'\buna\b', r'\bunos\b', r'\bunas\b'
        ]

    def _apply_phonetic_damage(self, word: str) -> str:
        """Aplica las reglas ortográficas de súper bajo nivel a una palabra."""
        if len(word) == 1 and not word.isalpha():
            return word
            
        w = word.lower()
        w = w.replace('qu', 'k')
        w = w.replace('ll', 'y')
        w = w.replace('ch', 'x')
        w = w.replace('h', '')
        w = w.replace('z', 's')
        w = w.replace('gue', 'ge')
        w = w.replace('gui', 'gi')
        return w

    def compress(self, text: str) -> list[str]:
        """
        Toma texto en español normal y lo convierte en una secuencia de tokens LAC.
        Utiliza NLP si está disponible para asignar etiquetas M/F precisas a sustantivos.
        """
        # 1. Si tenemos Spacy, hacemos un pre-análisis de las palabras para extraer su género
        word_genders = {}
        if nlp is not None:
            doc = nlp(text)
            for token in doc:
                # Solo taggeamos sustantivos y adjetivos
                if token.pos_ in ["NOUN", "ADJ", "PRON"]:
                    gender = token.morph.get("Gender")
                    if gender:
                        word_genders[token.text.lower()] = "M" if "Masc" in gender else "F"

        text_lower = text.lower()

        # 2. Reemplazar conectores lógicos
        for pattern, symbol in self.connectors.items():
            text_lower = re.sub(pattern, symbol, text_lower)

        # 3. Eliminar artículos
        for stop_word in self.stop_words:
            text_lower = re.sub(stop_word, '', text_lower)

        text_lower = re.sub(r'\s+', ' ', text_lower).strip()
        raw_tokens = text_lower.split(' ')
        compressed_tokens = []
        
        for token in raw_tokens:
            clean_token = re.sub(r'[^\w\s#>|@$\^?&]', '', token)
            if not clean_token:
                continue
                
            damaged = self._apply_phonetic_damage(clean_token)
            
            # 4. Asignar etiqueta de género precisa
            if damaged not in self.connectors.values():
                # Buscar si Spacy encontró el género para la palabra original
                # Es una heurística básica de emparejamiento, asumimos que clean_token es similar al original
                assigned_gender = ""
                for orig_word, gen in word_genders.items():
                    if orig_word.startswith(clean_token) or clean_token.startswith(orig_word[:3]):
                        assigned_gender = gen
                        break
                        
                if assigned_gender:
                    damaged = damaged + assigned_gender
                else:
                    # Fallback heurístico si Spacy no lo encontró o no está instalado
                    if clean_token.endswith('o') or clean_token.endswith('os'):
                        damaged = damaged.rstrip('os') + 'M'
                    elif clean_token.endswith('a') or clean_token.endswith('as'):
                        damaged = damaged.rstrip('as') + 'F'
                        
            compressed_tokens.append(damaged)

        return compressed_tokens
