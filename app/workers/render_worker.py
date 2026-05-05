from __future__ import annotations

import asyncio
from typing import Any

import structlog
from arq.connections import ArqRedis

from app.core.config import get_settings
from app.db import render_crud
from app.db.session import _get_engine
from app.models.render import RenderStatus
from app.services.render_service import RenderService, RenderServiceError

logger = structlog.get_logger(__name__)


async def run_render(ctx: dict[str, Any], render_id: str) -> None:
    """ARQ task: dequeue a render job and execute the full pipeline.

    Retrieves the render record, reconstructs the composition from the stored
    input JSON, and delegates to RenderService.execute_render(). On failure,
    ensures the render record is transitioned to FAILED status.
    """
    session_factory = ctx["session_factory"]
    render_service: RenderService = ctx["render_service"]
    settings = get_settings()

    structlog.contextvars.bind_contextvars(render_id=render_id)
    await logger.ainfo("worker_task_start", render_id=render_id)

    timeout = settings.render_timeout_seconds

    async with session_factory() as session:
        render = await render_crud.get_render_by_id(session, render_id)
        if render is None:
            await logger.aerror("worker_render_not_found", render_id=render_id)
            return

        if RenderStatus(render.status).is_terminal:
            await logger.awarning(
                "worker_render_already_terminal",
                render_id=render_id,
                status=render.status,
            )
            return

        if render.input_path is None:
            await logger.aerror(
                "worker_render_no_input",
                render_id=render_id,
            )
            await render_crud.update_render_status(
                session,
                render_id,
                RenderStatus.FAILED,
                error_code="NO_INPUT_DATA",
                error_message="Render record has no stored composition",
                stage="failed",
            )
            return

        from pathlib import Path

        input_path = Path(render.input_path)
        if not input_path.is_file():
            await logger.aerror(
                "worker_input_file_missing",
                render_id=render_id,
                path=str(input_path),
            )
            await render_crud.update_render_status(
                session,
                render_id,
                RenderStatus.FAILED,
                error_code="INPUT_FILE_MISSING",
                error_message=f"Input file not found: {input_path}",
                stage="failed",
            )
            return

        from app.models.composition import Composition

        input_json = input_path.read_text(encoding="utf-8")
        composition = Composition.model_validate_json(input_json)

    try:
        async with session_factory() as session:
            await asyncio.wait_for(
                render_service.execute_render(composition, session),
                timeout=timeout,
            )
        await logger.ainfo("worker_task_succeeded", render_id=render_id)

    except TimeoutError:
        await logger.aerror(
            "worker_task_timeout",
            render_id=render_id,
            timeout=timeout,
        )
        async with session_factory() as session:
            await render_crud.update_render_status(
                session,
                render_id,
                RenderStatus.FAILED,
                error_code="RENDER_TIMEOUT",
                error_message=f"Render exceeded {timeout}s timeout",
                stage="failed",
            )

    except RenderServiceError as exc:
        await logger.aerror(
            "worker_task_render_error",
            render_id=render_id,
            error_code=exc.error_code,
        )
        # RenderService already marks the render as failed internally

    except Exception as exc:
        await logger.aerror(
            "worker_task_unexpected_error",
            render_id=render_id,
            error=str(exc),
        )
        async with session_factory() as session:
            render = await render_crud.get_render_by_id(session, render_id)
            if render is not None and not RenderStatus(render.status).is_terminal:
                await render_crud.update_render_status(
                    session,
                    render_id,
                    RenderStatus.FAILED,
                    error_code="WORKER_UNEXPECTED_ERROR",
                    error_message=str(exc)[:500],
                    stage="failed",
                )


async def enqueue_render(pool: ArqRedis, render_id: str) -> None:
    """Enqueue a render job to ARQ for async processing."""
    await pool.enqueue_job("run_render", render_id)


async def worker_startup(ctx: dict[str, Any]) -> None:
    """ARQ on_startup hook: initialize DB engine and service dependencies."""
    from sqlmodel.ext.asyncio.session import AsyncSession as SQLModelAsyncSession

    from app.renderers.editly import EditlyRenderer
    from app.services.asset_service import AssetService
    from app.storage.local import LocalStorage

    settings = get_settings()

    engine = _get_engine()

    async def session_factory() -> SQLModelAsyncSession:
        return SQLModelAsyncSession(engine)

    storage = LocalStorage(workspace_root=settings.render_workspace_root)
    asset_service = AssetService(settings=settings)
    renderer = EditlyRenderer(settings=settings)
    render_service = RenderService(
        storage=storage,
        asset_service=asset_service,
        renderer=renderer,
    )

    ctx["session_factory"] = _make_session_context_manager(engine)
    ctx["render_service"] = render_service

    await logger.ainfo("worker_started")


def _make_session_context_manager(engine: Any) -> Any:
    """Build an async context manager that yields DB sessions."""
    from contextlib import asynccontextmanager

    from sqlmodel.ext.asyncio.session import AsyncSession as SQLModelAsyncSession

    @asynccontextmanager
    async def _session_ctx():  # type: ignore[no-untyped-def]
        async with SQLModelAsyncSession(engine) as session:
            yield session

    return _session_ctx


async def worker_shutdown(ctx: dict[str, Any]) -> None:
    """ARQ on_shutdown hook: cleanup resources."""
    await logger.ainfo("worker_shutdown")
