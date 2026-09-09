from abc import ABC, abstractmethod

from app.search.models import SearchResponse


class SearchProvider(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def search(
        self,
        query: str,
        limit: int = 5,
    ) -> SearchResponse:
        raise NotImplementedError
