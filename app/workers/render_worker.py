from __future__ import annotations

import asyncio
from typing import Any

import structlog
from arq.connections import ArqRedis

from app.core.config import get_settings
from app.db import render_crud
from app.db.session import _get_engine
from app.models.error_codes import ErrorCode, error_code_for_exception
from app.models.render import RenderStatus
from app.services.render_service import RenderService, RenderServiceError
from app.workers.log_collector import RenderLogCollector
from app.workers.workspace import WorkspaceManager

logger = structlog.get_logger(__name__)


async def run_render(ctx: dict[str, Any], render_id: str) -> None:
    """ARQ task: execute the full render pipeline with stage-by-stage transitions.

    Drives status transitions externally (QUEUED -> FETCHING -> COMPILING ->
    RENDERING -> UPLOADING -> SUCCEEDED/FAILED) and manages workspace lifecycle
    and log collection.
    """
    session_factory = ctx["session_factory"]
    render_service: RenderService = ctx["render_service"]
    workspace_mgr: WorkspaceManager = ctx["workspace_manager"]
    settings = get_settings()

    structlog.contextvars.bind_contextvars(render_id=render_id)
    await logger.ainfo("worker_task_start", render_id=render_id)

    log_collector = RenderLogCollector(render_id)
    log_collector.add("init", "Worker task started")

    workspace = None
    timeout = settings.render_timeout_seconds

    # Pre-flight checks
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
            await _mark_failed(
                session_factory,
                render_id,
                ErrorCode.NO_INPUT_DATA,
                "Render record has no stored composition",
                log_collector,
                workspace,
            )
            return

        from pathlib import Path

        input_path = Path(render.input_path)
        if not input_path.is_file():
            await _mark_failed(
                session_factory,
                render_id,
                ErrorCode.INPUT_FILE_MISSING,
                f"Input file not found: {input_path}",
                log_collector,
                workspace,
            )
            return

        from app.models.composition import Composition

        input_json = input_path.read_text(encoding="utf-8")
        composition = Composition.model_validate_json(input_json)

    # Pipeline execution with workspace lifecycle
    try:
        workspace = await workspace_mgr.create(render_id)
        log_collector.add("init", "Workspace created", extra={"path": str(workspace)})

        await _execute_pipeline(
            session_factory=session_factory,
            render_service=render_service,
            render_id=render_id,
            composition=composition,
            workspace=workspace,
            timeout=timeout,
            log_collector=log_collector,
        )

        # Flush logs before cleanup
        log_path = await log_collector.flush(workspace)
        if log_path is not None:
            async with session_factory() as session:
                await render_crud.update_render_paths(
                    session, render_id, log_path=str(log_path)
                )

        await workspace_mgr.cleanup_success(workspace)
        await logger.ainfo("worker_task_succeeded", render_id=render_id)

    except Exception as exc:
        error_code = _resolve_error_code(exc)
        error_message = str(exc)[:500]

        log_collector.add_error(
            "pipeline",
            f"Pipeline failed: {error_message}",
            extra={"error_code": error_code.value},
        )

        # Flush logs before marking failed
        if workspace is not None:
            await log_collector.flush(workspace)

        await _mark_failed(
            session_factory,
            render_id,
            error_code,
            error_message,
            log_collector,
            workspace,
        )

        if workspace is not None:
            await workspace_mgr.cleanup_failure(workspace)

    finally:
        structlog.contextvars.unbind_contextvars("render_id")


async def _execute_pipeline(
    *,
    session_factory: Any,
    render_service: RenderService,
    render_id: str,
    composition: Any,
    workspace: Any,
    timeout: int,
    log_collector: RenderLogCollector,
) -> None:
    """Drive all pipeline stages with status transitions and timeout."""

    async def _inner() -> None:
        # Stage 1: FETCHING - validate and expand
        async with session_factory() as session:
            await render_crud.update_render_status(
                session,
                render_id,
                RenderStatus.FETCHING,
                stage="validating",
                progress=5,
            )
        log_collector.add("fetching", "Status -> FETCHING")

        async with session_factory() as session:
            expanded = await render_service.stage_validate_and_expand(
                composition, render_id, workspace, session
            )
        log_collector.add("fetching", "Validation and expansion complete")

        # Stage 2: COMPILING - resolve assets and compile
        async with session_factory() as session:
            await render_crud.update_render_status(
                session,
                render_id,
                RenderStatus.COMPILING,
                stage="resolving_assets",
                progress=20,
            )
        log_collector.add("compiling", "Status -> COMPILING")

        async with session_factory() as session:
            compiled = await render_service.stage_resolve_and_compile(
                expanded, render_id, workspace, session
            )
        log_collector.add("compiling", "Compilation complete")

        # Stage 3: RENDERING - render video and store artifacts
        async with session_factory() as session:
            await render_crud.update_render_status(
                session,
                render_id,
                RenderStatus.RENDERING,
                stage="rendering",
                progress=50,
            )
        log_collector.add("rendering", "Status -> RENDERING")

        async with session_factory() as session:
            await render_service.stage_render_and_store(
                expanded, compiled, render_id, workspace, session
            )
        log_collector.add("rendering", "Render and store complete")

        # Stage 4: UPLOADING -> SUCCEEDED
        async with session_factory() as session:
            await render_crud.update_render_status(
                session,
                render_id,
                RenderStatus.UPLOADING,
                stage="finalizing",
                progress=90,
            )
        log_collector.add("uploading", "Status -> UPLOADING")

        async with session_factory() as session:
            await render_crud.update_render_status(
                session,
                render_id,
                RenderStatus.SUCCEEDED,
                stage="complete",
                progress=100,
            )
        log_collector.add("complete", "Status -> SUCCEEDED")

    await asyncio.wait_for(_inner(), timeout=timeout)


def _resolve_error_code(exc: Exception) -> ErrorCode:
    """Map an exception to a normalized error code."""
    if isinstance(exc, TimeoutError):
        return ErrorCode.RENDER_TIMEOUT
    if isinstance(exc, RenderServiceError):
        code_str = exc.error_code
        try:
            return ErrorCode(code_str)
        except ValueError:
            return (
                error_code_for_exception(exc.cause)
                if exc.cause
                else ErrorCode.WORKER_UNEXPECTED_ERROR
            )
    return error_code_for_exception(exc)


async def _mark_failed(
    session_factory: Any,
    render_id: str,
    error_code: ErrorCode,
    error_message: str,
    log_collector: RenderLogCollector,
    workspace: Any,
) -> None:
    """Transition render to FAILED status with error details."""
    log_collector.add_error("failed", f"{error_code.value}: {error_message}")

    async with session_factory() as session:
        render = await render_crud.get_render_by_id(session, render_id)
        if render is not None and not RenderStatus(render.status).is_terminal:
            await render_crud.update_render_status(
                session,
                render_id,
                RenderStatus.FAILED,
                error_code=error_code.value,
                error_message=error_message[:500],
                stage="failed",
            )

    await logger.aerror(
        "worker_task_failed",
        render_id=render_id,
        error_code=error_code.value,
    )


async def enqueue_render(pool: ArqRedis, render_id: str) -> None:
    """Enqueue a render job to ARQ for async processing."""
    await pool.enqueue_job("run_render", render_id)


async def worker_startup(ctx: dict[str, Any]) -> None:
    """ARQ on_startup hook: initialize DB engine and service dependencies."""

    from app.renderers.editly import EditlyRenderer
    from app.services.asset_service import AssetService
    from app.storage.local import LocalStorage

    settings = get_settings()

    engine = _get_engine()

    storage = LocalStorage(workspace_root=settings.render_workspace_root)
    asset_service = AssetService(settings=settings)
    renderer = EditlyRenderer(settings=settings)
    render_service = RenderService(
        storage=storage,
        asset_service=asset_service,
        renderer=renderer,
    )

    workspace_mgr = WorkspaceManager(workspace_root=settings.render_workspace_root)

    ctx["session_factory"] = _make_session_context_manager(engine)
    ctx["render_service"] = render_service
    ctx["workspace_manager"] = workspace_mgr

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
