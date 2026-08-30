from app.core.router import Router
from app.core.prompts import SYSTEM_PROMPT

from app.memory.store import MemoryStore
from app.memory.context import build_context
from app.memory.extractor import MemoryExtractor

from app.llm import LLMConfig, LLMEngine
from app.config import MODEL, MAX_GENERATION_TOKENS
from app.search.searxng import SearXNG

from app.tools.registry import ToolRegistry
from app.tools.executor import ToolExecutor
from app.tools.calculator import calculate


class Assistant:

    def __init__(self):
        self.router = Router()
        self.memory = MemoryStore()
        self.memory_extractor = MemoryExtractor()

        self.llm_config = LLMConfig(
            model=MODEL,
            temperature=0.7,
            top_p=0.9,
            max_tokens=MAX_GENERATION_TOKENS,
            context_window=8192,
            max_prompt_tokens=4096,
            stop_tokens=(),
            timeout=120.0,
            max_retries=2,
        )

        from app.llm import ModelManager

        self.model_manager = ModelManager(
            self.llm_config
        )

        self.llm = LLMEngine(
            self.model_manager,
            self.llm_config,
        )

        self.search = SearXNG()

        self.tool_registry = ToolRegistry()

        self.tool_executor = ToolExecutor(
            self.tool_registry
        )

        self.tool_registry.register(
            "calculator",
            calculate,
        )

    def chat(self, text: str):

        route = self.router.route(text)

        self.memory.add_message(
            "user",
            text,
        )

        memories = self.memory_extractor.extract(text)

        for memory in memories:
            self.memory.add_memory(**memory)

        if route == "tool:calculator":

            try:
                expression = self._extract_calculation(text)

                result = self.tool_executor.execute(
                    "calculator",
                    expression,
                )

                answer = str(result)

            except Exception as exc:
                answer = f"Calculator error: {exc}"

            print(f"\nAI: {answer}")

            self.memory.add_message(
                "assistant",
                answer,
            )

            return answer

        context = build_context(
            self.memory,
            text,
        )

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            }
        ]

        if context:
            messages.append(
                {
                    "role": "system",
                    "content": (
                        "Relevant conversation context:\n"
                        + context
                    ),
                }
            )

        if route == "search":

            results = self.search.search(text)

            if results:
                messages.append(
                    {
                        "role": "system",
                        "content": (
                            "Search results:\n"
                            + results
                        ),
                    }
                )

        messages.append(
            {
                "role": "user",
                "content": text,
            }
        )

        print(
            "\nAI: ",
            end="",
            flush=True,
        )

        answer = self.llm.stream(
            messages,
            max_tokens=MAX_GENERATION_TOKENS,
        )

        print()

        self.memory.add_message(
            "assistant",
            answer,
        )

        return answer
    
    # ========================================================
    # Benchmark
    # ========================================================

    def benchmark(self):
        return self.llm.benchmark(
            [
                {
                    "role": "user",
                    "content": "Say hello.",
                }
            ]
        )

    def shutdown(self):
        self.llm.shutdown()

    def _extract_calculation(
        self,
        text: str,
    ) -> str:

        text = text.strip()
        lower = text.lower()

        prefixes = [
            "calculate ",
            "compute ",
            "คำนวณ ",
        ]

        for prefix in prefixes:
            if lower.startswith(prefix):
                return text[len(prefix):].strip()

        if lower.startswith("what is "):

            expression = text[len("what is "):].strip()

            if expression.endswith("?"):
                expression = expression[:-1]

            return expression.strip()

        return text