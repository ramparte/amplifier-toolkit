#!/bin/bash
# Setup oMLX on Mac Studio M4 Max alongside Ollama
# Run this script on the Mac Studio directly:
#   bash setup-omlx.sh
# Or via SSH:
#   ssh sam@macstudio 'bash -s' < setup-omlx.sh

set -e

echo "================================================"
echo "  oMLX Setup - Mac Studio M4 Max 128GB"
echo "================================================"
echo ""

# Step 1: Install oMLX via Homebrew
echo "=== Step 1: Installing oMLX ==="
if command -v omlx &>/dev/null; then
    echo "oMLX already installed"
else
    echo "Tapping jundot/omlx..."
    brew tap jundot/omlx https://github.com/jundot/omlx 2>&1
    echo "Installing omlx..."
    brew install omlx 2>&1
    echo "oMLX installed."
fi

# Step 2: Create model directory on external storage
echo ""
echo "=== Step 2: Creating model directory ==="
OMLX_MODELS="/Volumes/ai-storage/models/omlx"
mkdir -p "$OMLX_MODELS"
mkdir -p "$OMLX_MODELS/.cache"
echo "Model directory: $OMLX_MODELS"

# Step 3: Download MLX-format model
echo ""
echo "=== Step 3: Downloading MLX-format Gemma 4 27B (4-bit) ==="
MODEL_DIR="$OMLX_MODELS/gemma-4-27b-it-4bit"
if [ -d "$MODEL_DIR" ] && [ -f "$MODEL_DIR/config.json" ]; then
    echo "Model already exists at $MODEL_DIR"
else
    # Install huggingface-cli if needed
    if ! command -v huggingface-cli &>/dev/null; then
        echo "Installing huggingface-cli..."
        pip3 install --user huggingface_hub[cli] 2>&1
    fi
    echo "Downloading mlx-community/gemma-4-27b-it-4bit..."
    echo "(This will take 15-30 minutes depending on connection speed)"
    huggingface-cli download mlx-community/gemma-4-27b-it-4bit \
        --local-dir "$MODEL_DIR" 2>&1
    echo "Model downloaded to $MODEL_DIR"
fi

# Step 4: Start oMLX
echo ""
echo "=== Step 4: Starting oMLX ==="
# Try brew service first, fall back to manual
if brew services start omlx 2>/dev/null; then
    echo "Started via brew services"
else
    echo "Starting manually..."
    nohup omlx serve \
        --model-dir "$OMLX_MODELS" \
        --port 8000 \
        --paged-ssd-cache-dir "$OMLX_MODELS/.cache" \
        > /tmp/omlx-serve.log 2>&1 &
    echo "Started with PID $!"
fi
sleep 5

# Step 5: Verify
echo ""
echo "=== Step 5: Verifying ==="
if curl -s http://localhost:8000/v1/models > /dev/null 2>&1; then
    echo "oMLX is running on port 8000!"
    echo "Available models:"
    curl -s http://localhost:8000/v1/models 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "(check admin dashboard)"
else
    echo "oMLX not responding yet."
    echo "Check: tail -f /tmp/omlx-serve.log"
    echo "Or:    brew services info omlx"
fi

echo ""
echo "================================================"
echo "  Setup Complete!"
echo ""
echo "  Ollama:  http://localhost:11434 (multi-model)"
echo "  oMLX:    http://localhost:8000  (fast MLX)"
echo ""
echo "  Admin:   http://localhost:8000/admin"
echo "================================================"
