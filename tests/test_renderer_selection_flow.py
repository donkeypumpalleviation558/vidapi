from __future__ import annotations

from copy import deepcopy
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from app.db import render_crud
from app.models.composition import Composition
from app.models.render import RenderStatus
from app.services.render_service import RenderService


async def _render_count(db_session) -> int:
    _items, total = await render_crud.list_renders(db_session)
    return total


@pytest.mark.asyncio
async def test_direct_render_without_renderer_persists_editly(
    client: AsyncClient,
    db_session,
    sample_composition: dict,
) -> None:
    response = await client.post("/v1/renders", json=sample_composition)

    assert response.status_code == 202
    render = await render_crud.get_render_by_id(db_session, response.json()["id"])
    assert render is not None
    assert render.renderer == "editly"


@pytest.mark.asyncio
async def test_direct_render_with_explicit_editly_persists_editly(
    client: AsyncClient,
    db_session,
    sample_composition: dict,
) -> None:
    payload = deepcopy(sample_composition)
    payload["renderer"] = "editly"

    response = await client.post("/v1/renders", json=payload)

    assert response.status_code == 202
    render = await render_crud.get_render_by_id(db_session, response.json()["id"])
    assert render is not None
    assert render.renderer == "editly"


@pytest.mark.asyncio
async def test_direct_render_rejects_unknown_renderer_without_record(
    client: AsyncClient,
    db_session,
    sample_composition: dict,
) -> None:
    payload = deepcopy(sample_composition)
    payload["renderer"] = "not-a-renderer"

    response = await client.post("/v1/renders", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "UNSUPPORTED_RENDERER"
    assert body["error"]["context"]["renderer"] == "not-a-renderer"
    assert await _render_count(db_session) == 0


@pytest.mark.asyncio
async def test_direct_render_rejects_unsupported_output_without_record_or_compile(
    client: AsyncClient,
    db_session,
    mock_renderer,
    sample_composition: dict,
) -> None:
    payload = deepcopy(sample_composition)
    payload["output"]["format"] = "webm"

    response = await client.post("/v1/renders", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "UNSUPPORTED_RENDERER_FEATURE"
    assert body["error"]["context"]["feature"] == "output.format"
    assert body["error"]["context"]["requested"] == "webm"
    assert await _render_count(db_session) == 0
    mock_renderer.compile.assert_not_awaited()


@pytest.mark.asyncio
async def test_render_service_revalidates_before_compile(
    db_session,
    render_service: RenderService,
    mock_renderer,
    sample_composition: dict,
) -> None:
    payload = deepcopy(sample_composition)
    payload["output"]["format"] = "gif"
    composition = Composition.model_validate(payload)

    render = await render_service.execute_render(composition, db_session)

    assert render.status == RenderStatus.FAILED.value
    assert render.error_code == "UNSUPPORTED_RENDERER_FEATURE"
    assert render.renderer == "editly"
    mock_renderer.compile.assert_not_awaited()


@pytest.mark.asyncio
async def test_render_service_resolves_explicit_editly(
    db_session,
    render_service: RenderService,
    mock_renderer,
    sample_composition: dict,
) -> None:
    payload = deepcopy(sample_composition)
    payload["renderer"] = "editly"
    composition = Composition.model_validate(payload)

    render = await render_service.execute_render(composition, db_session)

    assert render.renderer == "editly"
    assert isinstance(mock_renderer.compile, AsyncMock)
    mock_renderer.compile.assert_awaited_once()
