"""Base classes for composable blocks."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class SearchResult(BaseModel):
    """A single search result."""

    id: str
    score: float
    source: Dict[str, Any]
    index: Optional[str] = None
    rank: Optional[int] = None


class BlockResult(BaseModel):
    """Result from executing a block."""

    hits: List[SearchResult]
    total: int
    took_ms: Optional[float] = None
    metadata: Dict[str, Any] = {}


class Block(ABC):
    """Base class for all composable blocks."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize block with configuration."""
        self.config = config

    @abstractmethod
    async def execute(
        self,
        query: str,
        query_vector: Optional[List[float]] = None,
        context: Optional[Dict[str, Any]] = None,
        previous_results: Optional[List[BlockResult]] = None,
    ) -> BlockResult:
        """
        Execute the block.

        Args:
            query: The user's search query text
            query_vector: Optional pre-computed query embedding
            context: Additional context (user_id, filters, etc.)
            previous_results: Results from previous blocks in the pipeline

        Returns:
            BlockResult containing search hits
        """
        pass

    def validate_config(self) -> bool:
        """Validate the block configuration."""
        return True
