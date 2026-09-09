from app.tools.system import system_tool
from app.core.router import Router
from app.core.prompts import SYSTEM_PROMPT

from app.memory.store import MemoryStore
from app.memory.context import build_context
from app.memory.pipeline import MemoryPipeline

from app.llm import LLMConfig, LLMEngine, ModelManager
from app.config import MODEL
from app.search.searxng import SearXNG

from app.config import MAX_GENERATION_TOKENS

from app.tools.registry import ToolRegistry
from app.tools.executor import ToolExecutor
from app.tools.calculator import calculate


class Assistant:

    def __init__(self):

        # ====================================================
        # Core components
        # ====================================================

        self.router = Router()

        self.memory = MemoryStore()

        self.memory_pipeline = MemoryPipeline(
            store=self.memory
        )

        self.llm_config = LLMConfig(
            model=MODEL,
            max_tokens=MAX_GENERATION_TOKENS,
        )

        self.llm = LLMEngine(
            ModelManager(self.llm_config),
            self.llm_config,
        )

        self.search = SearXNG()

        # ====================================================
        # Tool system
        # ====================================================

        self.tool_registry = ToolRegistry()

        self.tool_executor = ToolExecutor(
            self.tool_registry
        )

        # Register calculator
        self.tool_registry.register(
            "calculator",
            calculate,
        )
        self.tool_registry.register(
            "system",
            system_tool,
        )

    # ========================================================
    # Main Chat
    # ========================================================

    def chat(self, text: str):

        # ----------------------------------------------------
        # Route request
        # ----------------------------------------------------

        route = self.router.route(text)

        # ----------------------------------------------------
        # Save user message
        # ----------------------------------------------------

        self.memory.add_message(
            "user",
            text,
        )

        # ----------------------------------------------------
        # Extract long-term memories
        # ----------------------------------------------------

        existing_memories = self.memory.all_memories_v2()

        memories = self.memory_pipeline.process(
            text,
            existing_memories=existing_memories,
        )

        self.memory_pipeline.store_memories(memories)

        # ====================================================
        # TOOL ROUTE
        # ====================================================

        if route == "tool:calculator":

            try:

                # Extract expression
                expression = self._extract_calculation(
                    text
                )

                # Execute calculator
                result = self.tool_executor.execute(
                    "calculator",
                    expression,
                )

                answer = str(result)

            except Exception as exc:

                answer = (
                    f"Calculator error: {exc}"
                )

            print(
                f"\nAI: {answer}"
            )

            # Save assistant response
            self.memory.add_message(
                "assistant",
                answer,
            )

            return answer
        
        if route == "tool:system":
            try:
                result = self.tool_executor.execute(
                    "system",
                    text,
                )

                answer = str(result)

            except Exception as exc:
                answer = f"System tool error: {exc}"

            print(
                f"\nAI: {answer}"
            )

            self.memory.add_message(
                "assistant",
                answer,
            )

            return answer

        # ====================================================
        # Build LLM context
        # ====================================================

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

        # ====================================================
        # SEARCH ROUTE
        # ====================================================

        if route == "search":

            results = self.search.search(
                text
            )

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

        # ====================================================
        # User message
        # ====================================================

        messages.append(
            {
                "role": "user",
                "content": text,
            }
        )

        # ====================================================
        # LLM
        # ====================================================

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

        # ====================================================
        # Save assistant response
        # ====================================================

        self.memory.add_message(
            "assistant",
            answer,
        )

        return answer

    # ========================================================
    # Calculator expression extraction
    # ========================================================

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

                return text[
                    len(prefix):
                ].strip()

        # Handle:
        #
        # What is 123 * 456?
        #

        if lower.startswith(
            "what is "
        ):

            expression = text[
                len("what is "):
            ].strip()

            if expression.endswith("?"):

                expression = expression[:-1]

            return expression.strip()

        return text
    
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
    
    # ========================================================
    # Shutdown
    # ========================================================

    def shutdown(self):
        self.llm.shutdown()