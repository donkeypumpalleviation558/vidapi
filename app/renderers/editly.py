from __future__ import annotations

import asyncio
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import structlog

from app.core.config import Settings, get_settings
from app.models.composition import (
    AudioAsset,
    Clip,
    ColorAsset,
    Composition,
    FitMode,
    ImageAsset,
    TextAsset,
    Track,
    VideoAsset,
)
from app.renderers.base import (
    CompileError,
    CompiledRender,
    RenderArtifact,
    RenderError,
)

logger = structlog.get_logger(__name__)

EPSILON = 1e-6


# ---------------------------------------------------------------------------
# Data structures for segment compilation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ActiveClip:
    """A clip that is active during a segment, with its track z-order."""

    clip: Clip
    track_index: int
    clip_offset: float


@dataclass(frozen=True)
class Segment:
    """A non-overlapping time segment with its active clips."""

    start: float
    end: float
    active_clips: list[ActiveClip]

    @property
    def duration(self) -> float:
        return self.end - self.start


# ---------------------------------------------------------------------------
# Segment Compiler
# ---------------------------------------------------------------------------


def collect_boundaries(tracks: list[Track], total_duration: float) -> list[float]:
    """Walk all clips and collect sorted, deduplicated time boundaries."""
    boundaries: set[float] = {0.0, total_duration}

    for track in tracks:
        for clip in track.clips:
            boundaries.add(clip.start)
            boundaries.add(clip.start + clip.length)

    sorted_bounds = sorted(boundaries)
    return _deduplicate_boundaries(sorted_bounds)


def _deduplicate_boundaries(boundaries: list[float]) -> list[float]:
    """Remove boundaries that differ by less than EPSILON."""
    if not boundaries:
        return []

    result: list[float] = [boundaries[0]]
    for b in boundaries[1:]:
        if b - result[-1] > EPSILON:
            result.append(b)
    return result


def generate_segments(
    boundaries: list[float],
    tracks: list[Track],
) -> list[Segment]:
    """Convert sorted boundaries into non-overlapping segments with active clips.

    Tracks are indexed from 0 (bottom/background) to N-1 (top/foreground).
    Active clips within each segment are ordered by track_index ascending
    so that higher-index tracks layer on top.
    """
    segments: list[Segment] = []

    for i in range(len(boundaries) - 1):
        seg_start = boundaries[i]
        seg_end = boundaries[i + 1]

        if seg_end - seg_start < EPSILON:
            continue

        active_clips: list[ActiveClip] = []

        for track_index, track in enumerate(tracks):
            for clip in track.clips:
                clip_start = clip.start
                clip_end = clip.start + clip.length

                if clip_start < seg_end - EPSILON and clip_end > seg_start + EPSILON:
                    offset = seg_start - clip_start
                    active_clips.append(
                        ActiveClip(
                            clip=clip,
                            track_index=track_index,
                            clip_offset=offset,
                        )
                    )

        active_clips.sort(key=lambda ac: ac.track_index)
        segments.append(Segment(start=seg_start, end=seg_end, active_clips=active_clips))

    return segments


def compute_total_duration(tracks: list[Track]) -> float:
    """Compute the total timeline duration from all clips."""
    max_end = 0.0
    for track in tracks:
        for clip in track.clips:
            end = clip.start + clip.length
            if end > max_end:
                max_end = end
    return max_end


# ---------------------------------------------------------------------------
# Layer Mapper
# ---------------------------------------------------------------------------


def _fit_mode_to_resize(fit: FitMode) -> str | None:
    """Translate VidAPI fit mode to Editly resizeMode."""
    mapping = {
        FitMode.COVER: "cover",
        FitMode.CONTAIN: "contain",
        FitMode.STRETCH: "stretch",
        FitMode.NONE: None,
    }
    return mapping.get(fit)


def map_video_layer(clip: Clip, active_clip: ActiveClip) -> dict:
    """Map a video asset clip to an Editly layer."""
    asset: VideoAsset = clip.asset  # type: ignore[assignment]
    layer: dict = {
        "type": "video",
        "path": asset.src,
    }

    resize_mode = _fit_mode_to_resize(clip.fit)
    if resize_mode is not None:
        layer["resizeMode"] = resize_mode

    if asset.trim is not None or active_clip.clip_offset > EPSILON:
        cut_from = (asset.trim or 0.0) + active_clip.clip_offset
        layer["cutFrom"] = round(cut_from, 6)
        layer["cutTo"] = round(cut_from + (active_clip.clip.length - active_clip.clip_offset), 6)
    elif active_clip.clip_offset > EPSILON:
        layer["cutFrom"] = round(active_clip.clip_offset, 6)

    if asset.volume < 1.0 - EPSILON:
        layer["mixVolume"] = asset.volume

    return layer


def map_image_layer(clip: Clip) -> dict:
    """Map an image asset clip to an Editly image-overlay layer."""
    asset: ImageAsset = clip.asset  # type: ignore[assignment]
    layer: dict = {
        "type": "image-overlay",
        "path": asset.src,
    }

    resize_mode = _fit_mode_to_resize(clip.fit)
    if resize_mode is not None:
        layer["resizeMode"] = resize_mode

    return layer


def map_text_png_layer(clip: Clip) -> dict:
    """Map a text asset (pre-rendered to PNG) to an Editly image-overlay layer.

    The text_renderer from Session 03 produces a PNG path that we reference here.
    The actual path resolution happens during compile when asset paths are resolved.
    """
    layer: dict = {
        "type": "image-overlay",
        "path": "",
    }
    return layer


def map_color_layer(clip: Clip) -> dict:
    """Map a color asset to an Editly fill-color background layer."""
    asset: ColorAsset = clip.asset  # type: ignore[assignment]
    layer: dict = {
        "type": "fill-color",
        "color": asset.color,
    }
    return layer


def map_clip_to_layer(clip: Clip, active_clip: ActiveClip) -> dict | None:
    """Route a clip to the appropriate layer mapper based on asset type."""
    asset = clip.asset

    if isinstance(asset, VideoAsset):
        return map_video_layer(clip, active_clip)
    elif isinstance(asset, ImageAsset):
        return map_image_layer(clip)
    elif isinstance(asset, TextAsset):
        return map_text_png_layer(clip)
    elif isinstance(asset, ColorAsset):
        return map_color_layer(clip)
    elif isinstance(asset, AudioAsset):
        return None

    return None


# ---------------------------------------------------------------------------
# Audio / Soundtrack Mapper
# ---------------------------------------------------------------------------


def map_soundtrack(soundtrack: AudioAsset | None) -> list[dict]:
    """Map VidAPI soundtrack to Editly audioTracks."""
    if soundtrack is None:
        return []

    track: dict = {
        "path": soundtrack.src,
    }

    if soundtrack.volume < 1.0 - EPSILON:
        track["mixVolume"] = soundtrack.volume

    if soundtrack.effect is not None:
        track["mixVolume"] = soundtrack.volume
        if soundtrack.effect.value == "fadeIn":
            track["cutFrom"] = 0
        elif soundtrack.effect.value == "fadeOut":
            pass

    return [track]


# ---------------------------------------------------------------------------
# Editly Spec Assembler
# ---------------------------------------------------------------------------


def assemble_editly_spec(
    segments: list[Segment],
    composition: Composition,
    output_path: str,
    *,
    asset_path_resolver: dict[str, str] | None = None,
) -> dict:
    """Assemble the full Editly JSON spec from segments and composition settings."""
    clips: list[dict] = []

    for segment in segments:
        if not segment.active_clips:
            clips.append({
                "duration": round(segment.duration, 6),
                "layers": [{"type": "fill-color", "color": composition.timeline.background}],
            })
            continue

        layers: list[dict] = []
        for active_clip in segment.active_clips:
            layer = map_clip_to_layer(active_clip.clip, active_clip)
            if layer is None:
                continue

            if asset_path_resolver and "path" in layer and layer["path"]:
                resolved = asset_path_resolver.get(layer["path"])
                if resolved:
                    layer["path"] = resolved

            layers.append(layer)

        if not layers:
            layers = [{"type": "fill-color", "color": composition.timeline.background}]

        clips.append({
            "duration": round(segment.duration, 6),
            "layers": layers,
        })

    spec: dict = {
        "width": composition.output.width,
        "height": composition.output.height,
        "fps": composition.output.fps,
        "outPath": output_path,
        "clips": clips,
        "allowRemoteRequests": False,
    }

    settings = get_settings()
    if settings.editly_fast_mode:
        spec["fast"] = True

    audio_tracks = map_soundtrack(composition.timeline.soundtrack)
    if audio_tracks:
        spec["audioTracks"] = audio_tracks

    return spec


def serialize_spec(spec: dict) -> str:
    """Deterministic JSON serialization for compiled Editly specs."""
    return json.dumps(spec, sort_keys=True, indent=2, ensure_ascii=True)


# ---------------------------------------------------------------------------
# Replay Metadata
# ---------------------------------------------------------------------------


def generate_replay_metadata(
    spec_path: Path,
    output_path: Path,
    workspace: Path,
    *,
    settings: Settings | None = None,
) -> dict:
    """Capture Editly executable path, args, env, and paths for manual re-run."""
    if settings is None:
        settings = get_settings()

    return {
        "renderer": "editly",
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "command": settings.editly_bin,
        "args": ["--json", str(spec_path)],
        "environment": {
            "PATH": os.environ.get("PATH", ""),
            "NODE_PATH": os.environ.get("NODE_PATH", ""),
        },
        "input_spec": str(spec_path),
        "output_path": str(output_path),
        "workspace": str(workspace),
        "timeout_seconds": settings.editly_timeout_seconds,
    }


# ---------------------------------------------------------------------------
# Error Classification
# ---------------------------------------------------------------------------


class EditlyRenderError(RenderError):
    """Structured error from Editly render subprocess."""

    def __init__(
        self,
        message: str,
        *,
        exit_code: int | None = None,
        error_type: str = "unknown",
        stderr: str = "",
    ) -> None:
        super().__init__(message, exit_code=exit_code)
        self.error_type = error_type
        self.stderr = stderr


def classify_render_error(
    *,
    exit_code: int | None,
    stderr: str,
    timed_out: bool,
    output_exists: bool,
) -> EditlyRenderError:
    """Map render failure conditions to structured error types."""
    if timed_out:
        return EditlyRenderError(
            "Render timed out",
            exit_code=exit_code,
            error_type="timeout",
            stderr=stderr,
        )

    if exit_code is not None and exit_code != 0:
        if "ENOENT" in stderr or "not found" in stderr.lower():
            return EditlyRenderError(
                "Editly binary not found or input file missing",
                exit_code=exit_code,
                error_type="not_found",
                stderr=stderr,
            )
        if "out of memory" in stderr.lower() or "ENOMEM" in stderr:
            return EditlyRenderError(
                "Render ran out of memory",
                exit_code=exit_code,
                error_type="oom",
                stderr=stderr,
            )
        return EditlyRenderError(
            f"Editly exited with code {exit_code}",
            exit_code=exit_code,
            error_type="exit_error",
            stderr=stderr,
        )

    if not output_exists:
        return EditlyRenderError(
            "Render completed but output file not found",
            exit_code=exit_code,
            error_type="missing_output",
            stderr=stderr,
        )

    return EditlyRenderError(
        "Unknown render failure",
        exit_code=exit_code,
        error_type="unknown",
        stderr=stderr,
    )


# ---------------------------------------------------------------------------
# EditlyRenderer
# ---------------------------------------------------------------------------


class EditlyRenderer:
    """Renderer backend using Editly (Node.js) subprocess."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    @property
    def name(self) -> str:
        return "editly"

    async def compile(
        self,
        composition: Composition,
        workspace: Path,
        *,
        render_id: str,
        asset_path_resolver: dict[str, str] | None = None,
    ) -> CompiledRender:
        """Transform a VidAPI Composition into an Editly JSON spec."""
        workspace.mkdir(parents=True, exist_ok=True)

        total_duration = compute_total_duration(composition.timeline.tracks)
        if total_duration < EPSILON:
            raise CompileError("Composition has zero duration")

        boundaries = collect_boundaries(
            composition.timeline.tracks, total_duration
        )
        segments = generate_segments(boundaries, composition.timeline.tracks)

        if not segments:
            raise CompileError("No segments generated from composition")

        output_filename = f"{render_id}.mp4"
        output_path = str(workspace / output_filename)

        spec = assemble_editly_spec(
            segments,
            composition,
            output_path,
            asset_path_resolver=asset_path_resolver,
        )

        spec_json = serialize_spec(spec)

        spec_path = workspace / "compiled.editly.json"
        spec_path.write_text(spec_json, encoding="ascii")

        replay_meta = generate_replay_metadata(
            spec_path,
            Path(output_path),
            workspace,
            settings=self._settings,
        )
        replay_path = workspace / "replay.json"
        replay_path.write_text(
            json.dumps(replay_meta, sort_keys=True, indent=2, ensure_ascii=True),
            encoding="ascii",
        )

        logger.info(
            "editly_compile_complete",
            render_id=render_id,
            segments=len(segments),
            spec_path=str(spec_path),
        )

        return CompiledRender(
            spec_path=spec_path,
            replay_path=replay_path,
            workspace=workspace,
            renderer_name=self.name,
            spec_json=spec_json,
        )

    async def render(
        self,
        compiled: CompiledRender,
        *,
        timeout_seconds: int | None = None,
    ) -> RenderArtifact:
        """Invoke Editly subprocess and produce output artifacts."""
        if timeout_seconds is None:
            timeout_seconds = self._settings.editly_timeout_seconds

        spec_data = json.loads(compiled.spec_json)
        output_path = Path(spec_data["outPath"])
        log_path = compiled.workspace / "render.log"

        cmd = [self._settings.editly_bin, "--json", str(compiled.spec_path)]

        start_time = time.monotonic()
        timed_out = False
        exit_code: int | None = None
        stderr_text = ""

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(compiled.workspace),
            )
            try:
                _stdout, stderr_bytes = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout_seconds,
                )
                exit_code = proc.returncode
                stderr_text = stderr_bytes.decode(errors="replace")
            except TimeoutError:
                timed_out = True
                proc.kill()
                await proc.wait()
                exit_code = proc.returncode
                stderr_text = "TIMEOUT: Process killed after exceeding time limit"

        except FileNotFoundError:
            timed_out = False
            exit_code = 127
            stderr_text = (
                f"Editly binary not found: {self._settings.editly_bin}. "
                "Ensure Node.js and Editly are installed."
            )

        elapsed = time.monotonic() - start_time

        log_path.write_text(stderr_text, encoding="utf-8")

        output_exists = output_path.is_file()

        if timed_out or (exit_code is not None and exit_code != 0) or not output_exists:
            error = classify_render_error(
                exit_code=exit_code,
                stderr=stderr_text,
                timed_out=timed_out,
                output_exists=output_exists,
            )
            logger.error(
                "editly_render_failed",
                error_type=error.error_type,
                exit_code=exit_code,
                elapsed=round(elapsed, 2),
            )
            raise error

        logger.info(
            "editly_render_complete",
            output_path=str(output_path),
            elapsed=round(elapsed, 2),
        )

        return RenderArtifact(
            output_path=output_path,
            poster_path=None,
            log_path=log_path,
            duration_seconds=round(elapsed, 3),
            exit_code=exit_code or 0,
        )
