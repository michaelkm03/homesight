# HomeSight

Interactive housing market map covering **26,000+ U.S. ZIP codes** and **8,700+ UK postcode sectors**. Visualizes home values, rent, appreciation, and sales trends powered by public government data.

**Live:** [homesight.live](https://homesight.live)

---

## Features

### US (Zillow data)
- **Choropleth map** — 26K+ ZIPs colored by median home value or year-over-year change
- **ZIP detail panel** — home value, rent, median sale, and new listing trend charts with YoY callouts
- **Appreciation history** — 1, 3, 5, 10, and 20-year appreciation bars per ZIP with investment signal badge
- **Listing links** — one-click to Zillow and Redfin for-sale listings from any selected ZIP
- **Area Rankings** — top-appreciating ZIPs across 900+ metro areas, sortable by 1/3/5/10/20-year periods

### UK (HM Land Registry data)
- **Choropleth map** — 8,700+ postcode sectors colored by median transaction price or year-over-year change
- **Sector detail panel** — full price history chart, 1/3/5/10/20-year appreciation bars, GBP median value
- **Investment signal badge** — Caution / Hold / Buy signal derived from 1yr + 5yr appreciation
- **Search by postcode** — accepts full postcodes (e.g. `SW1A 1AA`) or sector codes (e.g. `SW1A 1`)
- **Country toggle** — switch between US and UK map views; each has its own legend, stats, and color scale

### Shared infrastructure
- **Tile proxy** — CartoDB map tiles proxied and disk-cached locally; zero CDN calls after first visit
- **Zero external dependencies** — Leaflet.js and Chart.js vendored in `static/`; boundaries cached in IndexedDB
- **GA4 event tracking** — zip_search, zip_click, metric_change, metro_search
- **Uptime monitoring** — AWS Lambda + EventBridge (5-min) + SNS email alerts

---

## Tech Stack

| Layer | Tools |
|-------|-------|
| Backend | FastAPI, pandas, geopandas, uvicorn |
| Frontend | Leaflet.js, Chart.js, vanilla JS (all vendored) |
| Data | Parquet, gzip GeoJSON |
| Tiles | CartoDB Positron — proxied and disk-cached |
| Infra | AWS Lightsail, nginx, systemd, certbot (Let's Encrypt) |
| Monitoring | AWS Lambda + EventBridge + SNS |

---

## Quick Start

**1. Install dependencies**
```bash
pip install fastapi uvicorn pandas geopandas pyarrow httpx
```

**2. Ingest US data** (~5 min, one-time)
```bash
python ingest.py
```

Expected output:
```
  home_values: 6,378,211 rows
  rentals: 435,221 rows
  ...
  boundaries.geojson.gz saved (26,276 ZIPs)
Done. Run: uvicorn server:app --reload
```

**3. Ingest UK data** (~20 min first run, downloads ~4 GB raw CSV)
```bash
python ingest_uk.py            # downloads PPD, builds parquets
python ingest_uk.py --boundaries   # builds boundary GeoJSON (~180 MB shapefile)
```

Expected output:
```
  uk_monthly.parquet       saved (2,875,488 rows)
  uk_heatmap.parquet       saved (8,782 sectors)
  uk_boundaries.geojson.gz saved (8,782 sectors)
```

UK data is optional — the server starts fine without it; the UK tab will show an error message until ingested.

To refresh with the latest data:
```bash
python ingest.py --refresh       # US
python ingest_uk.py --refresh    # UK (re-downloads ~4 GB)
```

**4. Start**
```bash
uvicorn server:app --reload
```

Open **http://localhost:8000**

---

## API

All endpoints return JSON. Stats and heatmap cached 1 hour; boundaries and tiles cached 24 hours.

### US endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Map page |
| `GET /data` | Data sources page |
| `GET /health` | Server status, dataset summary, uptime, git version |
| `GET /api/heatmap` | All ZIPs with value, YoY%, and coordinates |
| `GET /api/stats` | National median value, median YoY, ZIP count |
| `GET /api/zip/{zip}` | Full time-series + appreciation for one ZIP |
| `GET /api/rank?metro=&metric=&limit=` | ZIPs in a metro ranked by metric |
| `GET /api/metros` | All metros sorted by ZIP count |
| `GET /api/boundaries` | GeoJSON polygons for all ZIPs (gzip, ~28 MB) |
| `GET /tiles/{layer}/{z}/{x}/{y}.png` | Tile proxy — `layer` is `base` or `labels` |
| `GET /sitemap.xml` | XML sitemap |
| `GET /BingSiteAuth.xml` | Bing Webmaster Tools verification |

**`/api/rank` parameters**

| Param | Default | Options |
|-------|---------|---------|
| `metro` | required | Any metro from `/api/metros` |
| `metric` | `appreciation_5y` | `appreciation_1y` `appreciation_3y` `appreciation_5y` `appreciation_10y` `appreciation_20y` `current_value` |
| `limit` | `50` | 1–999 |

### UK endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/uk/heatmap` | All sectors with value + appreciation metrics |
| `GET /api/uk/stats` | National median value, median YoY, sector count |
| `GET /api/uk/sector/{sector_code}` | Full price history + appreciation for one postcode sector |
| `GET /api/uk/boundaries` | GeoJSON polygons for all sectors (gzip, ~5–10 MB) |

---

## Data Schemas

### US — `/api/heatmap` item
```json
{
  "z": "98101",
  "v": 750000,
  "y": 3.2,
  "lat": 47.61,
  "lon": -122.33
}
```
| Field | Type | Description |
|-------|------|-------------|
| `z` | string | 5-digit ZIP code |
| `v` | integer | Median home value (USD) |
| `y` | float | Year-over-year % change |
| `lat` | float | ZIP centroid latitude |
| `lon` | float | ZIP centroid longitude |

### US — `/api/zip/{zip}` response
```json
{
  "city": "Seattle",
  "state": "WA",
  "metro": "Seattle-Tacoma-Bellevue, WA",
  "home_values": { "labels": ["2020-01", ...], "values": [680000, ...] },
  "rentals":     { "labels": [...], "values": [...] },
  "sales":       { "labels": [...], "values": [...] },
  "market_temp": { "labels": [...], "values": [...] },
  "for_sale_listings": { "labels": [...], "values": [...] },
  "appreciation": {
    "1y": 3.2, "3y": 12.1, "5y": 28.4, "10y": 87.2, "20y": 210.5
  },
  "current_value": 750000
}
```

### UK — `/api/uk/heatmap` item
```json
{
  "s": "SW1A 1",
  "v": 850000,
  "y": 2.1,
  "y3": 8.4,
  "y5": 19.2,
  "y10": 52.3,
  "y20": 140.1
}
```
| Field | Type | Description |
|-------|------|-------------|
| `s` | string | Postcode sector (e.g. `SW1A 1`) |
| `v` | integer | Median transaction price (GBP) |
| `y` | float | 1-year appreciation % |
| `y3` | float | 3-year appreciation % |
| `y5` | float | 5-year appreciation % |
| `y10` | float | 10-year appreciation % |
| `y20` | float | 20-year appreciation % |

### UK — `/api/uk/sector/{sector_code}` response
```json
{
  "sector": "SW1A 1",
  "currency": "GBP",
  "current_value": 850000,
  "prices": {
    "dates":  ["2020-01-01", ...],
    "values": [780000, ...]
  },
  "appreciation": {
    "y": 2.1, "y3": 8.4, "y5": 19.2, "y10": 52.3, "y20": 140.1
  }
}
```

### UK — `/api/uk/stats` response
```json
{
  "total_sectors": 8782,
  "median_value": 285000,
  "median_yoy": 1.8,
  "currency": "GBP",
  "source": "HM Land Registry Price Paid Data",
  "coverage": "England & Wales"
}
```

---

## Performance

All hot-path operations are O(1) or pre-computed at startup across 10M+ rows.

- **Binary search index** — `np.searchsorted` builds a `{zip: (start, end)}` index at boot; ZIP time-series lookups use `df.iloc` slices instead of boolean scans
- **Response cache** — ZIP and sector panel responses stored in memory after first open; repeated opens are instant
- **Pre-computed stats** — `/api/stats`, `/api/uk/stats`, and `/api/metros` computed once at boot, returned by reference
- **Smart map restyle** — ZIP/sector selection updates 2 Leaflet layers instead of redrawing all features
- **Client-side cache** — `zipDataCache` / `ukSectorCache` in browser; re-opening a ZIP/sector skips the network fetch entirely
- **IndexedDB boundary cache** — US (28 MB) and UK boundary files cached client-side for 1 hour; returning visits skip the fetch entirely
- **Persistent tile client** — `httpx.AsyncClient` lazily initialized and reused across tile requests

---

## Monitoring

The Lambda function in `lambda/monitor.py` runs every 5 minutes via EventBridge and checks:

1. `GET /health` — status must be `"ok"`, heatmap_zips ≥ 25,000
2. `GET /api/zip/98101` — must return home_values config + city/state metadata
3. `GET /api/heatmap` — must return a list of ≥ 25,000 items

On any failure it publishes to SNS, which emails `michaelkm03@gmail.com`.

**Resources:**
- Lambda: `homesight-monitor` (us-west-2)
- EventBridge rule: `homesight-monitor-schedule` (rate: 5 minutes)
- SNS topic: `arn:aws:sns:us-west-2:005097885341:homesight-alerts`

---

## Data Sources

### US
| Source | Provides | History | License |
|--------|---------|---------|---------|
| [Zillow Research](https://www.zillow.com/research/data/) | Home values (ZHVI), rent (ZORI), median sale, market temp, new listings | 2000–present | Free for non-commercial use |
| [Census TIGER/Line](https://www.census.gov/geographies/mapping-files.html) | ZIP boundary polygons (ZCTA shapefiles) | Annual release | Public domain |
| [GeoNames](https://www.geonames.org/) | ZIP coordinates, city names, state, metro area | CC BY 4.0 | CC BY 4.0 |

### UK
| Source | Provides | History | License |
|--------|---------|---------|---------|
| [HM Land Registry Price Paid Data](https://www.gov.uk/government/statistical-data-sets/price-paid-data-downloads) | All residential property transactions in England & Wales | 1995–present | OGL v3.0 (Open Government Licence) |
| [GeoLytix / Edinburgh DataShare](https://datashare.ed.ac.uk/handle/10283/2597) | Postcode sector boundary polygons | Current | Open Data |

**UK postcode sector format:** `{outward} {first digit of inward}` — e.g. full postcode `SW1A 1AA` → sector `SW1A 1`. There are ~8,782 sectors in England & Wales, comparable in granularity to U.S. ZIP codes.

---

## Project Structure

```
homesight/
├── ingest.py               # US pipeline — downloads and processes Zillow data
├── ingest_uk.py            # UK pipeline — downloads and processes HM Land Registry PPD
├── cron_runner.py          # Orchestrates US + UK refresh; logs to SQLite
├── server.py               # FastAPI backend — API, caching, tile proxy
├── map.html                # Map frontend — Leaflet, ZIP/sector panel, charts, country toggle
├── data.html               # Data sources page
├── LAUNCH.md               # Launch strategy and pre-launch checklist
├── MARKETING.md            # Channel-level marketing playbook
├── lambda/
│   └── monitor.py          # AWS Lambda uptime monitor (deploy via AWS console)
├── static/                 # Vendored JS/CSS — no CDN dependencies
│   ├── leaflet.js
│   ├── leaflet.css
│   ├── chart.umd.min.js
│   ├── logo.svg
│   ├── logo.png
│   └── og-image.png
├── tests/
│   └── test_server.py      # pytest suite covering all endpoints and edge cases
└── data/                   # Generated by ingest scripts (gitignored)
    ├── home_values.parquet
    ├── rentals.parquet
    ├── sales.parquet
    ├── market_temp.parquet
    ├── for_sale_listings.parquet
    ├── zip_meta.parquet
    ├── zips.parquet
    ├── boundaries.geojson.gz
    ├── uk_monthly.parquet       # Monthly median price per sector (generated by ingest_uk.py)
    ├── uk_heatmap.parquet       # Per-sector value + appreciation (generated by ingest_uk.py)
    ├── uk_boundaries.geojson.gz # Sector polygons (generated by ingest_uk.py --boundaries)
    ├── uk_last_refresh.json     # Tracks last UK ingest timestamp
    ├── last_refresh.json        # Tracks last US ingest timestamp
    └── tiles/                   # Tile cache — populated at runtime (gitignored)
```

---

## Code Style

All files use a consistent section-header comment convention:

**Python (`server.py`, `ingest.py`, `lambda/monitor.py`)**
```python
# ── Section name ──────────────────────────────────────────────────────────────
```

**JavaScript (`map.html`)**
```javascript
// ── Section name ─────────────────────────────────────────────────────────────
```

Rules:
- Comments explain **why**, not what — identifiers document what
- No multi-line docblocks except on non-obvious public functions
- Inline comments on non-obvious invariants, thresholds, or workarounds only
- All Python formatted to 100-char line length; JS uses 2-space indent

---

## Deployment

HomeSight runs on **AWS Lightsail** (4 GB RAM, Ubuntu 24.04) behind nginx with SSL via Let's Encrypt.

**Stack:**
- **nginx** — reverse proxy port 80/443 → uvicorn port 8000
- **systemd** — `homesight.service` keeps the app running and restarts on crash
- **certbot** — auto-renewing SSL for homesight.live

**Service management (on server):**
```bash
sudo systemctl status homesight     # check status
sudo systemctl restart homesight    # restart app
sudo journalctl -u homesight -f     # tail logs
```

**Deploy latest code (run locally):**
```bash
ssh -i C:\Users\micha\.ssh\beacon.pem ubuntu@44.198.184.19 "sudo git -C /opt/homesight pull origin main && sudo systemctl restart homesight.service"
```

**Refresh US data** (pulls latest Zillow CSVs, ~10 min):
```bash
# on the server
cd /opt/homesight
sudo python ingest.py
sudo systemctl restart homesight
```

**Ingest UK data** (first time — downloads ~4 GB, ~20 min):
```bash
# on the server
cd /opt/homesight
sudo python ingest_uk.py
sudo python ingest_uk.py --boundaries
sudo systemctl restart homesight
```

**Refresh UK data** (re-downloads only if source has changed):
```bash
sudo python ingest_uk.py --refresh
sudo systemctl restart homesight
```

---

## Tests

```bash
pytest tests/ -v
```

Covers all endpoints, data validation, sort correctness, and edge cases. Tests skip gracefully if data has not been ingested.

---

## Roadmap

Priority order for future development:

| Priority | Item | Notes |
|----------|------|-------|
| High | **Programmatic SEO** — `/housing-market/{zip}` static pages | Requires SSR (Jinja2 or Next.js); biggest long-term traffic driver |
| High | **Automated data refresh** — systemd timer for `cron_runner.py` | US + UK refresh orchestrated; timer not yet deployed |
| Med | **ZIP comparison tool** — side-by-side panel for 2–3 ZIPs | High-value feature for investors |
| Med | **Stale data alert** — Lambda check on `data_as_of`; alert if > 45 days old | Pairs with existing uptime monitor |
| Low | **Scotland / Northern Ireland** — extend UK coverage | Land Registry only covers England & Wales; separate data sources required |
| Low | **Saved ZIPs** — localStorage list of pinned ZIPs | No auth required |
| Low | **Embed widget** — `<iframe>` snippet for a single ZIP card | Distribution play |
| Low | **Mobile layout** — panel slides up from bottom on small screens | Currently usable but not optimized |
