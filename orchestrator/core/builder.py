"""Factory for creating block instances from configuration."""

from typing import Any, Dict

from elasticsearch import AsyncElasticsearch

from orchestrator.blocks import (
    Block,
    KeywordSearchBlock,
    VectorSearchBlock,
    MergeBlock,
    RerankBlock,
)
from orchestrator.config import BlockType


class BlockFactory:
    """Factory for creating block instances from configuration."""

    def __init__(self, es_client: AsyncElasticsearch, default_index: str):
        """
        Initialize block factory.

        Args:
            es_client: ElasticSearch async client
            default_index: Default index to search
        """
        self.es_client = es_client
        self.default_index = default_index

    def create_block(self, block_type: BlockType, config: Dict[str, Any]) -> Block:
        """
        Create a block instance from configuration.

        Args:
            block_type: Type of block to create
            config: Block configuration

        Returns:
            Block instance

        Raises:
            ValueError: If block type is unknown
        """
        # Get index from config or use default
        index = config.get("index", self.default_index)

        if block_type == BlockType.KEYWORD_SEARCH:
            return KeywordSearchBlock(config, self.es_client, index)

        elif block_type == BlockType.VECTOR_SEARCH:
            return VectorSearchBlock(config, self.es_client, index)

        elif block_type == BlockType.MERGE:
            return MergeBlock(config)

        elif block_type == BlockType.RERANK:
            return RerankBlock(config)

        else:
            raise ValueError(f"Unknown block type: {block_type}")
