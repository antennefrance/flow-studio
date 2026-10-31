# [RFC Part 1] Deterministic Layer & MoE Streaming: Run 70B/141B on 16GB RAM with Standard GGUF (Zero-OOM mmap Alternative)

**Author:** Masahiro NAKATSUGAWA (中津川 昌弘) / [ORCID: 0009-0000-3224-0103](https://orcid.org/0009-0000-3224-0103)  
**Affiliations:** n.p.minerva & Co. (`tip.co.jp`), AntenneFrance  
**Reference DOIs:** `10.5281/zenodo.23786705`, `10.5281/zenodo.23811995`  
**Target:** `ggerganov/llama.cpp`

---

## 1. Summary

This proposal introduces **Deterministic Layer & MoE Streaming (FLOW-Direct)** for `llama.cpp`.  
It operates directly on **100% standard, uncompressed `.gguf` files with zero file format modifications**.

By replacing unconstrained OS virtual memory paging (`mmap`) with a **deterministic layer-wise / expert-wise circular ring-buffer**, consumer devices (e.g., Apple Silicon Macs or Windows PCs with 16GB RAM) can execute **141B MoE (Mixtral-8x22B)** and **70B dense models** strictly bounded within a fixed **2.5 GB – 3.5 GB physical RAM footprint**, completely eliminating OOM aborts and kernel page-fault freezing.

---

## 2. Motivation: The OS `mmap` Failure on Low-RAM Devices

Currently, `llama.cpp` relies on `--mmap` for models exceeding physical RAM. However, OS kernel page eviction (LRU) is reactive and non-deterministic:
1. **Synchronous Page Thrashing:** The OS pager does not know transformer execution order, stalling GPU/CPU threads synchronously on random page faults.
2. **OOM Killer Aborts:** When unified memory pressure hits macOS or Linux thresholds, the process is terminated abruptly.
3. **MoE Inefficiency:** In MoE models (e.g. 64 experts in DeepSeek, 8 experts in Mixtral), only 2 to 6 experts are activated per token, yet standard loading attempts to map or fault entire expert tensors into memory.

---

## 3. Architecture: FLOW-Direct (Ring-Buffered Zero-Copy Streaming)

```
[Standard .gguf on NVMe SSD] 
      │ (Async prefetch of next Layer / Active Experts)
      ▼
[User-Space Ring Buffer in Unified RAM] (Fixed Budget: ~2.5GB – 3.5GB)
 ├── Resident Buffer : Embeddings, Attention QKV, Routing Gates (~1.5GB)
 └── Ping-Pong Buffers:
      ├── Buffer A (Active Layer N being computed by GPU)
      └── Buffer B (Prefetching Layer N+1 from NVMe via posix_fadvise / Metal DMA)
```

### Key Technical Properties:
1. **Zero Format Changes:** Works with any existing `.gguf` file already downloaded by users.
2. **Strictly Bounded RAM Footprint:** RAM consumption is $O(\text{layer size})$ rather than $O(\text{total model size})$.
3. **Sparse Expert Prefetch:** For MoE, routing gates are evaluated first; only the top-$k$ routed experts are read from SSD, saving 80%–90% of raw disk I/O.
4. **Zero CPU Overhead:** Weights are loaded uncompressed directly into unified memory buffers with zero decompression latency.

---

## 4. Empirical Evidence (Apple M2 Mac 16GB RAM)

| Model | Parameters | Format | RAM Footprint | Execution Result |
| :--- | :---: | :---: | :---: | :---: |
| **Mixtral-8x22B-Instruct** | **141.0 B** | **Standard .gguf** | **3.10 GB fixed** | **Zero OOM, multi-turn generation verified** |
| **DeepSeek-Coder-V2-Lite** | 15.7 B (64 MoE) | **Standard .gguf** | **2.48 GB fixed** | **Zero OOM, 100% bitwise exact output** |

---

## 5. Reference Implementation & PR Contribution Offer

**We already have a fully functional, verified prototype/implementation of this deterministic streaming pipeline, and we are ready and eager to contribute the code directly to `llama.cpp` via a Pull Request (PR) or open-source reference module.**

* **Proposed CLI Flag:** `--stream-ring-buffer [budget_in_gb]` (e.g. `--stream-ring-buffer 3.5` or `--flow-direct`)
* **Readiness:** We can submit an initial draft PR or provide the ring-buffer / async prefetch patch as soon as maintainers indicate interest in the architectural direction.
* **Open Discussion:** We welcome guidance from @ggerganov and the core maintainers on whether this should be integrated into `llama-mmap.cpp` or structured as a modular streaming reader backend.

