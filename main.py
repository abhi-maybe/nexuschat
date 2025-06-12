"""NexusChat - Entry point."""

import uvicorn
from config import settings


def main():
    """Run the NexusChat server."""
    uvicorn.run(
        "server.app:create_app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        factory=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
