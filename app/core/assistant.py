from app.core.router import Router
from app.core.prompts import SYSTEM_PROMPT
from app.memory.store import MemoryStore
from app.memory.context import build_context
from app.memory.extractor import MemoryExtractor
from app.llm import LocalLLM
from app.search.searxng import SearXNG
from app.config import MAX_GENERATION_TOKENS


class Assistant:
    def __init__(self):
        self.router = Router()
        self.memory = MemoryStore()
        self.memory_extractor = MemoryExtractor()
        self.llm = LocalLLM()
        self.search = SearXNG()

    def chat(self, text: str):
        route = self.router.route(text)

        # Save conversation
        self.memory.add_message(
            "user",
            text
        )

        # Extract long-term memories
        memories = self.memory_extractor.extract(text)

        for memory in memories:
            self.memory.add_memory(**memory)

        # Retrieve relevant conversation context
        context = build_context(
            self.memory,
            text
        )

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            }
        ]

        if context:
            messages.append({
                "role": "system",
                "content": (
                    "Relevant conversation context:\n"
                    + context
                ),
            })

        # Search when router requests it
        if route == "search":
            results = self.search.search(text)

            if results:
                messages.append({
                    "role": "system",
                    "content": (
                        "Search results:\n"
                        + results
                    ),
                })

        messages.append({
            "role": "user",
            "content": text,
        })

        print("\nAI: ", end="", flush=True)

        answer = self.llm.stream(
            messages,
            max_tokens=MAX_GENERATION_TOKENS,
        )

        print()

        # Save assistant response
        self.memory.add_message(
            "assistant",
            answer
        )

        return answer
