from __future__ import annotations

from pathlib import Path

import pytest

from app.api.errors import StorageError
from app.storage.base import ArtifactType
from app.storage.local import LocalStorage


@pytest.fixture
def storage(tmp_path: Path) -> LocalStorage:
    return LocalStorage(workspace_root=tmp_path)


RENDER_ID = "render_test123"


class TestWorkspaceLifecycle:
    """Storage adapter workspace create/read/write/list cycle."""

    @pytest.mark.asyncio
    async def test_create_workspace_returns_path(
        self,
        storage: LocalStorage,
        tmp_path: Path,
    ) -> None:
        ws = await storage.create_workspace(RENDER_ID)
        assert ws.exists()
        assert ws.is_dir()
        assert ws == (tmp_path / RENDER_ID).resolve()

    @pytest.mark.asyncio
    async def test_create_workspace_idempotent(
        self,
        storage: LocalStorage,
    ) -> None:
        ws1 = await storage.create_workspace(RENDER_ID)
        ws2 = await storage.create_workspace(RENDER_ID)
        assert ws1 == ws2

    @pytest.mark.asyncio
    async def test_workspace_path_without_create(
        self,
        storage: LocalStorage,
        tmp_path: Path,
    ) -> None:
        ws = await storage.workspace_path(RENDER_ID)
        assert ws == (tmp_path / RENDER_ID).resolve()
        assert not ws.exists()


class TestArtifactWriteRead:
    """Write and read back each artifact type."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("artifact_type", list(ArtifactType))
    async def test_write_and_read_artifact(
        self,
        storage: LocalStorage,
        artifact_type: ArtifactType,
    ) -> None:
        await storage.create_workspace(RENDER_ID)
        data = b'{"test": true}'
        suffix = ".mp4" if artifact_type is ArtifactType.OUTPUT else ""

        path = await storage.write_artifact(
            RENDER_ID,
            artifact_type,
            data,
            suffix=suffix,
        )
        assert path.exists()

        read_back = await storage.read_artifact(
            RENDER_ID,
            artifact_type,
            suffix=suffix,
        )
        assert read_back == data

    @pytest.mark.asyncio
    async def test_write_artifact_without_workspace_raises(
        self,
        storage: LocalStorage,
    ) -> None:
        with pytest.raises(StorageError, match="does not exist"):
            await storage.write_artifact(
                "nonexistent_render",
                ArtifactType.INPUT,
                b"data",
            )

    @pytest.mark.asyncio
    async def test_read_missing_artifact_raises_file_not_found(
        self,
        storage: LocalStorage,
    ) -> None:
        await storage.create_workspace(RENDER_ID)
        with pytest.raises(FileNotFoundError):
            await storage.read_artifact(RENDER_ID, ArtifactType.INPUT)

    @pytest.mark.asyncio
    async def test_output_artifact_with_suffix(
        self,
        storage: LocalStorage,
    ) -> None:
        await storage.create_workspace(RENDER_ID)
        data = b"\x00\x00\x00"

        path = await storage.write_artifact(
            RENDER_ID,
            ArtifactType.OUTPUT,
            data,
            suffix=".gif",
        )
        assert path.name == "output.gif"

        read_back = await storage.read_artifact(
            RENDER_ID,
            ArtifactType.OUTPUT,
            suffix=".gif",
        )
        assert read_back == data


class TestArtifactList:
    """List artifacts in a workspace."""

    @pytest.mark.asyncio
    async def test_list_artifacts_empty_workspace(
        self,
        storage: LocalStorage,
    ) -> None:
        await storage.create_workspace(RENDER_ID)
        artifacts = await storage.list_artifacts(RENDER_ID)
        assert artifacts == []

    @pytest.mark.asyncio
    async def test_list_artifacts_with_files(
        self,
        storage: LocalStorage,
    ) -> None:
        await storage.create_workspace(RENDER_ID)
        await storage.write_artifact(
            RENDER_ID,
            ArtifactType.INPUT,
            b'{"timeline": {}}',
        )
        await storage.write_artifact(
            RENDER_ID,
            ArtifactType.LOG,
            b"render log content",
        )

        artifacts = await storage.list_artifacts(RENDER_ID)
        names = {a.name for a in artifacts}
        assert "input.json" in names
        assert "render.log" in names

    @pytest.mark.asyncio
    async def test_list_artifacts_nonexistent_workspace(
        self,
        storage: LocalStorage,
    ) -> None:
        artifacts = await storage.list_artifacts("does_not_exist")
        assert artifacts == []


class TestDeterministicPaths:
    """Paths are deterministic from render ID."""

    @pytest.mark.asyncio
    async def test_same_id_same_path(
        self,
        storage: LocalStorage,
    ) -> None:
        p1 = await storage.workspace_path("render_abc")
        p2 = await storage.workspace_path("render_abc")
        assert p1 == p2

    @pytest.mark.asyncio
    async def test_different_ids_different_paths(
        self,
        storage: LocalStorage,
    ) -> None:
        p1 = await storage.workspace_path("render_abc")
        p2 = await storage.workspace_path("render_xyz")
        assert p1 != p2
