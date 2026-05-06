# RecallClaw — Positronic Memory System 🧠

Sistema de memoria semántica a largo plazo para agentes de inteligencia artificial. Permite a cualquier IA guardar, buscar y recuperar información de forma precisa, comprimida y completamente local, sin depender de servicios en la nube.

## ¿Qué hace?

RecallClaw actúa como una **capa de memoria persistente** que cualquier agente de IA puede importar. Cuando una IA necesita recordar algo, lo entrega a RecallClaw. Cuando necesita buscar algo, RecallClaw lo recupera en lenguaje natural exacto.

El sistema simula los ciclos biológicos de la memoria humana:
- **Aprende** comprimiendo la información al mínimo posible sin perder su significado
- **Consolida** eliminando el texto original de recuerdos antiguos, conservando solo su esencia matemática
- **Evoluciona** intentando comprimir aún más con el tiempo, validando que el significado no se pierda
- **Responde** reconstruyendo la información en lenguaje natural cuando se le consulta

## Características

- **Compresión Atómica (LAC)**: Reduce texto a tokens semánticos mínimos usando análisis morfológico NLP (spaCy). Ejemplo: `"El doctor recomendó agua"` → `doctorM recomendó aguaF`
- **Almacenamiento Relacional**: Grafo SQLite con deduplicación de palabras. Una palabra = un ID. Si 1.000 recuerdos usan la palabra "agua", se guarda una sola vez.
- **Búsqueda Vectorial (RAG)**: Convierte preguntas en vectores matemáticos y los compara con la memoria almacenada para recuperar el recuerdo más relevante.
- **Validación Semántica**: Un Juez interno verifica que cualquier compresión nueva mantenga el mismo significado original antes de guardarla permanentemente.
- **Sueño Automático**: Un proceso en segundo plano ejecuta ciclos de consolidación y optimización de memoria de forma autónoma.
- **La Colmena**: Intercambio criptográfico de vocabulario comprimido entre múltiples instancias (SHA-256). Las IAs comparten reglas de compresión sin compartir sus recuerdos privados.

## RosettaStone — El Árbitro Global

RecallClaw incluye integración con **RosettaStone**, un servidor central (diseñado para VPS) que actúa como árbitro de vocabulario entre todas las instancias de RecallClaw en la red.

Cuando múltiples IAs aprenden a comprimir una misma palabra de formas distintas, RosettaStone recibe todas las propuestas, compara sus significados matemáticos y **conserva únicamente la versión más corta y eficiente**, distribuyéndola al resto de la red en la siguiente sincronización.

Esto permite que una IA recién creada aprenda instantáneamente las reglas de compresión que otras IAs tardaron semanas en descubrir.

> 🔜 **RosettaStone estará disponible como proyecto independiente próximamente.**

## Instalación

```bash
git clone https://github.com/Cheoline/Recallclaw.git
cd Recallclaw
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
pip ricallclaw

from recallclaw import PositronicBrain

memoria = PositronicBrain(db_path="mi_memoria.db")

# Guardar información
memoria.memorize("El doctor Martínez recomendó tomar agua pura todos los días.")

# Consultar en lenguaje natural
respuesta = memoria.ask("¿Qué recomendó el doctor?")
print(respuesta)
# → "Tomar agua pura todos los días."

# Activar optimización automática en segundo plano (cada 24h)
memoria.start_background_evolution(check_interval_hours=24.0)
```

## Arquitectura

```
recallclaw/
├── memory.py        # API principal — memorize(), ask(), sleep_cycle()
├── lac_engine.py    # Motor de Compresión Atómica (LAC)
├── database.py      # Grafo relacional SQLite
├── validator.py     # Juez Semántico (sentence-transformers)
├── llm_connector.py # Conector LLM local (Ollama)
├── evolver.py       # Ciclos de consolidación y degradación progresiva
├── daemon.py        # Proceso autónomo de optimización en segundo plano
└── sync_engine.py   # La Colmena — intercambio de vocabulario entre IAs
```

## Licencia

MIT
