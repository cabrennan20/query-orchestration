"""Application settings using Pydantic settings management."""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ElasticSearch Configuration
    elasticsearch_hosts: str = "http://localhost:9200"
    elasticsearch_username: str = "elastic"
    elasticsearch_password: str = "changeme"
    elasticsearch_index_prefix: str = "search_"

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True

    # Algorithm Storage
    algorithm_config_path: str = "./configs/algorithms"
    algorithm_storage_type: str = "filesystem"

    # Testing Configuration
    test_query_index: str = "test_queries"
    enable_query_logging: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def elasticsearch_hosts_list(self) -> List[str]:
        """Parse comma-separated hosts into a list."""
        return [h.strip() for h in self.elasticsearch_hosts.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
