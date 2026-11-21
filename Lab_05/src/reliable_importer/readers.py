"""Потокові читачі даних (CSV, JSON, JSON Lines, YAML) та єдиний протокол Importer."""

from collections.abc import Iterator
import csv
import gzip
import json
from pathlib import Path
from typing import Protocol, TextIO
import yaml

from reliable_importer.exceptions import DataImportError


def _open_text_file(path: Path) -> TextIO:
    """Відкриває звичайний або gzip-стиснений текстовий файл у кодуванні UTF-8."""
    if path.suffix.lower() == ".gz":
        return gzip.open(path, mode="rt", encoding="utf-8", newline="")
    return path.open("r", encoding="utf-8", newline="")


class Importer(Protocol):
    """Протокол уніфікованого імпортера записів."""

    def read(self, path: Path) -> Iterator[tuple[int, dict[str, object]]]:
        """Потоково повертає пари (line_number, row_dict)."""
        ...


class CsvImporter:
    """Потоковий імпортер CSV-файлів."""

    def read(self, path: Path) -> Iterator[tuple[int, dict[str, object]]]:
        try:
            with _open_text_file(path) as file:
                reader = csv.DictReader(file)
                if reader.fieldnames is None:
                    raise DataImportError(f"CSV file is empty or missing header: {path}")
                for line_number, row in enumerate(reader, start=2):
                    yield line_number, dict(row)
        except DataImportError:
            raise
        except (OSError, csv.Error, UnicodeDecodeError) as error:
            raise DataImportError(f"Cannot read CSV input file: {path}") from error


class JsonLinesImporter:
    """Потоковий імпортер JSON Lines (.jsonl)."""

    def read(self, path: Path) -> Iterator[tuple[int, dict[str, object]]]:
        try:
            with _open_text_file(path) as file:
                for line_number, line in enumerate(file, start=1):
                    stripped = line.strip()
                    if not stripped:
                        continue
                    try:
                        item = json.loads(stripped)
                    except json.JSONDecodeError as error:
                        raise DataImportError(
                            f"Invalid JSON at line {line_number} in {path}"
                        ) from error
                    if not isinstance(item, dict):
                        raise DataImportError(
                            f"JSON Lines record at line {line_number} must be an object"
                        )
                    yield line_number, item
        except DataImportError:
            raise
        except (OSError, UnicodeDecodeError) as error:
            raise DataImportError(f"Cannot read JSONL input file: {path}") from error


class JsonImporter:
    """Імпортер JSON-масиву об'єктів."""

    def read(self, path: Path) -> Iterator[tuple[int, dict[str, object]]]:
        try:
            with _open_text_file(path) as file:
                data = json.load(file)
        except json.JSONDecodeError as error:
            raise DataImportError(f"Invalid JSON document: {path}") from error
        except (OSError, UnicodeDecodeError) as error:
            raise DataImportError(f"Cannot read JSON input file: {path}") from error

        if not isinstance(data, list):
            raise DataImportError(f"JSON root must be an array of records: {path}")

        for index, item in enumerate(data, start=1):
            if not isinstance(item, dict):
                raise DataImportError(f"JSON element #{index} is not an object")
            yield index, item


class YamlImporter:
    """Імпортер YAML-списку записів."""

    def read(self, path: Path) -> Iterator[tuple[int, dict[str, object]]]:
        try:
            with _open_text_file(path) as file:
                data = yaml.safe_load(file)
        except yaml.YAMLError as error:
            raise DataImportError(f"Invalid YAML document: {path}") from error
        except (OSError, UnicodeDecodeError) as error:
            raise DataImportError(f"Cannot read YAML input file: {path}") from error

        if not isinstance(data, list):
            raise DataImportError(f"YAML root must be a sequence of records: {path}")

        for index, item in enumerate(data, start=1):
            if not isinstance(item, dict):
                raise DataImportError(f"YAML element #{index} is not a mapping")
            yield index, item


def get_importer(path: Path, fmt: str = "auto") -> Importer:
    """Автоматично визначає або повертає імпортер за форматом/розширенням файлу."""
    resolved = fmt.lower()
    if resolved == "auto":
        suffixes = [s.lower() for s in path.suffixes]
        ext = suffixes[-2] if len(suffixes) >= 2 and suffixes[-1] == ".gz" else path.suffix.lower()
        resolved = ext.lstrip(".")

    if resolved == "csv":
        return CsvImporter()
    if resolved == "jsonl":
        return JsonLinesImporter()
    if resolved == "json":
        return JsonImporter()
    if resolved in {"yaml", "yml"}:
        return YamlImporter()
    raise DataImportError(f"Unsupported input format '{resolved}' for file {path}")


def read_csv_rows(path: Path) -> Iterator[tuple[int, dict[str, str]]]:
    """Базова функція потокового читання CSV-рядків (сумісна з прикладом у методичці)."""
    try:
        with path.open("r", encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames is None:
                raise DataImportError(f"CSV file is empty or missing header: {path}")
            for line_number, row in enumerate(reader, start=2):
                yield line_number, row
    except DataImportError:
        raise
    except (OSError, csv.Error, UnicodeDecodeError) as error:
        raise DataImportError(f"Cannot read input file: {path}") from error
