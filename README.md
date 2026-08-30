# J.A.R.V.I.S. Local

Zero-cost, local-first AI assistant foundation.

## Initial architecture

Input -> Router -> Memory/Search -> LLM -> Response

                         |
                       Tools
                         |
                      Security

## Target stack

- Python 3.11+
- MLX-LM
- Qwen3 8B 4-bit
- SQLite + FTS5
- SearXNG
- Local-first / $0 API cost
