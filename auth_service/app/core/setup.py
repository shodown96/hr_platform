from collections.abc import Callable
from contextlib import _AsyncGeneratorContextManager
from typing import Any

from app.core.config import (
    AppSettings,
    ClientSideCacheSettings,
    CORSSettings,
    DatabaseSettings,
    EnvironmentOption,
    EnvironmentSettings,
    RedisCacheSettings,
    RedisQueueSettings,
)
from app.core.db import SessionDep
from app.core.dependencies.auth import get_current_superuser
from app.core.health import check_database_health, check_redis_health
from app.core.lifespan import lifespan_factory
from app.core.utils import cache
from app.middleware.client_cache_middleware import ClientCacheMiddleware
from app.models import *  # noqa: F403
from fastapi import APIRouter, Depends, FastAPI, responses
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi


# -------------- application --------------
def create_application(
    router: APIRouter,
    settings: (
        DatabaseSettings
        | RedisCacheSettings
        | AppSettings
        | ClientSideCacheSettings
        | CORSSettings
        | RedisQueueSettings
        | EnvironmentSettings
    ),
    create_tables_on_start: bool = False,
    lifespan: Callable[[FastAPI], _AsyncGeneratorContextManager[Any]] | None = None,
    **kwargs: Any,
) -> FastAPI:
    """Creates and configures a FastAPI application based on the provided settings.

    This function initializes a FastAPI application and configures it with various settings
    and handlers based on the type of the `settings` object provided.

    Parameters
    ----------
    router : APIRouter
        The APIRouter object containing the routes to be included in the FastAPI application.

    settings
        An instance representing the settings for configuring the FastAPI application.
        It determines the configuration applied:

        - AppSettings: Configures basic app metadata like name, description, contact, and license info.
        - DatabaseSettings: Adds event handlers for initializing database tables during startup.
        - RedisCacheSettings: Sets up event handlers for creating and closing a Redis cache pool.
        - ClientSideCacheSettings: Integrates middleware for client-side caching.
        - CORSSettings: Integrates CORS middleware with specified origins.
        - RedisQueueSettings: Sets up event handlers for creating and closing a Redis queue pool.
        - EnvironmentSettings: Conditionally sets documentation URLs and integrates custom routes for API documentation
          based on the environment type.

    create_tables_on_start : bool
        A flag to indicate whether to create database tables on application startup.
        Defaults to True.

    **kwargs
        Additional keyword arguments passed directly to the FastAPI constructor.

    Returns
    -------
    FastAPI
        A fully configured FastAPI application instance.

    The function configures the FastAPI application with different features and behaviors
    based on the provided settings. It includes setting up database connections, Redis pools
    for caching, queue, and rate limiting, client-side caching, and customizing the API documentation
    based on the environment settings.
    """
    # --- before creating application ---
    if isinstance(settings, AppSettings):
        to_update = {
            "title": settings.APP_NAME,
            "description": settings.APP_DESCRIPTION,
            "contact": {"name": settings.CONTACT_NAME, "email": settings.CONTACT_EMAIL},
            "license_info": {"name": settings.LICENSE_NAME},
        }
        kwargs.update(to_update)

    if isinstance(settings, EnvironmentSettings):
        kwargs.update({"docs_url": None, "redoc_url": None, "openapi_url": None})

    # Use custom lifespan if provided, otherwise use default factory
    if lifespan is None:
        lifespan = lifespan_factory(
            settings, create_tables_on_start=create_tables_on_start
        )

    application = FastAPI(lifespan=lifespan, **kwargs)

    if isinstance(settings, ClientSideCacheSettings):
        application.add_middleware(
            ClientCacheMiddleware, max_age=settings.CLIENT_CACHE_MAX_AGE
        )

    if isinstance(settings, CORSSettings):
        application.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=settings.CORS_METHODS,
            allow_headers=settings.CORS_HEADERS,
        )

    if isinstance(settings, EnvironmentSettings):
        if settings.ENVIRONMENT != EnvironmentOption.PRODUCTION:
            base_router = APIRouter()
            docs_router = APIRouter()
            if settings.ENVIRONMENT != EnvironmentOption.LOCAL:
                docs_router = APIRouter(dependencies=[Depends(get_current_superuser)])

            @docs_router.get("/docs", include_in_schema=False)
            async def get_swagger_documentation() -> responses.HTMLResponse:
                return get_swagger_ui_html(openapi_url="/openapi.json", title="docs")

            @docs_router.get("/redoc", include_in_schema=False)
            async def get_redoc_documentation() -> responses.HTMLResponse:
                return get_redoc_html(openapi_url="/openapi.json", title="docs")

            @docs_router.get("/openapi.json", include_in_schema=False)
            async def openapi() -> dict[str, Any]:
                out: dict = get_openapi(
                    title=application.title,
                    version=application.version,
                    routes=application.routes,
                )
                return out

            @base_router.get("/", tags=["Base"])
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

            application.include_router(base_router)
            application.include_router(docs_router)
    application.include_router(router)

    return application
