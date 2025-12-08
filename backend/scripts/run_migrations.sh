#!/bin/bash
# Run database migrations using Alembic

set -e

cd "$(dirname "$0")/.."

echo "Running database migrations..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run migrations
python -m alembic upgrade head

echo "Migrations completed successfully!"

