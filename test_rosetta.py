"""
Test de la Piedra Rosetta
=========================
Simula 3 RecallClaw independientes que:
1. Aprenden frases distintas
2. Suben sus vocabularios a la Rosetta (VPS local)
3. Descargan lo que les falta
4. Prueban si ahora entienden palabras que nunca aprendieron
"""
import requests
import base64
from recallclaw import PositronicBrain

ROSETTA_URL = "http://localhost:7474"

def check_rosetta():
    """Verifica que la Rosetta esté corriendo."""
    try:
        r = requests.get(f"{ROSETTA_URL}/status", timeout=3)
        data = r.json()
        print(f"[OK] RosettaStone en línea: {data['tokens_totales'] if 'tokens_totales' in data else data}")
        return True
    except Exception:
        print("[ERROR] RosettaStone no está corriendo.")
        print("  → Abre otra ventana de PowerShell y ejecuta: cd C:\\Users\\User\\OneDrive\\Desktop\\RosettaStone && start_rosetta.bat")
        return False

def subir_vocabulario(cerebro: PositronicBrain, agent_id: str):
    """Sube el vocabulario del cerebro a la RosettaStone."""
    import base64
    tokens_payload = []
    
    with cerebro.db._get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT token, crypto_hash, semantic_hash FROM Lexicon WHERE source = 'local'")
        for token, crypto, s_hash in cursor.fetchall():
            tokens_payload.append({
                "token": token,
                "crypto_hash": crypto or cerebro.colmena._generate_hash(token),
                "semantic_hash": base64.b64encode(s_hash).decode('utf-8') if s_hash else None
            })
    
    if not tokens_payload:
        print(f"  [{agent_id}] No hay tokens para subir.")
        return
        
    r = requests.post(f"{ROSETTA_URL}/upload", json={
        "agent_id": agent_id,
        "tokens": tokens_payload
    })
    res = r.json()
    print(f"  [{agent_id}] Upload → Nuevos: {res['nuevos_aceptados']}, Mejorados: {res['mejorados']}, Rechazados: {res['rechazados']}")

def descargar_vocabulario(cerebro: PositronicBrain, agent_id: str):
    """Descarga de la RosettaStone lo que el cerebro no tiene."""
    with cerebro.db._get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT token FROM Lexicon")
        tokens_conocidos = [row[0] for row in cursor.fetchall()]
    
    r = requests.post(f"{ROSETTA_URL}/sync", json={
        "agent_id": agent_id,
        "known_tokens": tokens_conocidos
    })
    res = r.json()
    tokens_nuevos = res.get("tokens", [])
    print(f"  [{agent_id}] Sync → Recibirá {res['tokens_nuevos']} tokens nuevos de la Rosetta.")
    
    # Importar usando el motor ya existente
    cerebro.colmena.import_lexicon_from_list(tokens_nuevos)

def main():
    print("=== PRUEBA DE LA PIEDRA ROSETTA ===")
    
    if not check_rosetta():
        return
    
    print("\n--- PASO 1: Tres cerebros aprenden cosas distintas ---")
    
    cerebro_a = PositronicBrain(db_path="rosetta_test_a.db")
    cerebro_b = PositronicBrain(db_path="rosetta_test_b.db")
    cerebro_c = PositronicBrain(db_path="rosetta_test_c.db")
    
    cerebro_a.memorize("El corazón bombea sangre a través de las arterias y venas.")
    cerebro_b.memorize("La fotosíntesis convierte la luz solar en energía para las plantas.")
    cerebro_c.memorize("El algoritmo de cifrado protege la información confidencial.")
    
    print("\n--- PASO 2: Los tres suben su vocabulario a la Rosetta ---")
    subir_vocabulario(cerebro_a, "cerebro_A")
    subir_vocabulario(cerebro_b, "cerebro_B")
    subir_vocabulario(cerebro_c, "cerebro_C")
    
    print("\n--- PASO 3: Ver estadísticas de la Rosetta ---")
    r = requests.get(f"{ROSETTA_URL}/status")
    stats = r.json()
    print(f"  La Rosetta ahora tiene {stats['total_tokens']} tokens únicos de {stats['total_aportes_recibidos']} aportes totales.")
    
    print("\n--- PASO 4: Cerebro A descarga lo que le falta (vocabulario de B y C) ---")
    descargar_vocabulario(cerebro_a, "cerebro_A")
    
    print("\n--- PASO 5: ¿Cerebro A ahora entiende conceptos de B y C? ---")
    pregunta = "¿Qué es la fotosíntesis?"
    print(f"  Preguntando al Cerebro A: '{pregunta}'")
    respuesta = cerebro_a.ask(pregunta)
    print(f"  [Cerebro A]: {respuesta}")

if __name__ == "__main__":
    main()
