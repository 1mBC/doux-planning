from doux_planning.staff import Employee, Role, RoleLadder
from doux_planning.structures import (
    ArrivalWave,
    DepartureWave,
    RestaurantHours,
    ServiceStructure,
    brasserie_template,
)
from doux_planning.types import ServiceName, Team, WellbeingPreference


def cuisine_ladder() -> RoleLadder:
    roles = (
        Role("chef", 4, Team.CUISINE),
        Role("sous-chef", 3, Team.CUISINE),
        Role("commis", 2, Team.CUISINE),
        Role("plongeur", 1, Team.CUISINE),
    )
    return RoleLadder(Team.CUISINE, roles, substitution_explained=True)


def employee(name: str, role_name: str, hours: float = 35, employee_id: str | None = None) -> Employee:
    ladder = cuisine_ladder()
    role = ladder.by_name(role_name)
    return Employee(
        id=employee_id or name.lower(),
        name=name,
        role=role,
        team=Team.CUISINE,
        contractual_hours_per_week=hours,
    )


def kitchen_midday_structure(weekdays: set[str] | frozenset[str] | None = None) -> ServiceStructure:
    days = frozenset(weekdays or {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"})
    return ServiceStructure(
        id="cuisine-midday",
        team=Team.CUISINE,
        service_id=ServiceName.MIDDAY.value,
        weekdays=days,
        arrivals=(
            ArrivalWave(10 * 60, (4,)),
            ArrivalWave(11 * 60, (2, 2)),
            ArrivalWave(11 * 60 + 30, (1,)),
        ),
        departures=(
            DepartureWave(14 * 60 + 30, (4, 2)),
            DepartureWave(15 * 60, (4,)),
            DepartureWave(16 * 60, ()),
        ),
    )


def kitchen_staff() -> tuple[Employee, ...]:
    return (
        employee("ChefA", "chef", employee_id="chef-a"),
        employee("ChefB", "chef", employee_id="chef-b"),
        employee("Second", "sous-chef", employee_id="second"),
        employee("Sam", "commis", employee_id="sam"),
    )
