from dataclasses import dataclass
from typing import Optional
import time
import threading

from mlx_lm import load, stream_generate

from app.config import MODEL, TEMPERATURE, TOP_P


@dataclass
class LLMConfig:
    model: str = MODEL

    temperature: float = TEMPERATURE
    top_p: float = TOP_P

    max_tokens: int = 512

    context_window: int = 8192
    max_prompt_tokens: int = 6144

    stop_tokens: tuple[str, ...] = ()

    timeout: float = 120.0

    max_retries: int = 2


class ModelManager:
    def __init__(self, config: LLMConfig):
        self.config = config

        self.model = None
        self.tokenizer = None

    def load(self):
        if self.model is not None:
            return self.model, self.tokenizer

        print("\n[LLM] Loading model...")

        self.model, self.tokenizer = load(
            self.config.model
        )

        print("[LLM] Model ready.\n")

        return self.model, self.tokenizer

    def unload(self):
        self.model = None
        self.tokenizer = None


class LLMEngine:

    def __init__(
        self,
        model_manager: ModelManager,
        config: Optional[LLMConfig] = None,
    ):
        self.model_manager = model_manager
        self.config = config or model_manager.config
        self._shutdown_requested = False

    def count_tokens(self, text):
        _, tokenizer = self.model_manager.load()
        return len(tokenizer.encode(text))

    def _build_prompt(self, messages):
        _, tokenizer = self.model_manager.load()

        return tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

    def _trim_prompt(self, prompt):
        _, tokenizer = self.model_manager.load()

        tokens = tokenizer.encode(prompt)

        if len(tokens) <= self.config.max_prompt_tokens:
            return prompt

        tokens = tokens[-self.config.max_prompt_tokens:]

        return tokenizer.decode(tokens)
    
    def _generate_stream(
        self,
        model,
        tokenizer,
        prompt,
        generation_tokens,
    ):
        return stream_generate(
            model,
            tokenizer,
            prompt,
            max_tokens=generation_tokens,
        )
    
    def _run_with_timeout(self, func, timeout):
        result = []
        error = []

        def target():
            try:
                result.append(func())
            except Exception as exc:
                error.append(exc)

        thread = threading.Thread(
            target=target,
            daemon=True,
        )

        thread.start()
        thread.join(timeout)

        if thread.is_alive():
            raise TimeoutError(
                f"LLM generation timed out after {timeout} seconds"
            )

        if error:
            raise error[0]

        return result[0] if result else None
    
    def benchmark(self, messages, max_tokens: Optional[int] = None):
        generation_tokens = (
            max_tokens
            if max_tokens is not None
            else self.config.max_tokens
        )

        model, tokenizer = self.model_manager.load()

        prompt = self._build_prompt(messages)
        prompt = self._trim_prompt(prompt)

        prompt_tokens = self.count_tokens(prompt)

        start_time = time.perf_counter()
        first_token_time = None
        generated_tokens = 0

        responses = self._generate_stream(
            model,
            tokenizer,
            prompt,
            generation_tokens,
        )

        for response in responses:
            text = response.text

            if not text:
                continue

            now = time.perf_counter()

            if first_token_time is None:
                first_token_time = now

            # Count actual generated tokens when metadata is available.
            if hasattr(response, "generation_tokens"):
                generated_tokens = response.generation_tokens
            else:
                generated_tokens += 1

        end_time = time.perf_counter()

        total_time = end_time - start_time

        if first_token_time is None:
            ttft = total_time
        else:
            ttft = first_token_time - start_time

        generation_time = max(
            total_time - ttft,
            0.0,
        )

        tokens_per_second = (
            generated_tokens / generation_time
            if generation_time > 0
            else 0.0
        )

        return {
            "prompt_tokens": prompt_tokens,
            "generated_tokens": generated_tokens,
            "total_time": total_time,
            "time_to_first_token": ttft,
            "generation_time": generation_time,
            "tokens_per_second": tokens_per_second,
        }
    
    def shutdown(self):
        self._shutdown_requested = True
        self.model_manager.unload()

    def stream(
        self,
        messages,
        max_tokens: Optional[int] = None,
    ):
        model, tokenizer = self.model_manager.load()

        prompt = self._build_prompt(messages)
        prompt = self._trim_prompt(prompt)

        generation_tokens = (
            max_tokens
            if max_tokens is not None
            else self.config.max_tokens
        )

        last_error = None

        for attempt in range(self.config.max_retries + 1):
            try:
                answer_parts = []
                thinking = False

                responses = self._run_with_timeout(
                    lambda: self._generate_stream(
                        model,
                        tokenizer,
                        prompt,
                        generation_tokens,
                    ),
                    self.config.timeout,
                )

                for response in responses:
                    if self._shutdown_requested:
                       break
                    
                    text = response.text

                    if not text:
                        continue

                    # Hide Qwen thinking output
                    if "<think>" in text:
                        thinking = True
                        text = text.split(
                            "<think>",
                            1,
                        )[1]

                    if thinking:
                        if "</think>" in text:
                            thinking = False
                            text = text.split(
                                "</think>",
                                1,
                            )[1]
                        else:
                            continue

                    if not text:
                        continue

                    # Stop tokens
                    stopped = False

                    for stop in self.config.stop_tokens:
                        if stop in text:
                            text = text.split(
                                stop,
                                1,
                            )[0]
                            stopped = True
                            break

                    if text:
                        answer_parts.append(text)

                        print(
                            text,
                            end="",
                            flush=True,
                        )

                    if stopped:
                        break

                return "".join(answer_parts).strip()

            except Exception as error:
                last_error = error

                if attempt >= self.config.max_retries:
                    raise

                print(
                    f"\n[LLM] Generation failed "
                    f"(attempt {attempt + 1}/"
                    f"{self.config.max_retries + 1}). "
                    f"Retrying...",
                    flush=True,
                )

                time.sleep(0.5 * (attempt + 1))

        raise last_error
    def benchmark(
        self,
        messages,
        max_tokens: Optional[int] = None,
    ):
        model, tokenizer = self.model_manager.load()

        prompt = self._build_prompt(messages)
        prompt = self._trim_prompt(prompt)

        generation_tokens = (
            max_tokens
            if max_tokens is not None
            else self.config.max_tokens
        )

        start = time.perf_counter()
        first_token_time = None
        token_count = 0

        responses = self._generate_stream(
            model,
            tokenizer,
            prompt,
            generation_tokens,
        )

        for response in responses:
            if first_token_time is None:
                first_token_time = time.perf_counter()

            token_count += 1

        end = time.perf_counter()

        total_time = end - start

        ttft = (
            first_token_time - start
            if first_token_time is not None
            else None
        )

        tokens_per_sec = (
            token_count / total_time
            if total_time > 0
            else 0.0
        )

        return {
            "tokens": token_count,
            "total_time": total_time,
            "ttft": ttft,
            "tokens_per_sec": tokens_per_sec,
        }



class LocalLLM:
    """
    Backward-compatible wrapper.

    Existing Assistant code can continue using:
        LocalLLM().stream(...)
    """

    def __init__(self):
        self.config = LLMConfig()

        self.model_manager = ModelManager(
            self.config
        )

        self.engine = LLMEngine(
            self.model_manager,
            self.config,
        )

    def load(self):
        return self.model_manager.load()

    def stream(
        self,
        messages,
        max_tokens=None,
    ):
        return self.engine.stream(
            messages,
            max_tokens=max_tokens,
        )
