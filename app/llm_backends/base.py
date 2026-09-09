from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Iterator

@dataclass
class GenerationEvent:
    text: str = ""
    generation_tokens: int | None = None
    finish_reason: str | None = None

class LLMBackend(ABC):
    name: str
    platform: str
    model: str

    @abstractmethod
    def load(self) -> tuple[Any, Any]: ...

    @abstractmethod
    def unload(self) -> None: ...

    @abstractmethod
    def stream_generate(self, prompt: str, max_tokens: int, temperature: float, top_p: float) -> Iterator[GenerationEvent]: ...

    @abstractmethod
    def encode(self, text: str) -> list[int]: ...

    @abstractmethod
    def decode(self, tokens: list[int]) -> str: ...

    def available(self) -> bool:
        return True

    def info(self) -> dict[str, Any]:
        return {"backend": self.name, "platform": self.platform, "model": self.model, "available": self.available()}
