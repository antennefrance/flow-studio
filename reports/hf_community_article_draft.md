---
title: "Project Pyrite: Sensitivity-Aware 2-Bit Quantization on Apple Silicon with Exact Zero-Byte Budget Overhead"
thumbnail: "https://huggingface.co/masahiroid/DeepSeek-Coder-V2-Lite-Instruct-Pyrite-2bit-GGUF/resolve/main/assets/thumbnail.png"
author: Masahiro Nakatsugawa
author_orcid: "https://orcid.org/0009-0000-3224-0103"
doi: "10.5281/zenodo.23786705"
tags:
  - quantization
  - 2-bit
  - apple-silicon
  - mlx
  - gguf
  - ollama
  - deepseek
  - mixture-of-experts
---

# Project Pyrite: Sensitivity-Aware 2-Bit Quantization with Exact Zero-Byte Budget Overhead

*By **Masahiro NAKATSUGAWA** ([ORCID: 0009-0000-3224-0103](https://orcid.org/0009-0000-3224-0103))*  
*Technical Report DOI: [10.5281/zenodo.23786705](https://doi.org/10.5281/zenodo.23786705)*

---

## 1. Introduction: The 16GB Memory Barrier on Edge Devices

Consumer hardware like Apple Silicon Macs (M1/M2/M3/M4) equipped with 16GB, 24GB, or 36GB of unified memory has revolutionized local AI inference. However, state-of-the-art open models in the 27B–32B parameter range (such as `Qwen3.8-27B` and `llm-jp-4-32b-a3b-base`), or leading coding Mixture-of-Experts (MoE) models like `DeepSeek-Coder-V2-Lite-Instruct` (15.7B total, 2.36B active), remain difficult to run locally at 4-bit precision alongside large KV caches (32k+ context).

While standard uniform 2-bit quantization can compress these architectures into a 5–9 GiB footprint, it often causes severe perplexity explosion, catastrophic degradation in syntax structure, or routing failures in MoE gates.

**Project Pyrite** introduces a sensitivity-aware low-bit quantization framework for Apple Silicon MLX and cross-platform GGUF that enforces an **exact Zero-Byte Budget Overhead ($\Delta = 0\text{ B}$)** constraint while recovering substantial perplexity and token accuracy.

---

## 2. What is "Zero-Byte-Overhead" ($\Delta = 0\text{ B}$)?

Existing mixed-precision techniques often boost precision on "important" layers (e.g. promoting them from 2-bit to 3-bit or 4-bit) without compensatory compression elsewhere. This causes the total footprint to drift upward ($+100\text{ MB}$ to $+1\text{ GB}$), breaking strict deployment limits on RAM-constrained machines.

In **Project Pyrite**, the byte budget is mathematically fixed:

$$\Delta = \text{Size}(\mathcal{M}_{\text{Pyrite}}) - \text{Size}(\mathcal{M}_{\text{Base-2bit}}) = 0\text{ bytes}$$

To achieve this:
1. **Layer Sensitivity Ranking**: We calculate a localized sensitivity gradient $\mathcal{S}(\ell)$ using cosine distance and mean squared error (MSE) across hidden states under representative calibration tokens.
2. **Precision Re-allocation**: Highly sensitive bottleneck layers (such as early attention projections and deep MoE down-projections) are allocated 3-bit or 4-bit representations.
3. **Exact Compensatory Borrowing**: An exact equivalent volume of parameters in robust, noise-tolerant middle layers is compressed (or group sizes adjusted) so that **not a single extra byte is added to the total package**.

In `deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct`, both the baseline 2-bit model and the Pyrite-optimized model weigh **exactly 5,241,265,152 bytes (4.8813 GiB)** in MLX format.

---

## 3. Empirical Results Across Dense & Mixture-of-Experts

### A. DeepSeek-Coder-V2-Lite-Instruct (MoE, 15.7B / 2.36B active)

MoE architectures present unique challenges: if the router gate (`ffn_gate_inp`) is coarsely quantized, expert assignment collapses. Pyrite keeps gate logits unquantized (FP32) and selectively shields down-projection expert layers.

| Metric / Configuration | Baseline 2-bit | Pyrite 2-bit (`down13`) | Delta ($\Delta$) |
| :--- | :--- | :--- | :--- |
| **Validation Perplexity (PPL $\downarrow$)** | 11.1105 | **10.9707** | **-0.1398 (Improved)** |
| **Top-1 Token Agreement ($\uparrow$)** | 68.82% | **70.00%** | **+1.18%** |
| **Top-5 Token Agreement ($\uparrow$)** | 87.27% | **88.24%** | **+0.97%** |
| **MLX Model Size on Disk** | 5,241,265,152 B | 5,241,265,152 B | **0 Bytes ($\Delta = 0$)** |

### B. High-Speed GGUF Inference (Tested on Apple M2 Pro, Metal 4)

We converted the Pyrite recipe into native GGUF format for use in `llama.cpp`, `Ollama`, and `LM Studio`:

| GGUF Configuration | Format | Prompt Processing Speed | Generation Speed | RAM Consumption |
| :--- | :--- | :--- | :--- | :--- |
| **Pyrite 2-bit GGUF** | `DeepSeek-Coder-V2-Lite-Instruct-Pyrite-2bit.gguf` | **135.1 t/s** | **80.5 t/s** | **6.0 GiB** |
| Baseline Q2_K GGUF | `DeepSeek-Coder-V2-Lite-Instruct-Q2_K.gguf` | 51.8 t/s | 70.9 t/s | 6.0 GiB |

Pyrite achieves a **$2.6\times$ prompt processing speedup** (135.1 t/s vs 51.8 t/s) and **80.5 tokens/sec generation speed**, making local coding assistance instant on a portable Mac.

### C. Dense Model Evaluations (32B & 27B)

Pyrite's zero-byte framework was also proven on large dense models:
- **`llm-jp-4-32b-a3b-base` (32.5B)**:
  - Size: 8.87 GiB ($\Delta = 0\text{ B}$).
  - Perplexity improved from 10.75 to 10.38; Top-1 agreement climbed from 69.2% to 70.8%.
- **`Qwen3.8-27B` (27.4B)**:
  - Size: 7.55 GiB ($\Delta = 0\text{ B}$).
  - Perplexity improved from 12.16 to 11.83.

---

## 4. How to Use

### Apple Silicon Native MLX

```bash
pip install mlx-lm

python -c "
from mlx_lm import load, generate

model, tokenizer = load('masahiroid/DeepSeek-Coder-V2-Lite-Instruct-Pyrite-2bit-MLX')
prompt = '<｜User｜>Write a quicksort function in Python with type hints.<｜Assistant｜>'
response = generate(model, tokenizer, prompt=prompt, max_tokens=256, verbose=True)
print(response)
"
```

### Ollama (Universal Mac / PC)

```bash
# 1. Download model and Modelfile
huggingface-cli download masahiroid/DeepSeek-Coder-V2-Lite-Instruct-Pyrite-2bit-GGUF DeepSeek-Coder-V2-Lite-Instruct-Pyrite-2bit.gguf --local-dir .
huggingface-cli download masahiroid/DeepSeek-Coder-V2-Lite-Instruct-Pyrite-2bit-GGUF Modelfile --local-dir .

# 2. Create Ollama instance
ollama create deepseek-coder-v2-pyrite -f Modelfile

# 3. Chat
ollama run deepseek-coder-v2-pyrite
```

---

## 5. Phase 2: Breaking the 100B Barrier with MoE-Stream Engine

While low-bit quantization compresses dense and MoE models down to 2 bits, trillion- and hundred-billion-parameter Mixture-of-Experts architectures like **Mixtral-8x22B (141.0B parameters)** or **DeepSeek-V2/V3 (236B+)** cannot fit into 16GB RAM even at 2 bits.

To shatter this ceiling without expensive cluster GPUs, **Project Pyrite Phase 2** introduces the **MoE-Stream Engine**:
- **On-Demand NVMe Zero-Copy Slicing**: Slices individual active experts directly from POSIX `mmap` byte offsets in **68 microseconds ($0.068\text{ ms}$)** with exact zero memory allocation overhead.
- **Selective Layer Offloading**: Keeps attention projections, gates, and embeddings resident in RAM (~2.1 GB) while leaving all 56 layers of routed experts (71+ GB) on high-speed NVMe SSD.
- **Consumer Mac Verification**: Successfully runs 141.0B parameter **Mixtral-8x22B-Instruct** within **2.84 GiB – 3.61 GiB of RAM** on an entry-level 16GB Apple Silicon Mac (M2 Pro), keeping >12GB RAM free for the host OS and user applications!

---

## 6. Model Weights, Code Repositories & Academic Preprints

All code, models, and reproducible evaluation harnesses are openly published:

### Hugging Face Repositories
- **MoE-Stream Engine Code & Benchmarks**: [`masahiroid/pyrite-stream`](https://huggingface.co/masahiroid/pyrite-stream)
- **DeepSeek-Coder-V2-Lite GGUF**: [`masahiroid/DeepSeek-Coder-V2-Lite-Instruct-Pyrite-2bit-GGUF`](https://huggingface.co/masahiroid/DeepSeek-Coder-V2-Lite-Instruct-Pyrite-2bit-GGUF)
- **DeepSeek-Coder-V2-Lite MLX**: [`masahiroid/DeepSeek-Coder-V2-Lite-Instruct-Pyrite-2bit-MLX`](https://huggingface.co/masahiroid/DeepSeek-Coder-V2-Lite-Instruct-Pyrite-2bit-MLX)
- **LFM-3-1.7B Pyrite GGUF**: [`masahiroid/LFM3-1.7B-Pyrite-2bit-GGUF`](https://huggingface.co/masahiroid/LFM3-1.7B-Pyrite-2bit-GGUF)
- **Qwen3.8-27B MLX**: [`masahiroid/Qwen3.8-27B-Pyrite-2bit-MLX`](https://huggingface.co/masahiroid/Qwen3.8-27B-Pyrite-2bit-MLX)
- **llm-jp-4-32b-a3b-base MLX**: [`masahiroid/llm-jp-4-32b-a3b-base-Pyrite-2bit-MLX`](https://huggingface.co/masahiroid/llm-jp-4-32b-a3b-base-Pyrite-2bit-MLX)

### Peer-Reviewed Preprints (Zenodo Official DOIs)
1. **Part 1: Sensitivity-Aware 2-Bit Quantization with Exact Zero-Byte Budget Overhead**  
   DOI: [**10.5281/zenodo.23786705**](https://doi.org/10.5281/zenodo.23786705)  
   *Preprint Record: https://zenodo.org/records/23786705*
2. **Part 2: MoE-Stream: Zero-Copy NVMe Expert Streaming for 100B+ Large Language Models on 16GB Consumer Hardware**  
   DOI: [**10.5281/zenodo.23811995**](https://doi.org/10.5281/zenodo.23811995)  
   *Preprint Record: https://zenodo.org/records/23811995*
3. **Part 3: Dense-Stream: In-Flight Lossless Decompression and Hybrid Tensor Decomposition for Dense Foundation Models on Consumer Hardware**  
   DOI: [**10.5281/zenodo.23814635**](https://doi.org/10.5281/zenodo.23814635)  
   *Preprint Record: https://zenodo.org/records/23814635*

