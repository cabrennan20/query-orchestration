"""Entry point for running the API server."""

import uvicorn

from orchestrator.api.main import create_app
from orchestrator.config import get_settings


def main():
    """Run the API server."""
    settings = get_settings()

    app = create_app()

    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
    )


if __name__ == "__main__":
    main()
