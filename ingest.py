"""
ingest.py — Download Zillow data (ZIP, county, metro levels) + ZIP coordinates + boundaries.
Run once; re-run with --refresh to update.
Cron-safe: checks Last-Modified header on primary source before downloading anything.
"""
import io
import json
import argparse
import zipfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

CACHE_DIR    = Path("data")
REFRESH_FILE = CACHE_DIR / "last_refresh.json"

META_COLS = ["RegionID","SizeRank","RegionName","RegionType","StateName","State",
             "City","Metro","CountyName"]

# ZIP-level sources (wide CSV → long parquet)
ZIP_SOURCES = {
    "home_values":       "https://files.zillowstatic.com/research/public_csvs/zhvi/Zip_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv",
    "rentals":           "https://files.zillowstatic.com/research/public_csvs/zori/Zip_zori_uc_sfrcondomfr_sm_month.csv",
    "sales":             "https://files.zillowstatic.com/research/public_csvs/median_sale_price/Zip_median_sale_price_uc_sfrcondo_sm_month.csv",
    "market_temp":       "https://files.zillowstatic.com/research/public_csvs/market_temp_index/Zip_market_temp_index_uc_sfrcondo_month.csv",
    "for_sale_listings": "https://files.zillowstatic.com/research/public_csvs/new_listings/Zip_new_listings_uc_sfrcondo_month.csv",
}

# County + Metro sources (for ranking context and longer history)
EXTRA_SOURCES = {
    "county": "https://files.zillowstatic.com/research/public_csvs/zhvi/County_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv",
    "metro":  "https://files.zillowstatic.com/research/public_csvs/zhvi/Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv",
}

def get_remote_last_modified(url: str) -> datetime | None:
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=10) as r:
            lm = r.headers.get("Last-Modified")
            if lm:
                return datetime.strptime(lm, "%a, %d %b %Y %H:%M:%S %Z").replace(tzinfo=timezone.utc)
    except Exception as e:
        print(f"  WARNING: could not check remote Last-Modified: {e}")
    return None


def get_local_last_refresh() -> datetime | None:
    if REFRESH_FILE.exists():
        data = json.loads(REFRESH_FILE.read_text())
        ts   = data.get("source_last_modified")
        if ts:
            return datetime.fromisoformat(ts)
    return None


def write_refresh_record(source_last_modified: datetime | None) -> None:
    CACHE_DIR.mkdir(exist_ok=True)
    REFRESH_FILE.write_text(json.dumps({
        "timestamp":            datetime.now(timezone.utc).isoformat(),
        "source_last_modified": source_last_modified.isoformat() if source_last_modified else None,
        "trigger":              "cron",
    }, indent=2))


parser = argparse.ArgumentParser()
parser.add_argument("--refresh", action="store_true")
args = parser.parse_args()

CACHE_DIR.mkdir(exist_ok=True)

# ── Freshness check (cron-safe: exits early if source unchanged) ───────────────
remote_lm = get_remote_last_modified(ZIP_SOURCES["home_values"])
local_lm  = get_local_last_refresh()

if remote_lm:
    print(f"  Remote Last-Modified: {remote_lm.strftime('%Y-%m-%d %H:%M UTC')}")
if local_lm:
    print(f"  Last ingest:          {local_lm.strftime('%Y-%m-%d %H:%M UTC')}")

if not args.refresh and remote_lm and local_lm and remote_lm <= local_lm:
    print("  Source unchanged since last ingest — nothing to do.")
    raise SystemExit(1)  # 1 = no update; 0 = new data processed; 2+ = error

def melt_zillow(df, id_extras=None):
    """Melt a Zillow wide CSV → long format. id_extras = extra columns to keep."""
    base_id = ["RegionName", "City", "State", "StateName"]
    if id_extras:
        base_id += [c for c in id_extras if c in df.columns]
    id_cols  = [c for c in base_id if c in df.columns]
    date_cols = [c for c in df.columns if c not in META_COLS and len(c) == 10 and c[4] == "-"]
    if not date_cols:
        return None
    long = df[id_cols + date_cols].melt(id_vars=id_cols, var_name="date", value_name="value")
    rename = {"RegionName":"region","City":"city","State":"state","StateName":"state_name",
              "Metro":"metro","CountyName":"county"}
    long = long.rename(columns={k: v for k, v in rename.items() if k in long.columns})
    long["date"] = pd.to_datetime(long["date"])
    return long.dropna(subset=["value"]).sort_values(["region","date"])

# ── 1. ZIP coordinates ────────────────────────────────────────────────────────
zips_out = CACHE_DIR / "zips.parquet"
if zips_out.exists() and not args.refresh:
    print(f"  zips.parquet                 already cached")
else:
    print("  Downloading ZIP coordinates from GeoNames...")
    req = urllib.request.urlopen("https://download.geonames.org/export/zip/US.zip", timeout=30)
    zf  = zipfile.ZipFile(io.BytesIO(req.read()))
    with zf.open("US.txt") as f:
        zdf = pd.read_csv(f, sep="\t", header=None, dtype={"zip": str},
            names=["country","zip","city","state","state_code","county",
                   "county_code","community","community_code","lat","lng","accuracy"])
    zdf = (zdf[["zip","city","state_code","lat","lng"]]
           .rename(columns={"state_code":"state"})
           .drop_duplicates(subset="zip", keep="first"))
    zdf.to_parquet(zips_out, index=False)
    print(f"  zips.parquet                 saved ({len(zdf):,} ZIPs)")

# ── 2. ZIP metadata (Metro + County mapping) ──────────────────────────────────
meta_out = CACHE_DIR / "zip_meta.parquet"
if meta_out.exists() and not args.refresh:
    print(f"  zip_meta.parquet             already cached")
else:
    print("  Extracting ZIP → Metro/County metadata from home_values CSV...")
    try:
        url = ZIP_SOURCES["home_values"]
        keep = ["RegionName","City","State","StateName","Metro","CountyName"]
        df   = pd.read_csv(url, dtype={"RegionName": str},
                           usecols=lambda c: c in keep)
        df   = df.rename(columns={"RegionName":"zip","City":"city","State":"state",
                                   "StateName":"state_name","Metro":"metro",
                                   "CountyName":"county"})
        df["zip"] = df["zip"].astype(str).str.zfill(5)
        df.to_parquet(meta_out, index=False)
        metros = df["metro"].dropna().nunique()
        print(f"  zip_meta.parquet             saved ({len(df):,} ZIPs, {metros} metros)")
    except Exception as e:
        print(f"  FAILED zip_meta: {e}")

# ── 3. ZIP-level time series ──────────────────────────────────────────────────
for name, url in ZIP_SOURCES.items():
    out = CACHE_DIR / f"{name}.parquet"
    if out.exists() and not args.refresh:
        size = out.stat().st_size / 1_000_000
        print(f"  {name:<24} already cached ({size:.1f} MB)")
        continue
    print(f"  Downloading {name}...")
    try:
        df   = pd.read_csv(url, dtype={"RegionName": str})
        long = melt_zillow(df)
        if long is None:
            print(f"  WARNING: no date columns in {name}"); continue
        long = long.rename(columns={"region":"zip"})
        long["zip"] = long["zip"].astype(str).str.zfill(5)
        long.to_parquet(out, index=False)
        print(f"  {name:<24} saved ({len(long):,} rows, {out.stat().st_size/1e6:.1f} MB)")
    except Exception as e:
        print(f"  FAILED {name}: {e}")

# ── 4. County + Metro level (for ranking context) ────────────────────────────
for name, url in EXTRA_SOURCES.items():
    out = CACHE_DIR / f"{name}.parquet"
    if out.exists() and not args.refresh:
        size = out.stat().st_size / 1_000_000
        print(f"  {name:<24} already cached ({size:.1f} MB)")
        continue
    print(f"  Downloading {name}...")
    try:
        df        = pd.read_csv(url, dtype={"RegionName": str})
        date_cols = [c for c in df.columns if len(c) == 10 and c[4] == "-"]
        id_cols   = [c for c in ["RegionName","State","StateName","Metro"] if c in df.columns]
        if not date_cols:
            print(f"  WARNING: no date columns in {name}"); continue
        long = (df[id_cols + date_cols]
                .melt(id_vars=id_cols, var_name="date", value_name="value")
                .rename(columns={"RegionName":"region","State":"state",
                                 "StateName":"state_name","Metro":"metro"}))
        long["date"] = pd.to_datetime(long["date"])
        long = long.dropna(subset=["value"]).sort_values(["region","date"])
        long.to_parquet(out, index=False)
        print(f"  {name:<24} saved ({len(long):,} rows, {out.stat().st_size/1e6:.1f} MB)")
    except Exception as e:
        print(f"  FAILED {name}: {e}")

# ── 5. ZIP boundaries ─────────────────────────────────────────────────────────
bounds_out = CACHE_DIR / "boundaries.geojson.gz"
if bounds_out.exists() and not args.refresh:
    print(f"  boundaries.geojson.gz        already cached ({bounds_out.stat().st_size/1e6:.1f} MB)")
else:
    try:
        import gzip, geopandas as gpd, tempfile, os
        print("  Downloading ZIP boundaries from Census Bureau (~67 MB)...")
        url = "https://www2.census.gov/geo/tiger/GENZ2020/shp/cb_2020_us_zcta520_500k.zip"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = urllib.request.urlopen(req, timeout=120).read()
        with tempfile.TemporaryDirectory() as tmp:
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                zf.extractall(tmp)
            shp = next(os.path.join(tmp, f) for f in os.listdir(tmp) if f.endswith(".shp"))
            gdf = gpd.read_file(shp)
        zcta_col = next((c for c in gdf.columns if "ZCTA5" in c), None)
        if not zcta_col:
            raise ValueError(f"No ZCTA column: {list(gdf.columns)}")
        gdf = gdf[[zcta_col, "geometry"]].rename(columns={zcta_col: "zip"})
        gdf = gdf.to_crs("EPSG:4326")
        gdf["geometry"] = gdf["geometry"].simplify(0.0005, preserve_topology=True)
        hv_path = CACHE_DIR / "home_values.parquet"
        if hv_path.exists():
            zips = set(pd.read_parquet(hv_path)["zip"].unique())
            gdf  = gdf[gdf["zip"].isin(zips)]
        geojson_str = gdf.to_json()
        with gzip.open(bounds_out, "wt", encoding="utf-8") as f:
            f.write(geojson_str)
        print(f"  boundaries.geojson.gz        saved ({len(gdf):,} ZIPs, "
              f"{len(geojson_str)/1e6:.0f} MB raw → {bounds_out.stat().st_size/1e6:.1f} MB gz)")
    except ImportError:
        print("  SKIP boundaries: pip install geopandas")
    except Exception as e:
        print(f"  FAILED boundaries: {e}")

write_refresh_record(remote_lm)
print(f"  last_refresh.json            saved")
print("\nDone. Run: uvicorn server:app --reload")
