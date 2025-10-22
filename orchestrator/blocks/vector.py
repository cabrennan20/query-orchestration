"""Vector/semantic search block using ElasticSearch kNN search."""

from typing import Any, Dict, List, Optional
import time

from elasticsearch import AsyncElasticsearch

from .base import Block, BlockResult, SearchResult


class VectorSearchBlock(Block):
    """
    Vector/semantic search using ElasticSearch kNN search.

    Requires query_vector to be provided or a vector generation function.
    """

    def __init__(self, config: Dict[str, Any], es_client: AsyncElasticsearch, index: str):
        """
        Initialize vector search block.

        Args:
            config: Configuration dictionary (field, k, num_candidates, etc.)
            es_client: ElasticSearch async client
            index: Index name to search
        """
        super().__init__(config)
        self.es_client = es_client
        self.index = index

    async def execute(
        self,
        query: str,
        query_vector: Optional[List[float]] = None,
        context: Optional[Dict[str, Any]] = None,
        previous_results: Optional[List[BlockResult]] = None,
    ) -> BlockResult:
        """
        Execute vector search.

        Args:
            query: Search query text (for metadata only)
            query_vector: Query embedding vector (required)
            context: Additional context (filters, user info)
            previous_results: Unused for vector search

        Returns:
            BlockResult with vector search results
        """
        if query_vector is None:
            raise ValueError("query_vector is required for vector search")

        start_time = time.time()

        # Build kNN query
        knn_query = {
            "field": self.config["field"],
            "query_vector": query_vector,
            "k": self.config.get("k", 10),
            "num_candidates": self.config.get("num_candidates", 100),
        }

        # Add similarity if specified
        if "similarity" in self.config:
            knn_query["similarity"] = self.config["similarity"]

        # Add boost if specified
        boost = self.config.get("boost", 1.0)
        if boost != 1.0:
            knn_query["boost"] = boost

        # Add filters from context if provided
        if context and "filters" in context:
            knn_query["filter"] = context["filters"]

        # Execute kNN search
        es_query = {
            "knn": knn_query,
            "size": self.config.get("k", 10),
        }

        response = await self.es_client.search(index=self.index, body=es_query)

        # Parse results
        hits = []
        for idx, hit in enumerate(response["hits"]["hits"]):
            hits.append(
                SearchResult(
                    id=hit["_id"],
                    score=hit["_score"],
                    source=hit["_source"],
                    index=hit["_index"],
                    rank=idx + 1,
                )
            )

        elapsed_ms = (time.time() - start_time) * 1000

        return BlockResult(
            hits=hits,
            total=response["hits"]["total"]["value"] if "total" in response["hits"] else len(hits),
            took_ms=elapsed_ms,
            metadata={
                "block_type": "vector_search",
                "query": query,
                "es_took_ms": response["took"],
                "k": self.config.get("k", 10),
                "num_candidates": self.config.get("num_candidates", 100),
            },
        )
