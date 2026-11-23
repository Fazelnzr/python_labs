"""Конфігурація системи оцінювання студентів із підтримкою змінних середовища та YAML/JSON."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from grading.exceptions import ConfigurationError
from grading.models import validate_grade_value

DEFAULT_PASSING_THRESHOLD: float = 60.0
DEFAULT_HONORS_THRESHOLD: float = 90.0
DEFAULT_GRADING_MODE: str = "standard"


def get_passing_threshold() -> float:
    """Повертає поріг успішності зі змінної середовища GRADING_PASSING_THRESHOLD або 60.0 за замовчуванням."""
    raw = os.getenv("GRADING_PASSING_THRESHOLD")
    if raw is None or not raw.strip():
        return DEFAULT_PASSING_THRESHOLD
    try:
        value = float(raw.strip())
        return validate_grade_value(value)
    except ValueError as error:
        raise ConfigurationError(
            f"Invalid GRADING_PASSING_THRESHOLD value: {raw!r}"
        ) from error


def get_grading_mode() -> str:
    """Повертає режим оцінювання зі змінної середовища GRADING_MODE ('standard' або 'weighted')."""
    mode = os.getenv("GRADING_MODE", DEFAULT_GRADING_MODE).strip().lower()
    if mode not in {"standard", "weighted"}:
        raise ConfigurationError(f"Unsupported GRADING_MODE: {mode!r}")
    return mode


@dataclass(frozen=True, slots=True)
class GradingConfig:
    """Об'єкт конфігурації системи оцінювання."""

    passing_threshold: float = DEFAULT_PASSING_THRESHOLD
    honors_threshold: float = DEFAULT_HONORS_THRESHOLD
    mode: str = DEFAULT_GRADING_MODE
    allowed_disciplines: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        try:
            validated_passing = validate_grade_value(self.passing_threshold)
            validated_honors = validate_grade_value(self.honors_threshold)
        except ValueError as error:
            raise ConfigurationError(str(error)) from error

        if validated_passing > validated_honors:
            raise ConfigurationError(
                "passing_threshold cannot be greater than honors_threshold"
            )
        clean_mode = self.mode.strip().lower()
        if clean_mode not in {"standard", "weighted"}:
            raise ConfigurationError(f"Invalid grading mode: {self.mode!r}")

        object.__setattr__(self, "passing_threshold", validated_passing)
        object.__setattr__(self, "honors_threshold", validated_honors)
        object.__setattr__(self, "mode", clean_mode)
        object.__setattr__(
            self,
            "allowed_disciplines",
            tuple(d.strip() for d in self.allowed_disciplines if d and d.strip()),
        )


def load_config(path: Path | None = None) -> GradingConfig:
    """Завантажує конфігурацію з YAML/JSON файлу та застосовує перевизначення через змінні середовища."""
    raw_data: dict[str, Any] = {}
    if path is not None:
        if not path.exists():
            raise ConfigurationError(f"Configuration file not found: {path}")
        try:
            content = path.read_text(encoding="utf-8")
            if path.suffix.lower() == ".json":
                loaded = json.loads(content)
            else:
                loaded = yaml.safe_load(content)
        except (OSError, json.JSONDecodeError, yaml.YAMLError) as error:
            raise ConfigurationError(f"Failed to parse config file {path}: {error}") from error

        if loaded is not None:
            if not isinstance(loaded, dict):
                raise ConfigurationError("Configuration root must be a mapping/object")
            raw_data = loaded

    passing_threshold = (
        get_passing_threshold()
        if "GRADING_PASSING_THRESHOLD" in os.environ
        else float(raw_data.get("passing_threshold", DEFAULT_PASSING_THRESHOLD))
    )
    honors_threshold = float(raw_data.get("honors_threshold", DEFAULT_HONORS_THRESHOLD))
    mode = (
        get_grading_mode()
        if "GRADING_MODE" in os.environ
        else str(raw_data.get("mode", DEFAULT_GRADING_MODE))
    )
    disciplines_raw = raw_data.get("allowed_disciplines", ())
    if not isinstance(disciplines_raw, (list, tuple)):
        raise ConfigurationError("allowed_disciplines must be a list of strings")

    return GradingConfig(
        passing_threshold=passing_threshold,
        honors_threshold=honors_threshold,
        mode=mode,
        allowed_disciplines=tuple(str(item) for item in disciplines_raw),
    )
