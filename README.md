# HR Plaform (WIP)

## Services
- Auth Service
- Employee Management Service
- Payroll Service
- Time and Attendance Service

## Features
- FastAPI with async support
- Structured project layout
- Pydantic models for validation
- SQLAlchemy for managing DB models
- Albemic for managing migrations
- Dependency injection
- Environment-based configuration
- Automatic interactive API docs (Swagger & ReDoc)
- Authentication

## Getting Started

### 1. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```
### 3. Run migrations
```bash
cd [service_name] # start with auth
alembic revision --autogenerate -m 'MESSAGE' # for a new project
alembic upgrade head
alembic current # to check things went smoothly 
```

### Seed Data
```bash
cd auth-service
python -m app.scripts.seed_permissions 
python -m app.scripts.seed_admin # --reset (to reset the admin)
```

### 4. Run the server
```bash
fastapi dev
```

### 4. Test Microservices
```bash
cd [service_name] # start with auth
pytest -s
```

## Docs
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc