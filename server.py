"""
server.py — Beacon API
Serves ZIP-level housing trend data from Zillow Research public CSVs.
"""
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

DATA_DIR    = Path("data")
CACHE_1H    = "public, max-age=3600"
CACHE_24H   = "public, max-age=86400"
ZIP_CONFIGS = ["home_values", "rentals", "sales", "market_temp", "for_sale_listings"]

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
    global zip_df, zip_meta, heatmap_cache, appreciation_table, metro_to_zips

    for c in ZIP_CONFIGS:
        p = DATA_DIR / f"{c}.parquet"
        if p.exists():
            dfs[c] = pd.read_parquet(p)
            print(f"  {c}: {len(dfs[c]):,} rows")
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

    heatmap_cache      = _build_heatmap()
    appreciation_table = _build_appreciation_table()
    print(f"  Heatmap: {len(heatmap_cache):,} ZIPs ready")
    print(f"  Appreciation table: {len(appreciation_table):,} ZIPs ready")


def _build_appreciation_table() -> dict:
    """Compute historical appreciation for every ZIP using global cutoff dates."""
    if "home_values" not in dfs: return {}
    hv       = dfs["home_values"].sort_values(["zip", "date"])
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
    hv       = dfs["home_values"].sort_values(["zip","date"])
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
    if config not in dfs: return {}
    df  = dfs[config]
    sub = df[df["zip"] == zip_code].sort_values("date")
    if sub.empty: return {}
    return {
        "dates":  sub["date"].dt.strftime("%Y-%m").tolist(),
        "values": [_clean(v) for v in sub["value"]],
    }

# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
def index():
    return FileResponse("map.html")

@app.get("/api/heatmap")
def get_heatmap():
    if not heatmap_cache:
        raise HTTPException(503, "No data — run: python ingest.py")
    return JSONResponse(content=heatmap_cache,
                        headers={"Cache-Control": CACHE_1H})

@app.get("/api/stats")
def get_stats():
    if not heatmap_cache:
        raise HTTPException(503, "No data — run: python ingest.py")
    vals = sorted(r["v"] for r in heatmap_cache if r.get("v") is not None)
    yoys = [r["y"] for r in heatmap_cache if r.get("y") is not None]
    return JSONResponse(
        content={
            "total_zips":   len(heatmap_cache),
            "median_value": round(vals[len(vals)//2]) if vals else 0,
            "median_yoy":   round(sum(yoys)/len(yoys), 1) if yoys else 0,
        },
        headers={"Cache-Control": CACHE_1H},
    )

@app.get("/api/metros")
def get_metros():
    return JSONResponse(
        content=sorted(
            [{"metro": m, "zip_count": len(z)} for m, z in metro_to_zips.items()],
            key=lambda x: x["zip_count"], reverse=True,
        ),
        headers={"Cache-Control": CACHE_24H},
    )

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
    result   = {"zip": zip_code, "configs": {}}

    for name in ZIP_CONFIGS:
        s = _zip_series(name, zip_code)
        if s: result["configs"][name] = s

    if not result["configs"]:
        raise HTTPException(404, f"No data for ZIP {zip_code}")

    if zip_meta is not None:
        row = zip_meta[zip_meta["zip"] == zip_code]
        if not row.empty:
            r = row.iloc[0]
            result.update({
                "city":   _clean(r.get("city")),
                "state":  _clean(r.get("state")),
                "metro":  _clean(r.get("metro")),
                "county": _clean(r.get("county")),
            })

    if zip_code in appreciation_table:
        result["appreciation"] = {
            k: v for k, v in appreciation_table[zip_code].items()
            if k.startswith("appreciation_")
        }

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

@app.get("/health")
def health():
    return {
        "status": "ok",
        "heatmap_zips": len(heatmap_cache) if heatmap_cache else 0,
        "appreciation_zips": len(appreciation_table),
        "metros": len(metro_to_zips),
        "configs_loaded": list(dfs.keys()),
    }
