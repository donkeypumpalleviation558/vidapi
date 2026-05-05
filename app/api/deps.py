from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from arq.connections import ArqRedis
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.redis import get_arq_pool
from app.db.session import get_session
from app.renderers.editly import EditlyRenderer
from app.services.asset_service import AssetService
from app.services.render_service import RenderService
from app.services.template_service import TemplateService
from app.storage.local import LocalStorage

SettingsDep = Annotated[Settings, Depends(get_settings)]
DBSessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_arq_pool_dep() -> ArqRedis | None:
    """Dependency that provides the ARQ Redis pool for routes.

    Returns None when RENDER_MODE=sync to avoid requiring Redis.
    """
    settings = get_settings()
    if settings.render_mode != "async":
        return None
    return await get_arq_pool()


ArqPoolDep = Annotated[ArqRedis | None, Depends(get_arq_pool_dep)]


@lru_cache(maxsize=1)
def get_local_storage() -> LocalStorage:
    settings = get_settings()
    return LocalStorage(workspace_root=settings.render_workspace_root)


@lru_cache(maxsize=1)
def get_asset_service() -> AssetService:
    settings = get_settings()
    return AssetService(settings=settings)


@lru_cache(maxsize=1)
def get_editly_renderer() -> EditlyRenderer:
    settings = get_settings()
    return EditlyRenderer(settings=settings)


@lru_cache(maxsize=1)
def get_render_service() -> RenderService:
    return RenderService(
        storage=get_local_storage(),
        asset_service=get_asset_service(),
        renderer=get_editly_renderer(),
    )


@lru_cache(maxsize=1)
def get_template_service() -> TemplateService:
    return TemplateService()


TemplateServiceDep = Annotated[TemplateService, Depends(get_template_service)]
StorageDep = Annotated[LocalStorage, Depends(get_local_storage)]
AssetServiceDep = Annotated[AssetService, Depends(get_asset_service)]
EditlyRendererDep = Annotated[EditlyRenderer, Depends(get_editly_renderer)]
RenderServiceDep = Annotated[RenderService, Depends(get_render_service)]
