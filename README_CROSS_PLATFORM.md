# J.A.R.V.I.S. Local — Cross-platform runtime

The core assistant is hardware-neutral. Runtime-specific code is isolated under `app/llm_backends/`.

## LLM
- Apple Silicon macOS: `mlx-lm` backend, default for MLX model IDs.
- Windows, Linux, and Intel Mac: `llama-cpp-python` backend with local GGUF models.
- Set `LLM_BACKEND=auto` (default) or override with `mlx` / `llama.cpp`.
- On non-Apple platforms, set `LLAMA_MODEL_PATH=models/<your-model>.gguf`.
- NVIDIA CUDA is optional. The official llama-cpp-python docs describe CUDA builds and pre-built CUDA wheels. citeturn430117search1turn430117search0

## OCR
- macOS Apple Silicon: Apple Vision when available.
- Windows/Linux/Intel Mac: Tesseract fallback.
- Install Tesseract and Thai+English language data on non-Apple systems.

## Image generation
MFLUX/FLUX.2 Klein remains local on Apple Silicon. Other platforms receive a clear "not available" response instead of importing Apple-only packages at startup.

## Model switching
The Chat model selector calls `/api/models/select`; switching is serialized against chat generation so the old model is not unloaded while a request is using it.

## Start
macOS/Linux:
```bash
./scripts/run_web.sh
```
Windows:
```powershell
.\scripts\run_web.ps1
```
