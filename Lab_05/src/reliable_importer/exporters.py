"""Атомарний потоковий експорт даних у JSON, JSON Lines, CSV, YAML та експорт звітів."""

from collections.abc import Iterable
import csv
import json
from pathlib import Path
from typing import Protocol
import yaml

from reliable_importer.exceptions import DataExportError
from reliable_importer.models import ImportStatistics, InvalidRecordDetail, StudentGrade
from reliable_importer.utils import AtomicFileWriter


class Exporter(Protocol):
    """Протокол експортера даних."""

    def export(
        self,
        records: Iterable[StudentGrade],
        path: Path,
        *,
        backup_existing: bool = False,
    ) -> int:
        """Експортує записи у цільовий файл і повертає кількість експортованих об'єктів."""
        ...


class JsonExporter:
    """Потоковий атомарний експортер у JSON-масив."""

    def export(
        self,
        records: Iterable[StudentGrade],
        path: Path,
        *,
        backup_existing: bool = False,
    ) -> int:
        count = 0
        try:
            with AtomicFileWriter(path, backup_existing=backup_existing) as file:
                file.write("[\n")
                first = True
                for record in records:
                    if not first:
                        file.write(",\n")
                    serialized = json.dumps(
                        record.to_dict(),
                        ensure_ascii=False,
                        indent=2,
                    )
                    indented = "\n".join(f"  {line}" for line in serialized.splitlines())
                    file.write(indented)
                    first = False
                    count += 1
                file.write("\n]\n")
        except DataExportError:
            raise
        except (OSError, TypeError, ValueError) as error:
            raise DataExportError(f"Cannot export JSON data to {path}") from error
        return count


class JsonLinesExporter:
    """Потоковий атомарний експортер у формат JSON Lines (.jsonl)."""

    def export(
        self,
        records: Iterable[StudentGrade],
        path: Path,
        *,
        backup_existing: bool = False,
    ) -> int:
        count = 0
        try:
            with AtomicFileWriter(path, backup_existing=backup_existing) as file:
                for record in records:
                    line = json.dumps(record.to_dict(), ensure_ascii=False)
                    file.write(line + "\n")
                    count += 1
        except DataExportError:
            raise
        except (OSError, TypeError, ValueError) as error:
            raise DataExportError(f"Cannot export JSONL data to {path}") from error
        return count


class CsvExporter:
    """Потоковий атомарний експортер у CSV."""

    FIELDNAMES = ["student_id", "name", "discipline", "grade", "passed"]

    def export(
        self,
        records: Iterable[StudentGrade],
        path: Path,
        *,
        backup_existing: bool = False,
    ) -> int:
        count = 0
        try:
            with AtomicFileWriter(
                path,
                newline="",
                backup_existing=backup_existing,
            ) as file:
                writer = csv.DictWriter(file, fieldnames=self.FIELDNAMES)
                writer.writeheader()
                for record in records:
                    writer.writerow(record.to_dict())
                    count += 1
        except DataExportError:
            raise
        except (OSError, csv.Error, TypeError, ValueError) as error:
            raise DataExportError(f"Cannot export CSV data to {path}") from error
        return count


class YamlExporter:
    """Атомарний експортер у YAML."""

    def export(
        self,
        records: Iterable[StudentGrade],
        path: Path,
        *,
        backup_existing: bool = False,
    ) -> int:
        items = [record.to_dict() for record in records]
        try:
            with AtomicFileWriter(path, backup_existing=backup_existing) as file:
                yaml.safe_dump(
                    items,
                    file,
                    allow_unicode=True,
                    sort_keys=False,
                )
        except DataExportError:
            raise
        except (OSError, yaml.YAMLError, TypeError, ValueError) as error:
            raise DataExportError(f"Cannot export YAML data to {path}") from error
        return len(items)


def get_exporter(path: Path, fmt: str = "auto") -> Exporter:
    """Повертає експортер відповідно до формату або розширення файлу."""
    resolved = fmt.lower()
    if resolved == "auto":
        suffixes = [s.lower() for s in path.suffixes]
        ext = suffixes[-2] if len(suffixes) >= 2 and suffixes[-1] == ".gz" else path.suffix.lower()
        resolved = ext.lstrip(".")

    if resolved == "json":
        return JsonExporter()
    if resolved == "jsonl":
        return JsonLinesExporter()
    if resolved == "csv":
        return CsvExporter()
    if resolved in {"yaml", "yml"}:
        return YamlExporter()
    raise DataExportError(f"Unsupported output format '{resolved}' for file {path}")


def export_grades_json(
    records: Iterable[StudentGrade],
    path: Path,
    *,
    backup_existing: bool = False,
) -> int:
    """Базова функція потокового атомарного експорту в JSON."""
    return JsonExporter().export(records, path, backup_existing=backup_existing)


def export_invalid_records_csv(
    errors: Iterable[InvalidRecordDetail],
    path: Path,
) -> int:
    """Атомарно записує деталі некоректних записів в окремий error CSV."""
    fieldnames = ["line_number", "field", "message", "student_id", "name", "discipline", "grade"]
    count = 0
    try:
        with AtomicFileWriter(path, newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for item in errors:
                raw = item.raw_row or {}
                writer.writerow(
                    {
                        "line_number": item.line_number,
                        "field": item.field,
                        "message": item.message,
                        "student_id": raw.get("student_id", ""),
                        "name": raw.get("name", ""),
                        "discipline": raw.get("discipline", ""),
                        "grade": raw.get("grade", ""),
                    }
                )
                count += 1
    except DataExportError:
        raise
    except (OSError, csv.Error) as error:
        raise DataExportError(f"Cannot write invalid records CSV to {path}") from error
    return count


def export_summary_report(
    statistics: ImportStatistics,
    path: Path,
) -> None:
    """Атомарно записує підсумковий JSON-звіт (summary report) про виконання імпорту/експорту."""
    report = {
        "statistics": statistics.to_dict(),
        "errors": [err.to_dict() for err in statistics.errors],
    }
    try:
        with AtomicFileWriter(path) as file:
            json.dump(report, file, ensure_ascii=False, indent=2)
            file.write("\n")
    except DataExportError:
        raise
    except (OSError, TypeError) as error:
        raise DataExportError(f"Cannot write summary report to {path}") from error
