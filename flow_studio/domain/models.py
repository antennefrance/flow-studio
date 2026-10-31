"""FLOW Studio Domain Entities & Value Objects.

Defines pure data contracts for models, telemetry, and chat completions.
Zero framework dependencies.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class ArchitectureType(str, Enum):
    """Underlying neural model architecture classification."""

    MOE = "Mixture-of-Experts"
    DENSE = "Dense Transformer"
    STATE_SPACE = "Recurrent State-Space"


class StreamingMode(str, Enum):
    """Streaming execution paradigm."""

    DIRECT = "FLOW-Direct (Zero-Copy Non-Compressed)"
    BOOST = "FLOW-Boost (In-Flight Lossless Compressed)"


class CompressionFormat(str, Enum):
    """File extension and storage format classification."""

    FLOW_SAFETENSORS = ".safetensors.flow"
    FLOW_GGUF = ".gguf.flow"
    GGUF_STANDARD = ".gguf"
    MLX_STANDARD = ".safetensors"


@dataclass(frozen=True)
class ModelMetadata:
    """Immutable model catalog definition."""

    id: str
    name: str
    parameter_count: str
    architecture: ArchitectureType
    streaming_mode: StreamingMode
    primary_format: CompressionFormat
    active_ram_gb: float
    description: str
    owned_by: str = "masahiroid"


@dataclass(frozen=True)
class MemoryTelemetry:
    """Hardware unified memory snapshot."""

    used_gb: float
    total_gb: float
    utilization_percent: float
    app_gb: Optional[float] = None
    wired_gb: Optional[float] = None
    compressed_gb: Optional[float] = None
    cached_gb: Optional[float] = None

    @property
    def used_gb_formatted(self) -> str:
        return f"{self.used_gb:.2f}"

    @property
    def total_gb_formatted(self) -> str:
        return f"{self.total_gb:.1f}"

    @property
    def percent_formatted(self) -> str:
        return f"{self.utilization_percent:.1f}"

    def to_dict(self) -> Dict[str, str]:
        res = {
            "used_gb": self.used_gb_formatted,
            "total_gb": self.total_gb_formatted,
            "percent": self.percent_formatted,
        }
        if self.app_gb is not None:
            res["app_gb"] = f"{self.app_gb:.2f}"
        if self.wired_gb is not None:
            res["wired_gb"] = f"{self.wired_gb:.2f}"
        if self.compressed_gb is not None:
            res["compressed_gb"] = f"{self.compressed_gb:.2f}"
        if self.cached_gb is not None:
            res["cached_gb"] = f"{self.cached_gb:.2f}"
        return res


@dataclass
class ChatMessage:
    """OpenAI-compatible chat message payload."""

    role: str
    content: str


@dataclass
class GenerationRequestDTO:
    """Incoming prompt generation request data transfer object."""

    prompt: str
    model_id: str
    max_tokens: int
    temperature: float = 0.7


# Official Registry of Catalog Models (Supporting both Standard Models and FLOW-Boost Models)
CATALOG_MODELS: List[ModelMetadata] = [
    ModelMetadata(
        id="deepseek-direct",
        name="DeepSeek-Coder-V2-Lite (Standard GGUF)",
        parameter_count="15.7B (2.4B active / 64 MoE)",
        architecture=ArchitectureType.MOE,
        streaming_mode=StreamingMode.DIRECT,
        primary_format=CompressionFormat.GGUF_STANDARD,
        active_ram_gb=2.48,
        description="FLOW-Direct Mode: Standard .gguf with zero conversion. On-demand expert streaming in fixed 2.5GB RAM.",
    ),
    ModelMetadata(
        id="deepseek-boost",
        name="DeepSeek-Coder-V2-Lite-FLOW (.gguf.flow)",
        parameter_count="15.7B (2.4B active / 64 MoE)",
        architecture=ArchitectureType.MOE,
        streaming_mode=StreamingMode.BOOST,
        primary_format=CompressionFormat.FLOW_GGUF,
        active_ram_gb=2.48,
        description="FLOW-Boost Mode: Byte-Shuffle + Zstandard in-flight lossless decompression. 2.4x effective NVMe bus boost.",
    ),
    ModelMetadata(
        id="mixtral-direct",
        name="Mixtral-8x22B (Standard GGUF)",
        parameter_count="141.0B (39B active / 8 MoE)",
        architecture=ArchitectureType.MOE,
        streaming_mode=StreamingMode.DIRECT,
        primary_format=CompressionFormat.GGUF_STANDARD,
        active_ram_gb=3.10,
        description="FLOW-Direct Mode: Standard .gguf file. Runs 141B MoE on 16GB Mac under 3.5GB fixed RAM limit with zero OOM.",
    ),
    ModelMetadata(
        id="llmjp-direct",
        name="llm-jp-4-32b-a3b (Standard Safetensors)",
        parameter_count="32.5B",
        architecture=ArchitectureType.DENSE,
        streaming_mode=StreamingMode.DIRECT,
        primary_format=CompressionFormat.MLX_STANDARD,
        active_ram_gb=4.20,
        description="FLOW-Direct Mode: Standard .safetensors. Layer-by-layer ring-buffer streaming without format conversion.",
    ),
    ModelMetadata(
        id="lfm3-boost",
        name="LiquidAI LFM3-1.7B-FLOW (.gguf.flow)",
        parameter_count="1.7B",
        architecture=ArchitectureType.STATE_SPACE,
        streaming_mode=StreamingMode.BOOST,
        primary_format=CompressionFormat.FLOW_GGUF,
        active_ram_gb=1.20,
        description="FLOW-Boost Mode: Liquid Foundation Model with byte-shuffle lossless compression and DMA prefetch.",
    ),
]
