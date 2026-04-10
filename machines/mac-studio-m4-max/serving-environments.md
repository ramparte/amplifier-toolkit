# LLM Serving Environments on Apple Silicon

Notes on different LLM serving environments for the Mac Studio M4 Max 128GB.

## What Works on Apple Silicon

| Environment | Status | Backend | Notes |
|-------------|--------|---------|-------|
| **Ollama 0.20+** | Production | MLX (since 0.19) | Current setup. Multi-model, OpenAI-compat API |
| **mlx-lm** | Production | MLX native | Apple's framework. ~30% faster than Ollama for raw inference |
| **llama.cpp server** | Production | Metal GPU | Broadest GGUF format support. Ollama wraps this |
| **oMLX** | Promising | MLX | SSD-backed KV cache for agent workflows |
| **vllm-mlx** | Experimental | MLX | `pip install vllm-mlx`. 4.3x throughput at 16 concurrent |
| **LM Studio** | Production | llama.cpp | GUI + server. Uses llama.cpp under the hood |
| sglang | **Does not work** | N/A | No Apple Silicon support |
| vLLM (standard) | **CPU-only** | N/A | Useless on Mac -- CUDA-only GPU support |

## Current Setup: Ollama 0.20.4

Ollama is the right choice for Amplifier because:
- Amplifier has a native `provider-ollama` module
- Multi-model serving with automatic loading/unloading
- OpenAI-compatible API at `http://localhost:11434`
- MLX backend since v0.19 (automatic on Apple Silicon)
- KV cache quantization (`OLLAMA_KV_CACHE_TYPE=q8_0`)
- Flash attention (`OLLAMA_FLASH_ATTENTION=true`)

### Known Overhead

Ollama adds ~30% overhead vs raw MLX due to the Go wrapper layer. For a model
doing 80 tok/s through Ollama, raw mlx-lm might achieve ~110 tok/s. This is the
cost of multi-model management and API compatibility.

## Alternatives Worth Exploring

### oMLX (SSD-Backed KV Cache)

oMLX is specifically designed for coding agent workflows. Its key feature is
SSD-backed KV caching: when an agent conversation grows (tool calls accumulating),
every other runtime recomputes the full KV cache on each turn. oMLX stores it on
SSD and restores in milliseconds.

Benchmarks claim:
- 5x faster than LM Studio MLX at 8K context (49s -> 1.7s prefill)
- 1.6x faster for agent conversation patterns
- Supports OpenAI and Anthropic API endpoints, plus tool calling

This would be particularly valuable for Amplifier's multi-turn agent sessions
with growing context. However, it would require either:
- Pointing Amplifier's OpenAI provider at oMLX's API endpoint
- Or writing a dedicated provider module

### vllm-mlx (Concurrent Requests)

If running multiple Amplifier sessions simultaneously (e.g., parallel sub-agents
all hitting the same local model), vllm-mlx's concurrent request handling could
help. Standard Ollama serializes requests to the same model.

### Raw mlx-lm (Maximum Speed)

For single-model, single-session use where maximum speed matters. The 30% overhead
reduction might be worth it for specific use cases. Would require the OpenAI
provider pointing at an mlx-lm server.

## Not Relevant for This Machine

### sglang, vLLM (standard)
These are NVIDIA-focused. The coding partner's 3090 machines benefit from sglang
and vLLM, but they have no Apple Silicon GPU support. The Mac Studio should stick
with Ollama/MLX ecosystem.

## Apple Silicon Gotchas

### bf16 Support
M4 Max supports bf16 natively (unlike M1/M2). No emulation penalty for MLX
models shipped in bf16. This is a meaningful improvement over earlier chips.

### Memory Bandwidth is the Bottleneck
At ~546 GB/s, the M4 Max is bandwidth-bound for inference. This means:
- Tok/s scales linearly with active parameters (MoE wins)
- Quantization barely affects speed (Q4 vs Q8 is nearly identical tok/s)
- Quantization significantly affects quality (Q8 > Q4 for code tasks)

### Context Length vs Speed
Longer context windows reduce generation speed due to KV cache size. The default
`num_ctx: 8192` is a good balance. For long documents, consider increasing to
16384 or 32768 but expect slower generation.

### Multi-Model Warm Loading
With `OLLAMA_MAX_LOADED_MODELS=3` and 128GB, the three primary models stay
resident in memory (~77GB). This eliminates the 2-5s cold load penalty when
Amplifier swaps between general/coding/fast roles during a session. The remaining
~50GB handles KV caches, OS, and occasional 70B model loads.
