from __future__ import annotations

from typing import ClassVar

from arq.connections import RedisSettings

from app.core.redis import get_redis_settings
from app.workers.render_worker import run_render, worker_shutdown, worker_startup


class WorkerSettings:
    """ARQ worker configuration.

    Start with: arq app.workers.arq_settings.WorkerSettings
    """

    functions: ClassVar[list] = [run_render]
    on_startup = worker_startup
    on_shutdown = worker_shutdown
    max_jobs = 4
    job_timeout = 700
    health_check_interval = 30

    @staticmethod
    def redis_settings() -> RedisSettings:
        return get_redis_settings()
