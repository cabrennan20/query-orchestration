"""Algorithm executor - orchestrates the execution of search algorithms."""

import asyncio
from typing import Any, Dict, List, Optional
import time

from orchestrator.blocks import Block, BlockResult
from orchestrator.config import AlgorithmConfig, BlockType
from orchestrator.core.builder import BlockFactory


class ExecutionResult:
    """Result from executing an algorithm."""

    def __init__(
        self,
        algorithm_id: str,
        query: str,
        final_result: BlockResult,
        intermediate_results: List[BlockResult],
        total_time_ms: float,
        metadata: Dict[str, Any],
    ):
        self.algorithm_id = algorithm_id
        self.query = query
        self.final_result = final_result
        self.intermediate_results = intermediate_results
        self.total_time_ms = total_time_ms
        self.metadata = metadata

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "algorithm_id": self.algorithm_id,
            "query": self.query,
            "hits": [
                {
                    "id": hit.id,
                    "score": hit.score,
                    "rank": hit.rank,
                    "source": hit.source,
                }
                for hit in self.final_result.hits
            ],
            "total": self.final_result.total,
            "took_ms": self.total_time_ms,
            "metadata": {
                **self.metadata,
                "num_blocks": len(self.intermediate_results),
                "block_timings": [
                    {
                        "block_type": r.metadata.get("block_type", "unknown"),
                        "took_ms": r.took_ms,
                    }
                    for r in self.intermediate_results
                ],
            },
        }


class AlgorithmExecutor:
    """
    Executes search algorithms composed of multiple blocks.

    Handles orchestration, parallel execution, and result passing between blocks.
    """

    def __init__(self, block_factory: BlockFactory):
        """
        Initialize algorithm executor.

        Args:
            block_factory: Factory for creating block instances
        """
        self.block_factory = block_factory

    async def execute(
        self,
        algorithm: AlgorithmConfig,
        query: str,
        query_vector: Optional[List[float]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """
        Execute a search algorithm.

        Args:
            algorithm: Algorithm configuration
            query: Search query text
            query_vector: Optional pre-computed query embedding
            context: Additional context (filters, user_id, etc.)

        Returns:
            ExecutionResult with final and intermediate results
        """
        start_time = time.time()
        intermediate_results = []

        # Filter enabled components
        enabled_components = [c for c in algorithm.components if c.enabled]

        if not enabled_components:
            raise ValueError("No enabled components in algorithm")

        # Group components by execution order
        # For now, simple sequential execution
        # TODO: Support parallel execution for independent blocks
        previous_results = None

        for component in enabled_components:
            # Create block instance
            block = self.block_factory.create_block(component.type, component.config)

            # Execute block
            result = await block.execute(
                query=query,
                query_vector=query_vector,
                context=context,
                previous_results=[previous_results] if previous_results else None,
            )

            intermediate_results.append(result)

            # Pass result to next block if it's not a merge/rerank
            if component.type in [
                BlockType.KEYWORD_SEARCH,
                BlockType.VECTOR_SEARCH,
                BlockType.HYBRID_SEARCH,
            ]:
                # For search blocks, accumulate results for merging
                if previous_results is None:
                    previous_results = result
                else:
                    # If we have multiple search results, we need to handle them
                    # This would be the case for parallel searches
                    pass
            else:
                # For merge/rerank blocks, they produce the new result
                previous_results = result

        # Final result is the last intermediate result
        final_result = intermediate_results[-1]

        total_time_ms = (time.time() - start_time) * 1000

        return ExecutionResult(
            algorithm_id=algorithm.algorithm_id,
            query=query,
            final_result=final_result,
            intermediate_results=intermediate_results,
            total_time_ms=total_time_ms,
            metadata={
                "algorithm_version": algorithm.version,
                "algorithm_name": algorithm.name,
            },
        )

    async def execute_parallel_searches(
        self,
        algorithm: AlgorithmConfig,
        query: str,
        query_vector: Optional[List[float]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """
        Execute algorithm with parallel search blocks.

        Groups consecutive search blocks and runs them in parallel,
        then passes all results to the merge block.

        Args:
            algorithm: Algorithm configuration
            query: Search query text
            query_vector: Optional pre-computed query embedding
            context: Additional context

        Returns:
            ExecutionResult with final and intermediate results
        """
        start_time = time.time()
        intermediate_results = []

        enabled_components = [c for c in algorithm.components if c.enabled]

        if not enabled_components:
            raise ValueError("No enabled components in algorithm")

        # Group components into phases
        search_blocks = []
        post_search_blocks = []
        in_search_phase = True

        for component in enabled_components:
            if component.type in [
                BlockType.KEYWORD_SEARCH,
                BlockType.VECTOR_SEARCH,
                BlockType.HYBRID_SEARCH,
            ]:
                if in_search_phase:
                    search_blocks.append(component)
                else:
                    raise ValueError(
                        "Search blocks must come before merge/rerank blocks"
                    )
            else:
                in_search_phase = False
                post_search_blocks.append(component)

        # Execute search blocks in parallel
        if search_blocks:
            search_tasks = []
            for component in search_blocks:
                block = self.block_factory.create_block(component.type, component.config)
                task = block.execute(
                    query=query,
                    query_vector=query_vector,
                    context=context,
                    previous_results=None,
                )
                search_tasks.append(task)

            search_results = await asyncio.gather(*search_tasks)
            intermediate_results.extend(search_results)
        else:
            search_results = []

        # Execute post-search blocks sequentially
        previous_results = search_results
        for component in post_search_blocks:
            block = self.block_factory.create_block(component.type, component.config)
            result = await block.execute(
                query=query,
                query_vector=query_vector,
                context=context,
                previous_results=previous_results,
            )
            intermediate_results.append(result)
            previous_results = [result]

        # Final result is the last intermediate result
        final_result = intermediate_results[-1]

        total_time_ms = (time.time() - start_time) * 1000

        return ExecutionResult(
            algorithm_id=algorithm.algorithm_id,
            query=query,
            final_result=final_result,
            intermediate_results=intermediate_results,
            total_time_ms=total_time_ms,
            metadata={
                "algorithm_version": algorithm.version,
                "algorithm_name": algorithm.name,
                "parallel_searches": len(search_blocks),
            },
        )
