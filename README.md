# HR Platform

A microservices-based HR platform built with FastAPI, PostgreSQL, Redis, and RabbitMQ.

## Services

| Service | Port | Description |
|---|---|---|
| Auth Service | 8001 | Users, roles, permissions, JWT auth |
| Employee Service | 8002 | Employees, departments, positions |
| Payroll Service | 8003 | Salaries, payroll records |
| Time & Attendance | — | WIP |
| Audit Service | — | WIP |

## Stack

- **FastAPI** — async REST APIs with automatic Swagger/ReDoc docs
- **PostgreSQL** — per-service databases (isolated schemas)
- **Redis** — shared permission cache across services
- **RabbitMQ** — async event bus for cross-service communication
- **Alembic** — database migrations
- **Pydantic** — request/response validation
- **React + Vite** — admin frontend

---

## Backend Docker Setup (Recommended)

Runs all services, databases, Redis, and RabbitMQ in containers. Migrations run automatically on startup.

### Prerequisites

- Docker Desktop (or Docker Engine + Compose plugin)

### First run

```bash
chmod +x scripts/start.sh scripts/reset_db.sh
./scripts/start.sh
```

Builds all images, waits for dependencies to become healthy, seeds permissions and the default admin account, then tails the service logs. Press `Ctrl+C` to detach — the stack keeps running.

### Service URLs

| Service | URL |
|---|---|
| Auth Service API | http://localhost:8001/docs |
| Employee Service API | http://localhost:8002/docs |
| Payroll Service API | http://localhost:8003/docs |
| RabbitMQ Management UI | http://localhost:15672 |

RabbitMQ credentials: `guest` / `guest`

### Default admin account

```
username: admin
password: !Ch4ng3Th1sP4ssW0rd!
```

### Reset databases

Wipes all volumes, restarts the stack from scratch, and re-seeds everything:

```bash
./scripts/reset_db.sh
```

To only wipe volumes without restarting:

```bash
./scripts/reset_db.sh --wipe-only
```

### Common commands

```bash
docker compose up -d          # start in background
docker compose down           # stop all containers
docker compose logs -f        # tail all logs
docker compose logs -f auth_service   # tail one service
docker compose ps             # check container status
```

---

## Frontend Setup

A React + Vite admin dashboard that connects to the running backend services.

### Prerequisites

- Node.js 18+

### Install and run

```bash
cd frontend
npm install
npm run dev
```

The dev server starts at **http://localhost:5173**.

### Environment variables

The frontend reads API base URLs from environment variables. Create a `.env` file in the `frontend/` directory to override defaults:

```env
VITE_AUTH_API_URL=http://localhost:8001/api/v1
VITE_EMPLOYEE_API_URL=http://localhost:8002/api/v1
VITE_PAYROLL_API_URL=http://localhost:8003/api/v1
```

These default to the values above if not set, so no `.env` file is needed for local development against the Docker stack.

### Build for production

```bash
cd frontend
npm run build      # outputs to frontend/dist/
npm run preview    # preview the production build locally
```

---

## Local Development (without Docker)

For running individual services outside containers.

### 1. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
cd [service_name]
pip install -r requirements.txt
```

### 3. Run migrations

```bash
cd [service_name]
alembic upgrade head
alembic current   # verify
```

### 4. Seed data

```bash
cd auth_service
python -m app.scripts.seed_permissions
python -m app.scripts.seed_admin        # add --reset to recreate
```

### 5. Start a service

```bash
fastapi dev
```

### 6. Run tests

```bash
cd [service_name]
pytest -s
```

---

## API Docs

Each service exposes interactive docs at its root:

- Swagger UI: `http://localhost:<port>/docs`
- ReDoc: `http://localhost:<port>/redoc`
