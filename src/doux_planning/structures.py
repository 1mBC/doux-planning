from __future__ import annotations

from dataclasses import dataclass, replace

from doux_planning.types import ServiceName, Team, validate_quantum, WEEKDAYS


class StructuralEditRequiresCycleSandbox(ValueError):
    pass


@dataclass(frozen=True)
class ArrivalWave:
    time_minutes: int
    post_levels: tuple[int, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "time_minutes", validate_quantum(self.time_minutes))
        if not self.post_levels:
            raise ValueError("Arrival wave must fill at least one post")


@dataclass(frozen=True)
class DepartureWave:
    time_minutes: int
    remaining_post_levels: tuple[int, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "time_minutes", validate_quantum(self.time_minutes))


@dataclass(frozen=True)
class ServiceStructure:
    id: str
    team: Team
    service_id: str
    weekdays: frozenset[str]
    arrivals: tuple[ArrivalWave, ...]
    departures: tuple[DepartureWave, ...]
    weekday_choice_explained: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "weekdays", frozenset(day.lower() for day in self.weekdays))
        unknown = self.weekdays - set(WEEKDAYS)
        if unknown:
            raise ValueError(f"Unknown weekdays: {unknown}")
        if not self.weekday_choice_explained:
            raise ValueError(
                "Explain that a different structure can be defined for days that run differently."
            )
        times = [wave.time_minutes for wave in self.arrivals] + [
            wave.time_minutes for wave in self.departures
        ]
        if times != sorted(times):
            raise ValueError("Waves must be in chronological order")

    def applies_to(self, weekday: str) -> bool:
        return weekday.lower() in self.weekdays

    def with_weekdays(self, weekdays: frozenset[str] | set[str]) -> ServiceStructure:
        return replace(self, weekdays=frozenset(weekdays))


@dataclass(frozen=True)
class RestaurantHours:
    mode: str
    services: tuple[str, ...]
    closed_weekdays: frozenset[str] = frozenset()
    closed_services: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        object.__setattr__(self, "closed_weekdays", frozenset(self.closed_weekdays))
        object.__setattr__(self, "closed_services", frozenset(self.closed_services))
        if self.mode == ServiceName.CONTINUOUS.value:
            if self.services != (ServiceName.CONTINUOUS.value,):
                raise ValueError("Continuous mode uses a single continuous service")
        elif not self.services:
            raise ValueError("At least one service is required")

    def is_closed(self, weekday: str, service_id: str) -> bool:
        if weekday.lower() in self.closed_weekdays:
            return True
        return service_id in self.closed_services

    @classmethod
    def continuous(cls, closed_weekdays: frozenset[str] | set[str] = frozenset()) -> RestaurantHours:
        return cls(
            mode=ServiceName.CONTINUOUS.value,
            services=(ServiceName.CONTINUOUS.value,),
            closed_weekdays=frozenset(closed_weekdays),
        )

    @classmethod
    def multi_service(cls, *service_ids: str, closed_weekdays: frozenset[str] | set[str] = frozenset()) -> RestaurantHours:
        return cls(mode="services", services=service_ids, closed_weekdays=frozenset(closed_weekdays))


def brasserie_template(team: Team, service_id: str, weekdays: frozenset[str] | set[str]) -> ServiceStructure:
    """Editable pre-filled waves for a service-based brasserie."""
    if service_id == ServiceName.MIDDAY.value:
        arrivals = (
            ArrivalWave(10 * 60, (4,)),
            ArrivalWave(11 * 60, (2, 2)),
            ArrivalWave(11 * 60 + 30, (1,)),
        )
        departures = (
            DepartureWave(14 * 60 + 30, (4, 2)),
            DepartureWave(15 * 60, (4,)),
            DepartureWave(16 * 60, ()),
        )
    elif service_id == ServiceName.EVENING.value:
        arrivals = (
            ArrivalWave(17 * 60 + 30, (4,)),
            ArrivalWave(18 * 60, (2, 2)),
            ArrivalWave(18 * 60 + 30, (1,)),
        )
        departures = (
            DepartureWave(22 * 60, (4, 2)),
            DepartureWave(23 * 60, ()),
        )
    else:
        arrivals = (
            ArrivalWave(7 * 60, (3,)),
            ArrivalWave(8 * 60, (2,)),
        )
        departures = (
            DepartureWave(11 * 60, ()),
        )
    return ServiceStructure(
        id=f"template-{team.value}-{service_id}",
        team=team,
        service_id=service_id,
        weekdays=frozenset(weekdays),
        arrivals=arrivals,
        departures=departures,
        weekday_choice_explained=True,
    )
