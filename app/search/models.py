from dataclasses import dataclass
from typing import Optional


@dataclass
class SearchResult:
    title: str
    url: str
    content: str = ""
    engine: str = ""
    score: float = 0.0


@dataclass
class SearchResponse:
    query: str
    results: list[SearchResult]
    provider: Optional[str] = None
