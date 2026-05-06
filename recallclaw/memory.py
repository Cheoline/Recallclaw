from .database import RecallClawDB
from .lac_engine import LACEngine
from .validator import SemanticJudge
from .llm_connector import LLMConnector
from .evolver import Evolver
from .daemon import SubconsciousDaemon
from .sync_engine import SyncEngine

class PositronicBrain:
    def __init__(self, db_path: str = "positronic_brain.db", max_usage_limit: int = 1000, llm_model: str = "gemma3:4b"):
        self.db = RecallClawDB(db_path=db_path, max_usage_limit=max_usage_limit)
        self.lac = LACEngine()
        self.judge = SemanticJudge()
        self.llm = LLMConnector(default_model=llm_model)
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
        import emoji
        # Sanitización de emojis
        text = emoji.replace_emoji(text, replace='').strip()

        # Solución a Interferencia Semántica: Etiquetado de sujeto inteligente
        if context:
            text = f"[CONTEXTO: {context}] {text}"
        elif auto_context and text.strip():
            text = f"[{self._detect_subject_tag(text)}] {text}"

        print(f"[*] Inyectando recuerdo original: '{text}'")
        
        # 0. Generar Hash Semántico (Embedding Matemático del recuerdo completo)
        semantic_hash_bytes = None
        topic_fingerprint_bytes = None
        if self.judge.model is not None:
            # Hash semántico del texto completo (para la búsqueda principal)
            tensor = self.judge.model.encode(text)
            semantic_hash_bytes = tensor.tobytes()

            # Topic fingerprint: embedding de las palabras de contenido (sustantivos, verbos)
            # Filtramos stop words para capturar la esencia temática del recuerdo.
            palabras_contenido = self._extract_content_words(text)
            if palabras_contenido:
                topic_tensor = self.judge.model.encode(palabras_contenido)
                topic_fingerprint_bytes = topic_tensor.tobytes()
            else:
                # Si no hay palabras de contenido, usamos el hash general
                topic_fingerprint_bytes = semantic_hash_bytes
        
        # 1. Compresión LAC (Semántica y Fonética)
        tokens = self.lac.compress(text)
        print(f"[*] Compresión Atómica (LAC): {' '.join(tokens)}")
        
        # 2. Guardar en Base de Datos con fingerprint de tema
        memory_id = self.db.save_memory(
            original_text=text,
            tokens=tokens,
            semantic_hash=semantic_hash_bytes,
            topic_fingerprint=topic_fingerprint_bytes
        )
        
        return {
            "memory_id": memory_id,
            "compressed_tokens": tokens,
            "compression_ratio": f"{100 - (len(' '.join(tokens)) / len(text) * 100):.1f}%" if len(text) > 0 else "0%"
        }

    # Lista de indicadores de primera persona (el usuario habla de sí mismo)
    _FIRST_PERSON_MARKERS = {
        "yo", "me", "mi", "mí", "conmigo", "soy", "tengo", "vivo", "trabajo",
        "llamo", "llaman", "nací", "quiero", "pienso", "creo", "siento",
        "my name", "i am", "i'm", "i have"
    }
    # Indicadores de que se habla de un tercero
    _THIRD_PERSON_MARKERS = {
        "su", "sus", "él", "ella", "ellos", "ellas", "él", "hermano", "hermana",
        "padre", "madre", "amigo", "amiga", "jefe", "esposo", "esposa",
        "hijo", "hija", "primo", "prima", "vecino", "colega"
    }

    def _detect_subject_tag(self, text: str) -> str:
        """
        Detecta si el texto habla sobre el propio usuario (primera persona)
        o sobre un tercero, y retorna una etiqueta de sujeto precisa.
        Esto evita que el motor mezcle hechos del usuario con hechos de otras personas.
        """
        words = set(text.lower().split())

        is_first_person = bool(words & self._FIRST_PERSON_MARKERS)
        is_third_person = bool(words & self._THIRD_PERSON_MARKERS)

        if is_first_person and not is_third_person:
            return "SUJETO:YO"
        elif is_third_person and not is_first_person:
            return "SUJETO:TERCERO"
        elif is_first_person and is_third_person:
            return "SUJETO:YO+TERCERO"
        else:
            palabras = text.split()
            return f"CONTEXTO:{' '.join(palabras[:4])}"

    # Stop words comunes en español e inglés para el extractor de palabras de contenido
    _STOP_WORDS = {
        "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del",
        "en", "y", "o", "a", "que", "se", "es", "su", "sus", "con", "por",
        "para", "como", "pero", "mas", "si", "me", "le", "les", "lo", "al",
        "hay", "era", "fue", "son", "han", "the", "a", "an", "is", "are",
        "was", "were", "of", "in", "and", "or", "to", "it", "he", "she",
        "contexto", "sujeto"
    }

    def _extract_content_words(self, text: str) -> str:
        """
        Extrae solo las palabras de contenido semántico real (sustantivos, nombres,
        verbos principales) ignorando stop words y las etiquetas de contexto internas.
        El resultado se usa para calcular el Topic Fingerprint del recuerdo, que
        permite distinguir historias aunque compartan vocabulario superficial.
        """
        import re
        # Eliminar etiquetas internas como [SUJETO:YO] o [CONTEXTO:...]
        text_clean = re.sub(r'\[.*?\]', '', text).strip()
        words = text_clean.lower().split()
        content_words = [w for w in words if w not in self._STOP_WORDS and len(w) > 2]
        return " ".join(content_words) if content_words else text_clean

    # ═══════════════════════════════════════════════════════════════════
    # MÉTODOS DE ALTO NIVEL — Integración directa con agentes de IA
    # Diseñados para que cualquier desarrollador conecte su IA en 3 líneas.
    # ═══════════════════════════════════════════════════════════════════

    # Palabras que indican falta de contenido semántico real (stop words de intención)
    _TRIVIAL_INPUTS = {
        "hola", "hi", "hello", "ok", "okey", "sí", "si", "no", "claro",
        "gracias", "thanks", "ok gracias", "bye", "adios", "adiós",
        "entendido", "perfecto", "listo", "dale", "bien", "bueno",
        "vale", "ya", "eso", "ah", "eh", "uh", "mm", "mhm", "jaja",
        "jajaja", "lol", "xd", "😊", "👍", "❤️"
    }

    # Prefijos comunes que identifican la respuesta de una IA en un turno concatenado
    _AI_PREFIXES = ("ia:", "ai:", "asistente:", "assistant:", "bot:", "nexus:", "gemma:")

    def _sanitize(self, text: str) -> str:
        """Limpia el texto: elimina emojis y espacios sobrantes."""
        import emoji
        return emoji.replace_emoji(text, replace='').strip()

    def _is_trivial(self, text: str) -> bool:
        """Detecta si un mensaje no tiene contenido semántico valioso."""
        return (
            not text
            or len(text) < 5
            or text.lower().strip() in self._TRIVIAL_INPUTS
        )

    def _strip_ai_response(self, text: str) -> str:
        """
        Si el texto tiene el formato "Usuario: X\nIA: Y", extrae solo la parte del usuario.
        También descarta líneas que comiencen con prefijos de IA.
        """
        lineas_validas = []
        for linea in text.splitlines():
            lower = linea.lower().strip()
            # Descartar líneas que sean la voz de la IA
            if any(lower.startswith(p) for p in self._AI_PREFIXES):
                continue
            # Si la línea empieza con "usuario:" solo conservamos su contenido
            for prefix in ("usuario:", "user:", "humano:", "human:"):
                if lower.startswith(prefix):
                    linea = linea[len(prefix):].strip()
                    break
            lineas_validas.append(linea)
        return " ".join(lineas_validas).strip()

    def memorize_user_input(self, user_message: str, context: str = None) -> dict | None:
        """
        Método de alto nivel para agentes de IA.
        Guarda SOLO el mensaje del usuario, aplicando todas las reglas de calidad:
        - Filtra emojis automáticamente.
        - Ignora mensajes triviales o sin contenido semántico ("hola", "ok", etc.).
        - Descarta respuestas de la IA si se pasan por error.
        - Solo persiste información semánticamente valiosa.

        Uso recomendado (la forma más simple de conectar cualquier IA):
            contexto = brain.get_context_for(user_message)
            ai_response = mi_llm.chat(system=contexto, prompt=user_message)
            brain.memorize_user_input(user_message)  # ← Solo esto.

        Retorna el dict de memorize() si se guardó, o None si fue descartado.
        """
        clean = self._sanitize(user_message)
        clean = self._strip_ai_response(clean)

        if self._is_trivial(clean):
            print(f"[*] Mensaje descartado por falta de contenido semántico: '{user_message}'")
            return None

        return self.memorize(clean, context=context, auto_context=(context is None))

    def memorize_conversation(self, user_input: str, ai_response: str = "", context: str = None) -> dict | None:
        """
        Método de alto nivel para conversaciones completas.
        Acepta el turno completo (usuario + respuesta de la IA), pero internamente:
        - Extrae y guarda SOLO los hechos del user_input.
        - Descarta completamente la respuesta de la IA para no contaminar la memoria.
        - Aplica todas las reglas de filtrado (emojis, trivialidad, etc.).

        Uso recomendado:
            brain.memorize_conversation(user_input=mensaje_usuario, ai_response=respuesta_ia)
        """
        # La respuesta de la IA se descarta silenciosamente — solo el usuario aporta hechos.
        _ = ai_response
        return self.memorize_user_input(user_input, context=context)

    def get_context_for(self, question: str, system_prefix: str = None) -> str:
        """
        El Asistente de Contexto: Busca en la memoria vectorial el recuerdo más relevante
        y lo entrega formateado como un system_prompt listo para inyectar en cualquier LLM.

        Uso recomendado:
            contexto = brain.get_context_for(user_message)
            respuesta = mi_llm.chat(system=contexto, prompt=user_message)

        Parámetros:
            question:      El mensaje del usuario que servirá como consulta de búsqueda.
            system_prefix: Texto introductorio opcional para personalizar el system prompt.
                           Por defecto usa: "Eres un asistente con memoria. Usa estos recuerdos..."
        """
        print(f"[*] Buscando contexto para: '{question}'")

        if system_prefix is None:
            system_prefix = (
                "Eres un asistente con memoria persistente. "
                "Usa los siguientes recuerdos como contexto para responder con precisión. "
                "Si el recuerdo no es relevante para la pregunta, ignóralo."
            )

        all_hashes = self.db.get_all_memory_hashes()
        if not all_hashes:
            return system_prefix

        best_matches = self.judge.search_best_memory(question, all_hashes, top_k=3)
        if not best_matches:
            return system_prefix

        fragmentos = []
        for score, memory_id in best_matches:
            if score < 0.25:
                continue
            memoria = self.recall(memory_id)
            if "error" not in memoria:
                texto = memoria.get("original_text") or memoria.get("reconstructed_lac", "")
                if texto:
                    fragmentos.append(f"- {texto}")

        if not fragmentos:
            return system_prefix

        recuerdos_str = "\n".join(fragmentos)
        system_prompt = f"{system_prefix}\n\nRecuerdos relevantes:\n{recuerdos_str}"
        print(f"[*] Contexto generado con {len(fragmentos)} recuerdo(s).")
        return system_prompt

    # ═══════════════════════════════════════════════════════════════════

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

    def _rerank_by_topic(self, question: str, candidatos: list) -> tuple:
        """
        Segunda fase de búsqueda: re-rankea los candidatos usando los Topic Fingerprints.
        Combina la similitud semántica del texto completo (fase 1) con la similitud
        temática de las palabras de contenido (fase 2) para elegir el recuerdo correcto.

        Retorna (memory_id, combined_score) del recuerdo ganador.
        """
        if self.judge.model is None or len(candidatos) == 1:
            # Sin modelo o un solo candidato: confiamos en la fase 1 directamente
            return candidatos[0][1], candidatos[0][0]

        import numpy as np
        import torch
        from sentence_transformers import util

        # Calculamos el fingerprint temático de la pregunta
        palabras_pregunta = self._extract_content_words(question)
        if not palabras_pregunta:
            palabras_pregunta = question
        query_topic_tensor = self.judge.model.encode(palabras_pregunta, convert_to_tensor=True)

        # Obtenemos los topic fingerprints de los candidatos de la base de datos
        all_topic_fps = {mid: fp for mid, fp in self.db.get_all_topic_fingerprints()}

        mejor_id = candidatos[0][1]
        mejor_score = -1.0

        for vec_score, memory_id in candidatos:
            topic_fp = all_topic_fps.get(memory_id)
            if topic_fp is None:
                # Sin fingerprint temático, usamos solo el score vectorial
                combined = vec_score
            else:
                mem_topic_tensor = torch.tensor(
                    np.frombuffer(topic_fp, dtype=np.float32)
                ).to(query_topic_tensor.device)
                topic_sim = float(util.cos_sim(query_topic_tensor, mem_topic_tensor)[0][0])
                # Score combinado: 50% similitud de texto + 50% similitud de tema
                combined = (vec_score * 0.5) + (topic_sim * 0.5)
                print(f"[*]   Candidato {memory_id}: vec={vec_score:.2f} topic={topic_sim:.2f} combined={combined:.2f}")

            if combined > mejor_score:
                mejor_score = combined
                mejor_id = memory_id

        return mejor_id, mejor_score

    def ask(self, question: str) -> str:
        """
        El Bibliotecario: Busca en la base de datos la respuesta a una pregunta
        y la responde en lenguaje natural fluido.
        Usa un sistema de dos fases:
        1. Búsqueda vectorial (similitud semántica del texto completo).
        2. Re-ranking por Topic Fingerprint (similitud temática de palabras clave).
        Esto evita que el motor confunda historias distintas que comparten vocabulario.
        """
        print(f"[*] El Bibliotecario está analizando la pregunta: '{question}'")
        
        # 1. Obtener todos los hashes de la base de datos (Recuerdos)
        all_hashes = self.db.get_all_memory_hashes()
        
        if not all_hashes:
            return self._ask_lexicon(question)
        
        # 2. Fase 1: Búsqueda vectorial — top 5 candidatos por similitud de texto
        candidatos = self.judge.search_best_memory(question, all_hashes, top_k=min(5, len(all_hashes)))
        if not candidatos:
            return self._ask_lexicon(question)

        # 3. Fase 2: Re-ranking por Topic Fingerprint
        # Calculamos el fingerprint de la pregunta y lo comparamos con el de cada candidato
        # para elegir el recuerdo cuyo TEMA sea más afín, no solo su vocabulario superficial.
        memory_id, score = self._rerank_by_topic(question, candidatos)

        print(f"[*] Recuerdo elegido tras re-ranking: ID {memory_id} (Score combinado: {score:.2f})")

        # Umbral mínimo de confianza: si el mejor recuerdo no es suficientemente relevante,
        # es mejor admitir que no se sabe que mezclar hechos equivocados.
        if score < 0.40:
            print(f"[*] Similitud demasiado baja ({score:.2f}). Rechazando para evitar mezcla de recuerdos.")
            return "No tengo un recuerdo lo suficientemente claro sobre eso."
        
        # 3. Extraer la memoria (Puede ser el texto original o los tokens si ya fue consolidada)
        memoria_recuperada = self.recall(memory_id)
        if "error" in memoria_recuperada:
            return "Hubo un error al extraer la memoria de los engramas."
            
        texto_crudo = memoria_recuperada["original_text"]
        if not texto_crudo:
            texto_crudo = memoria_recuperada["reconstructed_lac"]
            print(f"[*] El Bibliotecario está leyendo una memoria consolidada: {texto_crudo}")
        
        # 4. Formular el prompt para el LLM — Instrucciones estrictas de sujeto
        prompt = f"""Eres un sistema de recuperación de memoria. Tu única función es responder la pregunta usando EXCLUSIVAMENTE el recuerdo proporcionado.

REGLAS ESTRICTAS (no las rompas bajo ningún concepto):
1. Responde SOLO con la información del recuerdo. Nada más.
2. Presta atención al SUJETO del recuerdo. Si el recuerdo habla de una tercera persona (hermano, amigo, etc.), NO confundas sus datos con los del usuario.
3. Si la pregunta es sobre "yo" o "me" y el recuerdo habla de otra persona, responde: 'No tengo ese dato del usuario en mis registros.'
4. NO inventes, NO supongas, NO mezcles datos de distintas personas.
5. Responde en español, de forma directa y breve.
6. Si la información no está en el recuerdo, responde solo: 'No tengo esa información.'

Recuerdo disponible: {texto_crudo}
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
