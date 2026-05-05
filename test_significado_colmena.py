import time
from recallclaw import PositronicBrain

def main():
    print("=== PRUEBA DE SIGNIFICADO APLICADO (RECALLCLAW) ===")
    cerebro = PositronicBrain(db_path="memoria_significado.db")
    
    # 1. La Colmena inyecta una palabra "alienígena" (un código de ultra-compresión)
    # Simulamos que 'Z-1' es el código para 'Sistema de Seguridad de Red'
    token_secreto = "Z-1"
    firma = cerebro.colmena._generate_hash(token_secreto)
    
    print(f"\n[COLMENA]: Inyectando palabra nueva de la red: '{token_secreto}'")
    with cerebro.db._get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO Lexicon (token, usage_count, is_sealed, source, crypto_hash)
            VALUES (?, 100, 1, 'global', ?)
        ''', (token_secreto, firma))
        conn.commit()

    # 2. Guardamos un recuerdo en lenguaje humano
    texto_humano = "El Sistema de Seguridad de Red detectó un ataque de denegación de servicio."
    print(f"\n[Usuario]: Guardando recuerdo humano: '{texto_humano}'")
    cerebro.memorize(texto_humano)

    # 3. Forzamos a RecallClaw a "Aprender la aplicación" del código Z-1
    # En un escenario real, esto lo haría el Evolucionador al notar que Z-1 
    # es un sinónimo ultra-corto para 'Sistema de Seguridad de Red'.
    # Aquí lo simulamos forzando la secuencia para la prueba.
    print("\n[RECALLCLAW]: Analizando el diccionario... 'Z-1' detectado como sinónimo de alta eficiencia.")
    with cerebro.db._get_conn() as conn:
        cursor = conn.cursor()
        # Buscamos el ID del token Z-1
        cursor.execute("SELECT id FROM Lexicon WHERE token = 'Z-1'")
        z1_id = cursor.fetchone()[0]
        # Sustituimos la secuencia del recuerdo 1 para que use el nuevo código aprendido
        cursor.execute("DELETE FROM Memory_Sequence WHERE memory_id = 1")
        cursor.execute("INSERT INTO Memory_Sequence (memory_id, lexicon_id, position) VALUES (1, ?, 0)", (z1_id,))
        # Borramos el texto original para que RecallClaw dependa SOLO de su aprendizaje de la Colmena
        cursor.execute("UPDATE Memories SET original_text = NULL WHERE id = 1")
        conn.commit()

    print("\n[SISTEMA]: La memoria ahora es solo el código 'Z-1'. El texto humano ha desaparecido.")
    
    # 4. Recuperación: ¿RecallClaw sabe qué significa Z-1?
    print("\n--- PRUEBA DE INTERPRETACIÓN ---")
    pregunta = "¿Qué pasó con la seguridad de la red?"
    print(f"[IA Externa]: Preguntando: '{pregunta}'")
    
    # Aquí RecallClaw debe usar su Búsqueda Vectorial para encontrar Z-1
    # y usar su inteligencia para explicar qué significa.
    respuesta = cerebro.ask(pregunta)
    print(f"\n[RecallClaw]: {respuesta}")

if __name__ == "__main__":
    main()
