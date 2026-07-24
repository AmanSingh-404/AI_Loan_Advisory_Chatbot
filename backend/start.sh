#!/bin/bash
echo "Building the document index..."
python ingest.py
echo "Starting the API server..."
uvicorn main:app --host 0.0.0.0 --port $PORT