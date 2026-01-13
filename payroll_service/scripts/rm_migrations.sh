#!/usr/bin/env bash
set -e

echo "⚠️  Removing Alembic migrations..."

# Remove all migration versions
if [ -d "alembic/versions" ]; then
  rm -f alembic/versions/*.py
  rm -f alembic/versions/*.pyc
  echo "✔ Removed alembic/versions files"
else
  echo "⚠ alembic/versions not found"
fi

# Optional: remove __pycache__
find alembic -type d -name "__pycache__" -exec rm -rf {} +

# Optional: reset alembic version table (Postgres example)
# Uncomment ONLY if you want to wipe migration history from DB
# echo "⚠ Resetting alembic_version table..."
# psql "$DATABASE_URL" -c "DROP TABLE IF EXISTS alembic_version;"

echo "✅ Alembic migrations cleared"
