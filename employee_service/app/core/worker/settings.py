from arq.connections import RedisSettings

from app.core.config import settings
from app.core.worker.functions import sample_background_task, shutdown, startup


class WorkerSettings:
    functions = [sample_background_task]
    redis_settings = RedisSettings(
        host=settings.REDIS_QUEUE_HOST, port=settings.REDIS_QUEUE_PORT
    )
    on_startup = startup
    on_shutdown = shutdown
    handle_signals = False
