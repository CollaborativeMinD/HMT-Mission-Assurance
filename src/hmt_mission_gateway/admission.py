"""Fail-closed bearer, origin, bounded concurrency and request deadline."""

import asyncio
import hmac

from pydantic import SecretStr
from starlette.datastructures import Headers
from starlette.responses import PlainTextResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .settings import Settings


class Admission:
    def __init__(self, app: ASGIApp, token: SecretStr, settings: Settings) -> None:
        self.app, self.token, self.settings = app, token, settings
        self.active = 0

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = Headers(scope=scope)
        supplied = headers.get("authorization", "")
        expected = "Bearer " + self.token.get_secret_value()
        if not hmac.compare_digest(supplied.encode(), expected.encode()):
            await PlainTextResponse("UNAUTHORIZED", 401)(scope, receive, send)
            return
        if "origin" in headers:
            await PlainTextResponse("ORIGIN_DENIED", 403)(scope, receive, send)
            return
        if self.active >= self.settings.max_active:
            await PlainTextResponse("CAPACITY", 503)(scope, receive, send)
            return
        self.active += 1
        started = False

        async def track(message: Message) -> None:
            nonlocal started
            started |= message["type"] == "http.response.start"
            await send(message)

        try:
            async with asyncio.timeout(self.settings.request_seconds):
                await self.app(scope, receive, track)
        except TimeoutError:
            if not started:
                await PlainTextResponse("DEADLINE", 504)(scope, receive, send)
        finally:
            self.active -= 1
