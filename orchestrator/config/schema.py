"""
Schema definitions for algorithm configurations.

Defines the structure of composable search algorithms using Pydantic models.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


class BlockType(str, Enum):
    """Types of composable blocks."""

    KEYWORD_SEARCH = "keyword_search"
    VECTOR_SEARCH = "vector_search"
    HYBRID_SEARCH = "hybrid_search"
    MERGE = "merge"
    RERANK = "rerank"
    FILTER = "filter"
    BOOST = "boost"


class MergeStrategy(str, Enum):
    """Strategies for merging multiple result sets."""

    RRF = "rrf"  # Reciprocal Rank Fusion
    WEIGHTED = "weighted"  # Weighted score combination
    CONCATENATE = "concatenate"  # Simple concatenation
    INTERLEAVE = "interleave"  # Round-robin interleaving


class KeywordSearchConfig(BaseModel):
    """Configuration for keyword search block."""

    fields: List[str] = Field(
        description="Fields to search with optional boost (e.g., 'title^3')"
    )
    operator: str = Field(default="or", description="Boolean operator: 'and' or 'or'")
    minimum_should_match: Optional[str] = Field(
        default=None, description="Minimum should match parameter (e.g., '75%' or '2')"
    )
    fuzziness: Optional[Union[str, int]] = Field(
        default=None, description="Fuzziness for fuzzy matching (e.g., 'AUTO' or 1)"
    )
    boost: float = Field(default=1.0, description="Overall query boost")


class VectorSearchConfig(BaseModel):
    """Configuration for vector/semantic search block."""

    field: str = Field(description="Name of the dense_vector field")
    k: int = Field(default=10, description="Number of results to return")
    num_candidates: int = Field(
        default=100, description="Number of candidates for approximate kNN"
    )
    similarity: Optional[str] = Field(
        default=None, description="Similarity function (cosine, dot_product, l2_norm)"
    )
    boost: float = Field(default=1.0, description="Overall query boost")


class MergeConfig(BaseModel):
    """Configuration for merging multiple result sets."""

    strategy: MergeStrategy = Field(description="Merge strategy to use")
    weights: Optional[Dict[str, float]] = Field(
        default=None, description="Weights for weighted merge strategy"
    )
    k: int = Field(default=60, description="Constant for RRF (typically 60)")
    max_results: int = Field(default=10, description="Maximum number of results to return")


class RerankConfig(BaseModel):
    """Configuration for re-ranking results."""

    function_score: Optional[Dict[str, Any]] = Field(
        default=None, description="ElasticSearch function_score configuration"
    )
    script_score: Optional[Dict[str, Any]] = Field(
        default=None, description="ElasticSearch script_score configuration"
    )
    boost_by_field: Optional[str] = Field(
        default=None, description="Field to use for boosting"
    )
    weight: float = Field(default=1.0, description="Weight for the boosting function")


class FilterConfig(BaseModel):
    """Configuration for filtering results."""

    filters: List[Dict[str, Any]] = Field(
        description="List of ElasticSearch filter clauses"
    )


class BlockConfig(BaseModel):
    """Configuration for a single composable block."""

    type: BlockType = Field(description="Type of the block")
    config: Dict[str, Any] = Field(description="Block-specific configuration")
    name: Optional[str] = Field(default=None, description="Optional name for this block")
    enabled: bool = Field(default=True, description="Whether this block is enabled")

    @field_validator("config")
    @classmethod
    def validate_config(cls, v: Dict[str, Any], info) -> Dict[str, Any]:
        """Validate block config matches its type."""
        # This could be enhanced to validate config structure per block type
        return v


class AlgorithmMetadata(BaseModel):
    """Metadata about the algorithm."""

    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(
        default="draft", description="Status: draft, testing, production"
    )
    ab_test_id: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class AlgorithmConfig(BaseModel):
    """Complete algorithm configuration."""

    algorithm_id: str = Field(description="Unique identifier for the algorithm")
    version: str = Field(default="1.0", description="Version of the algorithm")
    name: str = Field(description="Human-readable name")
    components: List[BlockConfig] = Field(description="Ordered list of components")
    metadata: AlgorithmMetadata = Field(default_factory=AlgorithmMetadata)

    model_config = {"json_schema_extra": {
        "example": {
            "algorithm_id": "hybrid-search-v1",
            "version": "1.0",
            "name": "Hybrid Search with Personalization",
            "components": [
                {
                    "type": "keyword_search",
                    "config": {
                        "fields": ["title^3", "description", "tags^2"],
                        "operator": "or",
                        "minimum_should_match": "75%",
                    },
                },
                {
                    "type": "vector_search",
                    "config": {
                        "field": "embedding_vector",
                        "k": 20,
                        "num_candidates": 100,
                    },
                },
                {
                    "type": "merge",
                    "config": {
                        "strategy": "rrf",
                        "k": 60,
                        "max_results": 10,
                    },
                },
            ],
            "metadata": {
                "created_by": "user@example.com",
                "status": "draft",
                "description": "Combines keyword and vector search using RRF",
            },
        }
    }}
