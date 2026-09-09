# J.A.R.V.I.S. Local — Cross-platform + runtime model switch + extensions chat

This build keeps Memory, Search, persistent documents/OCR, local image generation, and OAuth extensions while adding:

1. Hardware-neutral LLM backends.
2. Runtime model selection from Chat.
3. Real typing indicator and streaming cursor.
4. Chat-driven extension reads plus confirmation-gated writes.
5. Professional responsive UI.

## Important migration note
If you already connected Google before enabling write scopes, reconnect the affected Google service so the new write scope is granted. Existing read-only tokens are not silently upgraded.

## Mac Apple Silicon
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd web && npm install && npm run build && cd ..
./scripts/run_web.sh
```

## Windows
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
cd web; npm install; npm run build; cd ..
.\scripts\run_web.ps1
```
Set `LLAMA_MODEL_PATH` to a local `.gguf` model on Windows/Linux. For NVIDIA CUDA, install a CUDA-enabled llama-cpp-python build using the official instructions rather than installing Apple-only MLX packages.

## Linux
Same as Windows except use `source .venv/bin/activate` and `./scripts/run_web.sh`.

## Model switching
The Chat header uses `GET /api/models` and `POST /api/models/select`. Switching shares the same lock as generation, so JARVIS waits for the current generation to finish before unloading/reloading a model.
