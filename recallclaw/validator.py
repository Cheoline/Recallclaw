try:
    from sentence_transformers import SentenceTransformer, util
except ImportError:
    SentenceTransformer = None

class SemanticJudge:
    """
    Juez Semántico de RecallClaw.
    Utiliza embeddings matemáticos para realizar la Verificación Cruzada.
    """
    def __init__(self, model_name: str = 'paraphrase-multilingual-MiniLM-L12-v2'):
        self.model_name = model_name
        self.model = None
        self._load_model()

    def _load_model(self):
        if SentenceTransformer is None:
            print("[JUEZ] ADVERTENCIA: La librería 'sentence-transformers' no está instalada.")
            print("[JUEZ] Ejecuta: pip install sentence-transformers")
            return
            
        print(f"[JUEZ] Cargando modelo matemático de lenguaje: {self.model_name}...")
        # Este modelo es ideal porque entiende español y es ligero
        self.model = SentenceTransformer(self.model_name)
        print("[JUEZ] Modelo cargado. Listo para validación.")

    def verify_integrity(self, original_text: str, reconstructed_text: str, threshold: float = 0.85) -> dict:
        """
        Compara matemáticamente el texto original con la versión reconstruida a partir del LAC.
        Si el significado es idéntico (supera el threshold), aprueba la compresión.
        """
        if self.model is None:
            return {
                "approved": False,
                "similarity_score": 0.0,
                "error": "Modelo no cargado. Instala sentence-transformers."
            }

        # Generar vectores matemáticos (Embeddings) para ambas frases
        embedding_original = self.model.encode(original_text, convert_to_tensor=True)
        embedding_reconstructed = self.model.encode(reconstructed_text, convert_to_tensor=True)

        # Calcular la similitud del coseno (Cosine Similarity)
        # 1.0 significa significado idéntico, 0.0 significa nada que ver.
        cosine_scores = util.cos_sim(embedding_original, embedding_reconstructed)
        similarity = float(cosine_scores[0][0])

        approved = similarity >= threshold
        
        status = "APROBADO" if approved else "RECHAZADO"
        print(f"[JUEZ] Verificación: {status} (Similitud: {similarity:.2f} | Requerido: {threshold})")

        return {
            "approved": approved,
            "similarity_score": similarity,
            "threshold": threshold
        }

    def search_best_memory(self, query: str, memory_hashes: list, top_k: int = 1) -> list:
        """
        Busca las memorias más relevantes para una pregunta dada.
        memory_hashes es una lista de tuplas (memory_id, hash_bytes).
        """
        if self.model is None or not memory_hashes:
            return []

        try:
            import numpy as np
            import torch
        except ImportError:
            print("[JUEZ] Error: numpy o torch no instalados.")
            return []

        # Vectorizar la pregunta
        query_embedding = self.model.encode(query, convert_to_tensor=True)

        results = []
        for memory_id, hash_bytes in memory_hashes:
            # Reconstruir el vector desde los bytes
            mem_array = np.frombuffer(hash_bytes, dtype=np.float32)
            mem_tensor = torch.tensor(mem_array).to(query_embedding.device)
            
            # Calcular similitud
            cos_sim = util.cos_sim(query_embedding, mem_tensor)
            score = float(cos_sim[0][0])
            results.append((score, memory_id))

        # Ordenar por mayor similitud
        results.sort(key=lambda x: x[0], reverse=True)
        return results[:top_k]

