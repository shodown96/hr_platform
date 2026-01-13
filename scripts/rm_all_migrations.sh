#!/usr/bin/env bash
set -e

ROOT_DIR="$(pwd)"

echo "⚠️  Clearing Alembic migrations from microservices..."
echo "Root: $ROOT_DIR"
echo

# Find all alembic/versions directories under root
find "$ROOT_DIR" -type d -path "*/alembic/versions" | while read -r VERSIONS_DIR; do
  echo "→ Clearing: $VERSIONS_DIR"

  rm -f "$VERSIONS_DIR"/*.py
  rm -f "$VERSIONS_DIR"/*.pyc

done

# Remove __pycache__ inside alembic folders
find "$ROOT_DIR" -type d -path "*/alembic/__pycache__" -exec rm -rf {} +
find "$ROOT_DIR" -type d -path "*/alembic/versions/__pycache__" -exec rm -rf {} +

echo
echo "✅ Alembic migration files cleared across all services"
