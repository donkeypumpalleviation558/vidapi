from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.services.asset_service import AssetService
from app.storage.local import LocalStorage

SettingsDep = Annotated[Settings, Depends(get_settings)]


@lru_cache(maxsize=1)
def get_local_storage() -> LocalStorage:
    settings = get_settings()
    return LocalStorage(workspace_root=settings.render_workspace_root)


@lru_cache(maxsize=1)
def get_asset_service() -> AssetService:
    settings = get_settings()
    return AssetService(settings=settings)


StorageDep = Annotated[LocalStorage, Depends(get_local_storage)]
AssetServiceDep = Annotated[AssetService, Depends(get_asset_service)]
