from __future__ import annotations

from pathlib import Path

import structlog
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from app.api.deps import DBSessionDep, RenderServiceDep
from app.db import render_crud
from app.models.composition import Composition
from app.models.render import (
    CreateRenderResponse,
    RenderError as RenderErrorModel,
    RenderResponse,
    RenderStatus,
)

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["renders"])


@router.post(
    "/renders",
    response_model=CreateRenderResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_render(
    composition: Composition,
    render_service: RenderServiceDep,
    session: DBSessionDep,
) -> CreateRenderResponse:
    """Accept a composition and start rendering.

    Returns 202 Accepted with the render ID. In Phase 00 the render
    executes synchronously but the response shape matches the future
    async contract.
    """
    render = await render_service.execute_render(composition, session)
    return CreateRenderResponse(
        id=render.id,
        status=RenderStatus(render.status),
        progress=render.progress,
        created_at=render.created_at,
    )


@router.get(
    "/renders/{render_id}",
    response_model=RenderResponse,
)
async def get_render(
    render_id: str,
    session: DBSessionDep,
) -> RenderResponse:
    """Return full render status."""
    render = await render_crud.get_render_by_id(session, render_id)
    if render is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Render {render_id} not found",
        )

    render_status = RenderStatus(render.status)

    error: RenderErrorModel | None = None
    if render.error_code is not None:
        error = RenderErrorModel(
            code=render.error_code,
            message=render.error_message or "Unknown error",
        )

    url: str | None = None
    if render_status == RenderStatus.SUCCEEDED and render.output_path:
        url = f"/v1/renders/{render.id}/download"

    poster: str | None = None
    if render.poster_path:
        poster = f"/v1/renders/{render.id}/poster"

    return RenderResponse(
        id=render.id,
        status=render_status,
        stage=render.stage,
        progress=render.progress,
        url=url,
        poster=poster,
        created_at=render.created_at,
        started_at=render.started_at,
        completed_at=render.completed_at,
        error=error,
    )


@router.get("/renders/{render_id}/download")
async def download_render(
    render_id: str,
    session: DBSessionDep,
) -> FileResponse:
    """Stream the rendered output file."""
    render = await render_crud.get_render_by_id(session, render_id)
    if render is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Render {render_id} not found",
        )

    render_status = RenderStatus(render.status)
    if render_status != RenderStatus.SUCCEEDED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Render {render_id} is not complete (status: {render_status.value})",
        )

    if not render.output_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No output file for render {render_id}",
        )

    output_path = Path(render.output_path)
    if not output_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Output file missing for render {render_id}",
        )

    return FileResponse(
        path=output_path,
        media_type="video/mp4",
        filename=f"{render_id}.mp4",
    )
