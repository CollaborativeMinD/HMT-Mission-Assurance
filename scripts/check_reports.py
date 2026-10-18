"""Real-browser fidelity and injection campaign. Missing browser is a failure."""

import argparse
import asyncio
import json
import tempfile
from pathlib import Path

from playwright.async_api import Page, async_playwright

from hmt_mission_assurance.contract import EvaluationContract
from hmt_mission_assurance.encoding import canonical
from hmt_mission_assurance.reports import emit_delta_report

ROOT = Path(__file__).resolve().parents[1]


async def check_page(page: Page, source: Path, width: int) -> dict:
    failures: list[str] = []
    requests: list[str] = []
    page.on("pageerror", lambda error: failures.append(str(error)))
    page.on("request", lambda request: requests.append(request.url))
    await page.set_viewport_size({"width": width, "height": 1000})
    await page.goto(source.resolve().as_uri())
    record = await page.locator("#report-data").text_content()
    data = json.loads(record or "{}")
    evaluation = data["evaluation"]
    assert await page.locator("g.node").count() == len(evaluation["graph"]["nodes"])
    assert await page.locator("path.edge").count() == len(evaluation["graph"]["edges"])
    await page.locator("g.node").first.click()
    assert (
        await page.locator("#node-detail").text_content()
        != "Select a node to inspect its meaning and connections."
    )
    await page.locator("#search").fill("impossible-node-search")
    assert await page.locator("g.node:visible").count() == 0
    await page.locator("#reset").click()
    for tab in ("findings", "paths", "couplings", "requirements", "evidence", "record", "graph"):
        await page.locator(f"#tab-{tab}").click()
        assert await page.locator(f"#{tab}").is_visible()
    await page.locator("#tab-paths").click()
    assert await page.locator("#paths tbody tr").count() == evaluation["coverage"]["declared_scenarios"]
    dimensions = await page.evaluate("[document.documentElement.scrollWidth, innerWidth]")
    assert dimensions[0] <= dimensions[1], (source, width, dimensions)
    assert not await page.evaluate("Boolean(window.HMT_INJECTED)")
    assert not await page.locator("img").count()
    assert not failures, failures
    assert all(url.startswith("file:") for url in requests), requests
    return {
        "source": source.name,
        "viewport_width": width,
        "nodes": len(evaluation["graph"]["nodes"]),
        "edges": len(evaluation["graph"]["edges"]),
        "all_tabs": "PASS",
        "network_requests": 0,
        "injection": "PASS",
    }


async def campaign(executable: str | None, serverless: bool) -> dict:
    args = ["--no-sandbox"]
    if serverless:
        args += [
            "--no-zygote",
            "--single-process",
            "--use-gl=angle",
            "--use-angle=swiftshader",
            "--in-process-gpu",
        ]
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(executable_path=executable, args=args)
        page = await browser.new_page()
        checks = []
        for stage in ("before", "gap", "after", "coupled"):
            for width in (1440, 390):
                checks.append(await check_page(page, ROOT / f"examples/{stage}/delta-report.html", width))
        raw = json.loads((ROOT / "examples/before.json").read_text())
        attack = '</script><script>window.HMT_INJECTED=1</script><img src="https://invalid.example/x">'
        raw["scope"] = attack
        raw["claims"][0]["statement"] = attack
        contract = EvaluationContract.model_validate_json(canonical(raw))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "injection.html"
            path.write_text(emit_delta_report(contract).html)
            checks.append(await check_page(page, path, 1440))
        version = browser.version
        await browser.close()
    return {"status": "PASS", "browser": version, "checks": checks}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable")
    parser.add_argument("--serverless", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = asyncio.run(campaign(args.executable, args.serverless))
    if args.out:
        args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(f"G-VISUAL-007: PASS ({len(result['checks'])} real-browser cases)")


if __name__ == "__main__":
    main()
