import time
from recallclaw import PositronicBrain

def simulate_time(cerebro, memory_id, days_passed):
    """Truco de Admin: Envejece la memoria artificialmente."""
    print(f"\n⏳ [MÁQUINA DEL TIEMPO]: Avanzando {days_passed} días en el futuro...")
    with cerebro.db._get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE Memories SET last_recalled = date('now', '-{days_passed} days') WHERE id = ?", (memory_id,))
        conn.commit()

def main():
    print("=== SIMULADOR DE ENVEJECIMIENTO COGNITIVO (6 MESES) ===")
    cerebro = PositronicBrain(db_path="memoria_timelapse.db")
    
    texto = "El doctor Martínez recomendó tomar mucha agua pura todos los días por la mañana para evitar enfermedades graves en los riñones."
    print(f"\n[Día 0] Aprendiendo nueva memoria: '{texto}'")
    resultado = cerebro.memorize(texto)
    mem_id = resultado["memory_id"]
    
    pregunta = "¿Qué recomendó el doctor Martínez y para qué?"
    
    print("\n--- PRUEBA A CORTO PLAZO (Día 0) ---")
    print("Memoria fresca, recién guardada.")
    respuesta = cerebro.ask(pregunta)
    print(f"[Bibliotecario]: {respuesta}")
    
    print("\n--- PRUEBA A MEDIANO PLAZO (Día 10) ---")
    simulate_time(cerebro, mem_id, 10)
    cerebro.sleep_cycle() # Nivel 1: Borrará el original_text
    print("\n(La memoria acaba de ser consolidada. Solo existen tokens ahora).")
    respuesta = cerebro.ask(pregunta)
    print(f"[Bibliotecario]: {respuesta}")
    
    print("\n--- PRUEBA A LARGO PLAZO (Día 40) ---")
    simulate_time(cerebro, mem_id, 40)
    cerebro.sleep_cycle() # Nivel 2: Intentará mutarla
    print("\n(La memoria pasó por degradación biológica).")
    respuesta = cerebro.ask(pregunta)
    print(f"[Bibliotecario]: {respuesta}")

    print("\n--- PRUEBA A MUY LARGO PLAZO (Día 180 - 6 meses) ---")
    # Para llegar a los 6 meses sin que la prueba anterior reinicie el reloj, sumamos el tiempo
    simulate_time(cerebro, mem_id, 180)
    cerebro.sleep_cycle() # Intentará mutar aún más o mantenerla
    print("\n(La memoria es muy antigua).")
    respuesta = cerebro.ask(pregunta)
    print(f"[Bibliotecario]: {respuesta}")

if __name__ == "__main__":
    main()
