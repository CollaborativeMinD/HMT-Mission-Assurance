"""Capture the README gallery from bundled synthetic reports in Chromium."""

import asyncio
import hashlib
import json
import math
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
VIEWS = {
    "graph": "coupled",
    "findings": "before",
    "paths": "gap",
    "couplings": "coupled",
    "requirements": "gap",
    "evidence": "gap",
    "record": "before",
}
VIEWPORT = {"width": 1440, "height": 1320}


async def capture() -> None:
    destination = ROOT / "docs/screenshots"
    destination.mkdir(parents=True, exist_ok=True)
    captures = []
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(args=["--no-sandbox"])
        page = await browser.new_page(viewport=VIEWPORT, device_scale_factor=1, reduced_motion="reduce")
        errors: list[str] = []
        requests: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("request", lambda request: requests.append(request.url))
        for view, stage in VIEWS.items():
            source = ROOT / f"examples/{stage}/delta-report.html"
            await page.goto(source.as_uri())
            await page.locator(f"#tab-{view}").click()
            assert await page.locator(f"#{view}").is_visible()
            await page.evaluate("document.fonts.ready")
            image = destination / f"{view}.png"
            footer = await page.locator("footer").bounding_box()
            assert footer is not None
            height = min(VIEWPORT["height"], math.ceil(footer["y"] + footer["height"] + 28))
            clip = {"x": 0, "y": 0, "width": VIEWPORT["width"], "height": height}
            await page.screenshot(path=str(image), animations="disabled", clip=clip)
            captures.append(
                {
                    "view": view,
                    "source": str(source.relative_to(ROOT)),
                    "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                    "image": str(image.relative_to(ROOT)),
                    "image_sha256": hashlib.sha256(image.read_bytes()).hexdigest(),
                }
            )
        assert not errors, errors
        assert all(url.startswith("file:") for url in requests), requests
        metadata = {
            "browser": "Chromium " + browser.version,
            "viewport": VIEWPORT,
            "device_scale_factor": 1,
            "synthetic_examples": True,
            "external_requests": 0,
            "captures": captures,
        }
        await browser.close()
    (destination / "captures.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(f"README screenshots: PASS ({len(captures)} views, no external requests)")


if __name__ == "__main__":
    asyncio.run(capture())
