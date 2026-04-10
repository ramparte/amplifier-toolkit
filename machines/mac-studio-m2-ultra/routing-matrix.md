# Routing Matrix Configuration - Mac Studio M2 Ultra

## Design Philosophy

The routing matrix maps Amplifier's 13 model roles to local Ollama models. The
key constraints on this hardware are:

1. **Memory bandwidth (~800 GB/s) is the speed bottleneck** -- tok/s is
   proportional to active parameters, not total parameters
2. **External SSD storage means model swaps are expensive** -- 19-32s for 70B
   models, 2-5s for 30-35B models, <1s for <10GB models
3. **256GB unified memory** -- can load very large models; MoE models are ideal
   because only active parameters consume bandwidth

### Guiding Principles

- **Minimize model swaps**: Roles that fire frequently should share models
- **Reserve 70B for genuine deep reasoning**: The 19-32s swap cost must be justified
- **Prefer MoE models**: They deliver higher quality per tok/s on bandwidth-limited hardware
- **Use Q8 when possible**: With 256GB, quality > compression ratio

## Current Mapping

| Role | Model | Speed | Rationale |
|------|-------|-------|-----------|
| **general** | qwen3.5:35b | 42.9 tok/s | Best speed/capability tradeoff, 2s cold load, workhorse |
| **fast** | gemma4:e4b | 79.2 tok/s | MoE 26B (~4B active), 0.2s load, haiku-equivalent |
| **coding** | qwen3-coder:30b | 87.7 tok/s | Purpose-built for code, fastest model on the box |
| **ui-coding** | qwen3-coder:30b | 87.7 tok/s | Same as coding (no dedicated UI model locally) |
| **reasoning** | deepseek-r1:70b | 11.0 tok/s | Worth the 19s swap for deep chain-of-thought |
| **critique** | qwen3.5:35b | 42.9 tok/s | Fires often; 32s swap for cogito:70b not worth it |
| **creative** | gemma4:31b | 21.4 tok/s | Qualitatively different prose style from Qwen |
| **writing** | gemma4:31b | 21.4 tok/s | Google model strength in sustained prose |
| **research** | qwen3.5:35b | 42.9 tok/s | Fast synthesis, shares model with general |
| **vision** | qwen3-vl:32b | 21.9 tok/s | Only multimodal model installed |
| **security-audit** | qwen3.5:35b | 42.9 tok/s | Needs code + reasoning, speed matters |
| **critical-ops** | qwen3.5:35b | 42.9 tok/s | Reliable, fast, shares warm model |

## Model Swap Groups

Models that share the same Ollama model benefit from being "warm" (already loaded
in memory). The routing matrix is designed so frequently-used roles cluster:

```
Group 1 (most traffic): qwen3.5:35b
  general, critique, research, security-audit, critical-ops

Group 2 (code tasks): qwen3-coder:30b
  coding, ui-coding

Group 3 (lightweight): gemma4:e4b
  fast (session naming, utility sub-agents)

Group 4 (creative): gemma4:31b
  creative, writing

Group 5 (occasional): individual models
  reasoning -> deepseek-r1:70b (19s swap, used rarely)
  vision -> qwen3-vl:32b (only when processing images)
```

## Alternative Models Benchmarked

These models were benchmarked but not selected for the primary routing:

| Model | Speed | Why Not Primary |
|-------|-------|-----------------|
| qwen3-coder-next (51 GB) | 37.4 tok/s | Better quality than qwen3-coder:30b but 2.3x slower |
| glm-4.7-flash:q8_0 (31 GB) | 53.2 tok/s | Strong tool-calling; could replace qwen3.5 for some roles |
| cogito:70b (42 GB) | 11.1 tok/s | Good for critique but 32s cold load too expensive |
| llama3.3:70b (42 GB) | 11.1 tok/s | No clear advantage over deepseek-r1 for reasoning role |
| qwen3:8b (5.2 GB) | 75.3 tok/s | Replaced by gemma4:e4b (faster and smarter as MoE 26B) |
| mistral-small3.2 (15 GB) | 31.7 tok/s | Good prompt eval but slower generation than qwen3.5 |

## Potential Upgrades (Pending Benchmarks)

| Model | Expected Impact | Status |
|-------|-----------------|--------|
| qwen3.5:35b-a3b-q8_0 (38 GB) | MoE variant could hit 80-100+ tok/s as `general` | Downloading |
| qwen3.5:122b-a10b (~100 GB) | Frontier quality at ~50-70 tok/s, MoE (10B active) | Not yet pulled |

If qwen3.5:35b-a3b performs as expected, it could replace qwen3.5:35b as the
general-purpose workhorse at 2x the speed.

## Configuration File

The routing is configured in `~/.amplifier/settings.yaml` on the Mac Studio.
See [settings.yaml](settings.yaml) for the current configuration.
