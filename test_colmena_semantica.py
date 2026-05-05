import time
import base64
from recallclaw import PositronicBrain

def main():
    print("=== PRUEBA DE COLMENA SEMÁNTICA (CORREGIDA) ===")
    
    # 1. IA Maestra: Aprende un concepto técnico
    maestra = PositronicBrain(db_path="maestra_semantica.db")
    texto = "El protocolo de seguridad Z-1 bloquea intrusiones en la capa de transporte."
    print(f"\n[Maestra]: Memorizando concepto técnico: '{texto}'")
    maestra.memorize(texto)
    
    # Identificamos los tokens que RecallClaw generó y los sellamos para exportar
    with maestra.db._get_conn() as conn:
        cursor = conn.cursor()
        # Seleccionamos DISTINCT para evitar duplicados
        cursor.execute("SELECT DISTINCT token FROM Lexicon WHERE source = 'local'")
        tokens_encontrados = [row[0] for row in cursor.fetchall()]
        print(f"  -> Tokens detectados para sellar: {tokens_encontrados}")
        
        for t in tokens_encontrados:
            cursor.execute("UPDATE Lexicon SET is_sealed = 1 WHERE token = ?", (t,))
        conn.commit()
    
    # Exportamos a la Colmena
    maestra.colmena.export_lexicon("colmena_semantica.json")
    
    print("\n" + "="*50)
    
    # 2. IA Nueva: No sabe nada
    nueva = PositronicBrain(db_path="nueva_semantica.db")
    
    # Importamos desde la Colmena
    print("\n[IA Nueva]: Descargando conocimiento de la Colmena...")
    nueva.colmena.import_lexicon("colmena_semantica.json")
    
    # 3. Probamos si la IA Nueva puede interpretar el código
    print("\n--- PRUEBA DE INTERPRETACIÓN COLECTIVA ---")
    # Buscamos un token aprendido de la colmena para preguntar por él
    with nueva.db._get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT token FROM Lexicon WHERE source = 'global' LIMIT 1")
        row = cursor.fetchone()
        if not row:
            print("[ERROR]: No se aprendieron tokens de la colmena.")
            return
        token_aprendido = row[0]
        
        # Crear la memoria con el código aprendido
        cursor.execute("INSERT INTO Memories (original_text, creation_date, last_recalled) VALUES (NULL, datetime('now'), datetime('now'))")
        mem_id = cursor.lastrowid
        cursor.execute("SELECT id FROM Lexicon WHERE token = ?", (token_aprendido,))
        t_id = cursor.fetchone()[0]
        cursor.execute("INSERT INTO Memory_Sequence (memory_id, lexicon_id, position) VALUES (?, ?, 0)", (mem_id, t_id))
        conn.commit()

    pregunta = f"¿Qué significa el código '{token_aprendido}'?"
    print(f"[Usuario]: Preguntando: '{pregunta}'")
    
    respuesta = nueva.ask(pregunta)
    print(f"\n[IA Nueva]: {respuesta}")

if __name__ == "__main__":
    main()
