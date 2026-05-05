"""
ARCHIVO DE EJEMPLO — Solo para referencia del desarrollador
============================================================
Este archivo NO es parte del sistema RecallClaw.
Es un ejemplo de cómo cualquier agente externo (un chatbot, un bot de trading,
NanoClaw, o cualquier otra IA) puede conectarse a RecallClaw y usarlo como
su capa de memoria a largo plazo.

No es necesario modificar ni ejecutar este archivo para usar RecallClaw.
Sirve únicamente como guía de integración.
"""

import sys
import json

# Importamos la librería del cerebro positrónico que instalamos en el sistema
try:
    from recallclaw import PositronicBrain, SemanticJudge
except ImportError:
    print("Error: No se encontró la librería 'recallclaw'.")
    print("Asegúrate de haber ejecutado 'pip install -e .' en la carpeta de RecallClaw.")
    sys.exit(1)

class AgenteDeIA:
    """
    Simula una IA (como Ollama, un chatbot, etc.) que tiene su propio código,
    pero usa RecallClaw puramente como un disco duro biológico.
    """
    def __init__(self, nombre: str):
        self.nombre = nombre
        print(f"[{self.nombre}] Inicializando sistemas...")
        
        # Conecta con el cerebro positrónico (creará el archivo .db en la carpeta actual del agente)
        self.memoria_a_largo_plazo = PositronicBrain(db_path=f"memoria_{self.nombre}.db")
        self.juez = SemanticJudge()
        
    def aprender_del_usuario(self, texto_usuario: str):
        print(f"\n[{self.nombre}] Escuchando: '{texto_usuario}'")
        print(f"[{self.nombre}] Enviando al Cerebro Positrónico para almacenamiento profundo...")
        
        # La IA no sabe CÓMO se comprime, solo usa la API de RecallClaw
        resultado = self.memoria_a_largo_plazo.memorize(texto_usuario)
        
        print(f"[{self.nombre}] Recuerdo guardado exitosamente.")
        print(f"[{self.nombre}] ID del Recuerdo: {resultado['memory_id']}")
        print(f"[{self.nombre}] Tokens Atómicos guardados en el disco: {' '.join(resultado['compressed_tokens'])}")
        
    def intentar_recordar_y_reconstruir(self, memory_id: int):
        print(f"\n[{self.nombre}] Intentando extraer el recuerdo #{memory_id} del cerebro...")
        
        recuerdo_crudo = self.memoria_a_largo_plazo.recall(memory_id)
        
        if "error" in recuerdo_crudo:
            print(f"[{self.nombre}] Error: {recuerdo_crudo['error']}")
            return
            
        print(f"[{self.nombre}] Tokens recuperados del disco: {recuerdo_crudo['reconstructed_lac']}")
        
        # Aquí es donde esta IA llamaría a Ollama (o GPT/Gemini) para transformar los tokens en texto.
        # Simulamos que el LLM hizo el trabajo de rehidratación:
        reconstruccion_simulada_llm = "El usuario me dijo que le gusta programar IAs en Python."
        
        print(f"[{self.nombre}] (Simulación LLM) Reconstrucción: '{reconstruccion_simulada_llm}'")
        
        # Usar el juez de RecallClaw para validar que el LLM no inventó cosas
        validacion = self.juez.verify_integrity(recuerdo_crudo["original_text"], reconstruccion_simulada_llm)
        
        if validacion["approved"]:
            print(f"[{self.nombre}] Juez aprueba la memoria. Puedo usarla de forma segura.")
        else:
            print(f"[{self.nombre}] ADVERTENCIA: La memoria fue mal reconstruida o alucinada por el LLM. Descartar.")

if __name__ == "__main__":
    mi_agente = AgenteDeIA("NanoBot_X")
    mi_agente.aprender_del_usuario("Hoy aprendí a crear un cerebro positrónico modular en Python.")
    
    # Intentamos recordar el ID 1 que acabamos de crear
    mi_agente.intentar_recordar_y_reconstruir(1)
