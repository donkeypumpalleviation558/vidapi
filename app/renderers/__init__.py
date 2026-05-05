from __future__ import annotations

from app.renderers.base import (
    CompileError,
    CompiledRender,
    RenderArtifact,
    RenderError,
    RendererProtocol,
)
from app.renderers.editly import EditlyRenderer
from app.renderers.poster import PosterError, generate_poster

_RENDERER_REGISTRY: dict[str, type] = {
    "editly": EditlyRenderer,
}


def get_renderer(name: str | None = None) -> RendererProtocol:
    """Resolve a renderer by name. Defaults to editly for MVP."""
    if name is None or name == "auto":
        name = "editly"

    renderer_cls = _RENDERER_REGISTRY.get(name)
    if renderer_cls is None:
        raise ValueError(f"Unknown renderer: {name!r}. Available: {list(_RENDERER_REGISTRY)}")

    return renderer_cls()  # type: ignore[return-value]


__all__ = [
    "CompileError",
    "CompiledRender",
    "EditlyRenderer",
    "PosterError",
    "RenderArtifact",
    "RenderError",
    "RendererProtocol",
    "generate_poster",
    "get_renderer",
]
