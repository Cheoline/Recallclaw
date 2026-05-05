import time
from recallclaw import PositronicBrain

def main():
    print("=== Probando El Bibliotecario (Motor RAG) ===")
    cerebro = PositronicBrain(db_path="memoria_bibliotecario.db")
    
    # 1. Guardar un documento/recuerdo
    documento = "Ayer el abuelo me contó que su viejo camión verde se averió en la ruta 66 porque el motor se quedó sin aceite."
    print("\n[Usuario]: Guardando documento en la bóveda...")
    cerebro.memorize(documento)
    
    # Pausa pequeña para que leas la consola
    time.sleep(1)
    
    # 2. Hacer una pregunta exacta
    pregunta = "¿De qué color era el camión del abuelo y por qué se averió?"
    print(f"\n[Usuario]: Preguntando: '{pregunta}'")
    
    # El bibliotecario hace su magia
    respuesta = cerebro.ask(pregunta)
    
    print("\n" + "="*50)
    print("RESPUESTA DEL BIBLIOTECARIO:")
    print(respuesta)
    print("="*50)

if __name__ == "__main__":
    main()
