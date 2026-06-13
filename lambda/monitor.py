"""
monitor.py — HomeSight uptime monitor (AWS Lambda)

Runs every 5 minutes via EventBridge. Makes real HTTP requests to the
live site and asserts response shape. Publishes to SNS on any failure.

Environment variables:
  SITE_URL   — base URL to monitor (e.g. https://homesight.live)
  SNS_ARN    — ARN of the SNS topic to alert on failure
"""
import json
import os
import urllib.request
import urllib.error

SITE_URL = os.environ.get("SITE_URL", "https://homesight.live")
SNS_ARN  = os.environ.get("SNS_ARN", "")

# Known ZIP that should always have data
PROBE_ZIP = "98101"

# Zillow dataset has ~26,276 ZIPs; 25,000 catches major data loss
# without false-alerting on minor fluctuations as Zillow adds/removes ZIPs
MIN_HEATMAP_ZIPS = 25_000


def _get(path: str) -> tuple[int, dict]:
    url = f"{SITE_URL}{path}"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, {}
    except Exception as e:
        return 0, {"error": str(e)}


def _publish_alert(failures: list[str]) -> None:
    if not SNS_ARN:
        print("SNS_ARN not set — skipping alert")
        return
    import boto3
    sns = boto3.client("sns")
    message = "HomeSight monitor detected failures:\n\n" + "\n".join(f"  • {f}" for f in failures)
    sns.publish(
        TopicArn=SNS_ARN,
        Subject="🚨 HomeSight is down",
        Message=message,
    )


def lambda_handler(event, context):
    failures = []

    # ── Check 1: /health ─────────────────────────────────────────────────────
    status, body = _get("/health")
    if status != 200:
        failures.append(f"/health returned HTTP {status}")
    else:
        if body.get("status") != "ok":
            failures.append(f"/health status={body.get('status')} failing_checks={body.get('failing_checks')}")
        if body.get("heatmap_zips", 0) < MIN_HEATMAP_ZIPS:
            failures.append(f"/health heatmap_zips={body.get('heatmap_zips')} < {MIN_HEATMAP_ZIPS}")

    # ── Check 2: /api/zip/{PROBE_ZIP} ────────────────────────────────────────
    status, body = _get(f"/api/zip/{PROBE_ZIP}")
    if status != 200:
        failures.append(f"/api/zip/{PROBE_ZIP} returned HTTP {status}")
    else:
        if "home_values" not in body.get("configs", {}):
            failures.append(f"/api/zip/{PROBE_ZIP} missing home_values config")
        if not body.get("city") or not body.get("state"):
            failures.append(f"/api/zip/{PROBE_ZIP} missing city/state metadata")

    # ── Check 3: /api/heatmap ────────────────────────────────────────────────
    status, body = _get("/api/heatmap")
    if status != 200:
        failures.append(f"/api/heatmap returned HTTP {status}")
    elif not isinstance(body, list) or len(body) < MIN_HEATMAP_ZIPS:
        failures.append(f"/api/heatmap returned {len(body) if isinstance(body, list) else 'non-list'} items")

    # ── Result ───────────────────────────────────────────────────────────────
    if failures:
        print("FAILURES:", failures)
        _publish_alert(failures)
        return {"statusCode": 500, "body": json.dumps({"ok": False, "failures": failures})}

    print("All checks passed")
    return {"statusCode": 200, "body": json.dumps({"ok": True})}
