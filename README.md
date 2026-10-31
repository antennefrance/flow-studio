# FLOW Studio 🌊

> **Universal Streaming Runtime & Desktop Studio for Large Language Models on Apple Silicon**  
> Run 141B MoE models under a fixed 2.5 GB – 3.5 GB RAM footprint with zero-copy Metal streaming, and deploy 27B–33B Dense models in-memory via Pyrite zero-byte mixed-precision quantization.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Release](https://img.shields.io/badge/Release-v1.1.0--macOS%20DMG-blueviolet.svg)](https://github.com/antennefrance/flow-studio/releases/latest)
[![Organization](https://img.shields.io/badge/Organization-AntenneFrance-emerald.svg)](https://antennefrance.com)
[![ORCID](https://img.shields.io/badge/ORCID-0009--0000--3224--0103-green.svg)](https://orcid.org/0009-0000-3224-0103)
[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.23814635-blue.svg)](https://doi.org/10.5281/zenodo.23814635)
[![OpenAI Compatible](https://img.shields.io/badge/API-OpenAI%20%2F%20Ollama%20Compatible-orange.svg)](#local-api-usage)

---

## 💡 Overview & Engineering Reality

Conventional inference runtimes (llama.cpp, vLLM, transformers) presuppose that **$\text{RAM} > \text{Model Size}$**. When loading a 141B model on a 16GB RAM machine, operating systems either crash due to Out-Of-Memory (OOM) kills or freeze indefinitely due to synchronous swap thrashing.

**FLOW (Fast Lossless Offloaded Weights)** addresses the unified memory constraint of consumer Apple Silicon hardware through deterministic, user-space ring-buffered streaming and zero-copy Metal memory slicing.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       FLOW Dual Architecture                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Mode 1: ⚡ FLOW-Direct (Zero-Copy MoE Streaming)                        │
│  ├── Target: Sparse MoE Models (e.g., Mixtral 8x22B, DeepSeek)          │
│  ├── Architecture: mmap directly sliced into Apple Metal shared buffer  │
│  ├── Latency: 68 µs slice acquisition overhead per routed expert       │
│  └── RAM Footprint: Fixed 2.5 GB – 3.5 GB (Only active Top-k loaded)   │
│                                                                         │
│  Mode 2: 🚀 FLOW-Boost (In-Flight Byte-Shuffle + Zstd Codec)            │
│  ├── Target: .gguf.flow and .safetensors.flow containers                │
│  ├── Innovation: Byte-plane transposition (Sign/Exponent/Mantissa)      │
│  ├── BF16/FP16 Compression: ~31.5% size reduction (1.46x bus bandwidth)│
│  └── Quantized (2-bit/4-bit): ~10% size reduction (entropy bounded)     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### ⚠️ Physical Constraints & Model Placement Guide

To maintain engineering transparency, the relationship between model architecture, memory bandwidth, and I/O bus speed must be respected:

1. **Dense Models (27B–33B, e.g., Nanbeige 33B, Qwen 27B):**
   * *Physical Reality:* Dense models require 100% parameter traversal per generated token. Streaming a 30 GB uncompressed Dense model across a 5.5 GB/s NVMe bus yields a physical ceiling of:
     $$\text{Latency} \approx \frac{30\text{ GB}}{5.5\text{ GB/s}} \approx 5.45\text{ s/token} \implies \mathbf{0.18\text{ tokens/s}}$$
   * *Recommended Strategy:* **Do not stream Dense models from SSD.** Instead, compress them via **Pyrite** (sensitivity-aware zero-byte mixed-precision quantization) down to **9.8 GB – 10.7 GB** and keep them **fully resident in Unified Memory**, achieving interactive speeds of **15 – 25 tokens/s**.
2. **Mixture-of-Experts (MoE) Models (141B, e.g., Mixtral 8x22B):**
   * *Physical Reality:* Only active routed experts (e.g., Top-2 out of 8, ~39B active params) are executed per token.
   * *Recommended Strategy:* **Use FLOW-Direct / FLOW-Boost.** Keep the attention backbone and router resident in 2.5 GB RAM, and stream the active expert slices on-demand via zero-copy mmap. This enables 141B models to execute cleanly on 16GB Macs without OOM.

---

## 🚀 Quick Start

### 1. Download macOS Native App (.dmg Installer)
Download **[`FLOW_Studio_1.1.0_macOS_Installer.dmg`](FLOW_Studio_1.1.0_macOS_Installer.dmg)** directly from this repository or the [Releases page](https://github.com/antennefrance/flow-studio/releases).  
*Native Apple Silicon app, signed by `Developer ID Application: L'ASSOCIATION A BUT NON LUCRATIF ANTENNEFRANCE`.*

### 2. One-Click Launchers (No Terminal Required)

* **macOS (Apple Silicon M1/M2/M3/M4):**  
  Double-click **`FLOW_Studio.command`** in Finder.  
  *(Initializes native Metal telemetry, starts the engine, and automatically opens `http://127.0.0.1:8080` in your default browser).*

* **Windows 10/11 (CUDA / DirectML / CPU):**  
  Double-click **`FLOW_Studio.bat`** in Windows Explorer.  
  *(Auto-detects Win32 memory telemetry via `GlobalMemoryStatusEx` and launches the UI).*

### 3. Manual CLI Launch

```bash
# Clone the repository
git clone https://github.com/antennefrance/flow-studio.git
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
      {"role": "user", "content": "Explain the difference between in-memory quantization and out-of-core MoE streaming."}
    ],
    "max_tokens": 256
  }'
```

---

## 📦 Converting Models to FLOW-Boost (.flow)

To convert standard Safetensors or GGUF files to the bandwidth-multiplied `.flow` container:

```bash
# Convert a GGUF model to GGUF-FLOW
python flow_converter.py input_model.gguf models_flow/input_model.gguf.flow

# Convert Safetensors to Safetensors-FLOW
python flow_converter.py model.safetensors models_flow/model.safetensors.flow
```

* **Codec:** Lossless Byte-Shuffle transposition + Zstandard Level 1 ($\epsilon \equiv 0.0$ bitwise exact match).
* **BF16 / FP16 Tensors:** ~31.5% size cut (1.46x effective bus bandwidth boost due to clustered exponent planes).
* **2-bit / 4-bit Packed Tensors:** ~8%–12% size cut (due to high entropy in quantized representations).

---

## 🏛️ Prior Art & Academic Context

FLOW builds upon and acknowledges foundational prior work in weight offloading and compression:
* **Flash Offloading & Layer Streaming:** Apple's *LLM in a Flash* (Alizadeh et al., 2023), *FlexGen* (Sheng et al., 2023), *PowerInfer* (Song et al., 2024), and *AirLLM*. FLOW differentiates itself by focusing on Unified Memory zero-copy Metal buffer slicing without CPU-GPU PCIe bounce buffers.
* **Lossless Floating-Point Compression:** The *Blosc* filter suite, *IBM ZipNN* (2024), and *DFloat11* (NeurIPS 2024). FLOW adapts byte-shuffling into a streaming runtime container (`.flow`) targeting Apple Silicon unified pipelines.
* **Zero-Byte Mixed-Precision Quantization:** Project Pyrite formulates an exact zero-byte reallocation recipe ($\Delta = 0\text{ B}$) on Apple MLX affine kernels.

### Technical Attribution:
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
