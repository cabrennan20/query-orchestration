"""Re-ranking block for adjusting result order based on additional signals."""

from typing import Any, Dict, List, Optional
import time

from .base import Block, BlockResult, SearchResult


class RerankBlock(Block):
    """
    Re-rank results using additional signals.

    Supports:
    - Boosting by field value (e.g., popularity, recency)
    - Custom scoring functions
    """

    async def execute(
        self,
        query: str,
        query_vector: Optional[List[float]] = None,
        context: Optional[Dict[str, Any]] = None,
        previous_results: Optional[List[BlockResult]] = None,
    ) -> BlockResult:
        """
        Re-rank results from previous block.

        Args:
            query: Search query text (for metadata)
            query_vector: Unused for rerank
            context: Additional context
            previous_results: Results to re-rank (required)

        Returns:
            BlockResult with re-ranked results
        """
        if not previous_results or len(previous_results) == 0:
            raise ValueError("previous_results is required for rerank block")

        # For now, just take the first result set
        # In production, you might want to merge first
        results = previous_results[-1]

        start_time = time.time()

        # Apply boosting
        if "boost_by_field" in self.config:
            results = self._boost_by_field(results)

        elapsed_ms = (time.time() - start_time) * 1000

        return BlockResult(
            hits=results.hits,
            total=results.total,
            took_ms=elapsed_ms,
            metadata={
                "block_type": "rerank",
                "original_took_ms": results.took_ms,
            },
        )

    def _boost_by_field(self, results: BlockResult) -> BlockResult:
        """Boost results by a field value."""
        field = self.config["boost_by_field"]
        weight = self.config.get("weight", 1.0)

        for hit in results.hits:
            if field in hit.source:
                field_value = hit.source[field]
                if isinstance(field_value, (int, float)):
                    # Simple multiplicative boost
                    hit.score = hit.score * (1 + weight * field_value)

        # Re-sort by new scores
        results.hits.sort(key=lambda x: x.score, reverse=True)

        # Update ranks
        for idx, hit in enumerate(results.hits):
            hit.rank = idx + 1

        return results
