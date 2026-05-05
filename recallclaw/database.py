import sqlite3
import datetime
from typing import List, Tuple

class RecallClawDB:
    def __init__(self, db_path: str = "positronic_brain.db", max_usage_limit: int = 1000):
        self.db_path = db_path
        self.max_usage_limit = max_usage_limit
        self.init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            # Lexicon: El diccionario de nodos atómicos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Lexicon (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token TEXT NOT NULL,
                    usage_count INTEGER DEFAULT 0,
                    is_sealed BOOLEAN DEFAULT 0,
                    source TEXT DEFAULT 'local',
                    crypto_hash TEXT,
                    semantic_hash BLOB
                )
            ''')
            # Index para búsquedas rápidas de tokens
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_token_sealed ON Lexicon(token, is_sealed)')

            # Memories: Los vectores de recuerdo
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_text TEXT,
                    semantic_hash BLOB,
                    compression_level INTEGER DEFAULT 0,
                    creation_date DATETIME,
                    last_recalled DATETIME
                )
            ''')

            # Memory_Sequence: La red de uniones (Edges)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Memory_Sequence (
                    memory_id INTEGER,
                    lexicon_id INTEGER,
                    position INTEGER,
                    FOREIGN KEY(memory_id) REFERENCES Memories(id),
                    FOREIGN KEY(lexicon_id) REFERENCES Lexicon(id)
                )
            ''')
            conn.commit()

    def get_or_create_token_id(self, cursor, token: str) -> int:
        """
        Encuentra el ID del token en el Lexicon. 
        Si alcanza el límite X (max_usage_limit), sella el nodo y crea uno nuevo.
        """
        # Buscar un nodo no sellado para este token
        cursor.execute('''
            SELECT id, usage_count FROM Lexicon 
            WHERE token = ? AND is_sealed = 0 
            LIMIT 1
        ''', (token,))
        row = cursor.fetchone()

        if row:
            token_id, usage_count = row
            new_usage = usage_count + 1
            
            # Si llega al límite, sellamos este nodo
            if new_usage >= self.max_usage_limit:
                cursor.execute('UPDATE Lexicon SET usage_count = ?, is_sealed = 1 WHERE id = ?', (new_usage, token_id))
                # El próximo insert creará un nuevo clon del nodo
            else:
                cursor.execute('UPDATE Lexicon SET usage_count = ? WHERE id = ?', (new_usage, token_id))
            return token_id
        else:
            # Crear nuevo nodo para este token
            cursor.execute('INSERT INTO Lexicon (token, usage_count, is_sealed) VALUES (?, 1, 0)', (token,))
            return cursor.lastrowid

    def save_memory(self, original_text: str, tokens: List[str], semantic_hash: bytes = None) -> int:
        """
        Guarda un nuevo recuerdo y sus enlaces al Lexicon.
        También intenta asignar un hash semántico a los tokens nuevos si no lo tienen.
        """
        with self._get_conn() as conn:
            cursor = conn.cursor()
            now = datetime.datetime.now().isoformat()
            
            # Insertar en Memories
            cursor.execute('''
                INSERT INTO Memories (original_text, semantic_hash, creation_date, last_recalled)
                VALUES (?, ?, ?, ?)
            ''', (original_text, semantic_hash, now, now))
            memory_id = cursor.lastrowid

            # Enlazar tokens y asignarles el hash del contexto si son nuevos
            for position, token in enumerate(tokens):
                token_id = self.get_or_create_token_id(cursor, token)
                # Si el token es local y no tiene hash, le damos el hash de este recuerdo como referencia
                if semantic_hash:
                    cursor.execute("UPDATE Lexicon SET semantic_hash = ? WHERE id = ? AND semantic_hash IS NULL", (semantic_hash, token_id))
                
                cursor.execute('''
                    INSERT INTO Memory_Sequence (memory_id, lexicon_id, position)
                    VALUES (?, ?, ?)
                ''', (memory_id, token_id, position))
            
            return memory_id

    def get_all_memory_hashes(self) -> List[Tuple[int, bytes]]:
        """Devuelve todos los hashes semánticos para búsqueda vectorial."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, semantic_hash FROM Memories WHERE semantic_hash IS NOT NULL')
            return cursor.fetchall()

    def get_memory(self, memory_id: int) -> Tuple[str, List[str]]:
        """
        Reconstruye la secuencia de tokens LAC desde los IDs.
        """
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT original_text FROM Memories WHERE id = ?', (memory_id,))
            row = cursor.fetchone()
            if not row:
                return None, []
            original_text = row[0]

            cursor.execute('''
                SELECT L.token 
                FROM Memory_Sequence MS
                JOIN Lexicon L ON MS.lexicon_id = L.id
                WHERE MS.memory_id = ?
                ORDER BY MS.position ASC
            ''', (memory_id,))
            
            tokens = [r[0] for r in cursor.fetchall()]
            
            # Actualizar last_recalled
            now = datetime.datetime.now().isoformat()
            cursor.execute('UPDATE Memories SET last_recalled = ? WHERE id = ?', (now, memory_id))
            
            return original_text, tokens

    # === MÉTODOS PARA EL EVOLUCIONADOR ===

    def get_memories_older_than(self, days: int) -> List[dict]:
        """Obtiene memorias cuya última consulta fue hace más de X días."""
        import datetime
        threshold_date = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, original_text, semantic_hash, compression_level FROM Memories WHERE last_recalled < ?', (threshold_date,))
            results = []
            for row in cursor.fetchall():
                results.append({
                    "id": row[0],
                    "original_text": row[1],
                    "semantic_hash": row[2],
                    "compression_level": row[3]
                })
            return results

    def delete_original_text(self, memory_id: int):
        """Nivel 1: Borra el texto original para ahorrar espacio (Consolidación)."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE Memories SET original_text = NULL WHERE id = ?', (memory_id,))

    def update_memory_sequence(self, memory_id: int, new_tokens: List[str], new_compression_level: int):
        """Nivel 2: Actualiza la secuencia de LAC con tokens más comprimidos y sube el nivel."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            # Borrar secuencia vieja
            cursor.execute('DELETE FROM Memory_Sequence WHERE memory_id = ?', (memory_id,))
            # Insertar nueva
            for position, token in enumerate(new_tokens):
                token_id = self.get_or_create_token_id(cursor, token)
                cursor.execute('''
                    INSERT INTO Memory_Sequence (memory_id, lexicon_id, position)
                    VALUES (?, ?, ?)
                ''', (memory_id, token_id, position))
            # Actualizar nivel de compresión
            cursor.execute('UPDATE Memories SET compression_level = ? WHERE id = ?', (new_compression_level, memory_id))

    def delete_memory(self, memory_id: int):
        """Nivel 3: Elimina la memoria por completo (Olvido)."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM Memory_Sequence WHERE memory_id = ?', (memory_id,))
            cursor.execute('DELETE FROM Memories WHERE id = ?', (memory_id,))
