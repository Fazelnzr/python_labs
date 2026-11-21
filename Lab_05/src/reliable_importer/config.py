"""Завантаження та fail-fast валідація YAML-конфігурації з підтримкою змінних середовища."""

import os
from pathlib import Path
import yaml

from reliable_importer.exceptions import ConfigurationError
from reliable_importer.models import AppConfig, LoggingConfig, ProcessingConfig

SUPPORTED_INPUT_FORMATS = {"auto", "csv", "json", "jsonl", "yaml", "yml"}
SUPPORTED_OUTPUT_FORMATS = {"auto", "json", "jsonl", "csv", "yaml", "yml"}


def _parse_bool(value: object, *, field_name: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes"}:
            return True
        if lowered in {"false", "0", "no"}:
            return False
    raise ConfigurationError(f"Поле '{field_name}' повинно бути булевим значенням")


def load_config(path: Path) -> AppConfig:
    """Завантажує конфігурацію з YAML-файлу, застосовує env overrides та виконує валідацію."""
    try:
        with path.open("r", encoding="utf-8") as file:
            raw = yaml.safe_load(file)
    except FileNotFoundError as error:
        raise ConfigurationError(f"Configuration file not found: {path}") from error
    except yaml.YAMLError as error:
        raise ConfigurationError("Invalid YAML configuration") from error
    except OSError as error:
        raise ConfigurationError(f"Cannot read configuration file: {path}") from error

    if not isinstance(raw, dict):
        raise ConfigurationError("Configuration root must be a YAML mapping")

    try:
        input_section = raw["input"]
        output_section = raw["output"]
        processing_section = raw["processing"]
        logging_section = raw["logging"]

        if not all(
            isinstance(sec, dict)
            for sec in (input_section, output_section, processing_section, logging_section)
        ):
            raise TypeError("Configuration sections must be mappings")

        input_path_str = os.environ.get("IMPORTER_INPUT_PATH", input_section["path"])
        output_path_str = os.environ.get("IMPORTER_OUTPUT_PATH", output_section["path"])
        passing_grade_raw = os.environ.get(
            "IMPORTER_PASSING_GRADE",
            processing_section.get("passing_grade", processing_section.get("minimum_grade")),
        )
        if passing_grade_raw is None:
            raise KeyError("passing_grade")

        skip_invalid_raw = os.environ.get(
            "IMPORTER_SKIP_INVALID",
            processing_section["skip_invalid"],
        )
        log_level_raw = os.environ.get("IMPORTER_LOG_LEVEL", logging_section["level"])

        disciplines_raw = processing_section["allowed_disciplines"]
        if not isinstance(disciplines_raw, list) or not all(
            isinstance(item, str) and item.strip() for item in disciplines_raw
        ):
            raise ConfigurationError(
                "allowed_disciplines must be a non-empty list of non-empty strings"
            )

        error_csv_raw = output_section.get("error_csv_path")
        summary_report_raw = output_section.get("summary_report_path")
        error_log_raw = logging_section.get("error_log_path")

        config = AppConfig(
            input_path=Path(str(input_path_str)),
            output_path=Path(str(output_path_str)),
            input_format=str(input_section.get("format", "auto")).lower(),
            output_format=str(output_section.get("format", "auto")).lower(),
            error_csv_path=Path(str(error_csv_raw)) if error_csv_raw else None,
            summary_report_path=Path(str(summary_report_raw)) if summary_report_raw else None,
            backup_existing=_parse_bool(
                output_section.get("backup_existing", True),
                field_name="output.backup_existing",
            ),
            processing=ProcessingConfig(
                passing_grade=float(passing_grade_raw),
                skip_invalid=_parse_bool(
                    skip_invalid_raw,
                    field_name="processing.skip_invalid",
                ),
                allowed_disciplines=tuple(item.strip() for item in disciplines_raw),
            ),
            logging=LoggingConfig(
                level=str(log_level_raw).upper(),
                path=Path(str(logging_section["path"])),
                error_log_path=Path(str(error_log_raw)) if error_log_raw else None,
                max_bytes=int(logging_section.get("max_bytes", 1048576)),
                backup_count=int(logging_section.get("backup_count", 3)),
            ),
        )
    except ConfigurationError:
        raise
    except (KeyError, TypeError, ValueError) as error:
        raise ConfigurationError("Configuration structure is invalid") from error

    validate_config(config)
    return config


def validate_config(config: AppConfig) -> None:
    """Виконує fail-fast перевірку параметрів конфігурації на старті застосунку."""
    if not 0.0 <= config.processing.passing_grade <= 100.0:
        raise ConfigurationError("passing_grade must be between 0 and 100")

    if not config.processing.allowed_disciplines:
        raise ConfigurationError("allowed_disciplines cannot be empty")

    if config.input_format not in SUPPORTED_INPUT_FORMATS:
        raise ConfigurationError(f"Unsupported input format: {config.input_format}")

    if config.output_format not in SUPPORTED_OUTPUT_FORMATS:
        raise ConfigurationError(f"Unsupported output format: {config.output_format}")

    if not config.input_path.exists():
        raise ConfigurationError(f"Input file not found: {config.input_path}")

    if not config.input_path.is_file():
        raise ConfigurationError(f"Input path is not a file: {config.input_path}")
