"""API request and response models."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Request to execute a search algorithm."""

    query: str = Field(description="Search query text")
    algorithm_id: Optional[str] = Field(
        default=None, description="Algorithm ID to use (optional)"
    )
    algorithm_config: Optional[Dict[str, Any]] = Field(
        default=None, description="Inline algorithm configuration (optional)"
    )
    query_vector: Optional[List[float]] = Field(
        default=None, description="Pre-computed query embedding"
    )
    context: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional context (filters, user_id, etc.)"
    )
    index: Optional[str] = Field(
        default=None, description="ElasticSearch index to search"
    )
    parallel: bool = Field(
        default=True, description="Execute search blocks in parallel"
    )


class SearchHit(BaseModel):
    """A single search result."""

    id: str
    score: float
    rank: Optional[int] = None
    source: Dict[str, Any]


class SearchResponse(BaseModel):
    """Response from executing a search algorithm."""

    algorithm_id: str
    query: str
    hits: List[SearchHit]
    total: int
    took_ms: float
    metadata: Dict[str, Any] = {}


class CompareRequest(BaseModel):
    """Request to compare multiple algorithms."""

    query: str
    algorithm_ids: List[str] = Field(
        description="List of algorithm IDs to compare"
    )
    query_vector: Optional[List[float]] = None
    context: Optional[Dict[str, Any]] = None
    index: Optional[str] = None


class CompareResponse(BaseModel):
    """Response from comparing multiple algorithms."""

    query: str
    results: List[SearchResponse]
    comparison_metadata: Dict[str, Any] = {}


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    elasticsearch_connected: bool
    version: str
