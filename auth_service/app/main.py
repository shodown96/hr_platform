# from api import api_router
# from app.core.setup import create_application
# from app.core.config import settings

# app = create_application(router=api_router, settings=settings)

from app.api import api_router
from app.core.config import settings
from app.core.db import SessionDep
from app.core.health import check_database_health, check_redis_health
from app.core.lifespan import lifespan_factory
from app.core.utils import cache
from app.models import *  # noqa: F403
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="HR Auth Service",
    description="Authentication and Authorization Microservice",
    version="1.0.0",
    lifespan=lifespan_factory(settings),
)


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)


@app.get("/", tags=["Base"])
async def get_base_endpoint(db: SessionDep, redis: cache.RedisDep):
    db_health = await check_database_health(db)
    redis_health = await check_redis_health(redis)
    return {
        "message": "Welcome to HR Platform API | Auth Service",
        "health": {
            "database": f"{'un'if not db_health else ''}healthy",
            "redis": f"{'un'if not redis_health else ''}healthy",
        },
    }


# Include routers
app.include_router(api_router)

# from fastapi import Request
# from fastapi.exceptions import ResponseValidationError
# from fastapi.responses import JSONResponse
# @app.exception_handler(ResponseValidationError)
# async def response_validation_handler(request: Request, exc: ResponseValidationError):
#     return JSONResponse(
#         status_code=500,
#         content={"detail": exc.errors()},
#     )
