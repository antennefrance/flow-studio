#!/bin/bash
# -----------------------------------------------------------------------------
# FLOW Studio Desktop Launcher
# Double-click this file in Finder to launch FLOW Studio on macOS.
# -----------------------------------------------------------------------------

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "======================================================================"
echo " 🌊 Launching FLOW Studio (Fast Lossless Offloaded Weights)"
echo " Universal Streaming Engine for Apple Silicon Unified Memory"
echo "======================================================================"

# Automatically open default browser once server initializes
(sleep 1.2 && open "http://127.0.0.1:8080") &

# Execute refactored Flow Studio package
exec python3 "$DIR/pyrite_app.py"
