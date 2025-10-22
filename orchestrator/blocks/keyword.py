"""Keyword search block using ElasticSearch multi_match query."""

from typing import Any, Dict, List, Optional
import time

from elasticsearch import AsyncElasticsearch

from .base import Block, BlockResult, SearchResult


class KeywordSearchBlock(Block):
    """
    Keyword search using ElasticSearch multi_match query.

    Supports field boosting, operators, fuzziness, and minimum_should_match.
    """

    def __init__(self, config: Dict[str, Any], es_client: AsyncElasticsearch, index: str):
        """
        Initialize keyword search block.

        Args:
            config: Configuration dictionary (fields, operator, etc.)
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
        Execute keyword search.

        Args:
            query: Search query text
            query_vector: Unused for keyword search
            context: Additional context (filters, user info)
            previous_results: Unused for keyword search

        Returns:
            BlockResult with keyword search results
        """
        start_time = time.time()

        # Build multi_match query
        multi_match = {
            "query": query,
            "fields": self.config.get("fields", ["*"]),
            "type": "best_fields",  # Could be configurable
            "operator": self.config.get("operator", "or"),
        }

        # Add optional parameters
        if "minimum_should_match" in self.config:
            multi_match["minimum_should_match"] = self.config["minimum_should_match"]

        if "fuzziness" in self.config:
            multi_match["fuzziness"] = self.config["fuzziness"]

        # Build the complete query
        es_query = {"query": {"multi_match": multi_match}}

        # Add boost if specified
        boost = self.config.get("boost", 1.0)
        if boost != 1.0:
            es_query = {
                "query": {
                    "function_score": {
                        "query": es_query["query"],
                        "boost": boost,
                        "boost_mode": "multiply",
                    }
                }
            }

        # Add filters from context if provided
        if context and "filters" in context:
            es_query["query"] = {
                "bool": {
                    "must": es_query["query"],
                    "filter": context["filters"],
                }
            }

        # Add size parameter
        es_query["size"] = self.config.get("size", 10)

        # Execute search
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
            total=response["hits"]["total"]["value"],
            took_ms=elapsed_ms,
            metadata={
                "block_type": "keyword_search",
                "query": query,
                "es_took_ms": response["took"],
            },
        )
