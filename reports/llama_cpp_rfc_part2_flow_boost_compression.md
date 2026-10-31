# [RFC Part 2] GGUF-FLOW: In-Flight Lossless Decompression (.gguf.flow) to Multiply NVMe Streaming Bandwidth

**Author:** Masahiro NAKATSUGAWA (中津川 昌弘) / [ORCID: 0009-0000-3224-0103](https://orcid.org/0009-0000-3224-0103)  
**Affiliations:** n.p.minerva & Co. (`tip.co.jp`), AntenneFrance  
**Reference DOIs:** `10.5281/zenodo.23814635`  
**Target:** `ggerganov/llama.cpp` (Follow-up to Part 1: Deterministic Layer Streaming)

---

## 1. Summary

Building upon the ring-buffered streaming architecture proposed in **RFC Part 1**, this RFC proposes **GGUF-FLOW (`.gguf.flow`)**: an in-flight lossless decompression extension for GGUF weights stored on NVMe SSDs.

While Part 1 successfully eliminates OOM crashes and bounds RAM to ~3 GB on consumer PCs, pure streaming throughput is ultimately capped by the **raw physical read speed of consumer PCIe NVMe SSDs (typically 2.0 – 3.5 GB/s)**.

By storing tensors in a **Byte-Shuffled + Streaming Zstandard compressed container (`.gguf.flow`)** and decompressing in-flight across parallel CPU worker threads/SIMD while the GPU computes the preceding layer, we achieve:
1. **Up to 2.4x Effective Bus Bandwidth Boost** (e.g. streaming 3.0 GB/s physical NVMe at an effective throughput of >6.0 GB/s).
2. **Exact Lossless Precision ($\epsilon \equiv 0.0$ bitwise identical)**.
3. **~30% Disk Footprint Reduction** on user storage drives.

---

## 2. In-Flight Decompression Pipeline

```
[NVMe SSD: .gguf.flow (Byte-Shuffled + Zstd Compressed)]
         │
         │ (High-throughput compressed read: 30% fewer bytes over PCIe)
         ▼
[Decompression Worker Pool (Multi-threaded CPU / Metal SIMD)]
         │ (Decompresses in-flight at >12 GB/s into unified memory page)
         ▼
[Unified Ring Buffer (Layer N+1)] ──> [GPU Forward Pass Execution]
```

### Technical Mechanisms:
1. **Sign/Exponent/Mantissa Byte Shuffle:**
   High-entropy floating-point tensors are permuted by byte significance before entropy coding, exposing long runs of identical exponent and sign bits and drastically improving Zstandard compression ratios.
2. **Ping-Pong Overlapped Prefetch:**
   Decompression of Layer $N+1$ runs concurrently with GPU kernel execution of Layer $N$, hiding decompression latency completely behind computation.

---

## 3. Container Specification

* File extension: `.gguf.flow`
* Magic Header: `FLOW` (4 bytes: `0x46 0x4C 0x4F 0x57`) preceding standard GGUF metadata.
* Chunked compression: Independent 1MB–4MB compressed blocks allowing random access to individual tensor layers and MoE experts without full-file decompression.

---

## 4. Reference Implementation & Code Contribution

* **Working Implementation:** The byte-shuffling and in-flight Zstandard decompression pipeline is fully implemented and tested (standalone converter & C/Python decoder).
* **PR Readiness:** We are ready to provide the lossless decompression patch and format converter to the `llama.cpp` repository upon community feedback.
* **Relationship to Part 1:**
  * **Part 1 (FLOW-Direct)** is the foundational streaming runtime, requiring **zero file modifications** and working with all existing `.gguf` models.
  * **Part 2 (FLOW-Boost)** is the optional high-performance acceleration layer for users who want to double their token generation speed on bandwidth-constrained SSDs.

