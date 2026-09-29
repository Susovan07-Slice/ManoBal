#!/bin/sh
set -e

echo "=== [ManoBal Backend Container Starting] ==="

# Wait for database connectivity
echo "Checking database connectivity..."
python -c "
import sys, time
from sqlalchemy import text
from db.session import engine

max_retries = 30
for i in range(max_retries):
    try:
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
            print('Successfully connected to database.')
            sys.exit(0)
    except Exception as e:
        print(f'Waiting for database connection... ({i+1}/{max_retries})')
        time.sleep(1)
print('ERROR: Database connection timed out.')
sys.exit(1)
"

# Apply Alembic migrations
echo "Executing database migrations (alembic upgrade head)..."
alembic upgrade head

# Initialize schema and sync all columns
echo "Ensuring full database schema synchronization..."
python -m db.init_db

# Seed synthetic demo data if tables are empty
echo "Seeding synthetic demo records (if not present)..."
python -m db.seed

# Start production ASGI server
echo "Starting FastAPI ASGI application on port 8000..."
exec uvicorn api.main:app --host 0.0.0.0 --port 8000
