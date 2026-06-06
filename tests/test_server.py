"""
tests/test_server.py — API endpoint tests for Beacon.
Run with: pytest tests/ -v
"""
import pytest
from fastapi.testclient import TestClient

# Import the app (loads data on import — skip tests gracefully if data missing)
try:
    from server import app, heatmap_cache, appreciation_table, metro_to_zips
    DATA_LOADED = bool(heatmap_cache)
except Exception:
    DATA_LOADED = False

client = TestClient(app)
skip_no_data = pytest.mark.skipif(not DATA_LOADED, reason="Cache data not loaded — run ingest.py first")


# ── Health / root ─────────────────────────────────────────────────────────────

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert "status" in body
    assert body["status"] == "ok"

def test_root_serves_html():
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]


# ── Heatmap ───────────────────────────────────────────────────────────────────

@skip_no_data
def test_heatmap_returns_list():
    r = client.get("/api/heatmap")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) > 1000

@skip_no_data
def test_heatmap_entry_shape():
    r    = client.get("/api/heatmap")
    item = r.json()[0]
    assert "z" in item   # ZIP code
    assert "v" in item   # home value
    assert "lat" in item
    assert "lng" in item

@skip_no_data
def test_heatmap_has_cache_header():
    r = client.get("/api/heatmap")
    assert "cache-control" in r.headers


# ── Stats ─────────────────────────────────────────────────────────────────────

@skip_no_data
def test_stats_shape():
    r    = client.get("/api/stats")
    assert r.status_code == 200
    body = r.json()
    assert "total_zips"   in body
    assert "median_value" in body
    assert "median_yoy"   in body

@skip_no_data
def test_stats_values_reasonable():
    body = client.get("/api/stats").json()
    assert body["total_zips"]   > 10000
    assert body["median_value"] > 50000    # US median > $50K
    assert body["median_value"] < 5000000  # US median < $5M


# ── ZIP detail ────────────────────────────────────────────────────────────────

@skip_no_data
def test_zip_known():
    r = client.get("/api/zip/98101")  # Seattle downtown
    assert r.status_code == 200
    body = r.json()
    assert body["zip"] == "98101"
    assert "configs" in body
    assert "home_values" in body["configs"]

@skip_no_data
def test_zip_returns_appreciation():
    r    = client.get("/api/zip/98101")
    body = r.json()
    assert "appreciation" in body
    appr = body["appreciation"]
    assert "appreciation_1y"  in appr
    assert "appreciation_5y"  in appr
    assert "appreciation_10y" in appr

@skip_no_data
def test_zip_series_structure():
    body = client.get("/api/zip/98101").json()
    hv   = body["configs"]["home_values"]
    assert "dates"  in hv
    assert "values" in hv
    assert len(hv["dates"]) == len(hv["values"])
    assert len(hv["dates"]) > 12  # at least a year of monthly data

def test_zip_invalid_alpha():
    r = client.get("/api/zip/ABCDE")
    assert r.status_code == 400

def test_zip_invalid_short():
    r = client.get("/api/zip/123")
    # short ZIP gets zero-padded to "00123" — may return 404
    assert r.status_code in (200, 404)

def test_zip_not_found():
    r = client.get("/api/zip/00001")
    assert r.status_code == 404


# ── Metros ────────────────────────────────────────────────────────────────────

@skip_no_data
def test_metros_returns_list():
    r    = client.get("/api/metros")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) > 100

@skip_no_data
def test_metros_sorted_by_zip_count():
    data = client.get("/api/metros").json()
    counts = [m["zip_count"] for m in data[:10]]
    assert counts == sorted(counts, reverse=True)

@skip_no_data
def test_metros_contains_major_cities():
    data   = client.get("/api/metros").json()
    names  = {m["metro"] for m in data}
    majors = ["New York", "Los Angeles", "Chicago", "Seattle"]
    for city in majors:
        assert any(city in n for n in names), f"{city} not found in metros"


# ── Rankings ─────────────────────────────────────────────────────────────────

@skip_no_data
def test_rank_known_metro():
    # Find a real metro name
    metros = client.get("/api/metros").json()
    metro  = metros[0]["metro"]  # largest by ZIP count
    r = client.get(f"/api/rank?metro={metro}&metric=appreciation_5y&limit=10")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) <= 10

@skip_no_data
def test_rank_sorted_descending():
    metros = client.get("/api/metros").json()
    metro  = metros[0]["metro"]
    data   = client.get(f"/api/rank?metro={metro}&metric=appreciation_5y").json()
    vals   = [r.get("appreciation_5y") for r in data if r.get("appreciation_5y") is not None]
    assert vals == sorted(vals, reverse=True)

@skip_no_data
def test_rank_all_periods():
    metros = client.get("/api/metros").json()
    metro  = metros[0]["metro"]
    for period in ["appreciation_1y","appreciation_3y","appreciation_5y",
                   "appreciation_10y","appreciation_20y","current_value"]:
        r = client.get(f"/api/rank?metro={metro}&metric={period}&limit=5")
        assert r.status_code == 200

def test_rank_invalid_metric():
    r = client.get("/api/rank?metro=Test&metric=invalid_metric")
    assert r.status_code == 400

def test_rank_unknown_metro():
    r = client.get("/api/rank?metro=ZZZ+Nonexistent+City%2C+XX")
    assert r.status_code == 404


# ── Boundaries ────────────────────────────────────────────────────────────────

def test_boundaries_returns_geojson():
    r = client.get("/api/boundaries")
    # 200 if file exists, 503 if not yet ingested
    assert r.status_code in (200, 503)
    if r.status_code == 200:
        assert r.headers.get("content-encoding") == "gzip"
