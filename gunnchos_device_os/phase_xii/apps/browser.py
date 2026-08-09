"""Real browser workflows via Playwright (LMS/share/media/WAIKE)."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any


def browser_lms_workflow(lms_url: str, evidence_dir: Path, upload_file: Path | None = None) -> dict[str, Any]:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    started = time.time()
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        # Still hit LMS with httpx as process-level proof of real HTTP service
        import httpx

        r = httpx.get(lms_url, timeout=10)
        pdf = httpx.get(lms_url.rstrip("/") + "/assignment.pdf", timeout=10)
        dest = evidence_dir / "assignment.pdf"
        dest.write_bytes(pdf.content)
        submit = httpx.post(lms_url.rstrip("/") + "/submit", content=b"phase-xii-upload", timeout=10)
        return {
            "ok": r.status_code == 200 and submit.status_code == 200,
            "browser": False,
            "playwright": False,
            "downloaded": str(dest),
            "bytes": len(pdf.content),
            "receipt": submit.json() if submit.headers.get("content-type", "").startswith("application/json") else {},
            "execution_depth": "L4_REAL_APPLICATION_PROCESS",
            "duration_ms": int((time.time() - started) * 1000),
            "note": "playwright missing; used real HTTP client against HTML LMS",
        }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(accept_downloads=True)
        page = ctx.new_page()
        page.goto(lms_url, wait_until="domcontentloaded", timeout=30000)
        page.screenshot(path=str(evidence_dir / "lms_open.png"))
        with page.expect_download() as dl_info:
            page.click("#download")
        download = dl_info.value
        dest = evidence_dir / download.suggested_filename
        download.save_as(str(dest))
        if upload_file and upload_file.exists():
            page.set_input_files("#file", str(upload_file))
        else:
            page.set_input_files("#file", str(dest))
        page.click("button[type=submit]")
        page.wait_for_timeout(500)
        receipt = page.evaluate("() => window.__lms_receipt || null")
        page.screenshot(path=str(evidence_dir / "lms_submit.png"))
        browser.close()
    return {
        "ok": bool(receipt) and dest.exists(),
        "browser": True,
        "playwright": True,
        "downloaded": str(dest),
        "receipt": receipt,
        "screenshots": [str(evidence_dir / "lms_open.png"), str(evidence_dir / "lms_submit.png")],
        "execution_depth": "L5_REAL_GUI_INTERACTION",
        "duration_ms": int((time.time() - started) * 1000),
    }


def browser_open_url(url: str, evidence_dir: Path, name: str = "page") -> dict[str, Any]:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        import httpx

        r = httpx.get(url, timeout=10)
        (evidence_dir / f"{name}.html").write_bytes(r.content)
        return {"ok": r.status_code == 200, "browser": False, "status": r.status_code, "execution_depth": "L4_REAL_APPLICATION_PROCESS"}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        shot = evidence_dir / f"{name}.png"
        page.screenshot(path=str(shot))
        title = page.title()
        browser.close()
    return {"ok": True, "browser": True, "title": title, "screenshot": str(shot), "execution_depth": "L5_REAL_GUI_INTERACTION"}
