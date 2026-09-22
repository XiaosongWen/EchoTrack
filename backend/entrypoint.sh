#!/bin/bash
set -e

# Automatically create target database if it does not exist
if [ -n "$DATABASE_URL" ]; then
    echo "Checking and ensuring target database exists..."
    python3 -c "
import asyncio
from urllib.parse import urlparse
import asyncpg
import os

db_url = os.environ.get('DATABASE_URL')
# Convert SQLAlchemy asyncpg URL to standard postgresql:// for asyncpg connection
clean_url = db_url.replace('postgresql+asyncpg://', 'postgresql://')
parsed = urlparse(clean_url)

target_db = parsed.path.lstrip('/')
default_db_url = clean_url.rsplit('/', 1)[0] + '/postgres'

async def create_db():
    try:
        conn = await asyncpg.connect(default_db_url)
        exists = await conn.fetchval('SELECT 1 FROM pg_database WHERE datname = \$1', target_db)
        if not exists:
            print(f'Creating database {target_db}...')
            # Quote database name to prevent SQL injection or syntax issues
            await conn.execute(f'CREATE DATABASE \"{target_db}\"')
            print(f'Database {target_db} created successfully.')
        else:
            print(f'Database {target_db} already exists.')
        await conn.close()
    except asyncpg.exceptions.DuplicateDatabaseError:
        print(f'Database {target_db} already exists (caught DuplicateDatabaseError).')
    except Exception as e:
        print(f'ERROR: Database check/creation failed: {e}')
        raise SystemExit(1)

asyncio.run(create_db())
"
fi

echo "Running Alembic migrations..."
alembic upgrade head

echo "Starting FastAPI..."
# Cloud Run injects $PORT; fall back to 8000 for local / Docker Compose usage.
exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
