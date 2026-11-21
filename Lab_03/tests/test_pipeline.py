"""Модульні тести потокового конвеєра оцінювання студентів (Варіант 7)."""

from itertools import islice
from pathlib import Path
import tempfile
import unittest

from stream_processor.analytics import (
    analyze_grade_trends,
    group_by_discipline,
    group_by_student,
    lazy_students_above_average,
    streaming_average_grade,
    streaming_min_max_grade,
    top_n_rating,
)
from stream_processor.filters import batched_records, find_first_record
from stream_processor.models import GradeArchive, GradeRecord
from stream_processor.parsers import validate_grades
from stream_processor.pipeline import build_pipeline
from stream_processor.readers import (
    flatten_nested_records,
    infinite_grade_stream,
    read_multiple_files,
)


class TestStreamProcessorVariant7(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.csv_path = Path(self.temp_dir.name) / "test_grades.csv"
        self.csv_path.write_text(
            "student_id,name,discipline,grade\n"
            "1,anna koval,Programming,95.5\n"
            "2,oleh melnyk,Programming,82.0\n"
            "1,anna koval,Algorithms,91.0\n"
            "3,iryna bondar,Databases,74.5\n"
            "4,invalid grade,Programming,error\n"
            "5,out of range,Programming,105.0\n"
            "-1,negative id,Algorithms,88.0\n"
            "2,oleh melnyk,Algorithms,86.0\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_custom_iterable_and_iterator(self) -> None:
        records = list(build_pipeline(self.csv_path))
        archive = GradeArchive(records, min_grade=85.0, max_grade=100.0)
        # Перевірка, що archive є Iterable, а iter(archive) є Iterator
        self.assertIsNot(iter(archive), archive)
        it = iter(archive)
        self.assertIs(iter(it), it)
        first_pass = [r.grade for r in archive]
        second_pass = [r.grade for r in archive]
        self.assertEqual(first_pass, [95.5, 91.0, 86.0])
        self.assertEqual(first_pass, second_pass)

    def test_validation_and_discipline_filter(self) -> None:
        stats: dict[str, int] = {}
        prog_records = list(
            build_pipeline(self.csv_path, discipline="programming", validation_stats=stats)
        )
        self.assertEqual(stats["valid"], 5)
        self.assertEqual(stats["invalid"], 3)
        self.assertEqual(len(prog_records), 2)
        self.assertEqual(prog_records[0].name, "Anna Koval")

    def test_streaming_average_and_min_max(self) -> None:
        avg = streaming_average_grade(build_pipeline(self.csv_path, discipline="Programming"))
        self.assertAlmostEqual(avg, (95.5 + 82.0) / 2)
        min_r, max_r = streaming_min_max_grade(build_pipeline(self.csv_path))
        self.assertIsNotNone(min_r)
        self.assertIsNotNone(max_r)
        assert min_r is not None and max_r is not None
        self.assertEqual(min_r.grade, 74.5)
        self.assertEqual(max_r.grade, 95.5)

    def test_lazy_above_average_and_top_n(self) -> None:
        above_85 = list(lazy_students_above_average(build_pipeline(self.csv_path), threshold=85.0))
        self.assertEqual(len(above_85), 1)
        self.assertEqual(above_85[0].student_id, 1)
        self.assertAlmostEqual(above_85[0].average_grade, 93.25)

        top_2 = top_n_rating(build_pipeline(self.csv_path), n=2)
        self.assertEqual([s.student_id for s in top_2], [1, 2])

    def test_grouping_and_batching(self) -> None:
        by_disc = group_by_discipline(build_pipeline(self.csv_path))
        self.assertEqual(by_disc["Programming"]["count"], 2)
        self.assertEqual(by_disc["Algorithms"]["count"], 2)

        by_stud = list(group_by_student(build_pipeline(self.csv_path)))
        self.assertEqual(len(by_stud), 3)

        batches = list(batched_records(build_pipeline(self.csv_path), batch_size=2))
        self.assertEqual([len(b) for b in batches], [2, 2, 1])

    def test_itertools_and_extras(self) -> None:
        trends = analyze_grade_trends(build_pipeline(self.csv_path), limit=4)
        self.assertEqual(len(trends["pairwise_diffs"]), 3)
        self.assertEqual(len(trends["cumulative_sum"]), 4)

        inf_records = list(islice(validate_grades(infinite_grade_stream()), 5))
        self.assertEqual(len(inf_records), 5)

        flat = list(flatten_nested_records([1, [2, [3, 4]], 5]))
        self.assertEqual(flat, [1, 2, 3, 4, 5])

        found = find_first_record(build_pipeline(self.csv_path), lambda r: r.grade > 90)
        self.assertIsNotNone(found)

        second_csv = Path(self.temp_dir.name) / "part2.csv"
        second_csv.write_text(
            "student_id,name,discipline,grade\n10,petro novak,Databases,99.0\n",
            encoding="utf-8",
        )
        combined = list(read_multiple_files([self.csv_path, second_csv]))
        self.assertEqual(len(combined), 10)


if __name__ == "__main__":
    unittest.main()
