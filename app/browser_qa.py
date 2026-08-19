from __future__ import annotations
import json
from pathlib import Path


def run(url: str, screenshot: str | None = None) -> dict:
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        return {"ok": False, "skipped": True, "reason": f"Playwright not installed: {exc}"}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        try:
            response = page.goto(url, wait_until="networkidle", timeout=30000)
            title = page.title()
            if screenshot:
                Path(screenshot).parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=screenshot, full_page=True)
            return {
                "ok": bool(response and response.ok) and not console_errors,
                "status": response.status if response else None,
                "title": title,
                "console_errors": console_errors,
            }
        except Exception as exc:
            return {"ok": False, "error": str(exc), "console_errors": console_errors}
        finally:
            browser.close()
