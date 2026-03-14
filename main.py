"""Entry point for the SMA Research Platform API."""

import uvicorn

from src.sma_platform.api.app import create_app
from src.sma_platform.core.config import settings

app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
        reload=True,
    )
