"""Lifespan-owned stateless MCP and isolated metrics ASGI applications."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse, Response
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp.server.transport_security import TransportSecuritySettings
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.routing import Route

from hmt_mission_assurance.cli import skill_text
from hmt_mission_assurance.server import create_server

from .admission import Admission
from .metrics import Metrics
from .settings import Settings, read_secret
from .transport import Transport


def create_apps(settings: Settings) -> tuple[FastAPI, FastAPI]:
    token = read_secret(settings.token_file)
    metric_token = read_secret(settings.metrics_token_file)
    if token == metric_token:
        raise ValueError("SECRETS_MUST_DIFFER")
    metrics = Metrics()
    manager = StreamableHTTPSessionManager(
        create_server(metrics.execute),
        stateless=True,
        json_response=True,
        max_request_body_size=settings.max_body_bytes,
        security_settings=TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=[f"{host}:*" for host in settings.allowed_hosts] + settings.allowed_hosts,
            allowed_origins=[],
        ),
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        async with manager.run():
            yield

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    app.router.routes.append(Route("/mcp", endpoint=Transport(manager), methods=["POST", "GET", "DELETE"]))

    @app.get("/health/live")
    async def live() -> dict[str, str]:
        return {"status": "live"}

    @app.get("/skills/hmt-mission-assurance")
    async def skill() -> PlainTextResponse:
        return PlainTextResponse(skill_text())

    monitor = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    @monitor.get("/metrics")
    async def scrape() -> Response:
        return Response(generate_latest(metrics.registry), headers={"Content-Type": CONTENT_TYPE_LATEST})

    app.state.metrics = metrics
    for target, secret in ((app, token), (monitor, metric_token)):
        target.add_middleware(Admission, token=secret, settings=settings)
        target.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
    return app, monitor
