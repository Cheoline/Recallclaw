from .database import RecallClawDB
from .lac_engine import LACEngine
from .validator import SemanticJudge
from .llm_connector import LLMConnector
from .evolver import Evolver
from .daemon import SubconsciousDaemon
from .sync_engine import SyncEngine

class PositronicBrain:
    def __init__(self, db_path: str = "positronic_brain.db", max_usage_limit: int = 1000):
        self.db = RecallClawDB(db_path=db_path, max_usage_limit=max_usage_limit)
        self.lac = LACEngine()
        self.judge = SemanticJudge()
        self.llm = LLMConnector()
        self.evolver = Evolver(self)
        self.daemon = SubconsciousDaemon(self)
        self.colmena = SyncEngine(self)

    def start_background_evolution(self, check_interval_hours: float = 24.0):
        """Activa el daemon que ejecuta el sueño automáticamente en segundo plano."""
        self.daemon.check_interval_seconds = check_interval_hours * 3600
        self.daemon.start()

    def stop_background_evolution(self):
        """Detiene el daemon de sueño automático."""
        self.daemon.stop()

    def sleep_cycle(self):
        """Dispara el proceso de mantenimiento de la memoria (El Evolucionador)."""
        self.evolver.sleep_cycle()

    def memorize(self, text: str, context: str = None, auto_context: bool = True) -> dict:
        """
        Procesa un texto en español, lo comprime a formato LAC, y lo guarda en el grafo relacional.
        Se puede proveer un `context` explícito, o dejar que el motor infiera uno (auto_context)
        para evitar interferencias semánticas tras los ciclos de sueño.
        """
        # Solución a Interferencia Semántica: Marcador de contexto automático
        if context:
            text = f"[CONTEXTO: {context}] {text}"
        elif auto_context and text.strip():
            palabras = text.split()
            contexto_breve = " ".join(palabras[:5])
            text = f"[CONTEXTO: {contexto_breve}] {text}"

        print(f"[*] Inyectando recuerdo original: '{text}'")
        
        # 0. Generar Hash Semántico (Embedding Matemático)
        semantic_hash_bytes = None
        if self.judge.model is not None:
            tensor = self.judge.model.encode(text)
            semantic_hash_bytes = tensor.tobytes()
        
        # 1. Compresión LAC (Semántica y Fonética)
        tokens = self.lac.compress(text)
        print(f"[*] Compresión Atómica (LAC): {' '.join(tokens)}")
        
        # 2. Guardar en Base de Datos (Deduplicación de Nodos)
        memory_id = self.db.save_memory(original_text=text, tokens=tokens, semantic_hash=semantic_hash_bytes)
        
        return {
            "memory_id": memory_id,
            "compressed_tokens": tokens,
            "compression_ratio": f"{100 - (len(' '.join(tokens)) / len(text) * 100):.1f}%" if len(text) > 0 else "0%"
        }

    def recall(self, memory_id: int) -> dict:
        """
        Recupera un recuerdo desde el grafo usando su ID.
        (La fase 2 pasará esto por un LLM para rehidratar el lenguaje).
        """
        original, tokens = self.db.get_memory(memory_id)
        if original is None and not tokens:
            return {"error": "Memoria no encontrada"}
            
        return {
            "memory_id": memory_id,
            "reconstructed_lac": " ".join(tokens),
            "original_text": original
        }

    def ask(self, question: str) -> str:
        """
        El Bibliotecario: Busca en la base de datos la respuesta a una pregunta y la responde en lenguaje natural fluido.
        """
        print(f"[*] El Bibliotecario está analizando la pregunta: '{question}'")
        
        # 1. Obtener todos los hashes de la base de datos (Recuerdos)
        all_hashes = self.db.get_all_memory_hashes()
        
        # Si no hay recuerdos, el Bibliotecario consulta el LEXICON como diccionario
        if not all_hashes:
            return self._ask_lexicon(question)
            
        # 2. Buscar la memoria más relevante (RAG Vectorial)
        best_matches = self.judge.search_best_memory(question, all_hashes, top_k=1)
        if not best_matches:
            # También fallback al Lexicon si no hay coincidencias
            return self._ask_lexicon(question)
            
        score, memory_id = best_matches[0]
        print(f"[*] Recuerdo más relevante encontrado: ID {memory_id} (Similitud: {score:.2f})")
        
        # 3. Extraer la memoria (Puede ser el texto original o los tokens si ya fue consolidada)
        memoria_recuperada = self.recall(memory_id)
        if "error" in memoria_recuperada:
            return "Hubo un error al extraer la memoria de los engramas."
            
        texto_crudo = memoria_recuperada["original_text"]
        if not texto_crudo:
            texto_crudo = memoria_recuperada["reconstructed_lac"]
            print(f"[*] El Bibliotecario está leyendo una memoria consolidada: {texto_crudo}")
        
        # 4. Formular el prompt para el LLM
        prompt = f"""Instrucciones estrictas:
- Responde en español únicamente con la información del recuerdo.
- NO escribas frases como 'La respuesta es:', 'Según el recuerdo:', ni ningún encabezado o introducción.
- NO pongas nada después de la respuesta.
- Si el recuerdo tiene códigos técnicos cortos, interprétalos como conceptos de seguridad o redes.
- Si la respuesta no está en el recuerdo, responde solo: 'No tengo esa información.'

Recuerdo: {texto_crudo}
Pregunta: {question}
Respuesta directa:"""

        # 5. Generar respuesta fluida
        print("[*] Reconstruyendo respuesta con LLM local...")
        respuesta = self.llm.generate_response(prompt)
        
        return respuesta

    def _ask_lexicon(self, question: str) -> str:
        """
        Modo Diccionario: Cuando no hay recuerdos guardados, el Bibliotecario
        busca en el Lexicon por similitud semántica del Hash y explica el token encontrado.
        """
        import numpy as np
        import torch
        from sentence_transformers import util

        print("[*] No hay recuerdos aún. Consultando el Diccionario (Lexicon) de la Colmena...")

        # Buscar tokens en el Lexicon que tengan Hash Semántico
        with self.db._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT token, semantic_hash FROM Lexicon WHERE semantic_hash IS NOT NULL")
            lexicon_data = cursor.fetchall()

        if not lexicon_data:
            return "El cerebro positrónico no tiene recuerdos ni diccionario semántico disponible."

        # Convertir la pregunta a vector
        question_tensor = self.judge.model.encode(question, convert_to_tensor=True)

        mejor_token = None
        mejor_similitud = -1.0

        for token, s_hash in lexicon_data:
            token_tensor = torch.tensor(np.frombuffer(s_hash, dtype=np.float32)).to(question_tensor.device)
            sim = float(util.cos_sim(question_tensor, token_tensor)[0][0])
            if sim > mejor_similitud:
                mejor_similitud = sim
                mejor_token = token

        if not mejor_token or mejor_similitud < 0.3:
            return "No encontré ninguna palabra en mi diccionario relacionada con esa pregunta."

        print(f"[*] Palabra más relevante en el Diccionario: '{mejor_token}' (Similitud: {mejor_similitud:.2f})")

        prompt = f"""Instrucciones estrictas:
- Responde en español con una explicación directa y concisa.
- El token '{mejor_token}' es una forma comprimida de un concepto real.
- NO escribas introducciones, etiquetas, saludos ni nada antes o después de la respuesta.
- Si no puedes interpretarlo, responde solo: 'No tengo esa información.'

Pregunta: {question}
Respuesta directa:"""

        print("[*] Reconstruyendo respuesta desde el Diccionario...")
        return self.llm.generate_response(prompt)
