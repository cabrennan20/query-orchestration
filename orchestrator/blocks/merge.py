"""Merge block for combining results from multiple searches."""

from typing import Any, Dict, List, Optional
import time
from collections import defaultdict

from .base import Block, BlockResult, SearchResult


class MergeBlock(Block):
    """
    Merge results from multiple search blocks.

    Supports multiple strategies:
    - RRF (Reciprocal Rank Fusion): 1 / (k + rank)
    - Weighted: Combine scores with configurable weights
    - Concatenate: Simple concatenation
    - Interleave: Round-robin interleaving
    """

    async def execute(
        self,
        query: str,
        query_vector: Optional[List[float]] = None,
        context: Optional[Dict[str, Any]] = None,
        previous_results: Optional[List[BlockResult]] = None,
    ) -> BlockResult:
        """
        Merge results from previous blocks.

        Args:
            query: Search query text (for metadata)
            query_vector: Unused for merge
            context: Additional context
            previous_results: Results from previous blocks to merge (required)

        Returns:
            BlockResult with merged results
        """
        if not previous_results or len(previous_results) == 0:
            raise ValueError("previous_results is required for merge block")

        start_time = time.time()

        strategy = self.config.get("strategy", "rrf")

        if strategy == "rrf":
            merged = self._merge_rrf(previous_results)
        elif strategy == "weighted":
            merged = self._merge_weighted(previous_results)
        elif strategy == "concatenate":
            merged = self._merge_concatenate(previous_results)
        elif strategy == "interleave":
            merged = self._merge_interleave(previous_results)
        else:
            raise ValueError(f"Unknown merge strategy: {strategy}")

        # Limit results
        max_results = self.config.get("max_results", 10)
        merged = merged[:max_results]

        elapsed_ms = (time.time() - start_time) * 1000

        return BlockResult(
            hits=merged,
            total=len(merged),
            took_ms=elapsed_ms,
            metadata={
                "block_type": "merge",
                "strategy": strategy,
                "num_sources": len(previous_results),
            },
        )

    def _merge_rrf(self, results: List[BlockResult]) -> List[SearchResult]:
        """
        Merge using Reciprocal Rank Fusion.

        RRF score = sum(1 / (k + rank)) for each occurrence
        """
        k = self.config.get("k", 60)
        scores = defaultdict(float)
        doc_map = {}

        for result_set in results:
            for hit in result_set.hits:
                if hit.rank is None:
                    continue
                rrf_score = 1.0 / (k + hit.rank)
                scores[hit.id] += rrf_score
                if hit.id not in doc_map:
                    doc_map[hit.id] = hit

        # Sort by RRF score
        sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        # Build merged results
        merged = []
        for idx, (doc_id, score) in enumerate(sorted_docs):
            result = doc_map[doc_id]
            result.score = score
            result.rank = idx + 1
            merged.append(result)

        return merged

    def _merge_weighted(self, results: List[BlockResult]) -> List[SearchResult]:
        """
        Merge using weighted score combination.

        Each result set can have a different weight.
        """
        weights = self.config.get("weights", {})
        scores = defaultdict(float)
        doc_map = {}

        for idx, result_set in enumerate(results):
            weight = weights.get(str(idx), 1.0)
            for hit in result_set.hits:
                scores[hit.id] += hit.score * weight
                if hit.id not in doc_map:
                    doc_map[hit.id] = hit

        # Sort by weighted score
        sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        # Build merged results
        merged = []
        for idx, (doc_id, score) in enumerate(sorted_docs):
            result = doc_map[doc_id]
            result.score = score
            result.rank = idx + 1
            merged.append(result)

        return merged

    def _merge_concatenate(self, results: List[BlockResult]) -> List[SearchResult]:
        """Simple concatenation of results in order."""
        merged = []
        rank = 1
        for result_set in results:
            for hit in result_set.hits:
                hit.rank = rank
                merged.append(hit)
                rank += 1
        return merged

    def _merge_interleave(self, results: List[BlockResult]) -> List[SearchResult]:
        """Round-robin interleaving of results."""
        merged = []
        max_len = max(len(r.hits) for r in results)
        seen = set()

        for i in range(max_len):
            for result_set in results:
                if i < len(result_set.hits):
                    hit = result_set.hits[i]
                    if hit.id not in seen:
                        seen.add(hit.id)
                        hit.rank = len(merged) + 1
                        merged.append(hit)

        return merged
