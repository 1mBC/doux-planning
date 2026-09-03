from __future__ import annotations

from dataclasses import dataclass, field, replace

from doux_planning.types import (
    DEFAULT_MIN_SHIFT_HOURS,
    MAX_COUPURE_HOURS,
    MAX_DAILY_HOURS_CUISINE,
    MAX_DAILY_HOURS_SALLE,
    MAX_WEEKLY_HOURS,
    MIN_REST_BETWEEN_DAYS_HOURS,
    REST_DAYS_PER_WEEK,
    Team,
    WellbeingPreference,
    weekday_index,
)


class TeamMismatchError(ValueError):
    pass


class SubstitutionExplanationRequired(ValueError):
    pass


@dataclass(frozen=True)
class Role:
    name: str
    level: int
    team: Team

    def __post_init__(self) -> None:
        if self.level < 1:
            raise ValueError("Role level must be >= 1")


@dataclass(frozen=True)
class RoleLadder:
    team: Team
    roles: tuple[Role, ...]
    substitution_explained: bool

    def __post_init__(self) -> None:
        if not self.substitution_explained:
            raise SubstitutionExplanationRequired(
                "A higher level can fill any lower post on the same team; "
                "this rule must be explained when entering roles."
            )
        for role in self.roles:
            if role.team != self.team:
                raise TeamMismatchError(f"Role {role.name} is not on team {self.team.value}")

    def by_name(self, name: str) -> Role:
        for role in self.roles:
            if role.name == name:
                return role
        raise KeyError(name)


@dataclass(frozen=True)
class Unavailability:
    """Restaurateur-stated unavailability pattern."""

    weekday: str | None = None
    every_morning: bool = False
    every_evening: bool = False
    service_id: str | None = None

    def blocks(self, weekday: str, service_id: str, is_morning: bool, is_evening: bool) -> bool:
        if self.weekday and weekday_index(self.weekday) != weekday_index(weekday):
            return False
        if self.service_id and self.service_id != service_id:
            return False
        if self.every_morning and not is_morning:
            return False
        if self.every_evening and not is_evening:
            return False
        if self.weekday is None and not self.every_morning and not self.every_evening and not self.service_id:
            return False
        if self.weekday and not self.every_morning and not self.every_evening and not self.service_id:
            return True
        return True


@dataclass(frozen=True)
class Employee:
    id: str
    name: str
    role: Role
    team: Team
    contractual_hours_per_week: float
    unavailabilities: tuple[Unavailability, ...] = ()
    wellbeing: frozenset[WellbeingPreference] = field(default_factory=frozenset)
    forced_off_days: frozenset[int] = field(default_factory=frozenset)
    max_evenings_per_week: int | None = None
    max_mornings_per_week: int | None = None
    min_shift_hours: float = DEFAULT_MIN_SHIFT_HOURS

    def __post_init__(self) -> None:
        if self.team != self.role.team:
            raise TeamMismatchError(
                f"Employee {self.name} team {self.team.value} does not match role team {self.role.team.value}"
            )
        if self.min_shift_hours <= 0:
            raise ValueError("min_shift_hours must be > 0")
        object.__setattr__(self, "wellbeing", frozenset(self.wellbeing))
        object.__setattr__(self, "forced_off_days", frozenset(self.forced_off_days))

    @property
    def level(self) -> int:
        return self.role.level

    def with_unavailability(self, pattern: Unavailability) -> Employee:
        return replace(self, unavailabilities=self.unavailabilities + (pattern,))

    def with_wellbeing(self, preference: WellbeingPreference) -> Employee:
        return replace(self, wellbeing=self.wellbeing | {preference})


@dataclass(frozen=True)
class LegalRule:
    id: str
    label_fr: str
    severity: str = "interdit"


def default_legal_rules() -> tuple[LegalRule, ...]:
    return (
        LegalRule(
            "rest_between_days",
            f"{MIN_REST_BETWEEN_DAYS_HOURS}h de repos entre deux journées",
        ),
        LegalRule(
            "weekly_rest_days",
            f"{REST_DAYS_PER_WEEK} jours de repos par semaine",
        ),
        LegalRule(
            "max_coupure",
            f"{MAX_COUPURE_HOURS}h de pause maximum entre deux services",
        ),
        LegalRule(
            "max_daily_cuisine",
            f"{MAX_DAILY_HOURS_CUISINE}h de travail par jour max pour la cuisine",
        ),
        LegalRule(
            "max_daily_salle",
            f"{MAX_DAILY_HOURS_SALLE}h de travail par jour max pour la salle",
        ),
        LegalRule(
            "max_weekly_hours",
            f"{MAX_WEEKLY_HOURS}h maximum de travail par semaine",
        ),
    )
