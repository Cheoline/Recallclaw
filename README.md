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
- **Búsqueda Vectorial en Dos Fases (RAG)**: Primero encuentra candidatos por similitud semántica global, luego los re-rankea por *Topic Fingerprint* (similitud de las palabras clave de contenido) para elegir el recuerdo correcto incluso si varias historias comparten vocabulario superficial.
- **Topic Fingerprint**: Cada recuerdo guarda un segundo vector calculado solo con sus palabras de contenido (sustantivos, verbos, nombres), sin stop words. Esto permite distinguir entre dos historias que comparten palabras comunes pero hablan de temas completamente distintos.
- **Prevención de Interferencia Semántica**: Etiqueta automáticamente los recuerdos con anclas de sujeto (`[SUJETO:YO]`, `[SUJETO:TERCERO]`) para que el motor no confunda datos del usuario con datos de personas que el usuario menciona.
- **Sanitización Nativa de Emojis**: Elimina automáticamente emojis del texto antes de comprimirlo, evitando ruido en los tensores vectoriales y el motor LAC.
- **Filtro de Calidad Semántica**: Descarta automáticamente mensajes sin contenido valioso ("hola", "ok", "gracias") para no contaminar la base de recuerdos.
- **Validación Semántica**: Un Juez interno verifica que cualquier compresión nueva mantenga el mismo significado original antes de guardarla permanentemente.
- **Sueño Automático**: Un proceso en segundo plano ejecuta ciclos de consolidación y optimización de memoria de forma autónoma.
- **La Colmena**: Intercambio criptográfico de vocabulario comprimido entre múltiples instancias (SHA-256). Las IAs comparten reglas de compresión sin compartir sus recuerdos privados.
- **Agnóstico de Modelo LLM**: Compatible con cualquier modelo local de Ollama. Configurable en una sola línea al instanciar el cerebro.

## RosettaStone — El Árbitro Global

RecallClaw incluye integración con **RosettaStone**, un servidor central (diseñado para VPS) que actúa como árbitro de vocabulario entre todas las instancias de RecallClaw en la red.

Cuando múltiples IAs aprenden a comprimir una misma palabra de formas distintas, RosettaStone recibe todas las propuestas, compara sus significados matemáticos y **conserva únicamente la versión más corta y eficiente**, distribuyéndola al resto de la red en la siguiente sincronización.

Esto permite que una IA recién creada aprenda instantáneamente las reglas de compresión que otras IAs tardaron semanas en descubrir.

> 🔜 **RosettaStone estará disponible como proyecto independiente próximamente.**

## Instalación

### Desde GitHub (última versión)
```bash
pip install git+https://github.com/Cheoline/Recallclaw.git
```

### Desde PyPI
```bash
pip install recallclaw
```

### Para desarrolladores (modificar el código)
```bash
git clone https://github.com/Cheoline/Recallclaw.git
cd Recallclaw
pip install -e .
```
> `pip install -e .` instala el paquete en modo editable desde la carpeta actual. Cualquier cambio en el código se aplica de inmediato sin reinstalar.

### Dependencias

```bash
pip install spacy sentence-transformers torch emoji
python -m spacy download es_core_news_sm
```

> **Nota sobre el modelo matemático:** La primera vez que ejecutes RecallClaw, la librería `sentence-transformers` descargará automáticamente el modelo de IA vectorial (`paraphrase-multilingual-MiniLM-L12-v2`, aprox. 470 MB). Solo requiere internet la primera vez.

Requiere [Ollama](https://ollama.com/) corriendo localmente con un modelo instalado. Por defecto buscará `gemma3:4b`, pero es totalmente agnóstico y configurable:
```bash
ollama pull gemma3:4b
# o cualquier otro modelo que tengas instalado
ollama pull llama3
```

## Uso rápido (modo básico)

```python
from recallclaw import PositronicBrain

# Configura el cerebro con tu modelo de Ollama
memoria = PositronicBrain(db_path="mi_memoria.db", llm_model="gemma3:4b")

# Guardar información
memoria.memorize("El doctor Martínez recomendó tomar agua pura todos los días.")

# Consultar en lenguaje natural
respuesta = memoria.ask("¿Qué recomendó el doctor?")
print(respuesta)
# → "Tomar agua pura todos los días."

# Activar optimización automática en segundo plano (cada 24h)
memoria.start_background_evolution(check_interval_hours=24.0)
```

## Uso con cualquier IA (modo conversacional — 3 líneas)

Esta es la forma recomendada para conectar RecallClaw a cualquier agente de IA:

```python
from recallclaw import PositronicBrain

brain = PositronicBrain(db_path="mi_memoria.db", llm_model="gemma3:4b")

# Al recibir un mensaje del usuario:
contexto = brain.get_context_for(user_message)                    # 1. Busca recuerdos y arma el system prompt
ai_response = mi_llm.chat(system=contexto, prompt=user_message)   # 2. Tu IA responde con contexto
brain.memorize_user_input(user_message)                            # 3. Solo guarda el input del usuario
```

### Métodos de alto nivel disponibles

| Método | Descripción |
|---|---|
| `memorize_user_input(msg)` | Guarda SOLO el input del usuario. Filtra emojis, mensajes triviales y respuestas de IA automáticamente. |
| `memorize_conversation(user_input, ai_response)` | Acepta el turno completo pero descarta la respuesta de la IA. Solo persiste lo que dijo el usuario. |
| `get_context_for(question)` | Busca en la memoria vectorial y entrega un `system_prompt` listo para inyectar en cualquier LLM. |
| `memorize(text, context, auto_context)` | API de bajo nivel. Acepta contexto explícito o infiere uno automáticamente. |

### Parámetros de configuración de `PositronicBrain`

| Parámetro | Por defecto | Descripción |
|---|---|---|
| `db_path` | `"positronic_brain.db"` | Ruta del archivo SQLite donde se almacenan los recuerdos. |
| `llm_model` | `"gemma3:4b"` | Nombre del modelo de Ollama que usará el Bibliotecario para responder. |
| `max_usage_limit` | `1000` | Número máximo de usos de un nodo del Lexicon antes de sellarlo y crear uno nuevo. |

## Cómo funciona la búsqueda (Anti-Confusión de Historias)

El motor usa un sistema de **búsqueda en dos fases** para garantizar que nunca mezcle recuerdos de contextos diferentes:

```
Pregunta del usuario
       │
       ▼
 Fase 1: Búsqueda vectorial
 (top 5 candidatos por similitud semántica global)
       │
       ▼
 Fase 2: Re-ranking por Topic Fingerprint
 (compara las palabras CLAVE de la pregunta con las de cada candidato)
       │
       ▼
 Candidato con mayor score combinado (50% texto + 50% tema)
       │
       ▼
 Umbral mínimo 40% — si ningún recuerdo supera el umbral,
 el motor responde "No tengo esa información" en lugar de inventar.
```

> **Ejemplo:** Si la IA guardó "El Cuento del Dragón" y "El Cuento del Pescador", y el usuario pregunta algo sobre el dragón, el motor distinguirá correctamente entre los dos aunque compartan palabras como "el", "fue", "había".

## Arquitectura

```
recallclaw/
├── memory.py        # API principal — memorize(), ask(), sleep_cycle(), métodos de alto nivel
├── lac_engine.py    # Motor de Compresión Atómica (LAC)
├── database.py      # Grafo relacional SQLite + Topic Fingerprints
├── validator.py     # Juez Semántico (sentence-transformers)
├── llm_connector.py # Conector LLM local (Ollama) — agnóstico de modelo
├── evolver.py       # Ciclos de consolidación y degradación progresiva
├── daemon.py        # Proceso autónomo de optimización en segundo plano
└── sync_engine.py   # La Colmena — intercambio de vocabulario entre IAs
```

## Licencia

MIT
