from recallclaw.validator import SemanticJudge

def main():
    print("=== Probando Juez Semántico ===")
    juez = SemanticJudge()
    
    original = "Ayer mi abuelo me dijo que mañana no habrá queso en la tienda porque el camión se averió."
    # Reconstrucción casi perfecta
    reconstructed_good = "Ayer el abuelo me dijo que mañana no habrá queso en la tienda, debido a que el camión se dañó."
    # Reconstrucción con pérdida grave de significado
    reconstructed_bad = "Mi abuelo me dijo que mañana habrá mucho queso en la tienda."
    
    print("\n[Prueba 1: Reconstrucción Aceptable]")
    res1 = juez.verify_integrity(original, reconstructed_good)
    
    print("\n[Prueba 2: Reconstrucción Deficiente]")
    res2 = juez.verify_integrity(original, reconstructed_bad)

if __name__ == "__main__":
    main()
