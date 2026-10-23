#!/bin/bash
set -e

if [ ! -d "data/faiss_index" ]; then
  echo "Building document FAISS index..."
  python ingest.py
fi

echo "Starting Uvicorn API server..."
exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"