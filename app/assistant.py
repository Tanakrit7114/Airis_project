from app.core.router import Router
from app.core.prompts import SYSTEM_PROMPT

from app.memory.store import MemoryStore
from app.memory.context import build_context
from app.memory.extractor import MemoryExtractor

from app.llm import LLMConfig, LLMEngine
from app.config import MODEL, MAX_GENERATION_TOKENS
from app.search.manager import SearchManager
from app.search.providers.web_provider import WebProvider

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

        self.search = SearchManager(
            providers=[
                WebProvider(),
            ]
        )

        self.tool_registry = ToolRegistry()

        self.tool_executor = ToolExecutor(
            self.tool_registry
        )

        self.tool_registry.register(
            "calculator",
            calculate,
        )

    def _select_generation_tokens(self, text: str, route: str) -> int:
        """Choose an appropriate generation budget instead of using one fixed length."""
        t = text.strip().lower()
        explicit_short = any(k in t for k in [
            "สั้น", "สรุปสั้น", "brief", "short answer", "tl;dr",
        ])
        explicit_long = any(k in t for k in [
            "ละเอียด", "โดยละเอียด", "เชิงลึก", "อธิบายเต็ม", "ครบถ้วน",
            "ทีละขั้นตอน", "step by step", "in detail", "deep dive", "comprehensive",
        ])
        academic = any(k in t for k in [
            "อธิบาย", "วิเคราะห์", "เปรียบเทียบ", "ทำไม", "อย่างไร",
            "วิจัย", "เปเปอร์", "paper", "algorithm", "วิชา", "machine learning",
            "deep learning", "neural network", "programming", "โค้ด", "code",
            "สรุปเนื้อหา", "สอน",
        ])
        document_task = any(k in t for k in [
            "pdf", "เอกสาร", "ไฟล์", "ocr", "สรุปไฟล์", "สรุปเอกสาร",
            "document", "paper",
        ])

        if explicit_short:
            target = 320
        elif explicit_long or document_task:
            target = 1536
        elif academic:
            target = 1024
        elif route == "search":
            target = 768
        else:
            target = 512

        return min(target, MAX_GENERATION_TOKENS)

    def _response_style_instruction(self, text: str, route: str) -> str:
        budget = self._select_generation_tokens(text, route)
        if budget <= 320:
            style = "Give a concise answer. Include only the information needed to answer the question."
        elif budget >= 1536:
            style = "Give a detailed, well-structured answer. Preserve important details, steps, caveats, and examples when useful."
        elif budget >= 1024:
            style = "Explain clearly with enough depth for understanding. Use structure and examples when useful, without unnecessary filler."
        else:
            style = "Answer naturally with moderate detail. Be complete but avoid unnecessary repetition."
        return f"Response style for this request: {style}"

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

        messages.append(
            {
                "role": "system",
                "content": self._response_style_instruction(text, route),
            }
        )

        if route == "search":

            response = self.search.search(
                text,
                limit=5,
            )

            if response.results:

                search_text = []

                for i, result in enumerate(
                    response.results,
                    1,
                ):
                    search_text.append(
                        f"[{i}] {result.title}\n"
                        f"{result.content}\n"
                        f"Source: {result.url}"
                    )

                messages.append(
                    {
                        "role": "system",
                        "content": (
                            "Search results:\n\n"
                            + "\n\n".join(search_text)
                        ),
                    }
                )

        print(
            "\nAI: ",
            end="",
            flush=True,
        )

        answer = self.llm.stream(
            messages,
            max_tokens=self._select_generation_tokens(text, route),
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