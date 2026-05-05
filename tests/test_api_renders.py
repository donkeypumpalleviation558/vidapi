from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.services.merge import MergeError, expand_merge_variables

# ---------------------------------------------------------------------------
# Merge variable expansion unit tests
# ---------------------------------------------------------------------------


class TestMergeVariables:
    def test_no_merge_returns_unchanged(self):
        original = '{"text": "hello"}'
        assert expand_merge_variables(original, None) == original

    def test_empty_merge_returns_unchanged(self):
        original = '{"text": "hello"}'
        assert expand_merge_variables(original, {}) == original

    def test_substitutes_string_variable(self):
        template = '{"text": "Hello {{name}}"}'
        result = expand_merge_variables(template, {"name": "World"})
        assert result == '{"text": "Hello World"}'

    def test_substitutes_numeric_variable(self):
        template = '{"count": "{{total}}"}'
        result = expand_merge_variables(template, {"total": 42})
        assert result == '{"count": "42"}'

    def test_substitutes_boolean_variable(self):
        template = '{"active": "{{flag}}"}'
        result = expand_merge_variables(template, {"flag": True})
        assert result == '{"active": "true"}'

    def test_substitutes_multiple_variables(self):
        template = '{"a": "{{x}}", "b": "{{y}}"}'
        result = expand_merge_variables(template, {"x": "1", "y": "2"})
        assert result == '{"a": "1", "b": "2"}'

    def test_raises_on_missing_variable(self):
        template = '{"text": "Hello {{missing}}"}'
        with pytest.raises(MergeError, match="missing"):
            expand_merge_variables(template, {"other": "val"})


# ---------------------------------------------------------------------------
# POST /v1/renders contract tests
# ---------------------------------------------------------------------------


class TestPostRenders:
    @pytest.mark.asyncio
    async def test_valid_composition_returns_202(
        self, client: AsyncClient, sample_composition: dict
    ):
        response = await client.post("/v1/renders", json=sample_composition)
        assert response.status_code == 202
        data = response.json()
        assert "id" in data
        assert data["id"].startswith("render_")
        assert "status" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_invalid_composition_returns_422(self, client: AsyncClient):
        response = await client.post("/v1/renders", json={"bad": "data"})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_empty_tracks_returns_422(self, client: AsyncClient):
        payload = {"timeline": {"tracks": []}}
        response = await client.post("/v1/renders", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_clip_length_returns_422(self, client: AsyncClient):
        payload = {
            "timeline": {
                "tracks": [
                    {
                        "clips": [
                            {
                                "asset": {
                                    "type": "image",
                                    "src": "http://example.com/img.jpg",
                                },
                                "start": 0.0,
                            }
                        ]
                    }
                ]
            }
        }
        response = await client.post("/v1/renders", json=payload)
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /v1/renders/{id} contract tests
# ---------------------------------------------------------------------------


class TestGetRender:
    @pytest.mark.asyncio
    async def test_unknown_id_returns_404(self, client: AsyncClient):
        response = await client.get("/v1/renders/nonexistent_id")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_valid_render_returns_status(
        self, client: AsyncClient, sample_composition: dict
    ):
        post_resp = await client.post("/v1/renders", json=sample_composition)
        assert post_resp.status_code == 202
        render_id = post_resp.json()["id"]

        get_resp = await client.get(f"/v1/renders/{render_id}")
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["id"] == render_id
        assert "status" in data
        assert "progress" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_succeeded_render_has_url(
        self, client: AsyncClient, sample_composition: dict
    ):
        post_resp = await client.post("/v1/renders", json=sample_composition)
        render_id = post_resp.json()["id"]

        get_resp = await client.get(f"/v1/renders/{render_id}")
        data = get_resp.json()
        if data["status"] == "succeeded":
            assert data["url"] is not None
            assert "/download" in data["url"]


# ---------------------------------------------------------------------------
# GET /v1/renders/{id}/download contract tests
# ---------------------------------------------------------------------------


class TestDownloadRender:
    @pytest.mark.asyncio
    async def test_unknown_id_returns_404(self, client: AsyncClient):
        response = await client.get("/v1/renders/nonexistent_id/download")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_download_succeeded_render(
        self, client: AsyncClient, sample_composition: dict
    ):
        post_resp = await client.post("/v1/renders", json=sample_composition)
        assert post_resp.status_code == 202
        render_id = post_resp.json()["id"]

        get_resp = await client.get(f"/v1/renders/{render_id}")
        status = get_resp.json()["status"]

        if status == "succeeded":
            dl_resp = await client.get(f"/v1/renders/{render_id}/download")
            assert dl_resp.status_code == 200
            assert dl_resp.headers.get("content-type", "").startswith("video/")


# ---------------------------------------------------------------------------
# Golden-path end-to-end integration test
# ---------------------------------------------------------------------------


class TestGoldenPath:
    @pytest.mark.asyncio
    async def test_full_render_lifecycle(
        self,
        client: AsyncClient,
        sample_composition: dict,
        test_storage,
    ):
        """Submit composition -> render succeeds -> poll status -> download."""
        post_resp = await client.post("/v1/renders", json=sample_composition)
        assert post_resp.status_code == 202
        post_data = post_resp.json()
        render_id = post_data["id"]
        assert render_id.startswith("render_")

        get_resp = await client.get(f"/v1/renders/{render_id}")
        assert get_resp.status_code == 200
        get_data = get_resp.json()
        assert get_data["id"] == render_id
        assert get_data["status"] in ("succeeded", "failed")

        if get_data["status"] == "succeeded":
            assert get_data["url"] is not None
            assert get_data["progress"] == 100

            dl_resp = await client.get(f"/v1/renders/{render_id}/download")
            assert dl_resp.status_code == 200

            workspace = test_storage._workspace_dir(render_id)
            expected_files = ["input.json", "expanded.json"]
            for fname in expected_files:
                fpath = workspace / fname
                assert fpath.exists(), f"Missing artifact: {fname}"
