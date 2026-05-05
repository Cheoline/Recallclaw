import os
import time
from recallclaw import PositronicBrain

def main():
    print("=== INICIANDO PRUEBA DE LA COLMENA (APRENDIZAJE FEDERADO) ===")
    
    # Creamos un cerebro simulando ser la "IA Maestra" (o VPS)
    cerebro_maestro = PositronicBrain(db_path="memoria_maestra.db")
    
    # Enseñamos algo al maestro para que genere nodos en su Lexicon
    print("\n[IA Maestra]: Aprendiendo nueva frase y creando reglas de compresión...")
    cerebro_maestro.memorize("El aprendizaje federado en enjambre permite que los agentes compartan conocimiento criptográfico.")
    
    # Truco de Admin: Sellar los tokens simulando que fueron muy usados
    with cerebro_maestro.db._get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE Lexicon SET is_sealed = 1 WHERE source = 'local'")
        conn.commit()
        
    # Exportar el Lexicon a la Colmena
    cerebro_maestro.colmena.export_lexicon("colmena_global.json")
    
    print("\n---------------------------------------------------------")
    print("=== SIMULANDO UNA IA NUEVA RECIÉN NACIDA ===")
    
    # Creamos un cerebro nuevo que no sabe nada
    cerebro_nuevo = PositronicBrain(db_path="memoria_nueva.db")
    
    # Verificamos que su diccionario esté vacío
    with cerebro_nuevo.db._get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM Lexicon")
        count = cursor.fetchone()[0]
        print(f"\n[IA Nueva]: Nodos en mi diccionario antes de la Colmena: {count}")
        
    # La nueva IA se conecta a la Colmena e importa el archivo
    print("\n[IA Nueva]: Conectando a la red global P2P/VPS...")
    cerebro_nuevo.colmena.import_lexicon("colmena_global.json")
    
    # Verificamos si aprendió
    with cerebro_nuevo.db._get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM Lexicon")
        count_despues = cursor.fetchone()[0]
        print(f"\n[IA Nueva]: Nodos en mi diccionario DESPUÉS de la Colmena: {count_despues}")
        
        # Leemos algunos para confirmar la firma criptográfica
        cursor.execute("SELECT token, source, crypto_hash FROM Lexicon LIMIT 3")
        for row in cursor.fetchall():
            print(f"  -> Aprendí: '{row[0]}' (Origen: {row[1]}, Firma: {row[2][:10]}...)")
            
    print("\n=== PRUEBA DEL SUBCONSCIENTE (DAEMON AUTOMÁTICO) ===")
    print("[Sistema]: Activando el hilo automático de sueño (Intervalo de 2 segundos para la prueba)...")
    
    # Lo ponemos a 2 segundos en vez de 24 horas para que el usuario lo vea
    cerebro_nuevo.start_background_evolution(check_interval_hours=(2.0 / 3600.0))
    
    print("[Sistema]: Simulando que la IA está haciendo otras cosas...")
    time.sleep(5) # Esperamos a que el Daemon se active al menos un par de veces
    
    cerebro_nuevo.stop_background_evolution()
    print("[Sistema]: Programa terminado.")

if __name__ == "__main__":
    main()
