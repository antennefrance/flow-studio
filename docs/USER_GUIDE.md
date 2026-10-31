# FLOW Studio User Guide 📘

Welcome to **FLOW Studio**, the universal streaming runtime for running large language models on consumer hardware.

---

## 💻 Installation

### macOS (Apple Silicon M1/M2/M3/M4)

1. Download **`FLOW_Studio_1.0.0_macOS_Installer.dmg`** directly from this repository or the [Releases page](https://github.com/antennefrance/flow-studio/releases).
2. Double-click the downloaded `.dmg` file.
3. Drag **FLOW Studio** into your **Applications** folder.
4. Launch FLOW Studio from your Applications folder or Spotlight.

*Note: The application is signed by `Developer ID Application: L'ASSOCIATION A BUT NON LUCRATIF ANTENNEFRANCE`.*

### Windows 10/11

1. Clone or download this repository.
2. Double-click **`FLOW_Studio.bat`**.
3. FLOW Studio will start and automatically open in your default browser at `http://127.0.0.1:8080`.

---

## 🌊 Streaming Modes

FLOW Studio supports two execution modes:

* **⚡ FLOW-Direct:** Use your existing standard `.gguf` or `.safetensors` model files directly without any conversion or waiting time.
* **🚀 FLOW-Boost:** Use `.flow` format files to accelerate SSD transfer speeds on PCIe-bandwidth-constrained devices.

---

## 🔌 Connecting External Tools

FLOW Studio runs a standard OpenAI/Ollama compatible server on `http://localhost:8080/v1`.

### Cursor & VS Code (Continue Extension)
* **Base URL:** `http://localhost:8080/v1`
* **API Key:** Any string (e.g. `flow`)
* **Model ID:** Select from active models in `/v1/models` (e.g. `deepseek-direct`)

### Obsidian & Open WebUI
* Configure your local LLM provider URL to `http://localhost:8080/v1`.
