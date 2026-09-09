from app.tools.system import system_tool
from app.core.router import Router
from app.core.prompts import SYSTEM_PROMPT

from app.memory.store import MemoryStore
from app.memory.context import build_context
from app.memory.pipeline import MemoryPipeline

from app.llm import LLMConfig, LLMEngine, ModelManager
from app.config import MODEL, RAG_MODEL, RAG_BACKEND, LLM_FALLBACK_RESPONSE
from app.search.searxng import SearXNG
from app.documents.store import DocumentStore

from app.config import MAX_GENERATION_TOKENS, MAX_CONTINUATIONS, CONTINUATION_MIN_RATIO

from app.tools.registry import ToolRegistry
from app.tools.executor import ToolExecutor
from app.tools.calculator import calculate
from app.tools.extensions_tools import tool_description_text

from typing import Callable, Optional, Any


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
            max_continuations=MAX_CONTINUATIONS,
            continuation_min_ratio=CONTINUATION_MIN_RATIO,
        )

        self.llm = LLMEngine(
            ModelManager(self.llm_config),
            self.llm_config,
        )
        # RAG has its own selectable synthesis model. It is only loaded when
        # retrieved documents/search context is present, avoiding duplicate RAM use.
        self.rag_llm_config = LLMConfig(
            model=RAG_MODEL, backend=RAG_BACKEND, max_tokens=MAX_GENERATION_TOKENS,
            max_continuations=MAX_CONTINUATIONS, continuation_min_ratio=CONTINUATION_MIN_RATIO,
        )
        self.rag_llm = LLMEngine(ModelManager(self.rag_llm_config), self.rag_llm_config)

        self.search = SearXNG()
        self.documents = DocumentStore()

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
        self.extension_manager = None

    def _select_generation_tokens(self, text: str, route: str) -> int:
        """Select a response budget based on intent and requested detail."""
        t = text.strip().lower()

        explicit_short = any(k in t for k in (
            "สั้น", "สรุปสั้น", "ตอบสั้น", "brief", "short answer", "tl;dr",
        ))
        explicit_long = any(k in t for k in (
            "ละเอียด", "โดยละเอียด", "เชิงลึก", "อธิบายเต็ม", "ครบถ้วน",
            "ทีละขั้นตอน", "step by step", "in detail", "deep dive", "comprehensive",
        ))
        document_task = any(k in t for k in (
            "pdf", "เอกสาร", "ไฟล์", "ocr", "สรุปไฟล์", "สรุปเอกสาร",
            "document", "paper",
        ))
        academic = any(k in t for k in (
            "อธิบาย", "วิเคราะห์", "เปรียบเทียบ", "ทำไม", "อย่างไร",
            "วิจัย", "เปเปอร์", "paper", "algorithm", "วิชา", "machine learning",
            "deep learning", "neural network", "programming", "โค้ด", "code",
            "สรุปเนื้อหา", "สอน",
        ))

        if explicit_short:
            target = 320
        elif explicit_long or document_task or any(k in t for k in ('website', 'html', 'เว็บไซต์', 'เว็บเพจ', 'หน้าเว็บ')):
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
            return "Answer briefly and directly. Include only the information needed."
        if budget >= 1536:
            return "Answer in detail and preserve important steps, caveats, structure, and useful examples. Avoid filler."
        if budget >= 1024:
            return "Answer with enough depth for understanding. Use structure and examples when useful, without unnecessary repetition."
        return "Answer naturally with moderate detail. Be complete but concise enough for a normal question."

    # ========================================================
    # Main Chat
    # ========================================================

    def chat(
        self,
        text: str,
        on_token: Optional[Callable[[str], None]] = None,
        emit_console: bool = True,
        extra_context: Optional[str] = None,
        precomputed_search: Optional[list[dict[str, Any]]] = None,
    ):

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

            if emit_console:
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

            if emit_console:
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

        # Persistent document memory: uploaded files remain searchable across
        # sessions and restarts. A directly attached document is still given
        # priority, while previously uploaded files are retrieved by query.
        persistent_document_context, document_hits = self.documents.context(text, limit=5)
        if persistent_document_context:
            messages.append({
                "role": "system",
                "content": persistent_document_context,
            })

        if extra_context:
            messages.append({
                "role": "system",
                "content": "Current attached document text:\n" + extra_context,
            })

        messages.append({
            "role": "system",
            "content": "Response style: " + self._response_style_instruction(text, route),
        })
        if self.extension_manager is not None:
            connected = [x["name"] for x in self.extension_manager.list_extensions() if x["connected"]]
            if connected:
                messages.append({
                    "role": "system",
                    "content": tool_description_text() + " Connected now: " + ", ".join(connected) + ".",
                })

        # ====================================================
        # SEARCH ROUTE
        # ====================================================

        if route == "search":

            if precomputed_search is None:
                results = self.search.search(text)
                if results:
                    messages.append({
                        "role": "system",
                        "content": "Search results:\n" + results,
                    })
            else:
                formatted = "\n".join(
                    f"- {item.get('title','')}\n  {item.get('content','')}\n  {item.get('url','')}"
                    for item in precomputed_search
                )
                if formatted:
                    messages.append({
                        "role": "system",
                        "content": "Search results:\n" + formatted,
                    })

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

        if emit_console:
            print(
                "\nAI: ",
                end="",
                flush=True,
            )

        active_llm = self.llm
        if persistent_document_context or extra_context or precomputed_search:
            from app.core.rag_policy import choose_rag_model, installed_models
            selected=choose_rag_model(text,len(persistent_document_context or "")+len(extra_context or ""),self.llm.config.model,installed_models())
            if selected != self.llm.config.model:
                if self.rag_llm.config.model != selected:
                    self.rag_llm.model_manager.switch_model(selected,"ollama",False)
                active_llm=self.rag_llm
        try:
            answer = active_llm.stream(
                messages, max_tokens=self._select_generation_tokens(text, route),
                on_token=on_token, emit_console=emit_console,
            )
        except Exception:
            # Returning a visible response is preferable to an indefinitely
            # spinning client when a local model is unavailable or silent.
            answer = LLM_FALLBACK_RESPONSE
            if on_token:
                on_token(answer)
            if emit_console:
                print(answer, end="", flush=True)

        if emit_console:
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
        self.rag_llm.shutdown()
