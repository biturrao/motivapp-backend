#!/bin/bash
# startup.sh - Script de inicio para Azure App Service

echo "Starting Gunicorn with Uvicorn workers..."
python -m gunicorn app.main:app \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind=0.0.0.0:8000 \
    --timeout 600 \
    --log-level info
