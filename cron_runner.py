"""
cron_runner.py — Orchestrates US + UK data refresh. Run every 6 hours via systemd timer.

For each region:
  - Runs the ingest script (which checks Last-Modified before downloading)
  - Logs every run to cron_log table regardless of outcome
  - Restarts homesight.service only if at least one region downloaded new data

Exit codes from ingest scripts:
  0 = new data downloaded and processed
  1 = source unchanged, nothing to do
  2+ = error

Usage (manual):
  python cron_runner.py

Usage (systemd timer): see homesight-cron.service / homesight-cron.timer
"""

import json
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

DB_PATH    = Path("data/homesight.db")
INGEST_US  = Path("ingest.py")
INGEST_UK  = Path("ingest_uk.py")
SERVICE    = "homesight.service"

JOBS = [
    {"region": "us", "script": INGEST_US,  "refresh_file": Path("data/last_refresh.json")},
    {"region": "uk", "script": INGEST_UK,  "refresh_file": Path("data/uk_last_refresh.json")},
]


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cron_log (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            run_at               TEXT    NOT NULL,
            region               TEXT    NOT NULL,
            status               TEXT    NOT NULL,
            source_last_modified TEXT,
            duration_seconds     REAL,
            message              TEXT
        )
    """)
    conn.commit()


def log_run(conn: sqlite3.Connection, region: str, status: str,
            source_last_modified: str | None, duration: float, message: str) -> None:
    conn.execute(
        """INSERT INTO cron_log
           (run_at, region, status, source_last_modified, duration_seconds, message)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (datetime.now(timezone.utc).isoformat(), region, status,
         source_last_modified, round(duration, 2), message[:2000])
    )
    conn.commit()


def read_source_last_modified(refresh_file: Path) -> str | None:
    try:
        if refresh_file.exists():
            return json.loads(refresh_file.read_text()).get("source_last_modified")
    except Exception:
        pass
    return None


def run_ingest(job: dict, conn: sqlite3.Connection) -> int:
    region = job["region"]
    script = job["script"]
    start  = time.time()
    print(f"\n[{region.upper()}] Running {script} ...")

    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            timeout=7200,  # 2hr max for large downloads
        )
        duration = time.time() - start
        output   = (result.stdout + "\n" + result.stderr).strip()

        if result.returncode == 0:
            status = "updated"
        elif result.returncode == 1:
            status = "no_change"
        else:
            status = "error"

    except subprocess.TimeoutExpired:
        duration = time.time() - start
        status   = "error"
        output   = "Timed out after 7200s"
        result   = type("R", (), {"returncode": 2})()

    except Exception as e:
        duration = time.time() - start
        status   = "error"
        output   = str(e)
        result   = type("R", (), {"returncode": 2})()

    source_lm = read_source_last_modified(job["refresh_file"])
    log_run(conn, region, status, source_lm, duration, output)

    print(f"[{region.upper()}] status={status}  duration={duration:.1f}s")
    return result.returncode


def restart_service() -> None:
    print("\nNew data detected — restarting homesight.service ...")
    result = subprocess.run(
        ["sudo", "systemctl", "restart", SERVICE],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"  WARNING: restart failed: {result.stderr.strip()}")
    else:
        print("  Service restarted.")


def main() -> None:
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    updated = False
    for job in JOBS:
        code = run_ingest(job, conn)
        if code == 0:
            updated = True

    conn.close()

    if updated:
        restart_service()
    else:
        print("\nNo new data — service not restarted.")


if __name__ == "__main__":
    main()
