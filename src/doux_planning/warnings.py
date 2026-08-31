from __future__ import annotations

from dataclasses import dataclass

from doux_planning.types import WarningSeverity


@dataclass(frozen=True)
class Warning:
    severity: WarningSeverity
    code: str
    message: str
    employee_id: str | None = None
    day_index: int | None = None

    def key(self) -> tuple:
        return (self.severity.value, self.code, self.employee_id, self.day_index, self.message)
