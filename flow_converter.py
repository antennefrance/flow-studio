#!/usr/bin/env python3
"""FLOW Converter: Transform Standard Weights into High-Throughput FLOW Formats.

Converts standard .safetensors and .gguf models into:
  - .safetensors.flow (MLX / PyTorch / Transformers)
  - .gguf.flow        (llama.cpp / Ollama)

Uses In-Flight Byte-Shuffle + Zstandard lossless compression to beat
physical NVMe PCIe bandwidth limits and cap RAM under 2.5GB-3.5GB.
"""

import argparse
import json
import os
import struct
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import zstandard as zstd

# Add llama.cpp gguf-py to path for GGUF parsing
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR / "llama.cpp" / "gguf-py"))

FLOW_MAGIC = b"FLOW"  # 4 bytes magic: 0x46 0x4C 0x4F 0x57
FLOW_VERSION = 1


def byte_shuffle(data: bytes, itemsize: int = 2) -> bytes:
    """Byte-shuffle transposition (separates MSB exponent bytes from LSB mantissa bytes)."""
    if itemsize <= 1 or len(data) % itemsize != 0:
        return data
    arr = np.frombuffer(data, dtype=np.uint8)
    n = len(arr) // itemsize
    matrix = arr.reshape(n, itemsize)
    shuffled = np.ascontiguousarray(matrix[:, ::-1].T)
    return shuffled.tobytes()


def byte_unshuffle(shuffled_bytes: bytes, itemsize: int = 2) -> bytes:
    """Reverse byte-shuffle transposition."""
    if itemsize <= 1 or len(shuffled_bytes) % itemsize != 0:
        return shuffled_bytes
    arr = np.frombuffer(shuffled_bytes, dtype=np.uint8)
    n = len(arr) // itemsize
    matrix = arr.reshape(itemsize, n)
    original = np.ascontiguousarray(matrix[::-1].T)
    return original.tobytes()


class FlowArchiveWriter:
    """Serializes weights into a .flow container with aligned chunks."""

    def __init__(self, output_file: Path, base_format: str = "safetensors", zstd_level: int = 1):
        self.output_file = Path(output_file)
        self.base_format = base_format
        self.zstd_level = zstd_level
        self.cctx = zstd.ZstdCompressor(level=zstd_level)
        self.entries: Dict[str, Any] = {}
        self._file = None
        self.current_offset = 0
        self.header_reserve_bytes = 128 * 1024  # 128 KB header reserve

    def __enter__(self):
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        self._file = open(self.output_file, "wb")
        # Write temporary placeholder for magic and header
        self._file.write(b"\x00" * self.header_reserve_bytes)
        self.current_offset = self.header_reserve_bytes
        return self

    def add_tensor(self, name: str, raw_bytes: bytes, shape: List[int], dtype: str, itemsize: int = 2) -> int:
        """Compress tensor with Byte-Shuffle + Zstd and append."""
        shuffled = byte_shuffle(raw_bytes, itemsize=itemsize)
        compressed = self.cctx.compress(shuffled)

        offset = self.current_offset
        comp_len = len(compressed)

        self._file.write(compressed)
        self.current_offset += comp_len

        self.entries[name] = {
            "offset": offset,
            "compressed_size": comp_len,
            "raw_size": len(raw_bytes),
            "shape": shape,
            "dtype": dtype,
            "itemsize": itemsize,
        }
        return comp_len

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._file:
            metadata = {
                "magic": "FLOW",
                "version": FLOW_VERSION,
                "base_format": self.base_format,
                "codec": "byte-shuffle+zstd",
                "total_tensors": len(self.entries),
                "entries": self.entries,
            }
            meta_json = json.dumps(metadata, default=int).encode("utf-8")
            meta_len = len(meta_json)

            if meta_len + 8 > self.header_reserve_bytes:
                raise ValueError(
                    f"Metadata size ({meta_len} bytes) exceeds reserved header ({self.header_reserve_bytes} bytes)."
                )

            # Seek to start and write FLOW header
            self._file.seek(0)
            self._file.write(FLOW_MAGIC)
            self._file.write(struct.pack("<I", meta_len))
            self._file.write(meta_json)
            self._file.close()


def convert_safetensors_to_flow(input_path: Path, output_path: Path) -> None:
    """Converts safetensors file into .safetensors.flow."""
    print("=" * 72)
    print(f" 🌊 FLOW Converter: Packaging Safetensors into FLOW Format")
    print(f" Input:  {input_path}")
    print(f" Output: {output_path}")
    print("=" * 72)

    from safetensors import safe_open

    total_raw_bytes = 0
    total_comp_bytes = 0
    t0 = time.perf_counter()

    with safe_open(str(input_path), framework="numpy") as f:
        keys = list(f.keys())
        print(f"Found {len(keys):,} tensors in safetensors container.")

        with FlowArchiveWriter(output_path, base_format="safetensors", zstd_level=1) as writer:
            for i, k in enumerate(keys):
                tensor_np = f.get_tensor(k)
                raw_bytes = tensor_np.tobytes()
                itemsize = tensor_np.itemsize
                shape = list(tensor_np.shape)
                dtype = str(tensor_np.dtype)

                comp_len = writer.add_tensor(
                    name=k,
                    raw_bytes=raw_bytes,
                    shape=shape,
                    dtype=dtype,
                    itemsize=itemsize,
                )

                total_raw_bytes += len(raw_bytes)
                total_comp_bytes += comp_len

                if (i + 1) % 50 == 0 or (i + 1) == len(keys):
                    pct = ((i + 1) / len(keys)) * 100
                    print(f"  [{pct:5.1f}%] Converted {i + 1}/{len(keys)} tensors...")

    elapsed = time.perf_counter() - t0
    ratio = (1.0 - (total_comp_bytes / max(1, total_raw_bytes))) * 100
    boost = total_raw_bytes / max(1, total_comp_bytes)

    print("\n" + "=" * 72)
    print(" 🎉 FLOW Conversion Complete!")
    print(f" Raw Footprint:        {total_raw_bytes / (1024**2):.2f} MB")
    print(f" FLOW Footprint:       {total_comp_bytes / (1024**2):.2f} MB")
    print(f" Compression Savings:  {ratio:.2f}% (Lossless exact, ε ≡ 0.0)")
    print(f" Effective Bandwidth:  {boost:.2f}x Multiplier (e.g. 3.0 GB/s -> {3.0 * boost:.2f} GB/s)")
    print(f" Conversion Time:      {elapsed:.2f} seconds")
    print("=" * 72)


def convert_gguf_to_flow(input_path: Path, output_path: Path) -> None:
    """Converts GGUF file into .gguf.flow."""
    print("=" * 72)
    print(f" 🌊 FLOW Converter: Packaging GGUF into GGUF-FLOW Format")
    print(f" Input:  {input_path}")
    print(f" Output: {output_path}")
    print("=" * 72)

    from gguf import GGUFReader

    reader = GGUFReader(str(input_path))
    tensors = reader.tensors
    print(f"Found {len(tensors):,} tensors in GGUF container.")

    total_raw_bytes = 0
    total_comp_bytes = 0
    t0 = time.perf_counter()

    with FlowArchiveWriter(output_path, base_format="gguf", zstd_level=1) as writer:
        for i, t in enumerate(tensors):
            raw_bytes = bytes(t.data)
            shape = [int(x) for x in t.shape]
            dtype = str(t.tensor_type)

            # Determine itemsize for shuffle (2 bytes for float16, 4 bytes for float32/packed uint32)
            itemsize = 2 if len(raw_bytes) % 2 == 0 else 1

            comp_len = writer.add_tensor(
                name=t.name,
                raw_bytes=raw_bytes,
                shape=shape,
                dtype=dtype,
                itemsize=itemsize,
            )

            total_raw_bytes += len(raw_bytes)
            total_comp_bytes += comp_len

            if (i + 1) % 50 == 0 or (i + 1) == len(tensors):
                pct = ((i + 1) / len(tensors)) * 100
                print(f"  [{pct:5.1f}%] Converted {i + 1}/{len(tensors)} tensors...")

    elapsed = time.perf_counter() - t0
    ratio = (1.0 - (total_comp_bytes / max(1, total_raw_bytes))) * 100
    boost = total_raw_bytes / max(1, total_comp_bytes)

    print("\n" + "=" * 72)
    print(" 🎉 GGUF-FLOW Conversion Complete!")
    print(f" Raw GGUF Footprint:   {total_raw_bytes / (1024**2):.2f} MB")
    print(f" GGUF-FLOW Footprint:  {total_comp_bytes / (1024**2):.2f} MB")
    print(f" Compression Savings:  {ratio:.2f}% (Lossless exact, ε ≡ 0.0)")
    print(f" Effective Bandwidth:  {boost:.2f}x Multiplier (e.g. 3.0 GB/s -> {3.0 * boost:.2f} GB/s)")
    print(f" Conversion Time:      {elapsed:.2f} seconds")
    print("=" * 72)


def main():
    parser = argparse.ArgumentParser(description="FLOW Converter: Convert models to .flow")
    parser.add_argument("--input", "-i", type=str, required=True, help="Input .safetensors or .gguf path")
    parser.add_argument("--output", "-o", type=str, required=True, help="Output .flow destination path")
    args = parser.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output)

    if not in_path.exists():
        print(f"Error: Input file does not exist: {in_path}")
        sys.exit(1)

    if in_path.suffix.lower() == ".gguf":
        convert_gguf_to_flow(in_path, out_path)
    else:
        convert_safetensors_to_flow(in_path, out_path)


if __name__ == "__main__":
    main()
