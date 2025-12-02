#!/bin/bash
set -e

# Move into backend folder
cd backend

# Install backend deps (only runs in the container)
if [ -f requirements.txt ]; then
  pip install -r requirements.txt
fi

# Start FastAPI with uvicorn
uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
