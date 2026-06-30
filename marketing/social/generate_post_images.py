"""
generate_post_images.py
Generates per-post screenshots from HomeSight, uploads to server, patches buffer_schedule.py.

Usage:
  python generate_post_images.py              # screenshot + upload + patch
  python generate_post_images.py --dry-run    # screenshot only, no upload, no patch
  python generate_post_images.py --no-upload  # skip upload
  python generate_post_images.py --no-patch   # skip patching buffer_schedule.py

Requirements:
  pip install playwright
  playwright install chromium

How it works:
  - Imports POSTS from buffer_schedule.py (safe — execution is guarded by __main__)
  - For each post, extracts the first 5-digit US ZIP from the text
  - Opens homesight.live, calls openPanel(zip), waits for charts to render
  - Screenshots at 1200x630 (standard social og dimensions)
  - Posts with no ZIP are skipped (they use the default OG image)
  - Uploads PNGs to /opt/homesight/static/social/ via scp
  - Patches buffer_schedule.py with "image": "https://homesight.live/static/social/..."
    per post, keyed by scheduled_at time (unique per post)
"""

import re
import sys
import asyncio
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

from playwright.async_api import async_playwright

# ── Config ────────────────────────────────────────────────────────────────────

SITE       = "https://homesight.live"
OUT_DIR    = Path(__file__).parent / "post_images"
SSH_KEY    = r"C:\Users\micha\.ssh\beacon.pem"
SERVER     = "ubuntu@44.198.184.19"
REMOTE_DIR = "/opt/homesight/static/social"
PUBLIC_URL = "https://homesight.live/static/social"
SCHEDULE   = Path(__file__).parent / "buffer_schedule.py"

OUT_DIR.mkdir(exist_ok=True)

ZIP_RE = re.compile(r'\b(\d{5})\b')

CHANNEL_SHORT = {
    "6a41645d5ab6d2f10680e433": "TW",
    "6a41677f5ab6d2f10680f0d9": "FB",
    "6a4167a85ab6d2f10680f165": "LI",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def extract_zip(text: str) -> str | None:
    m = ZIP_RE.search(text)
    return m.group(1) if m else None

def post_filename(post: dict, zip_code: str) -> str:
    date = post["scheduled_at"][:10]
    ch   = CHANNEL_SHORT.get(post["channel"], "XX")
    return f"{date}-{ch}-{zip_code}.png"

def pt_call_str(post: dict) -> str:
    """Reconstruct the pt("YYYY-MM-DD", H) call as it appears in buffer_schedule.py."""
    sat = post["scheduled_at"]
    dt  = datetime.fromisoformat(sat)
    original_hour = dt.hour - 7  # pt() adds 7h to convert PT→UTC
    date_str = sat[:10]
    return f'pt("{date_str}", {original_hour})'

# ── Screenshot ────────────────────────────────────────────────────────────────

async def screenshot_zip(page, zip_code: str, out_path: Path) -> bool:
    try:
        await page.set_viewport_size({"width": 1200, "height": 630})
        await page.goto(SITE, wait_until="domcontentloaded", timeout=30000)

        # Wait for map JS to initialize
        await page.wait_for_function("typeof openPanel === 'function'", timeout=20000)

        # Let map tiles partially load so the background isn't blank
        await page.wait_for_timeout(2500)

        # Open the panel for this ZIP
        await page.evaluate(f"openPanel('{zip_code}')")

        # Wait for panel location text to populate (confirms data loaded)
        await page.wait_for_function(
            "document.getElementById('panel-loc') && "
            "document.getElementById('panel-loc').textContent.trim().length > 0",
            timeout=15000
        )

        # Extra wait for ApexCharts to finish rendering
        await page.wait_for_timeout(3000)

        await page.screenshot(path=str(out_path), full_page=False)
        return True
    except Exception as e:
        print(f"    ERROR taking screenshot: {e}")
        return False

# ── Upload ────────────────────────────────────────────────────────────────────

def upload_file(local_path: Path) -> bool:
    result = subprocess.run(
        ["scp", "-i", SSH_KEY, "-o", "StrictHostKeyChecking=no",
         str(local_path), f"{SERVER}:{REMOTE_DIR}/{local_path.name}"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"    scp error: {result.stderr.strip()}")
    return result.returncode == 0

# ── Patch buffer_schedule.py ──────────────────────────────────────────────────

def patch_schedule(post: dict, img_url: str) -> bool:
    src = SCHEDULE.read_text(encoding="utf-8")
    anchor = f'"scheduled_at": {pt_call_str(post)},'

    if anchor not in src:
        print(f"    WARN: anchor not found — {anchor}")
        return False

    # Check if already patched (image field exists in the ~300 chars after anchor)
    idx = src.index(anchor)
    snippet = src[idx:idx + 300]
    if '"image":' in snippet:
        print(f"    already patched — skipping")
        return False

    new_anchor = f'"scheduled_at": {pt_call_str(post)},\n        "image": "{img_url}",'
    patched = src.replace(anchor, new_anchor, 1)
    SCHEDULE.write_text(patched, encoding="utf-8")
    return True

# ── Main ──────────────────────────────────────────────────────────────────────

async def main(dry_run: bool, upload: bool, patch: bool):
    sys.path.insert(0, str(SCHEDULE.parent))
    import buffer_schedule as bs

    posts = bs.POSTS
    print(f"Loaded {len(posts)} posts from buffer_schedule.py\n")

    processed = []

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page    = await browser.new_page()

        for post in posts:
            zip_code = extract_zip(post["text"])
            ch       = CHANNEL_SHORT.get(post["channel"], "??")
            date     = post["scheduled_at"][:10]

            if not zip_code:
                print(f"  skip   {date} {ch} — no ZIP (default OG image)")
                continue

            fname  = post_filename(post, zip_code)
            fpath  = OUT_DIR / fname
            img_url = f"{PUBLIC_URL}/{fname}"

            if fpath.exists():
                print(f"  exists {fname}")
                processed.append((post, fpath, img_url))
                continue

            print(f"  shot   {date} {ch} ZIP {zip_code} → {fname}")
            ok = await screenshot_zip(page, zip_code, fpath)
            if ok:
                print(f"    saved {fpath}")
                processed.append((post, fpath, img_url))
            else:
                print(f"    FAILED — skipping")

        await browser.close()

    print(f"\n{len(processed)} screenshots ready.\n")

    if dry_run:
        print("Dry run — skipping upload and patch.")
        for post, fpath, img_url in processed:
            print(f"  would set: {img_url}")
        return

    if upload:
        print("Uploading to server...")
        for post, fpath, img_url in processed:
            ok = upload_file(fpath)
            status = "OK  " if ok else "FAIL"
            print(f"  {status} {fpath.name}")
        print()

    if patch:
        print("Patching buffer_schedule.py...")
        for post, fpath, img_url in processed:
            ch   = CHANNEL_SHORT.get(post["channel"], "??")
            date = post["scheduled_at"][:10]
            ok   = patch_schedule(post, img_url)
            status = "OK  " if ok else "skip"
            print(f"  {status} {date} {ch} → {img_url}")
        print()

    print("Done. Run buffer_schedule.py when ready to post to Buffer.")


if __name__ == "__main__":
    dry_run = "--dry-run"   in sys.argv
    upload  = "--no-upload" not in sys.argv and not dry_run
    patch   = "--no-patch"  not in sys.argv and not dry_run
    asyncio.run(main(dry_run=dry_run, upload=upload, patch=patch))
