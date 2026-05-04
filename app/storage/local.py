from __future__ import annotations

import asyncio
import contextlib
from pathlib import Path

import structlog

from app.api.errors import StorageError
from app.storage.base import ArtifactType

logger = structlog.get_logger(__name__)


class LocalStorage:
    """Local filesystem storage adapter for render workspaces.

    Workspace paths are deterministic: ``<root>/<render_id>/``.
    """

    def __init__(self, workspace_root: Path) -> None:
        self._root = workspace_root.resolve()

    async def create_workspace(self, render_id: str) -> Path:
        ws = self._workspace_dir(render_id)
        try:
            await asyncio.to_thread(ws.mkdir, parents=True, exist_ok=True)
        except OSError as exc:
            raise StorageError(
                detail=f"Failed to create workspace for {render_id}",
                context={"render_id": render_id, "path": str(ws)},
            ) from exc
        logger.info(
            "workspace_created",
            render_id=render_id,
            path=str(ws),
        )
        return ws

    async def write_artifact(
        self,
        render_id: str,
        artifact_type: ArtifactType,
        data: bytes,
        *,
        suffix: str = "",
    ) -> Path:
        ws = self._workspace_dir(render_id)
        if not ws.exists():
            raise StorageError(
                detail=f"Workspace does not exist for {render_id}",
                context={"render_id": render_id},
            )
        dest = self._artifact_path(ws, artifact_type, suffix)
        tmp = dest.with_suffix(dest.suffix + ".tmp")
        try:
            await asyncio.to_thread(tmp.write_bytes, data)
            await asyncio.to_thread(tmp.replace, dest)
        except OSError as exc:
            with contextlib.suppress(OSError):
                await asyncio.to_thread(tmp.unlink, missing_ok=True)
            raise StorageError(
                detail=f"Failed to write artifact {artifact_type.value}",
                context={
                    "render_id": render_id,
                    "artifact": artifact_type.value,
                },
            ) from exc
        logger.debug(
            "artifact_written",
            render_id=render_id,
            artifact=artifact_type.value,
            size=len(data),
        )
        return dest

    async def read_artifact(
        self,
        render_id: str,
        artifact_type: ArtifactType,
        *,
        suffix: str = "",
    ) -> bytes:
        ws = self._workspace_dir(render_id)
        dest = self._artifact_path(ws, artifact_type, suffix)
        try:
            return await asyncio.to_thread(dest.read_bytes)
        except FileNotFoundError:
            raise
        except OSError as exc:
            raise StorageError(
                detail=f"Failed to read artifact {artifact_type.value}",
                context={
                    "render_id": render_id,
                    "artifact": artifact_type.value,
                },
            ) from exc

    async def list_artifacts(self, render_id: str) -> list[Path]:
        ws = self._workspace_dir(render_id)
        if not ws.exists():
            return []
        try:
            return await asyncio.to_thread(
                lambda: sorted(p for p in ws.iterdir() if p.is_file()),
            )
        except OSError as exc:
            raise StorageError(
                detail=f"Failed to list artifacts for {render_id}",
                context={"render_id": render_id},
            ) from exc

    async def workspace_path(self, render_id: str) -> Path:
        return self._workspace_dir(render_id)

    def _workspace_dir(self, render_id: str) -> Path:
        return self._root / render_id

    @staticmethod
    def _artifact_path(
        ws: Path,
        artifact_type: ArtifactType,
        suffix: str,
    ) -> Path:
        if artifact_type is ArtifactType.OUTPUT and suffix:
            return ws / f"output{suffix}"
        return ws / artifact_type.value
