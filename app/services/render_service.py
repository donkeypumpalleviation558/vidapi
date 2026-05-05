from __future__ import annotations

from pathlib import Path

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import render_crud
from app.db.models import Render
from app.models.composition import (
    AudioAsset,
    Clip,
    Composition,
    ImageAsset,
    TextAsset,
    VideoAsset,
)
from app.models.render import RenderStatus
from app.renderers.base import CompileError, RenderError
from app.renderers.editly import EditlyRenderer
from app.renderers.poster import PosterError, generate_poster
from app.services.asset_service import AssetService
from app.services.merge import MergeError, expand_merge_variables
from app.storage.local import LocalStorage

logger = structlog.get_logger(__name__)


class RenderServiceError(Exception):
    """Top-level error from the render pipeline."""

    def __init__(
        self,
        message: str,
        *,
        error_code: str = "RENDER_PIPELINE_ERROR",
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.cause = cause


class RenderService:
    """Orchestrates the full render pipeline.

    Designed as a stateless service so the Phase 01 async worker can call
    ``execute_render()`` without changes to this class.
    """

    def __init__(
        self,
        storage: LocalStorage,
        asset_service: AssetService,
        renderer: EditlyRenderer,
    ) -> None:
        self._storage = storage
        self._asset_service = asset_service
        self._renderer = renderer

    async def execute_render(
        self,
        composition: Composition,
        session: AsyncSession,
    ) -> Render:
        """Run the full render pipeline for a composition.

        Pipeline stages:
        1. Create DB record, validate, expand merge variables
        2. Resolve assets, compile renderer spec
        3. Render video, generate poster, store artifacts
        4. Mark succeeded

        On failure at any stage, partial artifacts are persisted and the
        render is marked as failed with error details.
        """
        render = await render_crud.create_render(session)
        render_id = render.id

        structlog.contextvars.bind_contextvars(render_id=render_id)
        await logger.ainfo("render_pipeline_start", render_id=render_id)

        workspace: Path | None = None

        try:
            workspace = await self._storage.create_workspace(render_id)

            expanded_composition = await self._stage_validate_and_expand(
                composition,
                render_id,
                workspace,
                session,
            )

            compiled = await self._stage_resolve_and_compile(
                expanded_composition,
                render_id,
                workspace,
                session,
            )

            await self._stage_render_and_store(
                expanded_composition,
                compiled,
                render_id,
                workspace,
                session,
            )

            updated = await render_crud.update_render_status(
                session,
                render_id,
                RenderStatus.SUCCEEDED,
                stage="complete",
                progress=100,
            )
            if updated is not None:
                render = updated
            await logger.ainfo("render_pipeline_succeeded", render_id=render_id)

        except Exception as exc:
            await self._handle_failure(
                render_id,
                session,
                workspace,
                exc,
            )
            failed = await render_crud.get_render_by_id(session, render_id)
            if failed is not None:
                render = failed

        return render

    # ------------------------------------------------------------------
    # Stage 1: validate + merge + persist input artifacts
    # ------------------------------------------------------------------

    async def _stage_validate_and_expand(
        self,
        composition: Composition,
        render_id: str,
        workspace: Path,
        session: AsyncSession,
    ) -> Composition:
        await render_crud.update_render_status(
            session,
            render_id,
            RenderStatus.FETCHING,
            stage="validating",
            progress=5,
        )

        input_json = composition.model_dump_json(indent=2)
        input_path = workspace / "input.json"
        input_path.write_text(input_json, encoding="utf-8")
        await render_crud.update_render_paths(
            session,
            render_id,
            input_path=str(input_path),
        )

        try:
            expanded_json = expand_merge_variables(
                input_json,
                composition.merge,
            )
        except MergeError as exc:
            raise RenderServiceError(
                str(exc),
                error_code="MERGE_ERROR",
                cause=exc,
            ) from exc

        if expanded_json != input_json:
            expanded_composition = Composition.model_validate_json(expanded_json)
        else:
            expanded_composition = composition

        expanded_path = workspace / "expanded.json"
        expanded_path.write_text(
            expanded_composition.model_dump_json(indent=2),
            encoding="utf-8",
        )
        await render_crud.update_render_paths(
            session,
            render_id,
            expanded_path=str(expanded_path),
        )

        await logger.ainfo(
            "stage_validate_complete",
            render_id=render_id,
            progress=10,
        )
        return expanded_composition

    # ------------------------------------------------------------------
    # Stage 2: resolve assets + compile
    # ------------------------------------------------------------------

    async def _stage_resolve_and_compile(
        self,
        composition: Composition,
        render_id: str,
        workspace: Path,
        session: AsyncSession,
    ) -> object:
        await render_crud.update_render_status(
            session,
            render_id,
            RenderStatus.COMPILING,
            stage="resolving_assets",
            progress=20,
        )

        asset_map = await self._resolve_all_assets(composition, workspace)

        await render_crud.update_render_status(
            session,
            render_id,
            RenderStatus.COMPILING,
            stage="compiling",
            progress=30,
        )

        try:
            compiled = await self._renderer.compile(
                composition,
                workspace,
                render_id=render_id,
                asset_path_resolver=asset_map,
            )
        except CompileError as exc:
            raise RenderServiceError(
                str(exc),
                error_code="COMPILE_ERROR",
                cause=exc,
            ) from exc

        await render_crud.update_render_paths(
            session,
            render_id,
            compiled_path=str(compiled.spec_path),
            replay_path=str(compiled.replay_path),
            renderer=self._renderer.name,
        )

        await logger.ainfo(
            "stage_compile_complete",
            render_id=render_id,
            progress=40,
        )
        return compiled

    # ------------------------------------------------------------------
    # Stage 3: render + poster + store artifacts
    # ------------------------------------------------------------------

    async def _stage_render_and_store(
        self,
        composition: Composition,
        compiled: object,
        render_id: str,
        workspace: Path,
        session: AsyncSession,
    ) -> None:
        from app.renderers.base import CompiledRender

        compiled_render: CompiledRender = compiled  # type: ignore[assignment]

        await render_crud.update_render_status(
            session,
            render_id,
            RenderStatus.RENDERING,
            stage="rendering",
            progress=50,
        )

        try:
            artifact = await self._renderer.render(compiled_render)
        except RenderError as exc:
            raise RenderServiceError(
                str(exc),
                error_code="RENDER_ERROR",
                cause=exc,
            ) from exc

        await render_crud.update_render_paths(
            session,
            render_id,
            output_path=str(artifact.output_path),
            log_path=str(artifact.log_path),
        )

        await render_crud.update_render_status(
            session,
            render_id,
            RenderStatus.UPLOADING,
            stage="generating_poster",
            progress=85,
        )

        poster_path: Path | None = None
        try:
            poster_path = await generate_poster(
                artifact.output_path,
                workspace / "poster.jpg",
                video_duration=artifact.duration_seconds,
            )
        except PosterError:
            await logger.awarning(
                "poster_generation_failed_nonfatal",
                render_id=render_id,
            )

        if poster_path is not None:
            await render_crud.update_render_paths(
                session,
                render_id,
                poster_path=str(poster_path),
            )

        log_path = workspace / "logs.txt"
        if artifact.log_path.exists():
            log_content = artifact.log_path.read_text(
                encoding="utf-8", errors="replace"
            )
            log_path.write_text(log_content, encoding="utf-8")
            await render_crud.update_render_paths(
                session,
                render_id,
                log_path=str(log_path),
            )

        await logger.ainfo(
            "stage_render_complete",
            render_id=render_id,
            progress=95,
        )

    # ------------------------------------------------------------------
    # Asset resolution
    # ------------------------------------------------------------------

    async def _resolve_all_assets(
        self,
        composition: Composition,
        workspace: Path,
    ) -> dict[str, str]:
        """Walk all clips and resolve asset sources to local paths."""
        asset_map: dict[str, str] = {}

        for track in composition.timeline.tracks:
            for clip in track.clips:
                resolved = await self._resolve_clip_asset(clip, workspace)
                if resolved is not None:
                    src, local_path = resolved
                    asset_map[src] = local_path

        if composition.timeline.soundtrack is not None:
            src = composition.timeline.soundtrack.src
            resolved_asset = await self._asset_service.resolve_asset(
                src,
                workspace=workspace,
            )
            asset_map[src] = str(resolved_asset.local_path)

        return asset_map

    async def _resolve_clip_asset(
        self,
        clip: Clip,
        workspace: Path,
    ) -> tuple[str, str] | None:
        """Resolve a single clip's asset, returning (src, local_path) or None."""
        asset = clip.asset

        if isinstance(asset, (VideoAsset, ImageAsset, AudioAsset)):
            resolved = await self._asset_service.resolve_asset(
                asset.src,
                workspace=workspace,
            )
            return asset.src, str(resolved.local_path)

        if isinstance(asset, TextAsset):
            resolved = await self._asset_service.resolve_asset(
                "",
                text_asset=asset,
                workspace=workspace,
            )
            return "", str(resolved.local_path)

        return None

    # ------------------------------------------------------------------
    # Failure handling
    # ------------------------------------------------------------------

    async def _handle_failure(
        self,
        render_id: str,
        session: AsyncSession,
        workspace: Path | None,
        exc: Exception,
    ) -> None:
        """Persist partial artifacts and transition to failed status."""
        error_code = "RENDER_PIPELINE_ERROR"
        error_message = str(exc)

        if isinstance(exc, RenderServiceError):
            error_code = exc.error_code
            if exc.cause is not None:
                error_message = str(exc.cause)

        await logger.aerror(
            "render_pipeline_failed",
            render_id=render_id,
            error_code=error_code,
            error_message=error_message,
        )

        if workspace is not None and workspace.exists():
            log_path = workspace / "logs.txt"
            log_path.write_text(
                f"ERROR ({error_code}): {error_message}\n",
                encoding="utf-8",
            )
            await render_crud.update_render_paths(
                session,
                render_id,
                log_path=str(log_path),
            )

        try:
            render = await render_crud.get_render_by_id(session, render_id)
            if render is not None and not RenderStatus(render.status).is_terminal:
                await render_crud.update_render_status(
                    session,
                    render_id,
                    RenderStatus.FAILED,
                    error_code=error_code,
                    error_message=error_message[:500],
                    stage="failed",
                )
        except Exception:
            await logger.aerror(
                "failed_to_mark_render_as_failed",
                render_id=render_id,
            )
