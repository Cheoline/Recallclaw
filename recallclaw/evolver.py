import time
import re
from typing import List

class Evolver:
    """
    El "Sueño" de la IA.
    Proceso en segundo plano que optimiza el almacenamiento aplicando
    consolidación, degradación agresiva por refuerzo, y olvido.
    """
    def __init__(self, brain):
        self.brain = brain
        self.db = brain.db
        self.judge = brain.judge
        self.llm = brain.llm
        
    def _agressive_compress(self, tokens: List[str], current_level: int) -> List[str]:
        """Aplica un daño progresivo a los tokens LAC."""
        # Mientras mayor el nivel, palabras más cortas son atacadas
        # Nivel 0 -> Ataca > 6 chars
        # Nivel 1 -> Ataca > 5 chars
        # Nivel 2 -> Ataca > 4 chars
        # Nivel 3+ -> Ataca > 3 chars
        threshold = max(3, 6 - current_level)
        
        new_tokens = []
        for token in tokens:
            # Si es un símbolo lógico o muy corto, no lo tocamos
            if len(token) <= threshold or not token.isalpha():
                new_tokens.append(token)
                continue
                
            # Eliminar todas las vocales (excepto la primera letra si es vocal)
            first_char = token[0]
            rest = re.sub(r'[aeiouAEIOUáéíóúÁÉÍÓÚ]', '', token[1:])
            compressed = first_char + rest
            
            # Asegurar que no quede vacío
            if not compressed:
                compressed = token
                
            new_tokens.append(compressed)
            
        return new_tokens

    def sleep_cycle(self):
        """
        Ejecuta los ciclos de mantenimiento de memoria.
        Normalmente esto se llamaría cuando la IA está inactiva ("durmiendo").
        """
        print("[EVOLVER] Iniciando ciclo de sueño profundo...")
            
        # --- NIVEL 1: CONSOLIDACIÓN (>7 días) ---
        memories_to_consolidate = self.db.get_memories_older_than(days=7)
        for mem in memories_to_consolidate:
            if mem['original_text'] is not None:
                print(f"[EVOLVER] Nivel 1: Consolidando ID {mem['id']}. Borrando texto original para ahorrar espacio.")
                self.db.delete_original_text(mem['id'])

        # --- NIVEL 2: DEGRADACIÓN AGRESIVA (>30 días) ---
        memories_to_degrade = self.db.get_memories_older_than(days=30)
        for mem in memories_to_degrade:
            # Solo intentamos degradar si aún tenemos el hash semántico para verificar
            if not mem['semantic_hash']:
                continue
                
            mem_id = mem['id']
            current_level = mem.get('compression_level', 0)
            
            # Obtener tokens actuales (Esto actualiza el last_recalled a 'now')
            _, current_tokens = self.db.get_memory(mem_id)
            
            # Generar versión agresiva basada en el nivel actual
            super_compressed = self._agressive_compress(current_tokens, current_level)
            
            # Si no hubo cambios, saltar
            if super_compressed == current_tokens:
                continue
                
            print(f"[EVOLVER] Nivel 2: Probando degradación progresiva (Nivel {current_level+1}) en ID {mem_id}...")
            
            # Pedirle al LLM que intente reconstruir desde los tokens súper rotos
            prompt = f"""Instrucciones estrictas:
- Reconstruye una sola oración en español a partir de estos conceptos comprimidos.
- NO escribas introducciones, explicaciones, comentarios ni texto en inglés.
- Devuelve ÚNICAMENTE la oración reconstruida, nada más.

Conceptos: {' '.join(super_compressed)}
Oración:"""
            reconstruction = self.llm.generate_response(prompt)
            print(f"  -> [DEBUG] LLM reconstruyó: '{reconstruction}'")
            
            # Usar al Juez Semántico para ver si el LLM logró entender el significado
            # Simulamos el vector original pasando los bytes
            import numpy as np
            import torch
            from sentence_transformers import util
            
            mem_array = np.frombuffer(mem['semantic_hash'], dtype=np.float32)
            original_tensor = torch.tensor(mem_array)
            
            new_tensor = self.judge.model.encode(reconstruction, convert_to_tensor=True)
            
            cos_sim = util.cos_sim(original_tensor.to(new_tensor.device), new_tensor)
            similarity = float(cos_sim[0][0])
            
            if similarity >= 0.85:
                print(f"  -> Éxito. El significado sobrevivió (Similitud: {similarity:.2f}). Guardando Nivel {current_level+1}.")
                self.db.update_memory_sequence(mem_id, super_compressed, current_level + 1)
            else:
                print(f"  -> Fracaso. Pérdida semántica (Similitud: {similarity:.2f}). Se revierte el daño.")
                
        print("[EVOLVER] Ciclo de sueño finalizado.")
