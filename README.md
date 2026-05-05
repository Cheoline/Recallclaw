# RecallClaw — Cerebro Positrónico 🧠

Sistema de memoria a largo plazo de ultra-alta compresión para inteligencia artificial. Simula los ciclos biológicos de consolidación, degradación y recuperación de recuerdos.

## ¿Qué es?

RecallClaw es una librería Python que actúa como una **memoria persistente y portátil** para cualquier agente de IA. No depende de la nube, todo el procesamiento es local.

## Características

- **Compresión Atómica (LAC)**: Reduce texto a tokens semánticos mínimos con análisis morfológico NLP (spaCy).
- **Almacenamiento Relacional**: Grafo SQLite con deduplicación de palabras (un token = un ID).
- **El Bibliotecario (RAG)**: Búsqueda vectorial por similitud de coseno para responder preguntas.
- **El Evolucionador (Sueño)**: Daemon que consolida y degrada memorias automáticamente con validación semántica.
- **La Colmena**: Intercambio criptográfico de vocabulario entre cerebros (SHA-256).
- **RosettaStone**: Árbitro central que decide qué compresión es más eficiente (ver proyecto separado).

## Instalación

```bash
git clone https://github.com/TU_USUARIO/RecallClaw.git
cd RecallClaw
pip install -e .
```

### Dependencias

```bash
pip install spacy sentence-transformers torch
python -m spacy download es_core_news_sm
```

Requiere [Ollama](https://ollama.com/) corriendo localmente con un modelo instalado:
```bash
ollama pull llama3.2:1b
```

## Uso rápido

```python
from recallclaw import PositronicBrain

cerebro = PositronicBrain(db_path="mi_memoria.db")

# Guardar un recuerdo
cerebro.memorize("El doctor Martínez recomendó tomar agua pura todos los días.")

# Preguntar
respuesta = cerebro.ask("¿Qué recomendó el doctor?")
print(respuesta)

# Activar el sueño automático (cada 24h)
cerebro.start_background_evolution(check_interval_hours=24.0)
```

## Arquitectura

```
recallclaw/
├── memory.py        # PositronicBrain — API principal
├── lac_engine.py    # Motor de Compresión Atómica (LAC)
├── database.py      # Grafo relacional SQLite
├── validator.py     # Juez Semántico (sentence-transformers)
├── llm_connector.py # Conector LLM local (Ollama)
├── evolver.py       # El Evolucionador (sueño biológico)
├── daemon.py        # Daemon de sueño automático
└── sync_engine.py   # La Colmena (aprendizaje federado)
```

## Licencia

MIT
