from __future__ import annotations

from app.renderers.base import (
    CompiledRender,
    CompileError,
    RenderArtifact,
    RendererProtocol,
    RenderError,
)
from app.renderers.editly import EditlyRenderer
from app.renderers.poster import PosterError, generate_poster

_RENDERER_REGISTRY: dict[str, type[RendererProtocol]] = {
    "editly": EditlyRenderer,
}


def get_renderer(name: str | None = None) -> RendererProtocol:
    """Resolve a renderer by name. Defaults to editly for MVP."""
    if name is None or name == "auto":
        name = "editly"

    renderer_cls = _RENDERER_REGISTRY.get(name)
    if renderer_cls is None:
        raise ValueError(
            f"Unknown renderer: {name!r}. Available: {list(_RENDERER_REGISTRY)}"
        )

    return renderer_cls()


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
