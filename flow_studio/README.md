# FLOW Studio: Universal Streaming Inference Server

**FLOW Studio** is an open-source, local inference workstation and API server designed to stream 100B+ MoE and Dense foundation models on consumer Apple Silicon Macs (16GB RAM) under a strict physical memory ceiling (< 3.5GB).

Built on the **FLOW** (**F**ast **L**ossless **O**ffloaded / **O**verlapped **W**eights) architecture with dual extensions: `.safetensors.flow` and `.gguf.flow`.

---

## 🏛️ Architecture & Clean Design Principles

This codebase strictly adheres to the **Single Responsibility Principle (SRP)** and **Clean Layered Architecture**:

```
flow_studio/
├── constants.py              # Zero magic numbers: fixed hardware page sizes, MIME types, protocol strings
├── config.py                 # Strongly-typed configuration via AppSettings (FLOW_HOST, FLOW_PORT)
├── domain/                   # Enterprise Domain Layer (Pure POPO entities & protocols)
│   ├── models.py             # ModelMetadata, MemoryTelemetry, ChatMessage, DTOs
│   └── interfaces.py         # Abstract protocols: TelemetryProviderProtocol, InferenceEngineProtocol
├── services/                 # Application Services Layer (Use Cases)
│   ├── telemetry_service.py  # Coordinates hardware sampling and DTO serialization
│   └── inference_service.py  # Coordinates catalog lookups and token streaming
├── infrastructure/           # Infrastructure Layer (Concrete adapters)
│   ├── macos_telemetry.py    # Native sysctl & vm_stat parser (zero external C-extensions)
│   └── flow_engine.py        # Streaming inference engine adapter
├── api/                      # Presentation Layer (FastAPI Routers)
│   ├── routes_ui.py          # Static application delivery
│   ├── routes_telemetry.py   # /api/telemetry endpoint
│   ├── routes_chat.py        # /api/generate streaming endpoint
│   └── routes_openai.py      # /v1/models & /v1/chat/completions (OpenAI/Ollama compatibility)
├── static/                   # Static Frontend Assets (Zero inline CSS / Zero inline JS)
│   ├── index.html            # Semantic HTML5 layout
│   ├── css/style.css         # Glassmorphism dark theme with CSS custom properties
│   └── js/app.js             # Modular ES6 controller with SSE streaming
├── app.py                    # FastAPI Application Factory
└── main.py                   # CLI Entrypoint with argument parsing
```

---

## 🚀 Running the Server

### Option A: Finder Double-Click (macOS)
Double-click `FLOW_Studio.command` in the project root. It will automatically start the server and open your default browser to `http://127.0.0.1:8080`.

### Option B: Command Line Interface
```bash
python3 -m flow_studio.main --host 127.0.0.1 --port 8080
```

---

## 🔌 API Endpoints

* **Web Interface:** `GET /`
* **Telemetry:** `GET /api/telemetry`
* **OpenAI / Ollama Compatibility:**
  * `GET /v1/models`
  * `POST /v1/chat/completions` (Supports `"stream": true` and `"stream": false`)

---

## 📜 Citations & Research DOIs
* Phase 1: Sensitivity-Aware 2-Bit Quantization ([DOI: 10.5281/zenodo.23786705](https://doi.org/10.5281/zenodo.23786705))
* Phase 2: MoE-Stream Engine ([DOI: 10.5281/zenodo.23811995](https://doi.org/10.5281/zenodo.23811995))
* Phase 3: Dense Lossless Codec ([DOI: 10.5281/zenodo.23814635](https://doi.org/10.5281/zenodo.23814635))

