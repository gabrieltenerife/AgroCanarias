# AgroCanarias IA — Asistente Técnico IA para Agricultura Canaria

Asistente técnico especializado en agricultura canaria. Resuelve consultas sobre normativa fitosanitaria, cuaderno de campo, ayudas y subvenciones, exportación, denominaciones de origen y planificación meteorológica de tratamientos.

Combina un agente LLM con un sistema RAG sobre ChromaDB y herramientas MCP externas (AEMET, Tavily, Filesystem) para proporcionar respuestas fundamentadas y verificables.

---

## Arquitectura

```
┌──────────────┐     ┌──────────────────────────────────────────┐
│   Frontend   │────▶│              API (FastAPI)               │
│   Angular    │     │                                          │
│   (4200)      │     │  Agent ──▶ Tools ──▶ ChromaDB (RAG)     │
└──────────────┘     │          └─▶ MCP Servers                  │
                      │              ├─ AEMET (meteorología)      │
                      │              ├─ Tavily (búsqueda web)      │
                      │              └─ Filesystem (documentos)    │
                      └──────────────────────────────────────────┘
```

- **Agente**: `gemma4:26b` vía Ollama con system prompt especializado
- **RAG**: ChromaDB con ParentDocumentRetriever, embeddings `mxbai-embed-large`
- **Memoria**: SQLite checkpointer (LangGraph) para estado de conversación
- **Herramientas MCP**: integradas vía `langchain-mcp-adapters`
  - AEMET: datos meteorológicos oficiales (contenedor Docker)
  - Tavily: búsqueda web para alertas y convocatorias recientes
  - Filesystem: lectura de cuadernos de campo (.doc/.docx)

---

## Stack tecnológico

| Componente | Tecnología |
|---|---|
| Backend | Python 3.13, FastAPI, Uvicorn |
| LLM | OpenAI (`gpt-5.4-mini`) — ver nota abajo |
| Framework agente | LangChain, LangGraph |
| Base vectorial | ChromaDB |
| Embeddings | Ollama (`mxbai-embed-large`) |
| MCP | langchain-mcp-adapters, Docker (AEMET), npx (Tavily, Filesystem) |
| Frontend | Angular 21, TypeScript |
| Memoria | SQLite (LangGraph Checkpointer) |
| Conversión documentos | pypandoc + LibreOffice headless |

---

## Requisitos previos

- **Python** >= 3.13
- **Node.js** >= 20.x y **npm** >= 10.x
- **Ollama** corriendo en `localhost:11434` con los modelos descargados:
  ```bash
  ollama pull gemma4:26b
  ollama pull mxbai-embed-large
  ```
- **Docker** (para el contenedor AEMET-MCP)
- **LibreOffice** headless (para conversión de .doc):
  ```bash
  # Debian/Ubuntu
  sudo apt install libreoffice

  # macOS
  brew install libreoffice
  ```
- **Dependencias Python**: ver `requirements.txt`

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd PROYECTO
```

### 2. Configurar variables de entorno

Crear un archivo `.env` en la raíz del proyecto:

```env
Aemet_apiKey=<tu_api_key_aemet>
Tavily_apiKey=<tu_api_key_tavily>
OPENAI_API_KEY=<tu_api_key_openai>
```

- **AEMET**: solicitar en [opendata.aemet.es](https://opendata.aemet.es/)
- **Tavily**: obtener en [tavily.com](https://tavily.com/)
- **OpenAI**: obtener en [platform.openai.com](https://platform.openai.com/) (necesaria para el LLM por defecto)

> **Nota sobre el modelo LLM**: por defecto la demo usa **OpenAI (`gpt-5.4-mini`)** por simplicidad y calidad de respuesta. Si prefieres usar **Ollama local** (sin necesidad de clave ni conexión), edita `Agent/Agent.py:79`:
> - Comenta la línea de `ChatOpenAI(...)`
> - Descomenta la línea de `ChatOllama(model="gemma3:27b", num_ctx=50000)` (usa `gemma3` que sí existe; `gemma4` no está publicado en Ollama)
> - Asegúrate de tener el modelo descargado: `ollama pull gemma3:27b` y `ollama pull mxbai-embed-large`

### 3. Instalar dependencias Python

```bash
pip install -r requirements.txt
```

### 4. Construir imagen Docker de AEMET-MCP

```bash
docker build -t aemet-mcp <ruta-al-dockerfile-de-aemet-mcp>
```

### 5. Ingestar documentos en ChromaDB (primer vez)

Colocar los PDFs en la carpeta `Data/` y ejecutar:

```bash
python -m Rag.Ingestion
```

Esto procesa los documentos, extrae metadata con el LLM y crea el vectorstore en `Chroma_db/`.

### 6. Instalar dependencias del Frontend

```bash
cd Frontend
npm install
cd ..
```

---

## Ejecución

Se necesitan **dos terminales**:

### Backend

```bash
cd PROYECTO
uvicorn api.main:app --reload
```

La API arranca en `http://localhost:8000`. En el primer arranque se inicializan las conexiones MCP (Docker + npx), lo cual puede tardar unos segundos.

### Frontend

```bash
cd PROYECTO/Frontend
npm start
```

La aplicación estará disponible en `http://localhost:4200`.

---

## Estructura del proyecto

```
PROYECTO/
├── api/                    # API REST (FastAPI)
│   ├── main.py             # Endpoints y lifespan
│   ├── dependencies.py     # Inyección de dependencias (agente, MCP)
│   └── models.py           # Modelos Pydantic (request/response)
├── Agent/
│   ├── Agent.py            # Creación del agente LangGraph
│   └── Tools.py            # Herramientas RAG especializadas
├── Integrations/
│   └── Mpcs.py             # Cliente MCP (AEMET, Tavily, Filesystem)
├── Rag/
│   ├── Ingestion.py        # Pipeline de ingesta de documentos
│   └── Retriever.py        # Búsqueda thread-safe en ChromaDB
├── Chroma_db/               # Base vectorial persistente
├── Memory/                  # Base de datos SQLite (checkpoints)
├── Frontend/                # Angular 21 (SPA)
│   └── src/app/
│       ├── app.ts           # Componente raíz
│       ├── services/        # ChatService (comunicación con API)
│       ├── models/          # Interfaces TypeScript
│       └── components/     # Sidebar, MessageList, MessageInput
├── app.py                   # Punto de entrada CLI (debug)
├── .env                     # Variables de entorno (no versionado)
└── README.md
```

---

## API Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/chat/stream` | Enviar mensaje al agente (SSE streaming) |
| `POST` | `/conversations` | Crear nueva conversación |
| `GET` | `/conversations` | Listar conversaciones |
| `GET` | `/conversations/{thread_id}` | Obtener historial de una conversación |
| `DELETE` | `/conversations/{thread_id}` | Eliminar conversación |

---

## Licencia

Uso interno — CIFP César Manrique proyecto final Gabriel González 
