#!/usr/bin/env bash
# Wipe all databases and restart fresh.
# Usage:
#   ./scripts/reset_db.sh             # wipe + rebuild + tail logs
#   ./scripts/reset_db.sh --wipe-only # just drop volumes, don't restart

set -euo pipefail
COMPOSE="docker compose"
WIPE_ONLY=false
for arg in "$@"; do [[ "$arg" == "--wipe-only" ]] && WIPE_ONLY=true; done

echo "▶  Stopping all services..."
$COMPOSE down --remove-orphans

echo "▶  Removing database volumes..."
$COMPOSE down -v

echo "✅  All volumes removed."

if $WIPE_ONLY; then
    echo "ℹ️   --wipe-only set, skipping restart."
    exit 0
fi

echo "▶  Rebuilding and starting services..."
$COMPOSE up --build -d

echo ""
echo "⏳  Waiting for backing services to become healthy..."

wait_healthy() {
    local service=$1
    local max=60
    local i=0
    while [ $i -lt $max ]; do
        health=$(docker inspect --format='{{.State.Health.Status}}' \
            "$(docker compose ps -q "$service" 2>/dev/null)" 2>/dev/null || echo "unknown")
        if [[ "$health" == "healthy" ]]; then
            echo "  ✅  $service healthy"
            return
        fi
        sleep 2; i=$((i+2))
    done
    echo "  ⚠️   $service not healthy after ${max}s — check: docker compose logs $service"
}

wait_healthy auth_db
wait_healthy employee_db
wait_healthy payroll_db
wait_healthy redis
wait_healthy rabbitmq

echo ""
echo "⏳  Waiting for auth_service to finish seeding..."
sleep 8

echo "▶  Seeding permissions and admin account..."
$COMPOSE exec auth_service python -m app.scripts.seed_permissions
$COMPOSE exec auth_service python -m app.scripts.seed_admin
echo "✅  Seeding complete."

echo ""
echo "✅  Stack is up."
echo ""
echo "  Auth Service     → http://localhost:8001/docs"
echo "  Employee Service → http://localhost:8002/docs"
echo "  Payroll Service  → http://localhost:8003/docs"
echo "  RabbitMQ UI      → http://localhost:15672  (guest / guest)"
echo ""
echo "  Default admin credentials:"
echo "    username: admin"
echo "    password: !Ch4ng3Th1sP4ssW0rd!"
echo ""
echo "▶  Following logs (Ctrl+C to detach)..."
$COMPOSE logs -f auth_service employee_service payroll_service
