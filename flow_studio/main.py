"""FLOW Studio CLI Entrypoint & Server Launcher.

Parses command-line arguments and launches the Uvicorn ASGI server.
"""

import argparse
import sys
import uvicorn

from flow_studio.app import create_app
from flow_studio.config import settings


def main() -> None:
    parser = argparse.ArgumentParser(
        description="FLOW Studio: Universal Streaming Inference Server"
    )
    parser.add_argument(
        "--host",
        type=str,
        default=settings.host,
        help=f"Bind host address (default: {settings.host})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=settings.port,
        help=f"Bind port number (default: {settings.port})",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        default=settings.debug,
        help="Enable auto-reload on code changes",
    )
    args = parser.parse_args()

    print("=" * 72)
    print(" 🚀 Launching FLOW Studio Universal Inference Server")
    print(f" 📦 Dual Formats: .safetensors.flow / .gguf.flow")
    print(f" 🌐 WebUI:    http://{args.host}:{args.port}")
    print(f" 🔌 Local API: http://{args.host}:{args.port}/v1")
    print("=" * 72)

    app = create_app()
    uvicorn.run(app, host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()

