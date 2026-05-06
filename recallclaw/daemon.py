import time
import threading
# Eliminada cualquier referencia a importaciones circulares de memoryEliminada la importación circular de PositronicBrain

class SubconsciousDaemon:
    """
    El 'Subconsciente' de la IA.
    Corre en segundo plano y activa el ciclo de sueño del Evolucionador automáticamente.
    """
    def __init__(self, brain, check_interval_hours: float = 24.0):
        self.brain = brain
        self.check_interval_seconds = check_interval_hours * 3600
        self.running = False
        self.thread = None

    def _daemon_loop(self):
        print(f"[DAEMON] Subconsciente activado. Ciclos automáticos cada {self.check_interval_seconds / 3600} horas.")
        while self.running:
            # Esperar el intervalo
            time.sleep(self.check_interval_seconds)
            
            if self.running:
                print("\n[DAEMON] El cerebro ha estado inactivo. Activando ciclo de sueño automático...")
                try:
                    self.brain.sleep_cycle()
                except Exception as e:
                    print(f"[DAEMON] Error durante el sueño: {e}")

    def start(self):
        if self.running:
            return
        self.running = True
        # Daemon=True asegura que el hilo muera si el programa principal termina
        self.thread = threading.Thread(target=self._daemon_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            print("[DAEMON] Subconsciente detenido.")
