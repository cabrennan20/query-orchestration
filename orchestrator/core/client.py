"""ElasticSearch client wrapper with connection management."""

from typing import List, Optional

from elasticsearch import AsyncElasticsearch

from orchestrator.config import Settings


class ElasticsearchClient:
    """Wrapper for ElasticSearch async client with connection management."""

    def __init__(self, settings: Settings):
        """
        Initialize ElasticSearch client.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self._client: Optional[AsyncElasticsearch] = None

    async def connect(self) -> AsyncElasticsearch:
        """Connect to ElasticSearch cluster."""
        if self._client is None:
            self._client = AsyncElasticsearch(
                hosts=self.settings.elasticsearch_hosts_list,
                basic_auth=(
                    self.settings.elasticsearch_username,
                    self.settings.elasticsearch_password,
                ),
                verify_certs=False,  # For development; use True in production
            )

            # Verify connection
            await self._client.info()

        return self._client

    async def disconnect(self):
        """Close ElasticSearch connection."""
        if self._client is not None:
            await self._client.close()
            self._client = None

    async def get_client(self) -> AsyncElasticsearch:
        """Get or create ElasticSearch client."""
        if self._client is None:
            await self.connect()
        return self._client

    async def health_check(self) -> bool:
        """Check if ElasticSearch is healthy."""
        try:
            client = await self.get_client()
            health = await client.cluster.health()
            return health["status"] in ["green", "yellow"]
        except Exception:
            return False
