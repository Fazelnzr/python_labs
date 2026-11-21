"""Власні контекстні менеджери (custom context managers) для логування часу та транзакційного запису."""

from collections.abc import Iterator
from contextlib import contextmanager
import gzip
import logging
from pathlib import Path
import shutil
from time import perf_counter
from typing import TextIO

from reliable_importer.exceptions import DataExportError

logger = logging.getLogger(__name__)


@contextmanager
def logged_operation(operation: str) -> Iterator[None]:
    """Generator-based контекстний менеджер для вимірювання часу та логування операції."""
    logger.info("%s started", operation)
    start = perf_counter()
    try:
        yield
    except Exception:
        logger.exception("%s failed", operation)
        raise
    else:
        elapsed = perf_counter() - start
        logger.info("%s finished in %.6f s", operation, elapsed)


class AtomicFileWriter:
    """Класовий контекстний менеджер (__enter__/__exit__) для атомарного транзакційного запису файлу.

    Записує дані у тимчасовий файл (.tmp), за потреби створює резервну копію (.bak)
    існуючого файлу і виконує атомарний replace лише у разі відсутності помилок.
    У разі винятку тимчасовий файл автоматично видаляється, а попередній output залишається цілим.
    """

    def __init__(
        self,
        target_path: Path,
        *,
        encoding: str = "utf-8",
        newline: str | None = None,
        backup_existing: bool = False,
    ) -> None:
        self.target_path = target_path
        self.encoding = encoding
        self.newline = newline
        self.backup_existing = backup_existing
        self.temp_path = target_path.with_suffix(target_path.suffix + ".tmp")
        self.backup_path = target_path.with_suffix(target_path.suffix + ".bak")
        self._file: TextIO | None = None

    def __enter__(self) -> TextIO:
        try:
            self.target_path.parent.mkdir(parents=True, exist_ok=True)
            if self.target_path.suffix.lower() == ".gz":
                self._file = gzip.open(
                    self.temp_path,
                    mode="wt",
                    encoding=self.encoding,
                    newline=self.newline,
                )
            else:
                self._file = self.temp_path.open(
                    "w",
                    encoding=self.encoding,
                    newline=self.newline,
                )
            return self._file
        except OSError as error:
            self.temp_path.unlink(missing_ok=True)
            raise DataExportError(f"Cannot open temporary file for {self.target_path}") from error

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        if self._file is not None:
            try:
                self._file.close()
            except OSError as close_error:
                self.temp_path.unlink(missing_ok=True)
                if exc_type is None:
                    raise DataExportError(
                        f"Cannot close temporary file for {self.target_path}"
                    ) from close_error

        if exc_type is not None:
            self.temp_path.unlink(missing_ok=True)
            return False

        try:
            if self.backup_existing and self.target_path.exists():
                shutil.copy2(self.target_path, self.backup_path)
            self.temp_path.replace(self.target_path)
        except OSError as error:
            self.temp_path.unlink(missing_ok=True)
            raise DataExportError(f"Cannot atomically write output to {self.target_path}") from error

        return False
