"""Головна демонстраційна точка входу (main.py) системи оцінювання студентів."""

from __future__ import annotations

import logging
from pathlib import Path

from grading.config import load_config
from grading.exporters import export_grade_report_atomic
from grading.importers import import_assessments_from_csv


def configure_demo_logging(log_dir: Path) -> logging.Logger:
    """Налаштовує журналювання демонстраційного запуску в logs/application.log та logs/errors.log."""
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("grading.demo")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    app_handler = logging.FileHandler(log_dir / "application.log", encoding="utf-8")
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(formatter)

    err_handler = logging.FileHandler(log_dir / "errors.log", encoding="utf-8")
    err_handler.setLevel(logging.WARNING)
    err_handler.setFormatter(formatter)

    logger.addHandler(app_handler)
    logger.addHandler(err_handler)
    return logger


def run_demo_pipeline(
    config_path: Path = Path("config.yaml"),
    input_csv: Path = Path("data/grades.csv"),
    output_json: Path = Path("output/grade_report.json"),
    log_dir: Path = Path("logs"),
) -> dict[str, object]:
    """Виконує повний демонстраційний конвеєр: конфігурація -> CSV імпорт -> розрахунки -> JSON експорт."""
    logger = configure_demo_logging(log_dir)
    logger.info("Starting grading system pipeline with config=%s", config_path)

    config = load_config(config_path)
    grade_book = import_assessments_from_csv(input_csv, config=config)
    report = export_grade_report_atomic(grade_book, output_json, config=config)

    stats = report["statistics"]
    logger.info(
        "Pipeline finished successfully: students=%s, exported_to=%s",
        len(grade_book),
        output_json,
    )
    if isinstance(stats, dict) and int(stats.get("failed_students", 0)) > 0:
        logger.warning(
            "Detected %s student(s) with average grade below threshold %.1f",
            stats["failed_students"],
            config.passing_threshold,
        )

    for handler in list(logger.handlers):
        handler.close()
        logger.removeHandler(handler)

    return report


if __name__ == "__main__":  # pragma: no cover
    run_demo_pipeline()
