#!/bin/bash
set -e

if [ ! -f "data/boundaries.geojson.gz" ]; then
    echo "First run — downloading data (5–10 min)..."
    python ingest.py
fi

exec uvicorn server:app --host 0.0.0.0 --port $PORT
