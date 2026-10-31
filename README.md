# FLOW Studio 🌊

> **Universal Out-of-Core Streaming Runtime & Desktop Studio for Large Language Models**  
> Run 141B MoE and 32B models on consumer 16GB Apple Silicon Macs and Windows PCs under a fixed 2.5 GB – 3.5 GB RAM footprint with Zero OOM.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Organization](https://img.shields.io/badge/Organization-AntenneFrance-emerald.svg)](https://antennefrance.com)
[![ORCID](https://img.shields.io/badge/ORCID-0009--0000--3224--0103-green.svg)](https://orcid.org/0009-0000-3224-0103)
[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.23814635-blue.svg)](https://doi.org/10.5281/zenodo.23814635)
[![OpenAI Compatible](https://img.shields.io/badge/API-OpenAI%20%2F%20Ollama%20Compatible-orange.svg)](#local-api-usage)

---

## 💡 Overview

Conventional inference runtimes (llama.cpp, vLLM, transformers) presuppose that **$\text{RAM} > \text{Model Size}$**. When loading a 32B or 141B model on a 16GB RAM machine, operating systems either crash due to Out-Of-Memory (OOM) kills or freeze indefinitely due to synchronous swap page thrashing.

**FLOW (Fast Lossless Offloaded Weights)** fundamentally decouples RAM from NVMe storage through deterministic, user-space ring-buffered streaming.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      FLOW Dual Streaming Pipeline                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Mode 1: ⚡ FLOW-Direct (Zero-Copy Non-Compressed Streaming)            │
│  ├── Target: Any standard .gguf or .safetensors (Zero Conversion)       │
│  ├── Architecture: Deterministic Ping-Pong DMA Ring-Buffers             │
│  └── RAM Footprint: Fixed 2.5 GB – 3.5 GB (O(1 layer) bounded)          │
│                                                                         │
│  Mode 2: 🚀 FLOW-Boost (In-Flight Lossless Compressed Streaming)         │
│  ├── Target: .gguf.flow and .safetensors.flow containers                │
│  ├── Innovation: Byte-Shuffling + Parallel Streaming Zstandard          │
│  └── Performance: 2.4x Effective PCIe/NVMe Bus Bandwidth Multiplication│
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. One-Click Launchers (Zero Terminal Setup)

* **macOS (Apple Silicon M1/M2/M3/M4):**  
  Double-click **`FLOW_Studio.command`** in Finder.  
  *(Initializes native Metal telemetry, starts the engine, and automatically opens `http://127.0.0.1:8080` in your default browser).*

* **Windows 10/11 (CUDA / DirectML / CPU):**  
  Double-click **`FLOW_Studio.bat`** in Windows Explorer.  
  *(Auto-detects Win32 memory telemetry via `GlobalMemoryStatusEx` and launches the UI).*

### 2. Manual CLI Launch

```bash
# Clone the repository
git clone https://github.com/masahiroid/flow-studio.git
cd flow-studio

# Install lightweight dependencies
pip install -r requirements.txt

# Start the universal server (Default: Port 8080)
python pyrite_app.py
```

Open your browser at `http://127.0.0.1:8080`.

---

## 🔌 Local API Usage (OpenAI & Ollama Compatible)

FLOW Studio exposes standard OpenAI-compatible endpoints on `http://localhost:8080/v1`, allowing instant drop-in integration with **Cursor, VS Code Continue, Obsidian, Open WebUI**, and other tools.

### List Active Streaming Models
```bash
curl http://localhost:8080/v1/models
```

### Chat Completion Request
```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-direct",
    "messages": [
      {"role": "user", "content": "Explain how FLOW streaming eliminates OOM crashes on 16GB RAM."}
    ],
    "max_tokens": 256
  }'
```

---

## 📦 Converting Models to FLOW-Boost (.flow)

To convert standard Safetensors or GGUF files to the bandwidth-multiplied `.flow` format:

```bash
# Convert a GGUF model to GGUF-FLOW
python flow_converter.py input_model.gguf models_flow/input_model.gguf.flow

# Convert Safetensors to Safetensors-FLOW
python flow_converter.py model.safetensors models_flow/model.safetensors.flow
```

* Compression: Lossless ($\epsilon \equiv 0.0$ bitwise exact match).
* Space reduction: ~31.5% size cut.
* Bandwidth: Effective PCIe read speed boosted up to 2.4x.

---

## 🏛️ Research & Attribution

* **Chief Investigator:** Masahiro NAKATSUGAWA (中津川 昌弘) / [ORCID: 0009-0000-3224-0103](https://orcid.org/0009-0000-3224-0103)
* **Organization:** AntenneFrance (L'Association à but non lucratif AntenneFrance) / n.p.minerva & Co. (`tip.co.jp`)
* **Consortium Membership:** Member of NII LLM-jp Consortium (National Institute of Informatics, Japan)

### Technical Reports (Open Access DOIs):
1. **Phase 1 (Zero-Byte Overhead Quantization):** [10.5281/zenodo.23786705](https://doi.org/10.5281/zenodo.23786705)
2. **Phase 2 (MoE-Stream Out-of-Core Architecture):** [10.5281/zenodo.23811995](https://doi.org/10.5281/zenodo.23811995)
3. **Phase 3 (Dense Lossless Codec & Bandwidth Multiplication):** [10.5281/zenodo.23814635](https://doi.org/10.5281/zenodo.23814635)

---

## 📄 License

Licensed under the Apache License, Version 2.0 (the "License"). See [LICENSE](LICENSE) for details.

