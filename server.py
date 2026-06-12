"""
server.py — Beacon API
Serves ZIP-level housing trend data from Zillow Research public CSVs.
"""
from pathlib import Path
from typing import Optional

import httpx
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

BASE_DIR    = Path(__file__).parent
DATA_DIR    = BASE_DIR / "data"
STATIC_DIR  = BASE_DIR / "static"
TILE_DIR    = DATA_DIR / "tiles"
CACHE_1H    = "public, max-age=3600"
CACHE_24H   = "public, max-age=86400"
ZIP_CONFIGS = ["home_values", "rentals", "sales", "market_temp", "for_sale_listings"]

TILE_SOURCES = {
    "base":   "https://a.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}.png",
    "labels": "https://a.basemaps.cartocdn.com/light_only_labels/{z}/{x}/{y}.png",
}

app = FastAPI(title="Beacon API", version="1.0.0")
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])

# ── In-memory state ───────────────────────────────────────────────────────────
dfs:                dict[str, pd.DataFrame] = {}
zip_df:             Optional[pd.DataFrame]  = None
zip_meta:           Optional[pd.DataFrame]  = None
heatmap_cache:      Optional[list]          = None
appreciation_table: dict                    = {}
metro_to_zips:      dict[str, set]          = {}
zip_index:          dict[str, dict]         = {}  # config -> {zip: (start, end)}
zip_response_cache: dict                    = {}  # zip -> full API response dict
zip_meta_dict:      dict[str, dict]         = {}  # zip -> {city, state, metro, county} — O(1) vs O(n) DataFrame scan
stats_cache:        Optional[dict]          = None  # pre-computed at startup; /api/stats never recomputes
metros_cache:       Optional[list]          = None  # pre-sorted at startup; /api/metros never re-sorts
_cached_tile_count: int                     = 0     # incremented on write; avoids rglob on every /health
_tile_client:       Optional[httpx.AsyncClient] = None  # lazily created inside event loop on first tile fetch

# ── Serialisation helper ──────────────────────────────────────────────────────
def _clean(v):
    """Convert pandas/numpy scalars to JSON-safe Python types."""
    if v is None or v is pd.NA: return None
    if isinstance(v, float) and np.isnan(v): return None
    if isinstance(v, (np.integer,)):  return int(v)
    if isinstance(v, (np.floating,)): return None if np.isnan(v) else float(v)
    if isinstance(v, pd.Timestamp):   return v.isoformat()
    return v

def _clean_row(row: dict) -> dict:
    return {k: _clean(v) for k, v in row.items()}

# ── Startup ───────────────────────────────────────────────────────────────────
def load_all():
    global zip_df, zip_meta, heatmap_cache, appreciation_table, metro_to_zips, \
           zip_meta_dict, stats_cache, metros_cache, _cached_tile_count

    for c in ZIP_CONFIGS:
        p = DATA_DIR / f"{c}.parquet"
        if p.exists():
            df = pd.read_parquet(p).sort_values(["zip", "date"]).reset_index(drop=True)
            dfs[c] = df
            # Build binary-search index: zip -> (row_start, row_end)
            zips_arr = df["zip"].values
            idx = {}
            for z in df["zip"].unique():
                idx[z] = (
                    int(np.searchsorted(zips_arr, z, side="left")),
                    int(np.searchsorted(zips_arr, z, side="right")),
                )
            zip_index[c] = idx
            print(f"  {c}: {len(df):,} rows")
        else:
            print(f"  MISSING {c} — run python ingest.py")

    for name in ["county", "metro"]:
        p = DATA_DIR / f"{name}.parquet"
        if p.exists():
            dfs[name] = pd.read_parquet(p)

    zp = DATA_DIR / "zips.parquet"
    if zp.exists():
        zip_df = pd.read_parquet(zp)
        zip_df["zip"] = zip_df["zip"].astype(str).str.zfill(5)

    mp = DATA_DIR / "zip_meta.parquet"
    if mp.exists():
        zip_meta = pd.read_parquet(mp)
        zip_meta["zip"] = zip_meta["zip"].astype(str).str.zfill(5)
        # Vectorised metro index
        valid = zip_meta.dropna(subset=["metro"])
        for metro, grp in valid.groupby("metro"):
            metro_to_zips[str(metro)] = set(grp["zip"].tolist())
        print(f"  zip_meta: {len(zip_meta):,} ZIPs, {len(metro_to_zips):,} metros")
        zip_meta_dict = zip_meta.set_index("zip")[["city","state","metro","county"]].to_dict("index")  # O(1) lookup replaces per-request O(n) boolean filter

    heatmap_cache      = _build_heatmap()
    appreciation_table = _build_appreciation_table()
    print(f"  Heatmap: {len(heatmap_cache):,} ZIPs ready")
    print(f"  Appreciation table: {len(appreciation_table):,} ZIPs ready")

    # stats and metros never change after load — compute once, return reference thereafter
    vals = sorted(r["v"] for r in heatmap_cache if r.get("v") is not None)
    yoys = [r["y"] for r in heatmap_cache if r.get("y") is not None]
    stats_cache = {
        "total_zips":   len(heatmap_cache),
        "median_value": round(vals[len(vals)//2]) if vals else 0,
        "median_yoy":   round(sum(yoys)/len(yoys), 1) if yoys else 0,
    }
    metros_cache = sorted(
        [{"metro": m, "zip_count": len(z)} for m, z in metro_to_zips.items()],
        key=lambda x: x["zip_count"], reverse=True,
    )
    _cached_tile_count = sum(1 for _ in TILE_DIR.rglob("*.png")) if TILE_DIR.exists() else 0


def _build_appreciation_table() -> dict:
    """Compute historical appreciation for every ZIP using global cutoff dates."""
    if "home_values" not in dfs: return {}
    hv       = dfs["home_values"]  # already sorted by [zip, date] in load_all — no re-sort needed
    max_date = hv["date"].max()

    latest = (hv.groupby("zip")["value"].last()
                .rename("current_value").reset_index())

    result = latest.copy()
    for label, months in [("1y",12),("3y",36),("5y",60),("10y",120),("20y",240)]:
        cutoff = max_date - pd.DateOffset(months=months)
        old    = (hv[hv["date"] <= cutoff]
                  .groupby("zip")["value"].last()
                  .rename("old").reset_index())
        result = result.merge(old, on="zip", how="left")
        pct    = ((result["current_value"] - result["old"]) / result["old"] * 100)
        result[f"appreciation_{label}"] = pct.where(result["old"] > 0).round(1)
        result.drop(columns=["old"], inplace=True)

    result["current_value"] = result["current_value"].round().astype("Int64")

    if zip_meta is not None:
        result = result.merge(
            zip_meta[["zip","city","state","metro","county"]],
            on="zip", how="left"
        )

    return {row["zip"]: _clean_row(row)
            for row in result.to_dict(orient="records")}


def _build_heatmap() -> list:
    """Build ZIP-level map data: latest value, YoY change, coordinates."""
    if "home_values" not in dfs or zip_df is None: return []
    hv       = dfs["home_values"]  # already sorted by [zip, date] in load_all — no re-sort needed
    max_date = hv["date"].max()

    latest = (hv.groupby("zip")["value"].last()
                .rename("v").reset_index()
                .rename(columns={"zip":"z"}))
    latest["v"] = latest["v"].round()

    cutoff_1y = max_date - pd.DateOffset(months=12)
    old_1y    = (hv[hv["date"] <= cutoff_1y]
                 .groupby("zip")["value"].last()
                 .rename("old").reset_index())
    latest = (latest.merge(old_1y, left_on="z", right_on="zip", how="left")
                    .drop(columns=["zip"]))
    latest["y"] = ((latest["v"] - latest["old"]) / latest["old"] * 100
                   ).where(latest["old"] > 0).round(1)
    latest.drop(columns=["old"], inplace=True)

    df_out = (latest
              .merge(zip_df[["zip","city","state","lat","lng"]],
                     left_on="z", right_on="zip", how="left")
              .drop(columns=["zip"])
              .dropna(subset=["lat","lng"]))
    df_out["lat"] = df_out["lat"].round(4)
    df_out["lng"] = df_out["lng"].round(4)

    if zip_meta is not None:
        meta_map       = zip_meta.set_index("zip")["metro"].to_dict()
        df_out["metro"] = df_out["z"].map(meta_map)

    return [_clean_row(row) for row in df_out.to_dict(orient="records")]


load_all()

# ── Helpers ───────────────────────────────────────────────────────────────────
def _validate_zip(zip_code: str) -> str:
    z = zip_code.strip().zfill(5)
    if len(z) != 5 or not z.isdigit():
        raise HTTPException(400, f"Invalid ZIP code: {zip_code!r}")
    return z

def _zip_series(config: str, zip_code: str) -> dict:
    if config not in zip_index: return {}
    bounds = zip_index[config].get(zip_code)
    if bounds is None: return {}
    sub = dfs[config].iloc[bounds[0]:bounds[1]]
    if sub.empty: return {}
    return {
        "dates":  sub["date"].dt.strftime("%Y-%m").tolist(),
        "values": [_clean(v) for v in sub["value"]],
    }

# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
def index():
    return FileResponse(str(BASE_DIR / "map.html"))

@app.get("/data")
def data_page():
    return FileResponse(str(BASE_DIR / "data.html"))

@app.get("/api/heatmap")
def get_heatmap():
    if not heatmap_cache:
        raise HTTPException(503, "No data — run: python ingest.py")
    return JSONResponse(content=heatmap_cache,
                        headers={"Cache-Control": CACHE_1H})

@app.get("/api/stats")
def get_stats():
    if not stats_cache:
        raise HTTPException(503, "No data — run: python ingest.py")
    return JSONResponse(content=stats_cache, headers={"Cache-Control": CACHE_1H})

@app.get("/api/metros")
def get_metros():
    return JSONResponse(content=metros_cache or [], headers={"Cache-Control": CACHE_24H})

@app.get("/api/rank")
def get_rank(
    metro:  str = Query(...),
    metric: str = Query("appreciation_5y"),
    limit:  int = Query(50, ge=1, le=999),
):
    valid_metrics = {"appreciation_1y","appreciation_3y","appreciation_5y",
                     "appreciation_10y","appreciation_20y","current_value"}
    if metric not in valid_metrics:
        raise HTTPException(400, f"metric must be one of {sorted(valid_metrics)}")

    zips = metro_to_zips.get(metro)
    if not zips:
        raise HTTPException(404, f"Metro not found: {metro!r}")

    results = [appreciation_table[z] for z in zips if z in appreciation_table]
    # Fix: use `is None` not truthiness so 0.0 sorts correctly
    results.sort(key=lambda r: (r.get(metric) is None, -(r.get(metric) or 0)))
    return JSONResponse(content=results[:limit],
                        headers={"Cache-Control": CACHE_1H})

@app.get("/api/zip/{zip_code}")
def get_zip(zip_code: str):
    zip_code = _validate_zip(zip_code)
    if zip_code in zip_response_cache:
        return JSONResponse(content=zip_response_cache[zip_code],
                            headers={"Cache-Control": CACHE_1H})
    result   = {"zip": zip_code, "configs": {}}

    for name in ZIP_CONFIGS:
        s = _zip_series(name, zip_code)
        if s: result["configs"][name] = s

    if not result["configs"]:
        raise HTTPException(404, f"No data for ZIP {zip_code}")

    meta = zip_meta_dict.get(zip_code)
    if meta:
        result.update({
            "city":   _clean(meta.get("city")),
            "state":  _clean(meta.get("state")),
            "metro":  _clean(meta.get("metro")),
            "county": _clean(meta.get("county")),
        })

    if zip_code in appreciation_table:
        result["appreciation"] = {
            k: v for k, v in appreciation_table[zip_code].items()
            if k.startswith("appreciation_")
        }

    zip_response_cache[zip_code] = result
    return JSONResponse(content=result, headers={"Cache-Control": CACHE_1H})

@app.get("/api/boundaries")
def get_boundaries():
    p = DATA_DIR / "boundaries.geojson.gz"
    if not p.exists():
        raise HTTPException(503, "Boundaries missing — run: python ingest.py")
    return FileResponse(
        p, media_type="application/json",
        headers={"Content-Encoding": "gzip", "Cache-Control": CACHE_24H},
    )

@app.get("/tiles/{layer}/{z}/{x}/{y}.png")
async def proxy_tile(layer: str, z: int, x: int, y: int):
    if layer not in TILE_SOURCES:
        raise HTTPException(400, f"Invalid tile layer: {layer!r}")

    cache_path = TILE_DIR / layer / str(z) / str(x) / f"{y}.png"
    if cache_path.exists():
        return FileResponse(str(cache_path), media_type="image/png",
                            headers={"Cache-Control": CACHE_24H})

    global _tile_client, _cached_tile_count
    # Lazily create the persistent client on first tile request (must be inside the event loop)
    if _tile_client is None:
        _tile_client = httpx.AsyncClient(timeout=10.0, headers={"User-Agent": "Beacon/1.0"})

    url = TILE_SOURCES[layer].format(z=z, x=x, y=y)
    try:
        resp = await _tile_client.get(url)
        resp.raise_for_status()
    except Exception:
        raise HTTPException(502, "Tile fetch failed")

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(resp.content)
    _cached_tile_count += 1

    return Response(content=resp.content, media_type="image/png",
                    headers={"Cache-Control": CACHE_24H})


@app.get("/health")
def health():
    return {
        "status": "ok",
        "heatmap_zips": len(heatmap_cache) if heatmap_cache else 0,
        "appreciation_zips": len(appreciation_table),
        "metros": len(metro_to_zips),
        "configs_loaded": list(dfs.keys()),
        "cached_tiles": _cached_tile_count,
    }

# Static files mounted last so API routes take priority
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
