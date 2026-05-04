from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Protocol, runtime_checkable


class ArtifactType(StrEnum):
    INPUT = "input.json"
    EXPANDED = "expanded.json"
    COMPILED = "compiled.json"
    OUTPUT = "output"
    POSTER = "poster.png"
    REPLAY = "replay.sh"
    LOG = "render.log"


@runtime_checkable
class StorageProtocol(Protocol):
    """Contract for render workspace storage backends."""

    async def create_workspace(self, render_id: str) -> Path:
        """Create a workspace directory for a render job.

        Returns the absolute path to the workspace root.
        Must be idempotent -- calling twice with the same ID returns the
        same path without error.
        """
        ...

    async def write_artifact(
        self,
        render_id: str,
        artifact_type: ArtifactType,
        data: bytes,
        *,
        suffix: str = "",
    ) -> Path:
        """Write an artifact to the render workspace.

        ``suffix`` overrides the file extension for ArtifactType.OUTPUT
        (e.g. ".mp4", ".gif").  Ignored for other artifact types.

        Returns the absolute path to the written file.
        """
        ...

    async def read_artifact(
        self,
        render_id: str,
        artifact_type: ArtifactType,
        *,
        suffix: str = "",
    ) -> bytes:
        """Read an artifact from the render workspace.

        Raises ``FileNotFoundError`` if the artifact does not exist.
        """
        ...

    async def list_artifacts(self, render_id: str) -> list[Path]:
        """Return absolute paths of all files in the render workspace."""
        ...

    async def workspace_path(self, render_id: str) -> Path:
        """Return the absolute workspace directory path for a render ID.

        Does NOT create the directory -- use ``create_workspace`` for that.
        """
        ...
