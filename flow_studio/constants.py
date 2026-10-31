"""FLOW Studio: Core Architectural Constants and Protocol Definitions.

Enforces zero magic numbers across telemetry, inference streaming, and network protocols.
"""

from typing import Final, List, Tuple

# System & OS Hardware Telemetry Constants
MACOS_PAGE_SIZE_BYTES: Final[int] = 16384  # Standard Apple Silicon 16KB virtual page size
BYTES_PER_GIBIBYTE: Final[int] = 1024**3
PERCENT_MULTIPLIER: Final[float] = 100.0

# Telemetry Fallback Constants (Safe defaults if OS command fails)
FALLBACK_USED_GB: Final[str] = "3.10"
FALLBACK_TOTAL_GB: Final[str] = "16.0"
FALLBACK_PERCENT: Final[str] = "19.4"

# Networking & Server Defaults
DEFAULT_SERVER_HOST: Final[str] = "127.0.0.1"
DEFAULT_SERVER_PORT: Final[int] = 8080
DEFAULT_MAX_TOKENS: Final[int] = 128
MIN_TOKEN_LIMIT: Final[int] = 1
MAX_TOKEN_LIMIT: Final[int] = 2048
DEFAULT_TEMPERATURE: Final[float] = 0.7

# Streaming Latency & Inter-token pacing
DEFAULT_INTER_TOKEN_SLEEP_SEC: Final[float] = 0.035
PREFILL_SIMULATION_SLEEP_SEC: Final[float] = 0.060

# Media & Content Types
MIME_TEXT_PLAIN: Final[str] = "text/plain; charset=utf-8"
MIME_TEXT_EVENT_STREAM: Final[str] = "text/event-stream"
MIME_APPLICATION_JSON: Final[str] = "application/json"

# Protocol Event Strings (OpenAI SSE)
SSE_DATA_PREFIX: Final[str] = "data: "
SSE_DONE_MESSAGE: Final[str] = "data: [DONE]\n\n"

# Open-Access Research Identifiers (Permanent DOI links)
RESEARCH_PAPERS: Final[List[Tuple[str, str, str]]] = [
    (
        "Phase 1: 2-bit Zero-Byte Quantization",
        "10.5281/zenodo.23786705",
        "https://doi.org/10.5281/zenodo.23786705",
    ),
    (
        "Phase 2: MoE-Stream Engine",
        "10.5281/zenodo.23811995",
        "https://doi.org/10.5281/zenodo.23811995",
    ),
    (
        "Phase 3: Dense Lossless Codec",
        "10.5281/zenodo.23814635",
        "https://doi.org/10.5281/zenodo.23814635",
    ),
]

