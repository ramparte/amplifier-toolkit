# Mac Studio M2 Ultra - Amplifier Local LLM Configuration

Machine: Mac Studio M2 Ultra, 256GB unified memory
Hostname: `macstudio` (Tailscale)
Storage: `/Volumes/ai-storage` (external SSD for Ollama models)
OS User: `sam`
GitHub: `ramparte`

## Hardware Specs

| Spec | Value |
|------|-------|
| Chip | Apple M2 Ultra |
| Memory | 256GB unified |
| Memory bandwidth | ~800 GB/s |
| GPU cores | 76 |
| Storage (models) | External SSD via Thunderbolt |
| Network | Tailscale (variable, ~5-15 MB/s for downloads) |

## Software Stack

| Component | Version | Notes |
|-----------|---------|-------|
| Ollama | 0.20.4 | MLX backend (since 0.19) |
| Amplifier | Latest | `uv tool install` |
| Bundle | `my-amplifier` | Custom routing matrix |

## Ollama Environment

Set via `launchctl`:
- `OLLAMA_KV_CACHE_TYPE=q8_0` (KV cache quantization)
- `OLLAMA_FLASH_ATTENTION=true`
- Model storage: `/Volumes/ai-storage/models/ollama/`

## Quick Reference

```bash
# SSH access
ssh sam@macstudio

# Check running models
curl -s http://localhost:11434/api/ps | python3 -m json.tool

# List installed models
ollama list

# Check Amplifier config
cat ~/.amplifier/settings.yaml

# Monitor GPU memory
sudo powermetrics --samplers gpu_power -i 1000
```

## Key Characteristics for Routing

1. **256GB unified memory** -- can load even 70B+ models at Q8
2. **External SSD model storage** -- cold load for 70B models takes 19-32s
3. **~800 GB/s memory bandwidth** -- tok/s is bandwidth-bound, not compute-bound
4. **MoE models shine** -- only active parameters consume bandwidth per token
5. **Minimize model swaps** -- the 19-32s cold load penalty for 70B models is the biggest latency cost

## See Also

- [benchmarks.md](benchmarks.md) -- Full benchmark results
- [routing-matrix.md](routing-matrix.md) -- Role-to-model mapping and rationale
- [settings.yaml](settings.yaml) -- Current Amplifier configuration
