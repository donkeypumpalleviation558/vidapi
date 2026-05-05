from __future__ import annotations

import asyncio
import shutil
from pathlib import Path

import structlog

from app.core.config import get_settings

logger = structlog.get_logger(__name__)

PRESERVE_ON_FAILURE = {
    "input.json",
    "expanded.json",
    "logs.txt",
    "compiled.editly.json",
}


class WorkspaceManager:
    """Manages per-render workspace lifecycle with guaranteed cleanup.

    Each render gets an isolated directory under the configured workspace root.
    After artifacts are persisted, temp files are removed. On failure, diagnostic
    files (input, logs, compiled spec) are preserved for debugging.
    """

    def __init__(self, workspace_root: Path) -> None:
        self._root = workspace_root.resolve()

    async def create(self, render_id: str) -> Path:
        """Create an isolated workspace directory for a render job.

        If the directory already exists (e.g. from a previous attempt),
        it is removed and recreated to ensure a clean state.
        """
        ws = self._root / render_id
        if ws.exists():
            await asyncio.to_thread(shutil.rmtree, ws, ignore_errors=True)
        await asyncio.to_thread(ws.mkdir, parents=True, exist_ok=True)
        await logger.ainfo("workspace_created", render_id=render_id, path=str(ws))
        return ws

    async def cleanup_success(self, workspace: Path) -> None:
        """Remove the entire workspace after successful artifact persistence."""
        settings = get_settings()
        if not settings.workspace_cleanup_enabled:
            await logger.ainfo(
                "workspace_cleanup_skipped_disabled", path=str(workspace)
            )
            return

        try:
            await asyncio.to_thread(shutil.rmtree, workspace, ignore_errors=True)
            await logger.ainfo("workspace_cleanup_success", path=str(workspace))
        except Exception as exc:
            await logger.awarning(
                "workspace_cleanup_error",
                path=str(workspace),
                error=str(exc),
            )

    async def cleanup_failure(self, workspace: Path) -> None:
        """Partial cleanup on failure: remove temp files, keep diagnostics."""
        settings = get_settings()
        if not settings.workspace_cleanup_enabled:
            await logger.ainfo(
                "workspace_cleanup_skipped_disabled", path=str(workspace)
            )
            return

        if not settings.workspace_cleanup_keep_on_failure:
            await self.cleanup_success(workspace)
            return

        if not workspace.exists():
            return

        try:
            entries = await asyncio.to_thread(list, workspace.iterdir())
            for entry in entries:
                if entry.name not in PRESERVE_ON_FAILURE:
                    if entry.is_dir():
                        await asyncio.to_thread(
                            shutil.rmtree, entry, ignore_errors=True
                        )
                    else:
                        await asyncio.to_thread(entry.unlink, missing_ok=True)
            await logger.ainfo(
                "workspace_cleanup_failure_partial",
                path=str(workspace),
                preserved=[e.name for e in workspace.iterdir() if e.exists()],
            )
        except Exception as exc:
            await logger.awarning(
                "workspace_cleanup_error",
                path=str(workspace),
                error=str(exc),
            )
