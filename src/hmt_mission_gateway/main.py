"""One application process, two bounded listeners; no forwarded-header trust."""

import asyncio

import uvicorn

from .application import create_apps
from .settings import Settings


async def run() -> None:
    app, metrics = create_apps(Settings())
    options = {
        "host": "0.0.0.0",
        "access_log": False,
        "proxy_headers": False,
        "timeout_keep_alive": 5,
        "limit_concurrency": 20,
    }
    servers = [
        uvicorn.Server(uvicorn.Config(app, port=8000, **options)),
        uvicorn.Server(uvicorn.Config(metrics, port=9000, **options)),
    ]
    try:
        await asyncio.gather(*(server.serve() for server in servers))
    finally:
        for server in servers:
            server.should_exit = True


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
