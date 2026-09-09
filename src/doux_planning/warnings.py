from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from doux_planning.types import WarningSeverity


FACT_AXIS = {
    "empty_post": "couverture",
    "post_held": "couverture",
    "assigned_on_closure": "couverture",
    "rest_between_days": "legal",
    "weekly_rest_days": "legal",
    "max_coupure": "legal",
    "max_daily_hours": "legal",
    "max_weekly_hours": "legal",
    "unavailability": "contrat",
    "contract_hours": "contrat",
    "consecutive_rest_days": "wellbeing",
    "weekend_rest_day": "wellbeing",
    "weekend_every_two_weeks": "wellbeing",
    "weekend_even_weeks": "wellbeing",
    "weekend_odd_weeks": "wellbeing",
    "max_mornings": "wellbeing",
    "max_middays": "wellbeing",
    "max_evenings": "wellbeing",
    "max_coupures": "wellbeing",
    "role_gap": "roles",
}


def freeze_payload(payload: dict | None) -> tuple:
    def freeze(value):
        if isinstance(value, dict):
            return tuple((key, freeze(value[key])) for key in sorted(value))
        if isinstance(value, (list, tuple)):
            return tuple(freeze(item) for item in value)
        if isinstance(value, Enum):
            return value.value
        return value

    return freeze(dict(payload or {}))


@dataclass(frozen=True)
class Warning:
    severity: WarningSeverity
    code: str
    payload: dict = field(default_factory=dict)
    employee_id: str | None = None
    day_index: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", dict(self.payload or {}))

    @property
    def kind(self) -> str:
        return self.code

    def key(self) -> tuple:
        return (self.severity.value, self.code, self.employee_id, self.day_index, freeze_payload(self.payload))


@dataclass(frozen=True)
class ScoreFact:
    axis: str
    kind: str
    polarity: str
    severity: WarningSeverity | None
    employee_id: str | None = None
    day_index: int | None = None
    payload: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", dict(self.payload or {}))


def score_fact_from_warning(warning: Warning) -> ScoreFact:
    return ScoreFact(
        axis=FACT_AXIS[warning.code],
        kind=warning.code,
        polarity="miss",
        severity=warning.severity,
        employee_id=warning.employee_id,
        day_index=warning.day_index,
        payload=dict(warning.payload),
    )


def score_fact(
    kind: str,
    *,
    polarity: str,
    payload: dict,
    employee_id: str | None = None,
    day_index: int | None = None,
    severity: WarningSeverity | None = None,
) -> ScoreFact:
    return ScoreFact(
        axis=FACT_AXIS[kind],
        kind=kind,
        polarity=polarity,
        severity=severity,
        employee_id=employee_id,
        day_index=day_index,
        payload=dict(payload),
    )
