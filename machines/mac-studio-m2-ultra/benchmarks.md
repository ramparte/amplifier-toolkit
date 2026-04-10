# Ollama Model Benchmarks - Mac Studio M2 Ultra 256GB

Benchmarked: 2026-04-09/10
Ollama: 0.20.4 (MLX backend)
Environment: `OLLAMA_KV_CACHE_TYPE=q8_0`, `OLLAMA_FLASH_ATTENTION=true`
Prompt: "Write a 200-word essay about the future of artificial intelligence."
Method: Cold start (model unloaded before each test), `num_ctx=4096`

## Summary Table

| Model | Size | Cold Load | Gen tok/s | Prompt tok/s | Output Tokens |
|-------|------|-----------|-----------|--------------|---------------|
| qwen3-coder:30b | 18 GB | 3.7s | **87.7** | 143.4 | 242 |
| gemma4:e4b | 9.6 GB | 0.2s | **79.2** | 1466.8 | 372 |
| qwen3:8b | 5.2 GB | 0.8s | 75.3 | 215.5 | 580 |
| glm-4.7-flash:q8_0 | 31 GB | 4.4s | 53.2 | 90.7 | 1192 |
| qwen3.5:35b | 23 GB | 2.0s | 42.9 | 162.6 | 4103 |
| qwen3-coder-next | 51 GB | 2.9s | 37.4 | 70.1 | 338 |
| mistral-small3.2 | 15 GB | 3.4s | 31.7 | 249.9 | 293 |
| qwen3-vl:32b | 20 GB | 4.6s | 21.9 | 91.8 | 807 |
| qwen3:32b | 20 GB | 4.1s | 21.7 | 116.5 | 592 |
| gemma4:31b | 19 GB | 1.6s | 21.4 | 76.4 | 717 |
| cogito:70b | 42 GB | 32.1s | 11.1 | 54.2 | 274 |
| llama3.3:70b | 42 GB | 18.8s | 11.1 | 60.4 | 238 |
| deepseek-r1:70b | 42 GB | 18.7s | 11.0 | 37.4 | 580 |

Note: qwen3.5:35b generated 4103 tokens because it used thinking tokens. Its
effective output speed may differ in non-thinking mode.

## Speed Tiers

### Tier 1: Fast (>60 tok/s) -- sub-agents, utility, session naming
- **qwen3-coder:30b** (87.7) -- purpose-built for code, fastest model on the box
- **gemma4:e4b** (79.2) -- MoE 26B (4B active), 0.2s cold load, haiku-tier
- **qwen3:8b** (75.3) -- smallest model, fast but less capable

### Tier 2: Mid (30-60 tok/s) -- general use, research, coding
- **glm-4.7-flash:q8_0** (53.2) -- strong at tool calling and agent instructions
- **qwen3.5:35b** (42.9) -- best speed/capability tradeoff, workhorse model
- **qwen3-coder-next** (37.4) -- improved coder quality but 51GB, slower than old coder
- **mistral-small3.2** (31.7) -- good prompt eval speed (250 tok/s)

### Tier 3: Capable (20-30 tok/s) -- creative, vision
- **qwen3-vl:32b** (21.9) -- only multimodal/vision model
- **qwen3:32b** (21.7) -- dense 32B, no particular advantage over qwen3.5:35b
- **gemma4:31b** (21.4) -- Google's model, qualitatively different prose style

### Tier 4: Heavy (10-12 tok/s) -- deep reasoning only
- **cogito:70b** (11.1) -- 32s cold load, analytical thinking
- **llama3.3:70b** (11.1) -- 19s cold load
- **deepseek-r1:70b** (11.0) -- 19s cold load, strong chain-of-thought

## Observations

### MoE Models Are the Sweet Spot
MoE (Mixture of Experts) models only activate a fraction of their parameters per
token, so they achieve high tok/s despite having many total parameters:
- gemma4:e4b (26B total, ~4B active) = 79.2 tok/s
- qwen3.5:35b uses MoE-like architecture = 42.9 tok/s

With 256GB memory, larger MoE models like qwen3.5:122b-a10b (122B total, 10B
active) could offer frontier quality at mid-tier speed.

### Cold Load Cost Varies Dramatically
Models stored on the external SSD have load times proportional to file size:
- 5-10 GB: 0.2-0.8s (trivial)
- 15-23 GB: 1.6-4.1s (acceptable)
- 42 GB: 18-32s (significant -- avoid unnecessary model swaps)
- 51 GB: 2.9s (coder-next loaded surprisingly fast despite size)

### Memory Bandwidth Is the Bottleneck
All 30-35B dense models cluster around 21-22 tok/s regardless of architecture
(qwen3, qwen3-vl, gemma4). This is the M2 Ultra's memory bandwidth ceiling for
that parameter count. Only MoE models or smaller models break above this.

### Quantization Matters Less Than Architecture
With 256GB, we can afford Q8 or even larger quantizations. The difference between
Q4 and Q8 is primarily quality (fewer logic errors in code), not speed, since the
bottleneck is memory bandwidth not compute.

## Pending Benchmarks

- [ ] qwen3.5:35b-a3b-q8_0 (38 GB, MoE -- expected 80-100+ tok/s)
- [ ] qwen3.5:122b-a10b (not yet pulled)
