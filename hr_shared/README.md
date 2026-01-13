# 8. USAGE IN AUTH SERVICE

# auth-service/requirements.txt
"""
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
asyncpg==0.29.0
alembic==1.13.1
pydantic==2.5.3
pydantic-settings==2.1.0
passlib[bcrypt]==1.7.4
aio-pika==9.3.1
httpx==0.25.2

# Shared library (local development)
cd ../auth-service
pip install -e ../hr_shared

cd ../employee-service
pip install -e ../hr_shared

# OR for production (from git)
# git+https://github.com/yourorg/hr-shared.git@v0.1.0#egg=hr-shared
"""

# auth-service/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"

settings = Settings()


# auth-service/dependencies.py
from hr_shared.auth.dependencies import create_auth_dependencies
from app.core.config import settings

# Create auth dependencies for this service
auth_deps = create_auth_dependencies(
    auth_service_url="http://localhost:8001",  # Self reference
    secret_key=settings.SECRET_KEY,
    algorithm=settings.ALGORITHM
)

# Export for use in routes
get_current_user_from_token = auth_deps["get_current_user_from_token"]
get_current_active_user = auth_deps["get_current_active_user"]
check_permission = auth_deps["check_permission"]


# auth-service/services/auth_service.py
from hr_shared.auth.jwt_utils import JWTManager
from app.core.config import settings

jwt_manager = JWTManager(
    secret_key=settings.SECRET_KEY,
    algorithm=settings.ALGORITHM
)

async def create_access_token(user, permissions):
    """Create JWT token with permissions"""
    return jwt_manager.create_token(
        user_id=str(user.id),
        username=user.username,
        employee_id=user.employee_id,
        is_superuser=user.is_superuser,
        permissions=permissions,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )