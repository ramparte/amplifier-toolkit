# Mac Studio M4 Max - Amplifier Local LLM Configuration

Machine: Mac Studio M4 Max, 128GB unified memory
Hostname: `macstudio` (Tailscale)
Storage: `/Volumes/ai-storage` (4TB external NVMe SSD via Thunderbolt)
OS User: `sam`
GitHub: `ramparte`

## Hardware Specs

| Spec | Value |
|------|-------|
| Chip | Apple M4 Max |
| Memory | 128GB unified |
| Memory bandwidth | ~546 GB/s |
| GPU cores | 40 (Metal 4) |
| CPU cores | 16 (12P + 4E) |
| Model storage | 4TB external NVMe SSD (Thunderbolt, PCIe) |
| Network | Tailscale (variable, ~5-15 MB/s for downloads) |

## Software Stack

| Component | Version | Notes |
|-----------|---------|-------|
| Ollama | 0.20.4 | MLX backend (since 0.19) |
| Amplifier | Latest | `uv tool install` |
| Bundle | `my-amplifier` | Custom routing matrix |

## Ollama Environment

Configured via `~/.ollama/env`:

```bash
# Core
OLLAMA_HOST=http://0.0.0.0:11434
OLLAMA_MODELS=/Volumes/ai-storage/models/ollama
OLLAMA_FLASH_ATTENTION=1
OLLAMA_KV_CACHE_TYPE=q8_0

# Multi-model warm loading (3 models simultaneously)
OLLAMA_MAX_LOADED_MODELS=3

# Keep models loaded 30 min (default was 5m)
OLLAMA_KEEP_ALIVE=30m

# Allow 2 concurrent requests per model
OLLAMA_NUM_PARALLEL=2

# Spread work across loaded models
OLLAMA_SCHED_SPREAD=true
```

## Warm Model Strategy

With 128GB and `OLLAMA_MAX_LOADED_MODELS=3`, the three primary routing
groups stay loaded simultaneously:

```
qwen3.5:35b      31.9 GB  (general, critique, research, security, critical-ops)
qwen3-coder:30b  33.1 GB  (coding, ui-coding)
gemma4:e4b       11.9 GB  (fast, session naming, utility agents)
TOTAL:           76.8 GB  of 128 GB (~60% utilization)
```

This leaves ~50GB for the OS, KV caches, and occasional heavy model loads
(70B reasoning models swap in on demand). With `OLLAMA_KEEP_ALIVE=30m`,
models stay warm across an entire Amplifier session instead of unloading
after the default 5 minutes.

## Quick Reference

```bash
# SSH access
ssh sam@macstudio

# Check running/loaded models
curl -s http://localhost:11434/api/ps | python3 -m json.tool

# List installed models
ollama list

# Pre-warm the 3 primary models
for m in gemma4:e4b qwen3-coder:30b qwen3.5:35b; do
  curl -s http://localhost:11434/api/generate \
    -d "{\"model\":\"$m\",\"prompt\":\"hi\",\"stream\":false,\"options\":{\"num_predict\":1}}" \
    > /dev/null
done

# Check Amplifier config
cat ~/.amplifier/settings.yaml

# Restart Ollama (picks up ~/.ollama/env changes)
pkill -f "ollama serve" && sleep 2 && nohup ollama serve &
```

## Key Characteristics for Routing

1. **128GB unified memory** -- can keep 3 models warm (~77GB), with room for 70B on demand
2. **External NVMe SSD** -- cold loads are fast (0.2-4.6s for most models, 19-32s for 70B)
3. **~546 GB/s memory bandwidth** -- tok/s is bandwidth-bound, not compute-bound
4. **MoE models shine at Q4** -- only active parameters consume bandwidth per token (but Q8 negates the advantage)
5. **M4 Max supports bf16 natively** -- unlike M1/M2, no emulation penalty for MLX models
6. **Minimize model swaps** -- the 19-32s cold load penalty for 70B models is the biggest latency cost

## Tuning Applied

| Setting | Default | Tuned | Impact |
|---------|---------|-------|--------|
| `OLLAMA_MAX_LOADED_MODELS` | 1 | **3** | Keep 3 models warm; eliminates cold loads for primary roles |
| `OLLAMA_KEEP_ALIVE` | 5m | **30m** | Models stay warm across full Amplifier sessions |
| `OLLAMA_NUM_PARALLEL` | 1 | **2** | Sub-agents hitting same model can overlap |
| `OLLAMA_SCHED_SPREAD` | false | **true** | Work distributed across loaded models |
| `disksleep` | 10 | **0** (manual) | Prevent external SSD from sleeping |

### Manual: Disable disk sleep

Run once (requires sudo):
```bash
sudo pmset -a disksleep 0
```
Prevents the external NVMe SSD from sleeping after 10 min of inactivity,
which would cause a latency spike on the next model cold load.

## See Also

- [benchmarks.md](benchmarks.md) -- Full benchmark results
- [routing-matrix.md](routing-matrix.md) -- Role-to-model mapping and rationale
- [settings.yaml](settings.yaml) -- Current Amplifier configuration
- [serving-environments.md](serving-environments.md) -- Ollama vs MLX vs llama.cpp comparison
