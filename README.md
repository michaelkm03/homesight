# HomeSight

Interactive U.S. housing market map built on Zillow's public research data. Visualizes home values, rent, appreciation, and sales trends across 26,000+ ZIP codes.

**Live:** [homesight.live](https://homesight.live)

---

## Features

- **Choropleth map** — 26K+ ZIPs colored by median home value or year-over-year change
- **ZIP detail panel** — home value, rent, median sale, and new listing trend charts with YoY callouts
- **Appreciation history** — 1, 3, 5, 10, and 20-year appreciation bars per ZIP with investment signal badge
- **Listing links** — one-click to Zillow and Redfin for-sale listings from any selected ZIP
- **Area Rankings** — top-appreciating ZIPs across 900+ metro areas, sortable by 1/3/5/10/20-year periods
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

**2. Ingest data** (~5 min, one-time)
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

To refresh with the latest Zillow data:
```bash
python ingest.py --refresh
```

**3. Start**
```bash
uvicorn server:app --reload
```

Open **http://localhost:8000**

---

## API

All endpoints return JSON. Stats and heatmap cached 1 hour; boundaries and tiles cached 24 hours.

| Endpoint | Description |
|----------|-------------|
| `GET /` | Map page |
| `GET /data` | Data sources page |
| `GET /health` | Server status, dataset summary, uptime, git version |
| `GET /api/heatmap` | All ZIPs with value, YoY%, and coordinates |
| `GET /api/stats` | National median value, median YoY, ZIP count |
| `GET /api/zip/{zip}` | Full time-series configs + appreciation for one ZIP |
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

---

## Performance

All hot-path operations are O(1) or pre-computed at startup across 10M+ rows.

- **Binary search index** — `np.searchsorted` builds a `{zip: (start, end)}` index at boot; ZIP time-series lookups use `df.iloc` slices instead of boolean scans
- **Response cache** — ZIP panel responses stored in memory after first open; repeated opens are instant
- **Pre-computed stats** — `/api/stats` and `/api/metros` computed once at boot, returned by reference
- **Smart map restyle** — ZIP selection updates 2 Leaflet layers instead of all 26K
- **Deferred close restyle** — panel close resets 1 layer immediately; full opacity restore deferred to `requestAnimationFrame`
- **Client-side ZIP cache** — `zipDataCache` in browser; re-opening a ZIP skips the network fetch entirely
- **Persistent tile client** — `httpx.AsyncClient` lazily initialized and reused across tile requests
- **IndexedDB boundary cache** — 28 MB boundary file cached client-side for 1 hour; returning visits skip the fetch entirely

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

| Source | Provides | History |
|--------|---------|---------|
| [Zillow Research](https://www.zillow.com/research/data/) | Home values (ZHVI), rent (ZORI), median sale, market temp, new listings | 2000–present |
| [Census TIGER/Line](https://www.census.gov/geographies/mapping-files.html) | ZIP boundary polygons (ZCTA shapefiles) | Annual release |
| [GeoNames](https://www.geonames.org/) | ZIP coordinates, city names, state, metro area | CC BY 4.0 |

---

## Project Structure

```
homesight/
├── ingest.py               # Data pipeline — downloads and processes all sources
├── server.py               # FastAPI backend — API, caching, tile proxy
├── map.html                # Map frontend — Leaflet, ZIP panel, charts
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
└── data/                   # Generated by ingest.py (gitignored)
    ├── home_values.parquet
    ├── rentals.parquet
    ├── sales.parquet
    ├── market_temp.parquet
    ├── for_sale_listings.parquet
    ├── zip_meta.parquet
    ├── zips.parquet
    ├── boundaries.geojson.gz
    └── tiles/              # Tile cache — populated at runtime (gitignored)
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
# bash / Git Bash
ssh -i ~/.ssh/homesight.pem ubuntu@44.198.184.19 "cd /opt/homesight && sudo git pull && sudo systemctl restart homesight"
```

**Refresh data** (pulls latest Zillow CSVs, ~10 min):
```bash
# on the server
cd /opt/homesight
sudo venv/bin/python ingest.py
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
| High | **Automated data refresh** — weekly cron on server running `ingest.py` | Zillow updates monthly; currently manual |
| Med | **ZIP comparison tool** — side-by-side panel for 2–3 ZIPs | High-value feature for investors |
| Med | **Stale data alert** — Lambda check on `data_as_of`; alert if > 45 days old | Pairs with existing uptime monitor |
| Low | **Saved ZIPs** — localStorage list of pinned ZIPs | No auth required |
| Low | **Embed widget** — `<iframe>` snippet for a single ZIP card | Distribution play |
| Low | **Mobile layout** — panel slides up from bottom on small screens | Currently usable but not optimized |
