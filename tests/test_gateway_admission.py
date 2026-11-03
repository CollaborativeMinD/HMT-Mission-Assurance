import asyncio
from contextlib import suppress

from pydantic import SecretStr

from hmt_mission_gateway.admission import Admission
from hmt_mission_gateway.settings import Settings


async def receive():
    return {"type": "http.request", "body": b"", "more_body": False}


def test_capacity_deadline_and_cancellation():
    async def campaign():
        scope = {"type": "http", "headers": [(b"authorization", b"Bearer test")]}
        settings = Settings(request_seconds=0.01, max_active=1)
        entered, release = asyncio.Event(), asyncio.Event()

        async def slow(scope, receive, send):
            entered.set()
            await release.wait()

        messages = []

        async def send(message):
            messages.append(message)

        middleware = Admission(slow, SecretStr("test"), settings)
        first = asyncio.create_task(middleware(scope, receive, send))
        await entered.wait()
        await middleware(scope, receive, send)
        await first
        assert [m["status"] for m in messages if m["type"] == "http.response.start"] == [503, 504]
        assert middleware.active == 0
        second = asyncio.create_task(middleware(scope, receive, send))
        await asyncio.sleep(0)
        second.cancel()
        with suppress(asyncio.CancelledError):
            await second
        assert middleware.active == 0

    asyncio.run(campaign())


def test_runner_owns_both_listeners(monkeypatch):
    from hmt_mission_gateway import main

    instances = []

    class FakeServer:
        def __init__(self, config):
            self.config, self.should_exit = config, False
            instances.append(self)

        async def serve(self):
            return None

    monkeypatch.setattr(main, "create_apps", lambda settings: (object(), object()))
    monkeypatch.setattr(main.uvicorn, "Server", FakeServer)
    main.main()
    assert {item.config.port for item in instances} == {8000, 9000}
    assert all(item.should_exit for item in instances)
    assert all(not item.config.proxy_headers for item in instances)


def test_deadline_is_cooperative_not_cpu_preemption():
    from time import monotonic, sleep

    async def campaign():
        messages = []

        async def send(message):
            messages.append(message)

        async def blocking(scope, receive, send):
            sleep(0.03)
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b"ok"})

        app = Admission(blocking, SecretStr("test"), Settings(request_seconds=0.001))
        scope = {"type": "http", "headers": [(b"authorization", b"Bearer test")]}
        start = monotonic()
        await app(scope, receive, send)
        assert monotonic() - start >= 0.03
        assert messages[0]["status"] == 200
        assert app.active == 0

    asyncio.run(campaign())
