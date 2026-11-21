"""Типізовані словники (TypedDict) та DTO для зовнішніх даних (payloads)."""

from __future__ import annotations

from typing import NotRequired, TypedDict


class AssessmentPayload(TypedDict):
    """Зовнішній словник даних про оцінювання з дисципліни."""

    discipline_id: int
    discipline_name: str
    credits: int
    score: float
    assessment_type: NotRequired[str]


class StudentPayload(TypedDict):
    """Зовнішній JSON-подібний payload студента з переліком його оцінок."""

    id: int
    full_name: str
    group: str
    email: str
    funding_type: str  # "state" або "contract"
    contract_tuition_fee: NotRequired[float]
    assessments: list[AssessmentPayload]
