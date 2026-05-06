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

        print(f"[*] Inyectando recuerdo original: '{text[:50]}...'")
        
        print(f"[*] Analizando ADN temático del texto completo...")
        
        # 0. Extracción del "ADN Global" (Palabras clave del documento completo)
        # Esto permite que cada fragmento herede el contexto general del cuento
        adn_global = self._extract_content_words(text, top_n=10)
        
        # 1. Fragmentación Semántica (Chunking)
        fragmentos = self._chunk_text(text)
        results = []
        
        for i, frag in enumerate(fragmentos):
            if len(fragmentos) > 1:
                print(f"[*] Procesando fragmento {i+1}/{len(fragmentos)}...")
                
            # 2. Generar Hash Semántico y Topic Fingerprint
            semantic_hash_bytes = None
            topic_fingerprint_bytes = None
            if self.judge.model is not None:
                # El vector principal sigue siendo el fragmento local
                tensor = self.judge.model.encode(frag)
                semantic_hash_bytes = tensor.tobytes()
                
                # El Topic Fingerprint ahora combina el ADN GLOBAL + CONTENIDO LOCAL
                # Esto crea el vínculo "quién va con quién" que pidió el usuario
                palabras_locales = self._extract_content_words(frag, top_n=None)
                combo_tematico = f"{adn_global} {palabras_locales}"
                
                topic_tensor = self.judge.model.encode(combo_tematico)
                topic_fingerprint_bytes = topic_tensor.tobytes()
            
            # 3. Compresión LAC
            tokens = self.lac.compress(frag)
            
            # 4. Guardar en Base de Datos
            memory_id = self.db.save_memory(
                original_text=frag,
                tokens=tokens,
                semantic_hash=semantic_hash_bytes,
                topic_fingerprint=topic_fingerprint_bytes
            )
            results.append(memory_id)
        
        return {
            "memory_ids": results,
            "chunks_count": len(fragmentos),
            "total_text_length": len(text)
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

    def _extract_content_words(self, text: str, top_n: int = 15) -> str:
        """
        Extrae las palabras con mayor carga semántica (sustantivos, nombres propios, verbos).
        Si top_n está presente, devuelve solo las N palabras más frecuentes.
        """
        import re
        from collections import Counter
        
        # Limpieza básica
        text_clean = re.sub(r'\[.*?\]', '', text).strip()
        words = re.findall(r'\b\w{3,}\b', text_clean.lower()) # Solo palabras de >2 letras
        
        # Filtrar stop words
        content_words = [w for w in words if w not in self._STOP_WORDS]
        
        if not content_words:
            return text_clean[:100]

        # Si queremos un resumen de palabras clave (para el ADN global)
        if top_n:
            counts = Counter(content_words)
            return " ".join([w for w, c in counts.most_common(top_n)])
            
        return " ".join(content_words)

    def _chunk_text(self, text: str, max_words: int = 120) -> list:
        """
        Divide un texto largo en fragmentos más pequeños basados en párrafos o puntos.
        Esto asegura que cada fragmento mantenga una alta densidad semántica.
        """
        if len(text.split()) <= max_words:
            return [text]
            
        chunks = []
        # Intentamos dividir por párrafos primero
        paragraphs = text.split('\n')
        current_chunk = []
        current_count = 0
        
        for p in paragraphs:
            p = p.strip()
            if not p: continue
            words = p.split()
            if current_count + len(words) > max_words and current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = []
                current_count = 0
            current_chunk.append(p)
            current_count += len(words)
            
        if current_chunk:
            chunks.append("\n".join(current_chunk))
            
        return chunks

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

    def ask(self, question: str) -> str:
        """
        El Bibliotecario: Busca en la base de datos la respuesta a una pregunta
        y la responde en lenguaje natural fluido.
        Usa un sistema multiclave: recupera los fragmentos más relevantes y los une
        para que el LLM tenga todo el contexto necesario.
        """
        print(f"[*] El Bibliotecario está analizando la pregunta: '{question}'")
        
        all_hashes = self.db.get_all_memory_hashes()
        if not all_hashes:
            return self._ask_lexicon(question)
        
        # 1. Obtener los mejores candidatos (top 8 para tener margen de maniobra)
        candidatos = self.judge.search_best_memory(question, all_hashes, top_k=min(8, len(all_hashes)))
        if not candidatos:
            return self._ask_lexicon(question)

        # 2. Re-rankear y seleccionar los mejores fragmentos (Top 3)
        # Esto permite responder preguntas que requieren unir datos de diferentes párrafos.
        mejores_candidatos = self._get_top_relevant_snippets(question, candidatos, top_n=3)
        
        if not mejores_candidatos:
            return "No tengo un recuerdo lo suficientemente claro sobre eso."

        # 3. Extraer y combinar los textos de los recuerdos elegidos
        contexto_textos = []
        for mid, score in mejores_candidatos:
            mem = self.recall(mid)
            txt = mem.get("original_text") or mem.get("reconstructed_lac", "")
            if txt:
                contexto_textos.append(txt)
        
        texto_unificado = "\n---\n".join(contexto_textos)
        print(f"[*] Contexto recuperado: {len(contexto_textos)} fragmentos (Confianza: {mejores_candidatos[0][1]:.2f})")

        # 4. Formular el prompt para el LLM — Modo Analítico
        prompt = f"""Actúa como un Sistema de Memoria de alta precisión.
Tu misión es extraer datos EXACTOS de los recuerdos proporcionados para responder la pregunta.

REGLAS DE ORO:
1. Usa ÚNICAMENTE los recuerdos de abajo. Si el dato no está (ej. un año, un color, un nombre), di 'No tengo esa información'.
2. SÉ PRECISO CON LOS NÚMEROS Y FECHAS. No los aproximes ni los inventes.
3. No asumas que un lugar es una dirección cardinal a menos que el texto lo diga explícitamente.
4. Si hay contradicciones o falta de información, admítelo. No intentes "completar" la historia.
5. Responde en español de forma directa y clara.

Recuerdos disponibles:
{texto_unificado}

Pregunta del usuario: {question}
Respuesta basada en evidencia:"""

        print("[*] Generando respuesta con LLM local...")
        return self.llm.generate_response(prompt)

    def _get_top_relevant_snippets(self, question: str, candidatos: list, top_n: int = 3) -> list:
        """
        Filtra y re-rankea candidatos usando un sistema de Coherencia Temática.
        Selecciona el mejor candidato como 'Ancla' y solo permite otros fragmentos
        si su Topic Fingerprint es muy cercano al del ancla.
        """
        import numpy as np
        import torch
        from sentence_transformers import util

        all_topic_fps = {mid: fp for mid, fp in self.db.get_all_topic_fingerprints()}
        
        # Pre-calcular embedding de tema para la pregunta
        palabras_pregunta = self._extract_content_words(question) or question
        query_topic_tensor = self.judge.model.encode(palabras_pregunta, convert_to_tensor=True)

        scored_candidates = []
        for vec_score, mid in candidatos:
            topic_fp = all_topic_fps.get(mid)
            if topic_fp is None:
                combined = vec_score
                topic_tensor = None
            else:
                topic_tensor = torch.tensor(np.frombuffer(topic_fp, dtype=np.float32)).to(query_topic_tensor.device)
                topic_sim = float(util.cos_sim(query_topic_tensor, topic_tensor)[0][0])
                # Mayor peso al tema (65%) para evitar confusiones de vocabulario
                combined = (vec_score * 0.35) + (topic_sim * 0.65)
            
            if combined >= 0.42: # Umbral de relevancia más estricto
                scored_candidates.append({
                    "mid": mid,
                    "score": combined,
                    "topic_tensor": topic_tensor
                })
        
        if not scored_candidates:
            return []

        # Ordenar por score combinado
        scored_candidates.sort(key=lambda x: x["score"], reverse=True)
        
        # EL ANCLA: El mejor resultado define el TEMA de la respuesta
        anchor = scored_candidates[0]
        final_snippets = [(anchor["mid"], anchor["score"])]
        
        # Solo añadimos otros snippets si son temáticamente coherentes con el Ancla
        # (Esto evita que una historia de 'llaves' se mezcle con una de 'relojes')
        if anchor["topic_tensor"] is not None:
            for other in scored_candidates[1:]:
                if other["topic_tensor"] is not None:
                    # Similitud entre el tema del ancla y el tema del candidato adicional
                    coherence = float(util.cos_sim(anchor["topic_tensor"], other["topic_tensor"])[0][0])
                    if coherence > 0.75: # Alta exigencia de coherencia temática
                        final_snippets.append((other["mid"], other["score"]))
                        if len(final_snippets) >= top_n:
                            break
        
        return final_snippets

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
