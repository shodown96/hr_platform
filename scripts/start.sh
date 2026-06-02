#!/usr/bin/env bash
# Initial startup — builds images and brings the full stack up.
# Run this once after cloning or after changing Dockerfiles/requirements.
# For a clean-slate reset use reset_db.sh instead.

set -euo pipefail
COMPOSE="docker compose"

echo "▶  Building images and starting services..."
$COMPOSE up --build -d

echo ""
echo "⏳  Waiting for backing services to become healthy..."

wait_healthy() {
    local service=$1
    local max=90
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
    echo "  ⚠️   $service not healthy after ${max}s"
}

wait_healthy auth_db
wait_healthy employee_db
wait_healthy payroll_db
wait_healthy redis
wait_healthy rabbitmq

echo ""
echo "⏳  Waiting for auth_service to finish starting..."
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
