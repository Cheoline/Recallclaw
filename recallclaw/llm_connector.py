import requests
import json

class LLMConnector:
    """
    Conector simple para interactuar con un LLM local (ej. Ollama).
    Usado por "El Bibliotecario" para reconstruir memorias y responder preguntas.
    """
    def __init__(self, host: str = "http://localhost:11434", default_model: str = "gemma3:4b"):
        self.host = host
        self.default_model = default_model
        
    def generate_response(self, prompt: str, model: str = None) -> str:
        """
        Envía un prompt a Ollama y retorna la respuesta.
        """
        model = model or self.default_model
        url = f"{self.host}/api/generate"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code != 200:
                print(f"[LLM] HTTP {response.status_code} desde Ollama: {response.text}")
            response.raise_for_status()
            data = response.json()
            return data.get("response", "").strip()
        except requests.exceptions.RequestException as e:
            print(f"[LLM] Error al conectar con Ollama en {self.host}: {e}")
            print("[LLM] Asegúrate de que Ollama esté ejecutándose y el modelo esté descargado (ej: ollama run llama3)")
            return "[Error: LLM local no disponible. No se pudo formular la respuesta.]"
