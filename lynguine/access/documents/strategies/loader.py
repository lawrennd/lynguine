"""Load YAML strategy configs into ``YamlStrategy`` adapters (CIP-0013)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from ..engines import get_engine
from ..errors import DocumentSegmentError
from ..model import Document
from ..unit import Unit

REQUIRED_KEYS = ("id", "aspects", "engine")


@dataclass(frozen=True)
class StrategySpec:
    """Parsed YAML strategy definition."""

    id: str
    aspects: tuple[str, ...]
    engine: str
    grain: str | None
    recogniser: dict[str, Any]
    params: dict[str, Any]
    source_path: str


def _as_aspects(raw: Any) -> tuple[str, ...]:
    if isinstance(raw, str):
        return (raw,)
    if isinstance(raw, (list, tuple)) and raw:
        return tuple(str(a) for a in raw)
    raise DocumentSegmentError(
        f"Strategy YAML 'aspects' must be a non-empty string or list, got {raw!r}"
    )


def parse_strategy_yaml(data: dict[str, Any], *, source_path: str) -> StrategySpec:
    missing = [k for k in REQUIRED_KEYS if k not in data or data[k] in (None, "")]
    if missing:
        raise DocumentSegmentError(
            f"Strategy YAML {source_path!r} missing required keys: {', '.join(missing)}"
        )
    return StrategySpec(
        id=str(data["id"]),
        aspects=_as_aspects(data["aspects"]),
        engine=str(data["engine"]),
        grain=str(data["grain"]) if data.get("grain") is not None else None,
        recogniser=dict(data.get("recogniser") or {}),
        params=dict(data.get("params") or {}),
        source_path=source_path,
    )


def load_strategy_yaml(path: str | Path) -> YamlStrategy:
    """Load a strategy YAML file and return a ready-to-register adapter."""
    path = Path(path)
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise DocumentSegmentError(
            f"Cannot read strategy YAML {path}: {exc}"
        ) from exc
    except yaml.YAMLError as exc:
        raise DocumentSegmentError(
            f"Invalid strategy YAML {path}: {exc}"
        ) from exc
    if not isinstance(raw, dict):
        raise DocumentSegmentError(
            f"Strategy YAML {path} must be a mapping at the top level"
        )
    spec = parse_strategy_yaml(raw, source_path=str(path))
    # Validate engine exists early
    get_engine(spec.engine)
    return YamlStrategy(spec)


class YamlStrategy:
    """``SegmentStrategy`` adapter that delegates to a named engine."""

    def __init__(self, spec: StrategySpec):
        self.spec = spec
        self.id = spec.id
        self.aspects = spec.aspects
        self.engine = spec.engine
        self.grain = spec.grain
        self.recogniser = spec.recogniser
        self.params = spec.params

    def segment(self, document: Document, **overlay) -> list[Unit]:
        engine = get_engine(self.engine)
        params = dict(self.params)
        for key, value in overlay.items():
            if value is not None:
                params[key] = value
        return engine.run(
            document,
            params,
            strategy_id=self.id,
            aspects=self.aspects,
        )


def packaged_strategy_yaml_paths() -> list[Path]:
    """Return ``*.yml`` / ``*.yaml`` files next to this package."""
    here = Path(__file__).resolve().parent
    paths = sorted(here.glob("*.yml")) + sorted(here.glob("*.yaml"))
    return paths


def load_packaged_yaml_strategies() -> list[YamlStrategy]:
    return [load_strategy_yaml(p) for p in packaged_strategy_yaml_paths()]
