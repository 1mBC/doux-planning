from __future__ import annotations

import secrets
from dataclasses import dataclass, field, replace

from types import MappingProxyType

from doux_planning.types import (
    DEFAULT_MIN_SHIFT_HOURS,
    MAX_COUPURE_HOURS,
    MAX_DAILY_HOURS_CUISINE,
    MAX_DAILY_HOURS_SALLE,
    MAX_WEEKLY_HOURS,
    MIN_REST_BETWEEN_DAYS_HOURS,
    REST_DAYS_PER_WEEK,
    ServiceName,
    Team,
    WEEKDAYS,
    WeekendChoice,
    weekday_index,
)

COMPANY_SERVICE_IDS = frozenset(
    {ServiceName.MORNING.value, ServiceName.MIDDAY.value, ServiceName.EVENING.value}
)
REMOVED_WELLBEING_KEYS = frozenset(
    {
        "at_least_one_weekend_rest_day",
        "no_evening_service",
        "no_morning_service",
        "max_two_coupures_per_week",
        "max_three_coupures_per_week",
        "two_consecutive_rest_days",
        "weekend_off_every_two_weeks",
    }
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
class Wellbeing:
    consecutive_rest: bool = False
    weekend: WeekendChoice | None = None
    max_services: MappingProxyType[str, int] = field(default_factory=lambda: MappingProxyType({}))
    max_coupures_per_week: int | None = None

    def __post_init__(self) -> None:
        if self.weekend is not None and not isinstance(self.weekend, WeekendChoice):
            object.__setattr__(self, "weekend", WeekendChoice(self.weekend))
        caps: dict[str, int] = {}
        for service_id, limit in dict(self.max_services).items():
            if service_id not in COMPANY_SERVICE_IDS:
                raise ValueError(f"Unknown max_services key: {service_id}")
            if int(limit) < 0:
                raise ValueError("max_services limits must be >= 0")
            caps[service_id] = int(limit)
        object.__setattr__(self, "max_services", MappingProxyType(caps))
        if self.max_coupures_per_week is not None and self.max_coupures_per_week < 0:
            raise ValueError("max_coupures_per_week must be >= 0")


@dataclass(frozen=True)
class Unavailability:
    """Restaurateur-stated unavailability: one weekday × one company service."""

    weekday: str
    service_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "weekday", self.weekday.lower())
        if self.weekday not in WEEKDAYS:
            raise ValueError(f"Unknown weekday: {self.weekday}")
        if self.service_id not in COMPANY_SERVICE_IDS:
            raise ValueError(f"Unknown company service: {self.service_id}")

    def blocks(self, weekday: str, service_id: str) -> bool:
        return weekday_index(self.weekday) == weekday_index(weekday) and self.service_id == service_id


@dataclass(frozen=True)
class Employee:
    id: str
    name: str
    role: Role
    team: Team
    contractual_hours_per_week: float
    unavailabilities: tuple[Unavailability, ...] = ()
    wellbeing: Wellbeing = field(default_factory=Wellbeing)
    forced_off_days: frozenset[int] = field(default_factory=frozenset)
    min_shift_hours: float = DEFAULT_MIN_SHIFT_HOURS
    invite_token: str = field(default_factory=lambda: secrets.token_urlsafe(16))

    def __post_init__(self) -> None:
        if self.team != self.role.team:
            raise TeamMismatchError(
                f"Employee {self.name} team {self.team.value} does not match role team {self.role.team.value}"
            )
        if self.min_shift_hours <= 0:
            raise ValueError("min_shift_hours must be > 0")
        object.__setattr__(self, "forced_off_days", frozenset(self.forced_off_days))
        if not self.invite_token or self.invite_token == self.id:
            token = secrets.token_urlsafe(16)
            while token == self.id:
                token = secrets.token_urlsafe(16)
            object.__setattr__(self, "invite_token", token)

    @property
    def level(self) -> int:
        return self.role.level

    def with_unavailability(self, pattern: Unavailability) -> Employee:
        return replace(self, unavailabilities=self.unavailabilities + (pattern,))

    def with_wellbeing(self, wellbeing: Wellbeing) -> Employee:
        return replace(self, wellbeing=wellbeing)


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
