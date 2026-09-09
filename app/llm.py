from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Optional
import time, threading
from app.config import MODEL, LLM_BACKEND, LLAMA_MODEL_PATH, MAX_GENERATION_TOKENS, MAX_CONTINUATIONS, CONTINUATION_MIN_RATIO, TEMPERATURE, TOP_P, LLM_RESPONSE_TIMEOUT
from app.llm_backends.factory import select_backend

@dataclass
class LLMConfig:
    model: str = MODEL
    temperature: float = TEMPERATURE
    top_p: float = TOP_P
    max_tokens: int = 512
    context_window: int = 8192
    max_prompt_tokens: int = 6144
    stop_tokens: tuple[str, ...] = ()
    timeout: float = LLM_RESPONSE_TIMEOUT
    max_retries: int = 2
    max_continuations: int = MAX_CONTINUATIONS
    continuation_min_ratio: float = CONTINUATION_MIN_RATIO
    backend: str = LLM_BACKEND

class ModelManager:
    def __init__(self, config: LLMConfig):
        self.config = config
        self.backend = select_backend(config.model, config.backend)
        if self.backend.name == "llama.cpp" and not str(config.model).lower().endswith(".gguf"):
            from app.llm_backends.llama_cpp_backend import LlamaCppBackend
            config.model = LLAMA_MODEL_PATH
            self.backend = LlamaCppBackend(LLAMA_MODEL_PATH)
        self.model = None
        self.tokenizer = None
        self._lock = threading.RLock()
        self._status = "unloaded"
        self._on_status = None

    def set_status_callback(self, callback):
        self._on_status = callback

    def _set_status(self, status: str, error: str | None = None):
        self._status = status
        if self._on_status:
            try: self._on_status(status, self.config.model, error)
            except Exception: pass

    @property
    def status(self): return self._status

    @property
    def backend_name(self): return self.backend.name

    def load(self):
        with self._lock:
            if self.model is not None or self.backend.name == "llama.cpp":
                self._set_status("loading")
                try:
                    self.model, self.tokenizer = self.backend.load()
                    self._set_status("ready")
                    return self.model, self.tokenizer
                except Exception as exc:
                    self._set_status("error", str(exc)); raise
            self._set_status("loading")
            try:
                self.model, self.tokenizer = self.backend.load(); self._set_status("ready"); return self.model, self.tokenizer
            except Exception as exc:
                self._set_status("error", str(exc)); raise

    def unload(self):
        with self._lock:
            try: self.backend.unload()
            finally:
                self.model = None; self.tokenizer = None; self._set_status("unloaded")

    def switch_model(self, model: str, backend: str | None = None, load: bool = True):
        with self._lock:
            old_model, old_backend, old_name = self.config.model, self.backend, self.config.backend
            self.unload()
            self.config.model = model
            if backend: self.config.backend = backend
            self.backend = select_backend(model, self.config.backend)
            try:
                return self.load() if load else (None, None)
            except Exception:
                self.config.model, self.backend, self.config.backend = old_model, old_backend, old_name
                self.model = None; self.tokenizer = None; self._set_status("unloaded")
                raise

class LLMEngine:
    def __init__(self, model_manager: ModelManager, config: Optional[LLMConfig] = None):
        self.model_manager = model_manager; self.config = config or model_manager.config; self._shutdown_requested = False
    def count_tokens(self, text):
        try:
            return len(self.model_manager.backend.encode(text))
        except Exception:
            return max(1, len(str(text).split()))

    def _build_prompt(self, messages):
        if self.model_manager.backend.name == "mlx":
            _, tokenizer = self.model_manager.load()
            return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        return "\n\n".join(f"{m['role'].upper()}: {m['content']}" for m in messages) + "\n\nASSISTANT:"
    def _trim_prompt(self, prompt):
        if self.model_manager.backend.name == "ollama":
            # Approximate a token budget without losing the original text; the
            # Ollama HTTP API does not expose a tokenizer through this backend.
            return prompt[-self.config.max_prompt_tokens * 4:]
        try:
            tokens = self.model_manager.backend.encode(prompt)
            if len(tokens) <= self.config.max_prompt_tokens: return prompt
            return self.model_manager.backend.decode(tokens[-self.config.max_prompt_tokens:])
        except Exception:
            tokens = str(prompt).split()
            if len(tokens) <= self.config.max_prompt_tokens: return str(prompt)
            return " ".join(tokens[-self.config.max_prompt_tokens:])
    @staticmethod
    def _looks_incomplete(text: str) -> bool:
        text=text.rstrip()
        if not text: return False
        if text.endswith((":", ",", ";", "-", "•", "→", "=")): return True
        if any(text.count(a)>text.count(b) for a,b in (("(",")"),("[","]"),("{","}"))): return True
        if text.count("$")%2: return True
        if text.count("```")%2: return True
        lines=[x.strip() for x in text.splitlines() if x.strip()]
        if lines and (lines[-1].startswith("#") or len(lines[-1])<10 and lines[-1].startswith(("- ","* ","• "))): return True
        return not text.endswith((".","!","?","。","！","？",")","]","}","`")) and len(text)>120
    def _should_continue(self, answer, generated_tokens, generation_tokens, finish_reason):
        if not answer.strip() or self._shutdown_requested: return False
        if finish_reason:
            if any(x in finish_reason.lower() for x in ("stop","eos","end","length","max")): return self._looks_incomplete(answer)
        return generated_tokens >= int(generation_tokens*self.config.continuation_min_ratio) and self._looks_incomplete(answer)
    def _build_continuation_messages(self, original_messages, answer):
        return list(original_messages)+[{"role":"assistant","content":answer},{"role":"user","content":"Continue exactly where the previous answer stopped. Do not repeat earlier content. Finish the current thought/section and then continue naturally."}]
    def _generate_stream(self, model, tokenizer, prompt, generation_tokens):
        return self.model_manager.backend.stream_generate(prompt, generation_tokens, self.config.temperature, self.config.top_p)

    def stream(self, messages, max_tokens=None, on_token: Optional[Callable[[str],None]]=None, emit_console=True):
        started = time.monotonic()
        emitted = False
        def deliver(text):
            nonlocal emitted
            emitted = True
            if on_token: on_token(text)
        for attempt in range(max(0, self.config.max_retries) + 1):
            try:
                return self._stream_once(messages, max_tokens, deliver, emit_console, started)
            except TimeoutError:
                raise
            except (RuntimeError, ConnectionError, OSError) as exc:
                # Retrying a partially streamed answer duplicates visible text.
                # Memory/configuration failures are not transient either.
                fatal = any(word in str(exc).lower() for word in ("out of memory", "not found", "not installed", "unavailable"))
                status = getattr(getattr(exc.__cause__, "response", None), "status_code", None)
                if status is not None and status < 500 and status not in (408, 429):
                    fatal = True
                if emitted or fatal or self._shutdown_requested or attempt >= self.config.max_retries:
                    raise
                delay = min(0.25 * 2 ** attempt, 2.0)
                if time.monotonic() - started + delay >= self.config.timeout:
                    raise TimeoutError("Model retry exceeded response deadline") from exc
                time.sleep(delay)

    def _stream_once(self, messages, max_tokens, on_token, emit_console, started):
        if time.monotonic() - started >= self.config.timeout:
            raise TimeoutError("Model response deadline exceeded")
        self.model_manager.load(); generation_tokens=max_tokens or self.config.max_tokens; current=list(messages); base=list(messages); full=""
        for continuation_index in range(self.config.max_continuations+1):
            prompt=self._trim_prompt(self._build_prompt(current)); pieces=[]; generated=0; finish=None
            for response in self._generate_stream(self.model_manager.model,self.model_manager.tokenizer,prompt,generation_tokens):
                if time.monotonic() - started > self.config.timeout:
                    raise TimeoutError(f"Model response exceeded {self.config.timeout:.0f} seconds")
                if self._shutdown_requested: break
                text=response.text or ""; finish=getattr(response,"finish_reason",None) or finish; generated=max(generated, getattr(response,"generation_tokens",0) or 0)
                if not text: continue
                if text.strip()=="<think>": continue
                for stop in self.config.stop_tokens:
                    if stop in text: text=text.split(stop,1)[0]; finish=finish or "stop"
                if text:
                    pieces.append(text)
                    if on_token: on_token(text)
                    if emit_console: print(text,end="",flush=True)
            if time.monotonic() - started > self.config.timeout:
                raise TimeoutError(f"Model response exceeded {self.config.timeout:.0f} seconds")
            piece="".join(pieces).strip()
            if piece: full=(full+piece) if full else piece
            if continuation_index>=self.config.max_continuations or not self._should_continue(full,generated,generation_tokens,finish): break
            current=self._build_continuation_messages(base,full)
        answer = full.strip()
        if not answer:
            raise RuntimeError("The selected model returned an empty response")
        return answer
    def benchmark(self,messages,max_tokens=None):
        start=time.perf_counter(); first=None; tokens=0; prompt=self._trim_prompt(self._build_prompt(messages)); generation=max_tokens or self.config.max_tokens
        for ev in self._generate_stream(self.model_manager.model,self.model_manager.tokenizer,prompt,generation):
            if first is None: first=time.perf_counter()
            tokens=max(tokens,ev.generation_tokens or 0)
        total=time.perf_counter()-start; ttft=(first-start if first else total); return {"tokens":tokens,"total_time":total,"ttft":ttft,"tokens_per_sec":tokens/max(total-ttft,0.001)}
    def shutdown(self): self._shutdown_requested=True; self.model_manager.unload()

class LocalLLM:
    def __init__(self):
        self.config=LLMConfig(); self.model_manager=ModelManager(self.config); self.engine=LLMEngine(self.model_manager,self.config)
    def load(self): return self.model_manager.load()
    def stream(self,messages,max_tokens=None): return self.engine.stream(messages,max_tokens=max_tokens)
