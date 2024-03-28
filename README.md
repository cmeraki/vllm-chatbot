# vllm-chatbot

Chatbot powered by vLLM backend

## Rough calculations

### Memory requirements

- block size = 16
- mistral 7b
- params
  - dim: 4096
  - layers: 32
  - n_heads: 8
  - kv_heads: 8
- memory required per block
  - `2 * 2 * 128 * 8 * 32` per token
- 0.13 MB per token
- 2.09 MB per block (assuming 16 as the block size)
- 1.06 GB per sequence (assuming 8k context len)
- blocks required for a sequence: ~500

### Single GPU

- 24 GB
- 14 GB by model
- 7 GB remaining (90% gpu utilization)
- ~3k blocks
- ~55k tokens
- ~6-7 requests with 8k context len will fill the KV cache

## Simulation params

Validation of the highest number of concurrent requests

- 6 requests
- Each chance: 100-200 tokens input and 500 tokens output
- After 15 turns, will have > 8k tokens, maximum utilization of a request
- TTFT: 10s + TTFT: 500ms total = 10 + 0.05*500 = 15s
- Each turn takes ~15s
- After ~3-4 mins, requests will reach full capacity

## Real life simulation

- 1 user connects every 2 seconds
- Conversation goes for an average 10 turns
- Total tokens per request - (150+500)*10 = 6500
- Total time 2 mins for a conversation

3k tokens
