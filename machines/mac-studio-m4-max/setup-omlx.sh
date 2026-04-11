#!/bin/bash
# Setup oMLX on Mac Studio M4 Max alongside Ollama
# Run on the Mac Studio directly: bash setup-omlx.sh
#
# Prerequisites: uv, Homebrew
# Model storage: /Volumes/ai-storage/models/omlx/

set -e

echo "================================================"
echo "  oMLX Setup - Mac Studio M4 Max 128GB"
echo "================================================"
echo ""

OMLX_MODELS="/Volumes/ai-storage/models/omlx"
OMLX_VENV="/opt/homebrew/opt/omlx-venv"
MODEL="mlx-community/gemma-4-31b-it-4bit"
MODEL_DIR="$OMLX_MODELS/gemma-4-31b-it-4bit"

# Step 1: Install oMLX via uv (Python 3.13 venv)
echo "=== Step 1: Installing oMLX ==="
if [ -x "$OMLX_VENV/bin/omlx" ]; then
    echo "oMLX already installed at $OMLX_VENV"
else
    echo "Creating venv with Python 3.13..."
    uv venv "$OMLX_VENV" --python 3.13 2>&1
    echo "Installing oMLX from git..."
    uv pip install --python "$OMLX_VENV/bin/python3" \
        "omlx @ git+https://github.com/jundot/omlx.git" 2>&1
    ln -sf "$OMLX_VENV/bin/omlx" /opt/homebrew/bin/omlx
    echo "oMLX installed and symlinked to /opt/homebrew/bin/omlx"
fi

# Step 2: Create model directory
echo ""
echo "=== Step 2: Creating model directory ==="
mkdir -p "$OMLX_MODELS/.cache"
echo "Model dir: $OMLX_MODELS"

# Step 3: Download MLX-format model
echo ""
echo "=== Step 3: Downloading $MODEL ==="
if [ -d "$MODEL_DIR" ] && [ -f "$MODEL_DIR/config.json" ] && ls "$MODEL_DIR"/*.safetensors >/dev/null 2>&1; then
    echo "Model already exists at $MODEL_DIR"
    du -sh "$MODEL_DIR"
else
    export PATH="$OMLX_VENV/bin:$PATH"
    echo "Downloading (15-20 min depending on network)..."
    hf download "$MODEL" --local-dir "$MODEL_DIR" 2>&1
    echo "Model downloaded."
    du -sh "$MODEL_DIR"
fi

# Step 4: Start oMLX
echo ""
echo "=== Step 4: Starting oMLX ==="
pkill -f "omlx serve" 2>/dev/null || true
sleep 1
nohup "$OMLX_VENV/bin/omlx" serve \
    --model-dir "$OMLX_MODELS" \
    --port 8000 \
    --paged-ssd-cache-dir "$OMLX_MODELS/.cache" \
    > /tmp/omlx-serve.log 2>&1 &
echo "Started oMLX (PID: $!)"
sleep 5

# Step 5: Verify
echo ""
echo "=== Step 5: Verifying ==="
if curl -s http://localhost:8000/v1/models > /dev/null 2>&1; then
    echo "oMLX is running on port 8000!"
    curl -s http://localhost:8000/v1/models 2>/dev/null | python3 -m json.tool 2>/dev/null
else
    echo "oMLX not responding yet. Check: tail -f /tmp/omlx-serve.log"
fi

echo ""
echo "================================================"
echo "  Ollama:  http://localhost:11434 (multi-model)"
echo "  oMLX:    http://localhost:8000  (fast MLX)"
echo "  Admin:   http://localhost:8000/admin"
echo "================================================"
