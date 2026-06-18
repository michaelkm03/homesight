"""
ingest_uk.py — Download and process HM Land Registry Price Paid Data (England & Wales).
Aggregates raw transactions -> postcode-sector level monthly median prices -> appreciation metrics.

Full run (download once, process all ~30M rows):
  python ingest_uk.py

Dev mode (use cached raw file, process first 500K rows only):
  python ingest_uk.py --sample

Build boundary file (run after full ingest):
  python ingest_uk.py --boundaries

Refresh (re-download raw file):
  python ingest_uk.py --refresh
"""

import argparse
import io
import json
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

CACHE_DIR    = Path("data")
REFRESH_FILE = CACHE_DIR / "uk_last_refresh.json"

# HM Land Registry — complete Price Paid dataset (England & Wales, 1995–present)
PPD_URL = "http://prod.publicdata.landregistry.gov.uk.s3-website-eu-west-1.amazonaws.com/pp-complete.csv"


def get_remote_last_modified() -> datetime | None:
    try:
        req = urllib.request.Request(PPD_URL, method="HEAD")
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

# Column names — file has no header row (per Land Registry spec)
PPD_COLS = [
    "transaction_id", "price", "date", "postcode",
    "property_type",  # D=Detached S=Semi T=Terraced F=Flat O=Other
    "old_new",        # Y=new build N=established
    "duration",       # F=Freehold L=Leasehold
    "paon", "saon", "street", "locality", "town", "district", "county",
    "ppd_category",   # A=standard market sale B=repossession/buy-to-let
    "record_status",  # A=add C=change D=delete (monthly files only; blank in full file)
]

SAMPLE_ROWS = 500_000

parser = argparse.ArgumentParser()
parser.add_argument("--sample",     action="store_true", help="Process first 500K rows only (dev mode)")
parser.add_argument("--refresh",    action="store_true", help="Re-download raw PPD file")
parser.add_argument("--boundaries", action="store_true", help="Download + build UK boundary GeoJSON only")
args = parser.parse_args()

CACHE_DIR.mkdir(exist_ok=True)

# ── Boundaries (run independently with --boundaries) ──────────────────────────
BOUNDARIES_URL = "https://datashare.ed.ac.uk/bitstreams/7f8ddb3e-f886-422e-a359-a74c9c725193/download"
BOUNDARIES_OUT = CACHE_DIR / "uk_boundaries.geojson.gz"

if args.boundaries:
    try:
        import gzip
        import geopandas as gpd
        import tempfile, os

        raw_zip = CACHE_DIR / "uk_postcodes_raw.zip"
        if not raw_zip.exists() or args.refresh:
            print("  Downloading GB postcode boundaries (GeoLytix / Edinburgh DataShare, ~180 MB) ...")
            urllib.request.urlretrieve(BOUNDARIES_URL, raw_zip)
            print(f"  uk_postcodes_raw.zip         saved ({raw_zip.stat().st_size/1e6:.0f} MB)")
        else:
            print(f"  uk_postcodes_raw.zip         already cached")

        print("  Extracting postcode sector shapefile ...")
        with tempfile.TemporaryDirectory() as tmp:
            with zipfile.ZipFile(raw_zip) as zf:
                sector_files = [f for f in zf.namelist()
                                if "ector" in f and f.endswith(".shp")]
                if not sector_files:
                    raise FileNotFoundError(
                        f"No sector .shp found. Files: {[f for f in zf.namelist() if f.endswith('.shp')]}"
                    )
                stem = sector_files[0].rsplit(".", 1)[0]
                for name in zf.namelist():
                    if name.startswith(stem):
                        zf.extract(name, tmp)
                shp_path = os.path.join(tmp, sector_files[0])
                gdf = gpd.read_file(shp_path)

            print(f"  Loaded {len(gdf):,} sectors. Columns: {list(gdf.columns)}")

            code_col = next(
                (c for c in gdf.columns if c.lower() in ("strsect", "name", "sector", "pc_sector")),
                None
            )
            if not code_col:
                raise ValueError(f"Cannot find sector code column. Columns: {list(gdf.columns)}")

            gdf = gdf.rename(columns={code_col: "sector"})
            gdf["sector"] = gdf["sector"].str.strip().str.upper()

            # GeoLytix format: "AB101" — no space between outward and inward first digit.
            # Our format:      "AB10 1" — space before last char.
            # Fix: insert space before last character.
            gdf["sector"] = gdf["sector"].apply(
                lambda s: s[:-1] + " " + s[-1] if isinstance(s, str) and len(s) >= 3 else s
            )

            print(f"  Boundary sample (normalised): {gdf['sector'].head(5).tolist()}")

            heatmap_path = CACHE_DIR / "uk_heatmap.parquet"
            if heatmap_path.exists():
                known     = set(pd.read_parquet(heatmap_path)["sector"].unique())
                hm_sample = sorted(known)[:5]
                print(f"  Heatmap sample:              {hm_sample}")

                before = len(gdf)
                gdf    = gdf[gdf["sector"].isin(known)]
                print(f"  Filtered {before:,} -> {len(gdf):,} sectors (matched to heatmap)")

            gdf = gdf[["sector", "geometry"]].to_crs("EPSG:4326")
            gdf["geometry"] = gdf["geometry"].simplify(0.0002, preserve_topology=True)

            geojson_str = gdf.to_json()
            with gzip.open(BOUNDARIES_OUT, "wt", encoding="utf-8") as f:
                f.write(geojson_str)
            print(f"  uk_boundaries.geojson.gz     saved ({len(gdf):,} sectors, "
                  f"{len(geojson_str)/1e6:.0f} MB raw -> {BOUNDARIES_OUT.stat().st_size/1e6:.1f} MB gz)")

    except ImportError:
        print("  SKIP boundaries: pip install geopandas")
    except Exception as e:
        print(f"  FAILED boundaries: {e}")
        raise

    raise SystemExit(0)

# ── 1. Download raw PPD CSV ────────────────────────────────────────────────────
raw_out = CACHE_DIR / "uk_ppd_raw.csv"

remote_lm  = get_remote_last_modified()
local_lm   = get_local_last_refresh()

if remote_lm:
    print(f"  Remote Last-Modified: {remote_lm.strftime('%Y-%m-%d %H:%M UTC')}")
if local_lm:
    print(f"  Last ingest:          {local_lm.strftime('%Y-%m-%d %H:%M UTC')}")

needs_download = (
    args.refresh
    or not raw_out.exists()
    or (remote_lm and local_lm and remote_lm > local_lm)
    or (raw_out.exists() and not local_lm)  # cached but never recorded
)

if not needs_download and not args.sample:
    print("  Source unchanged since last ingest — nothing to do.")
    raise SystemExit(1)  # 1 = no update; 0 = new data processed; 2+ = error
elif not needs_download and args.sample:
    print("  Source unchanged — using cached raw file for sample run.")
elif needs_download and not args.sample:
    print("  Downloading Land Registry PPD (full dataset ~4 GB) ...")
    urllib.request.urlretrieve(PPD_URL, raw_out)
    print(f"  uk_ppd_raw.csv               saved ({raw_out.stat().st_size/1e9:.2f} GB)")

# ── 2. Load + parse ────────────────────────────────────────────────────────────
print(f"  Loading {'first {:,} rows'.format(SAMPLE_ROWS) if args.sample else 'full dataset'} ...")
read_kwargs = dict(
    filepath_or_buffer=raw_out,
    header=None,
    names=PPD_COLS,
    dtype={"price": float, "postcode": str},
    parse_dates=["date"],
    usecols=["price", "date", "postcode", "property_type", "ppd_category"],
    encoding="latin-1",
)
if args.sample:
    read_kwargs["nrows"] = SAMPLE_ROWS

df = pd.read_csv(**read_kwargs)
print(f"  Loaded {len(df):,} rows")

# ── 3. Filter ──────────────────────────────────────────────────────────────────
# Keep only standard residential market sales (category A) with valid postcodes
df = df[
    (df["ppd_category"] == "A") &
    df["postcode"].notna() &
    (df["price"] >= 1_000) &
    (df["price"] <= 99_999_999)
].copy()
print(f"  After filter (cat A, valid postcode, sane price): {len(df):,} rows")

# ── 4. Derive postcode sector ──────────────────────────────────────────────────
# "SW1A 1AA" -> "SW1A 1"  (outward code + space + first char of inward code)
df["postcode"] = df["postcode"].str.strip().str.upper()
parts = df["postcode"].str.rsplit(" ", n=1, expand=True)
df["sector"] = parts[0] + " " + parts[1].str[0]
df = df[df["sector"].notna() & (df["sector"].str.len() >= 4)]

# Truncate date to month
df["month"] = df["date"].dt.to_period("M").dt.to_timestamp()

print(f"  Unique postcode sectors: {df['sector'].nunique():,}")
print(f"  Date range: {df['date'].min().date()} -> {df['date'].max().date()}")

# ── 5. Aggregate: monthly median price per postcode sector ─────────────────────
print("  Aggregating to monthly median per sector ...")
monthly = (
    df.groupby(["sector", "month"])["price"]
    .median()
    .reset_index()
    .rename(columns={"price": "value"})
    .sort_values(["sector", "month"])
)
print(f"  Monthly series: {len(monthly):,} rows, {monthly['sector'].nunique():,} sectors")

# ── 6. Compute appreciation metrics ───────────────────────────────────────────
print("  Computing appreciation metrics ...")
latest_month = monthly["month"].max()

# Latest median value per sector
latest = (
    monthly.groupby("sector")["value"]
    .last()
    .rename("v")
    .reset_index()
)

# Appreciation over N months: ((latest - old) / old) * 100
for label, months in [("y", 12), ("y3", 36), ("y5", 60), ("y10", 120), ("y20", 240)]:
    cutoff = latest_month - pd.DateOffset(months=months)
    old = (
        monthly[monthly["month"] <= cutoff]
        .groupby("sector")["value"]
        .last()
        .rename("old")
        .reset_index()
    )
    latest = latest.merge(old, on="sector", how="left")
    latest[label] = (
        ((latest["v"] - latest["old"]) / latest["old"] * 100)
        .where(latest["old"] > 0)
        .round(1)
    )
    latest = latest.drop(columns=["old"])

latest["v"] = latest["v"].round().astype("Int64")

# ── 7. Save outputs ────────────────────────────────────────────────────────────
suffix = "_sample" if args.sample else ""

series_out = CACHE_DIR / f"uk_monthly{suffix}.parquet"
monthly.to_parquet(series_out, index=False)
print(f"  uk_monthly{suffix}.parquet       saved ({series_out.stat().st_size/1e6:.1f} MB)")

heatmap_out = CACHE_DIR / f"uk_heatmap{suffix}.parquet"
latest.to_parquet(heatmap_out, index=False)
print(f"  uk_heatmap{suffix}.parquet       saved ({heatmap_out.stat().st_size/1e6:.1f} MB)")

print(f"\n  Sectors with current value:  {latest['v'].notna().sum():,}")
print(f"  Sectors with 1yr %:          {latest['y'].notna().sum():,}")
print(f"  Sectors with 5yr %:          {latest['y5'].notna().sum():,}")
print(f"  Sectors with 20yr %:         {latest['y20'].notna().sum():,}")

if not args.sample:
    write_refresh_record(remote_lm)
    print(f"  uk_last_refresh.json         saved")

print("\nDone. Next: python ingest_uk.py (full) or review uk_heatmap_sample.parquet")
