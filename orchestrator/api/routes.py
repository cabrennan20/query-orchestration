"""API route handlers."""

import json
from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException, Depends
from elasticsearch import AsyncElasticsearch

from orchestrator import __version__
from orchestrator.config import AlgorithmConfig, Settings, get_settings
from orchestrator.core import ElasticsearchClient, BlockFactory, AlgorithmExecutor
from orchestrator.api.models import (
    SearchRequest,
    SearchResponse,
    CompareRequest,
    CompareResponse,
    HealthResponse,
    SearchHit,
)

router = APIRouter()

# Dependency to get ES client
_es_client_instance = None


async def get_es_client(settings: Settings = Depends(get_settings)) -> ElasticsearchClient:
    """Get or create ElasticSearch client."""
    global _es_client_instance
    if _es_client_instance is None:
        _es_client_instance = ElasticsearchClient(settings)
        await _es_client_instance.connect()
    return _es_client_instance


@router.get("/health", response_model=HealthResponse)
async def health_check(
    es_client: ElasticsearchClient = Depends(get_es_client),
) -> HealthResponse:
    """Check API and ElasticSearch health."""
    es_healthy = await es_client.health_check()

    return HealthResponse(
        status="healthy" if es_healthy else "degraded",
        elasticsearch_connected=es_healthy,
        version=__version__,
    )


@router.post("/search", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    settings: Settings = Depends(get_settings),
    es_client: ElasticsearchClient = Depends(get_es_client),
) -> SearchResponse:
    """
    Execute a search algorithm.

    Either provide algorithm_id to load a saved algorithm,
    or provide algorithm_config to execute an inline algorithm.
    """
    # Get algorithm configuration
    if request.algorithm_config:
        # Use inline algorithm config
        try:
            algorithm = AlgorithmConfig(**request.algorithm_config)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid algorithm config: {e}")

    elif request.algorithm_id:
        # Load algorithm from storage
        algorithm = await load_algorithm(request.algorithm_id, settings)
        if algorithm is None:
            raise HTTPException(
                status_code=404, detail=f"Algorithm not found: {request.algorithm_id}"
            )
    else:
        raise HTTPException(
            status_code=400,
            detail="Either algorithm_id or algorithm_config must be provided",
        )

    # Get index name
    index = request.index or f"{settings.elasticsearch_index_prefix}products"

    # Create executor
    client = await es_client.get_client()
    factory = BlockFactory(client, index)
    executor = AlgorithmExecutor(factory)

    # Execute algorithm
    try:
        if request.parallel:
            result = await executor.execute_parallel_searches(
                algorithm=algorithm,
                query=request.query,
                query_vector=request.query_vector,
                context=request.context,
            )
        else:
            result = await executor.execute(
                algorithm=algorithm,
                query=request.query,
                query_vector=request.query_vector,
                context=request.context,
            )

        # Convert to response
        return SearchResponse(
            algorithm_id=result.algorithm_id,
            query=result.query,
            hits=[
                SearchHit(
                    id=hit.id,
                    score=hit.score,
                    rank=hit.rank,
                    source=hit.source,
                )
                for hit in result.final_result.hits
            ],
            total=result.final_result.total,
            took_ms=result.total_time_ms,
            metadata=result.metadata,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search execution failed: {e}")


@router.post("/compare", response_model=CompareResponse)
async def compare_algorithms(
    request: CompareRequest,
    settings: Settings = Depends(get_settings),
    es_client: ElasticsearchClient = Depends(get_es_client),
) -> CompareResponse:
    """
    Compare multiple algorithms side-by-side.

    Executes the same query against multiple algorithms and returns all results.
    """
    results = []

    for algorithm_id in request.algorithm_ids:
        # Create search request for this algorithm
        search_req = SearchRequest(
            query=request.query,
            algorithm_id=algorithm_id,
            query_vector=request.query_vector,
            context=request.context,
            index=request.index,
        )

        try:
            result = await search(search_req, settings, es_client)
            results.append(result)
        except Exception as e:
            # Log error but continue with other algorithms
            print(f"Error executing algorithm {algorithm_id}: {e}")

    if not results:
        raise HTTPException(
            status_code=500,
            detail="All algorithms failed to execute",
        )

    return CompareResponse(
        query=request.query,
        results=results,
        comparison_metadata={
            "num_algorithms": len(request.algorithm_ids),
            "successful": len(results),
            "failed": len(request.algorithm_ids) - len(results),
        },
    )


@router.get("/algorithms", response_model=List[AlgorithmConfig])
async def list_algorithms(
    settings: Settings = Depends(get_settings),
) -> List[AlgorithmConfig]:
    """List all available algorithms."""
    algorithms = []

    if settings.algorithm_storage_type == "filesystem":
        config_path = Path(settings.algorithm_config_path)
        if config_path.exists():
            for config_file in config_path.glob("*.json"):
                try:
                    with open(config_file) as f:
                        config = json.load(f)
                        algorithms.append(AlgorithmConfig(**config))
                except Exception as e:
                    print(f"Error loading algorithm from {config_file}: {e}")

    return algorithms


@router.get("/algorithms/{algorithm_id}", response_model=AlgorithmConfig)
async def get_algorithm(
    algorithm_id: str,
    settings: Settings = Depends(get_settings),
) -> AlgorithmConfig:
    """Get a specific algorithm by ID."""
    algorithm = await load_algorithm(algorithm_id, settings)

    if algorithm is None:
        raise HTTPException(
            status_code=404,
            detail=f"Algorithm not found: {algorithm_id}",
        )

    return algorithm


@router.post("/algorithms", response_model=AlgorithmConfig, status_code=201)
async def save_algorithm(
    algorithm: AlgorithmConfig,
    settings: Settings = Depends(get_settings),
) -> AlgorithmConfig:
    """Save a new algorithm configuration."""
    if settings.algorithm_storage_type == "filesystem":
        config_path = Path(settings.algorithm_config_path)
        config_path.mkdir(parents=True, exist_ok=True)

        file_path = config_path / f"{algorithm.algorithm_id}.json"

        if file_path.exists():
            raise HTTPException(
                status_code=409,
                detail=f"Algorithm already exists: {algorithm.algorithm_id}",
            )

        with open(file_path, "w") as f:
            json.dump(algorithm.model_dump(), f, indent=2, default=str)

    return algorithm


async def load_algorithm(
    algorithm_id: str, settings: Settings
) -> AlgorithmConfig | None:
    """Load an algorithm from storage."""
    if settings.algorithm_storage_type == "filesystem":
        config_path = Path(settings.algorithm_config_path)
        file_path = config_path / f"{algorithm_id}.json"

        if not file_path.exists():
            return None

        try:
            with open(file_path) as f:
                config = json.load(f)
                return AlgorithmConfig(**config)
        except Exception as e:
            print(f"Error loading algorithm {algorithm_id}: {e}")
            return None

    return None
