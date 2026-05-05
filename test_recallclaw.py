from recallclaw.memory import PositronicBrain
import os

def main():
    print("=== Iniciando RecallClaw (Cerebro Positrónico) Fase 1 ===")
    
    # Base de datos de prueba
    db_path = "test_brain.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        
    brain = PositronicBrain(db_path=db_path, max_usage_limit=5)
    
    text1 = "Ayer mi abuelo me dijo que mañana no habrá queso en la tienda porque el camión se averió en la calle, pero que él comprará pan."
    print("\n--- Inyectando Memoria 1 ---")
    res1 = brain.memorize(text1)
    print(f"Resultado: {res1}")
    
    text2 = "El queso de la tienda estaba muy rico, comprará más mañana."
    print("\n--- Inyectando Memoria 2 ---")
    res2 = brain.memorize(text2)
    print(f"Resultado: {res2}")
    
    print("\n--- Comprobando Grafo y Deduplicación ---")
    # Imprimir todos los nodos en Lexicon
    with brain.db._get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, token, usage_count, is_sealed FROM Lexicon")
        rows = cur.fetchall()
        print(f"Nodos Totales en el Grafo (Lexicon): {len(rows)}")
        for r in rows:
            if r[2] > 1: # Print shared tokens
                print(f"  Nodo Reutilizado -> ID: {r[0]} | Token: '{r[1]}' | Usos: {r[2]}")

if __name__ == "__main__":
    main()
