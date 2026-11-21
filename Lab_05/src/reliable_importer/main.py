"""Головна точка входу (main.py) для модуля імпорту та експорту системи оцінювання студентів."""

import argparse
import logging
from pathlib import Path

from reliable_importer.config import load_config
from reliable_importer.exceptions import ApplicationError
from reliable_importer.exporters import (
    export_invalid_records_csv,
    export_summary_report,
    get_exporter,
)
from reliable_importer.logging_config import configure_logging
from reliable_importer.models import ImportStatistics
from reliable_importer.services import filter_by_passing_grade, import_student_grades
from reliable_importer.utils import logged_operation

logger = logging.getLogger(__name__)


def run_pipeline(config_path: Path = Path("config.yaml")) -> ImportStatistics:
    """Виконує повний конвеєр завантаження конфігурації, імпорту, валідації, фільтрації та експорту."""
    config = load_config(config_path)
    configure_logging(
        config.logging.level,
        config.logging.path,
        error_log_path=config.logging.error_log_path,
        max_bytes=config.logging.max_bytes,
        backup_count=config.logging.backup_count,
    )

    statistics = ImportStatistics()
    with logged_operation("Student grades import/export"):
        grades_stream = import_student_grades(
            config.input_path,
            skip_invalid=config.processing.skip_invalid,
            statistics=statistics,
            allowed_disciplines=config.processing.allowed_disciplines,
            passing_grade=config.processing.passing_grade,
            input_format=config.input_format,
        )
        selected_stream = filter_by_passing_grade(
            grades_stream,
            config.processing.passing_grade,
        )
        exporter = get_exporter(config.output_path, fmt=config.output_format)
        statistics.exported = exporter.export(
            selected_stream,
            config.output_path,
            backup_existing=config.backup_existing,
        )

        if config.error_csv_path is not None:
            export_invalid_records_csv(statistics.errors, config.error_csv_path)

        if config.summary_report_path is not None:
            export_summary_report(statistics, config.summary_report_path)

    logger.info(
        "Total=%s, valid=%s, invalid=%s, passed=%s, below_threshold=%s, exported=%s",
        statistics.total,
        statistics.valid,
        statistics.invalid,
        statistics.passed,
        statistics.failed_threshold,
        statistics.exported,
    )
    return statistics


def main(argv: list[str] | None = None) -> None:
    """CLI-точка входу із контрольованим завершенням при критичних помилках."""
    parser = argparse.ArgumentParser(
        description="Надійний модуль імпорту та експорту системи оцінювання студентів (Варіант 7)"
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=Path("config.yaml"),
        help="Шлях до YAML-файлу конфігурації (за замовчуванням: config.yaml)",
    )
    args = parser.parse_args(argv)

    try:
        run_pipeline(args.config)
    except ApplicationError as error:
        logger.error("Application error: %s", error)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
