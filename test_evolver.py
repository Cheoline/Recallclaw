import time
from recallclaw import PositronicBrain

def main():
    print("=== Probando el Sueño de la IA (Evolucionador) ===")
    cerebro = PositronicBrain(db_path="memoria_bibliotecario.db")
    
    # Truco: Vamos a modificar artificialmente las fechas en la base de datos
    # para hacerle creer a la IA que sus recuerdos son viejos.
    with cerebro.db._get_conn() as conn:
        cursor = conn.cursor()
        
        # 1. Hacemos que un recuerdo parezca de hace 40 días (Nivel 2: Degradación)
        print("\n[Admin]: Envejeciendo memorias artificialmente...")
        cursor.execute("UPDATE Memories SET last_recalled = date('now', '-40 days') WHERE id = 1")
        conn.commit()
        
    print("[Admin]: Listo. Activando el ciclo de sueño...")
    time.sleep(1)
    
    # 2. La IA se va a dormir y activa su evolución
    cerebro.sleep_cycle()

if __name__ == "__main__":
    main()
