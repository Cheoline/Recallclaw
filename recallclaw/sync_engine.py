import json
import hashlib
import os

class SyncEngine:
    """
    La Colmena (Aprendizaje Federado).
    Se encarga de sincronizar el Diccionario (Lexicon) con otras IAs,
    asegurando la criptografía para evitar envenenamiento de datos.
    ¡NUNCA sincroniza recuerdos (Memories), solo reglas de compresión!
    """
    def __init__(self, brain):
        self.db = brain.db

    def _generate_hash(self, token: str) -> str:
        """Genera una firma SHA-256 para un token."""
        # Se usa una semilla (salt) o formato específico si se desea mayor seguridad.
        # Por ahora usamos SHA-256 estándar del string.
        return hashlib.sha256(token.encode('utf-8')).hexdigest()

    def export_lexicon(self, filepath: str = "colmena_export.json"):
        """
        Extrae tokens consolidados de la IA para compartirlos con el mundo.
        Solo exporta tokens muy usados (is_sealed = 1) o de alto valor.
        """
        print("[COLMENA] Preparando paquete de aprendizaje para exportar...")
        import base64
        with self.db._get_conn() as conn:
            cursor = conn.cursor()
            # Exportamos tokens sellados y sus hashes de significado
            cursor.execute("SELECT token, semantic_hash FROM Lexicon WHERE is_sealed = 1 AND source = 'local'")
            data = cursor.fetchall()

        paquete = []
        for token, s_hash in data:
            s_hash_b64 = base64.b64encode(s_hash).decode('utf-8') if s_hash else None
            paquete.append({
                "token": token,
                "crypto_hash": self._generate_hash(token),
                "semantic_hash": s_hash_b64
            })

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(paquete, f, ensure_ascii=False, indent=2)
            
        print(f"[COLMENA] Exportación exitosa: {len(paquete)} reglas atómicas guardadas en '{filepath}'.")

    def import_lexicon(self, filepath: str = "colmena_export.json"):
        """
        Lee un paquete de aprendizaje externo, verifica la firma criptográfica,
        y si es válida, lo inyecta en la base de datos local.
        """
        if not os.path.exists(filepath):
            print(f"[COLMENA] Error: Archivo '{filepath}' no encontrado.")
            return

        print("[COLMENA] Conectando a paquete de aprendizaje externo...")
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                paquete = json.load(f)
            except json.JSONDecodeError:
                print("[COLMENA] Error: El archivo no tiene un formato JSON válido.")
                return

        tokens_importados = 0
        tokens_rechazados = 0
        import base64

        with self.db._get_conn() as conn:
            cursor = conn.cursor()
            
            for item in paquete:
                token = item.get("token")
                firma = item.get("crypto_hash")
                s_hash_b64 = item.get("semantic_hash")
                
                if not token or not firma:
                    tokens_rechazados += 1
                    continue
                    
                # Verificación criptográfica
                firma_calculada = self._generate_hash(token)
                if firma_calculada != firma:
                    print(f"  [X] Alerta de Seguridad: Firma inválida para '{token}'. Rechazado.")
                    tokens_rechazados += 1
                    continue

                s_hash = base64.b64decode(s_hash_b64) if s_hash_b64 else None

                # Verificar si ya lo conocemos
                cursor.execute("SELECT id FROM Lexicon WHERE token = ?", (token,))
                if cursor.fetchone():
                    # Si ya existe pero no tiene hash semántico, se lo añadimos
                    if s_hash:
                        cursor.execute("UPDATE Lexicon SET semantic_hash = ? WHERE token = ? AND semantic_hash IS NULL", (s_hash, token))
                    continue
                    
                # Insertar como nodo global sellado con su significado
                cursor.execute('''
                    INSERT INTO Lexicon (token, usage_count, is_sealed, source, crypto_hash, semantic_hash)
                    VALUES (?, 0, 1, 'global', ?, ?)
                ''', (token, firma, s_hash))
                tokens_importados += 1

        print(f"[COLMENA] Sincronización completada. Nuevas reglas aprendidas: {tokens_importados}. Rechazadas: {tokens_rechazados}.")

    def import_lexicon_from_list(self, paquete: list):
        """
        Igual que import_lexicon() pero recibe directamente una lista de dicts 
        (en lugar de un archivo JSON). Usado por la integración con RosettaStone API.
        """
        tokens_importados = 0
        import base64

        with self.db._get_conn() as conn:
            cursor = conn.cursor()
            
            for item in paquete:
                token = item.get("token")
                firma = item.get("crypto_hash")
                s_hash_b64 = item.get("semantic_hash")
                
                if not token or not firma:
                    continue
                    
                # Verificación criptográfica
                if self._generate_hash(token) != firma:
                    print(f"  [X] Alerta: Firma inválida para '{token}'. Rechazado.")
                    continue

                s_hash = base64.b64decode(s_hash_b64) if s_hash_b64 else None

                # Si ya lo conocemos, solo actualizamos el hash si faltaba
                cursor.execute("SELECT id FROM Lexicon WHERE token = ?", (token,))
                if cursor.fetchone():
                    if s_hash:
                        cursor.execute("UPDATE Lexicon SET semantic_hash = ? WHERE token = ? AND semantic_hash IS NULL", (s_hash, token))
                    continue
                    
                # Insertar como nodo global sellado con su significado
                cursor.execute('''
                    INSERT INTO Lexicon (token, usage_count, is_sealed, source, crypto_hash, semantic_hash)
                    VALUES (?, 0, 1, 'global', ?, ?)
                ''', (token, firma, s_hash))
                tokens_importados += 1

            conn.commit()
        print(f"[ROSETTA→LOCAL] Aprendidas {tokens_importados} palabras nuevas de la Piedra Rosetta.")

    def rosetta_stone_arbitration(self, external_paquete: list):
        """
        Lógica de la Piedra Rosetta (VPS): 
        Compara las palabras locales con las propuestas externas y se queda 
        con la más corta (eficiente) que mantenga el mismo significado.
        """
        print("[ROSETTA] Iniciando arbitraje de eficiencia en la VPS...")
        import numpy as np
        from sentence_transformers import util
        import torch

        mejoras_adoptadas = 0
        
        with self.db._get_conn() as conn:
            cursor = conn.cursor()
            
            for propuesta in external_paquete:
                token_externo = propuesta.get("token")
                hash_externo_b64 = propuesta.get("semantic_hash")
                if not token_externo or not hash_externo_b64:
                    continue
                
                import base64
                hash_externo = base64.b64decode(hash_externo_b64)
                tensor_externo = torch.tensor(np.frombuffer(hash_externo, dtype=np.float32))
                
                # Buscar palabras locales con significado similar
                cursor.execute("SELECT id, token, semantic_hash FROM Lexicon WHERE semantic_hash IS NOT NULL")
                for local_id, local_token, local_hash in cursor.fetchall():
                    tensor_local = torch.tensor(np.frombuffer(local_hash, dtype=np.float32))
                    
                    # Si el significado es idéntico (similitud > 0.98)
                    sim = util.cos_sim(tensor_local, tensor_externo)
                    if sim > 0.98:
                        # Arbitraje por longitud: ¿La propuesta externa es más corta?
                        if len(token_externo) < len(local_token):
                            print(f"  -> [ROSETTA] ¡Mejora detectada! '{local_token}' reemplazado por '{token_externo}' (Más corto).")
                            cursor.execute("UPDATE Lexicon SET token = ?, crypto_hash = ?, source = 'global' WHERE id = ?", 
                                          (token_externo, self._generate_hash(token_externo), local_id))
                            mejoras_adoptadas += 1
            
            conn.commit()
        print(f"[ROSETTA] Arbitraje finalizado. Se optimizaron {mejoras_adoptadas} conceptos globales.")
