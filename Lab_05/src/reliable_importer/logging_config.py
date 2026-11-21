"""Налаштування системи логування із підтримкою ротації та окремого error log."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def configure_logging(
    level: str,
    path: Path,
    *,
    error_log_path: Path | None = None,
    max_bytes: int = 1048576,
    backup_count: int = 3,
) -> None:
    """Налаштовує основний логер, ротацію файлів та окремий файл для помилок/попереджень."""
    path.parent.mkdir(parents=True, exist_ok=True)
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    formatter = logging.Formatter(LOG_FORMAT)

    main_file_handler = RotatingFileHandler(
        path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    main_file_handler.setLevel(numeric_level)
    main_file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(numeric_level)
    stream_handler.setFormatter(formatter)

    handlers: list[logging.Handler] = [main_file_handler, stream_handler]

    if error_log_path is not None:
        error_log_path.parent.mkdir(parents=True, exist_ok=True)
        error_handler = RotatingFileHandler(
            error_log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.WARNING)
        error_handler.setFormatter(formatter)
        handlers.append(error_handler)

    logging.basicConfig(
        level=numeric_level,
        format=LOG_FORMAT,
        handlers=handlers,
        force=True,
    )
