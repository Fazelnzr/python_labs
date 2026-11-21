"""Демонстраційний сценарій Лабораторної роботи №4 (Варіант 7 — Система оцінювання студентів)."""

from __future__ import annotations

import sys

from grade_system.dto import StudentPayload
from grade_system.models import (
    CreditWeightedPolicy,
    Discipline,
    StandardAveragePolicy,
    Student,
)
from grade_system.protocols import Serializable
from grade_system.repositories import InMemoryRepository, scale_score
from grade_system.services import (
    ConsoleNotificationSender,
    GradeBookService,
    MarkdownReportFormatter,
)
from grade_system.value_objects import Grade


def build_sample_payloads() -> list[StudentPayload]:
    """Формує тестові зовнішні дані (TypedDict payloads) для імпорту."""
    return [
        {
            "id": 101,
            "full_name": "Коваленко Анна Ігорівна",
            "group": "КН-21",
            "email": "anna.kovalenko@university.edu.ua",
            "funding_type": "state",
            "assessments": [
                {
                    "discipline_id": 1,
                    "discipline_name": "Об'єктно-орієнтоване програмування",
                    "credits": 5,
                    "score": 96.0,
                    "assessment_type": "Екзамен",
                },
                {
                    "discipline_id": 2,
                    "discipline_name": "Алгоритми і структури даних",
                    "credits": 5,
                    "score": 93.0,
                    "assessment_type": "Екзамен",
                },
                {
                    "discipline_id": 3,
                    "discipline_name": "Бази даних",
                    "credits": 4,
                    "score": 91.0,
                    "assessment_type": "Залік",
                },
            ],
        },
        {
            "id": 102,
            "full_name": "Мельник Богдан Сергійович",
            "group": "КН-21",
            "email": "bohdan.melnyk@university.edu.ua",
            "funding_type": "state",
            "assessments": [
                {
                    "discipline_id": 1,
                    "discipline_name": "Об'єктно-орієнтоване програмування",
                    "credits": 5,
                    "score": 84.0,
                },
                {
                    "discipline_id": 2,
                    "discipline_name": "Алгоритми і структури даних",
                    "credits": 5,
                    "score": 78.0,
                },
                {
                    "discipline_id": 3,
                    "discipline_name": "Бази даних",
                    "credits": 4,
                    "score": 88.0,
                },
            ],
        },
        {
            "id": 103,
            "full_name": "Шевченко Дарина Олександрівна",
            "group": "КН-22",
            "email": "daryna.shevchenko@university.edu.ua",
            "funding_type": "contract",
            "contract_tuition_fee": 42000.0,
            "assessments": [
                {
                    "discipline_id": 1,
                    "discipline_name": "Об'єктно-орієнтоване програмування",
                    "credits": 5,
                    "score": 95.0,
                },
                {
                    "discipline_id": 2,
                    "discipline_name": "Алгоритми і структури даних",
                    "credits": 5,
                    "score": 92.0,
                },
                {
                    "discipline_id": 3,
                    "discipline_name": "Бази даних",
                    "credits": 4,
                    "score": 94.0,
                },
            ],
        },
        {
            "id": 104,
            "full_name": "Ткаченко Дмитро Васильович",
            "group": "КН-22",
            "email": "dmytro.tkachenko@university.edu.ua",
            "funding_type": "contract",
            "assessments": [
                {
                    "discipline_id": 1,
                    "discipline_name": "Об'єктно-орієнтоване програмування",
                    "credits": 5,
                    "score": 68.0,
                },
                {
                    "discipline_id": 2,
                    "discipline_name": "Алгоритми і структури даних",
                    "credits": 5,
                    "score": 61.0,
                },
                {
                    "discipline_id": 3,
                    "discipline_name": "Бази даних",
                    "credits": 4,
                    "score": 72.0,
                },
            ],
        },
        {
            "id": 105,
            "full_name": "Бондаренко Ілля Петрович",
            "group": "КН-21",
            "email": "illia.bondarenko@university.edu.ua",
            "funding_type": "state",
            "assessments": [
                {
                    "discipline_id": 1,
                    "discipline_name": "Об'єктно-орієнтоване програмування",
                    "credits": 5,
                    "score": 65.0,
                },
                {
                    "discipline_id": 2,
                    "discipline_name": "Алгоритми і структури даних",
                    "credits": 5,
                    "score": 52.0,
                },
                {
                    "discipline_id": 3,
                    "discipline_name": "Бази даних",
                    "credits": 4,
                    "score": 63.0,
                },
            ],
        },
    ]


def main() -> None:
    """Точка входу демонстраційного застосунку."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 92)
    print(
        "ЛАБОРАТОРНА РОБОТА №4 — ВАРІАНТ 7: СИСТЕМА ОЦІНЮВАННЯ СТУДЕНТІВ"
    )
    print("=" * 92)

    # 1. Створення типізованих Generic репозиторіїв та залежностей (Dependency Injection)
    student_repo = InMemoryRepository[Student]()
    discipline_repo = InMemoryRepository[Discipline]()
    formatter = MarkdownReportFormatter()
    notifier = ConsoleNotificationSender()
    policy = StandardAveragePolicy()

    service = GradeBookService(
        student_repo=student_repo,
        discipline_repo=discipline_repo,
        evaluation_policy=policy,
        report_formatter=formatter,
        notifier=notifier,
        title="Осінній семестр 2026/2027 (Потік КН)",
    )

    # 2. Імпорт студентів із TypedDict payloads
    for payload in build_sample_payloads():
        service.import_student_payload(payload)

    # 3. Додавання нової дисципліни та виставлення оцінок через сервіс
    discrete_math = Discipline(
        id=4,
        name="Дискретна математика",
        _credits=4,
    )
    service.register_discipline(discrete_math)

    print("\n--- 1. Додавання нових оцінок та автоматичне сповіщення ---")
    service.assign_grade(
        student_id=101,
        discipline_id=4,
        score=98.0,
        assessment_type="Екзамен",
    )
    service.assign_grade(
        student_id=102,
        discipline_id=4,
        score=89.0,
        assessment_type="Екзамен",
    )
    service.assign_grade(
        student_id=103,
        discipline_id=4,
        score=91.0,
        assessment_type="Екзамен",
    )

    # 4. Перевірка роботи dunder-методів та runtime_checkable Protocol
    grade_book = service.grade_book
    anna = grade_book[101]
    print("\n--- 2. Перевірка dunder-методів та контейнерної поведінки ---")
    print(f"Кількість студентів у журналі (len(grade_book)): {len(grade_book)}")
    print(f"Чи є студент ID=101 у журналі (101 in grade_book): {101 in grade_book}")
    print(f"Кількість оцінок у {anna.full_name} (len(student)): {len(anna)}")
    print(
        f"Чи складена дисципліна ID=4 у студента 101 (4 in student): {4 in anna}"
    )
    print(
        f"Порівняння об'єктів Grade(98) > Grade(89): {Grade(98.0) > Grade(89.0)}"
    )
    print(
        f"Сума двох оцінок Grade(98) + Grade(89): {Grade(98.0) + Grade(89.0):.1f}"
    )
    print(
        f"Перевірка isinstance(anna, Serializable): {isinstance(anna, Serializable)}"
    )
    print(
        f"Масштабування бала (constrained TypeVar): {scale_score(95, 1.05):.2f}"
    )

    # 5. Обчислення індивідуальної та групової статистики (середній, мін, макс, успішність)
    print("\n--- 3. Статистика успішності за студентами ---")
    for student in grade_book:
        summary = service.get_student_summary(student.id)
        print(
            f"• {summary['full_name']}: середній = {summary['average']:.2f}, "
            f"зважений = {summary['weighted_average']:.2f}, "
            f"мін = {summary['min']}, макс = {summary['max']} | "
            f"Успішність: {summary['performance_level']}"
        )

    group_avg, group_min, group_max = grade_book.calculate_group_statistics()
    print(
        f"\nЗагальна статистика по журналу -> Середній бал: {group_avg:.2f} | "
        f"Мінімальний: {group_min:.1f} | Максимальний: {group_max:.1f}"
    )

    # 6. Сортування студентів за середнім балом та формування звіту
    print("\n--- 4. Рейтингова відомість (сортування за спаданням середнього бала) ---")
    print(service.generate_ranking_report())

    # 7. Пошук студентів вище заданого порога
    threshold = 85.0
    print(f"\n--- 5. Студенти з середнім балом вище порога {threshold:.1f} ---")
    top_students = service.find_students_above_threshold(threshold)
    for idx, st in enumerate(top_students, start=1):
        print(f"  {idx}. {st} | {st.academic_status_note()}")

    # 8. Сповіщення відмінників (поріг >= 90.0)
    print("\n--- 6. Розсилка відзнак студентам із балом > 90.0 ---")
    service.notify_honor_students(threshold=90.0)

    # 9. Демонстрація зміни політики оцінювання (Open/Closed Principle + Strategy)
    print("\n--- 7. Порівняння з кредитно-зваженою політикою (CreditWeightedPolicy) ---")
    weighted_policy = CreditWeightedPolicy()
    for st in top_students:
        print(
            f"  {st.full_name}: стандартний = {policy.calculate_rating(st):.2f}, "
            f"кредитно-зважений = {weighted_policy.calculate_rating(st):.2f}"
        )


if __name__ == "__main__":
    main()
