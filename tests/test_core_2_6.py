from dataclasses import replace

from doux_planning.engine import PlanningDraft
from doux_planning.engines import core_2_6
from doux_planning.engines.mix_0 import MIX0_EXPERTS
from doux_planning.engines.registry import generate_for, list_engine_refs
from doux_planning.staff import Wellbeing
from doux_planning.structures import ArrivalWave, DepartureWave, RestaurantHours, ServiceStructure
from doux_planning.types import SearchEffort, ServiceName, Team, WEEKDAYS, WeekendChoice
from tests.fixtures import employee


def _person(
    name: str,
    employee_id: str,
    *,
    hours: float = 35,
    weekend: WeekendChoice | None = None,
    min_shift: float | None = None,
    forced_off: frozenset[int] = frozenset(),
):
    person = employee(name, "plongeur", hours=hours, employee_id=employee_id)
    person = person.with_wellbeing(Wellbeing(weekend=weekend))
    updates = {}
    if min_shift is not None:
        updates["min_shift_hours"] = {ServiceName.MIDDAY.value: min_shift}
    if forced_off:
        updates["forced_off_days"] = forced_off
    if updates:
        person = replace(person, **updates)
    return person


def _posts(structure_id: str, weekdays, start: int, end: int, levels: tuple[int, ...] = (1,)):
    return ServiceStructure(
        id=structure_id,
        team=Team.CUISINE,
        service_id=ServiceName.MIDDAY.value,
        weekdays=frozenset(weekdays),
        arrivals=(ArrivalWave(start, levels),),
        departures=(DepartureWave(end, ()),),
    )


def _span_posts():
    """A 4h post inside a service that runs until 18:00, plus the later 6h post."""
    return ServiceStructure(
        id="span",
        team=Team.CUISINE,
        service_id=ServiceName.MIDDAY.value,
        weekdays=frozenset({"monday"}),
        arrivals=(ArrivalWave(10 * 60, (1,)), ArrivalWave(12 * 60, (1,))),
        departures=(DepartureWave(14 * 60, (1,)), DepartureWave(18 * 60, ()),),
    )


def _draft(people, structures, closed_weekdays=frozenset()):
    return PlanningDraft(
        employees=tuple(people),
        structures=tuple(structures),
        hours=RestaurantHours.multi_service(
            ServiceName.MIDDAY.value, closed_weekdays=frozenset(closed_weekdays)
        ),
    )


def _off_both(assignments, employee_id: str, days: tuple[int, int]) -> bool:
    return not any(
        shift.employee_id == employee_id and shift.day_index in days for shift in assignments
    )


def _week_hours(assignments, employee_id: str, week_start: int) -> float:
    return sum(
        shift.duration_hours
        for shift in assignments
        if shift.employee_id == employee_id and week_start <= shift.day_index < week_start + 7
    )


def _holder(assignments, day_index: int, start: int):
    matches = [
        shift
        for shift in assignments
        if shift.day_index == day_index and shift.start_minutes == start
    ]
    assert len(matches) == 1
    return matches[0]


def test_four_every_two_split_two_and_two():
    people = [
        _person(f"E{index}", f"e{index}", weekend=WeekendChoice.EVERY_TWO) for index in range(1, 5)
    ]
    draft = _draft(people, [_posts("midi", WEEKDAYS, 10 * 60, 14 * 60, (1, 1))])
    result = core_2_6.generate_cycle(draft, SearchEffort.MINIMAL)
    off_a = [person.id for person in people if _off_both(result.assignments, person.id, (5, 6))]
    off_b = [person.id for person in people if _off_both(result.assignments, person.id, (12, 13))]
    assert off_a == ["e1", "e3"]
    assert off_b == ["e2", "e4"]
    for person in people:
        assert _off_both(result.assignments, person.id, (5, 6)) != _off_both(
            result.assignments, person.id, (12, 13)
        )


def test_even_and_odd_stay_locked_with_gap_at_most_one():
    people = [
        _person("Even", "even", weekend=WeekendChoice.EVEN),
        _person("Odd", "odd", weekend=WeekendChoice.ODD),
        _person("P1", "p1", weekend=WeekendChoice.EVERY_TWO),
        _person("P2", "p2", weekend=WeekendChoice.EVERY_TWO),
    ]
    draft = _draft(people, [_posts("midi", WEEKDAYS, 10 * 60, 14 * 60, (1, 1))])
    result = core_2_6.generate_cycle(draft, SearchEffort.MINIMAL)
    assert _off_both(result.assignments, "even", (5, 6))
    assert not _off_both(result.assignments, "even", (12, 13))
    assert _off_both(result.assignments, "odd", (12, 13))
    assert not _off_both(result.assignments, "odd", (5, 6))
    off_a = sum(_off_both(result.assignments, person.id, (5, 6)) for person in people)
    off_b = sum(_off_both(result.assignments, person.id, (12, 13)) for person in people)
    assert abs(off_a - off_b) <= 1


def test_closed_sunday_counts_as_off_and_saturday_is_the_shift():
    person = _person("Even", "even", weekend=WeekendChoice.EVEN)
    draft = _draft(
        [person],
        [_posts("midi", WEEKDAYS, 10 * 60, 14 * 60, (1,))],
        closed_weekdays=frozenset({"sunday"}),
    )
    result = core_2_6.generate_cycle(draft, SearchEffort.MINIMAL)
    worked = {shift.day_index for shift in result.assignments}
    assert 5 not in worked
    assert 6 not in worked
    assert 12 in worked
    assert 13 not in worked


def test_infeasible_balance_keeps_even_lock():
    people = [
        _person("Even", "even", weekend=WeekendChoice.EVEN),
        _person("P", "p", weekend=WeekendChoice.EVERY_TWO, forced_off=frozenset({5, 6})),
    ]
    draft = _draft(people, [_posts("midi", WEEKDAYS, 10 * 60, 14 * 60, (1,))])
    result = core_2_6.generate_cycle(draft, SearchEffort.MINIMAL)
    assert _off_both(result.assignments, "even", (5, 6))
    assert not _off_both(result.assignments, "even", (12, 13))


def test_infeasible_balance_reenumerates_hard_calendars():
    first = _person("A", "a", weekend=WeekendChoice.EVERY_TWO, forced_off=frozenset({12, 13}))
    second = _person("B", "b", weekend=WeekendChoice.EVERY_TWO)
    draft = _draft([first, second], [_posts("midi", WEEKDAYS, 10 * 60, 14 * 60, (1,))])
    calendars = core_2_6._enumerate_rest_days(draft, SearchEffort.MINIMAL)
    assert len(calendars) > 1
    for off in calendars:
        assert {12, 13} <= off["a"]
        assert not ({5, 6} <= off["a"])
    result = core_2_6.generate_cycle(draft, SearchEffort.MINIMAL)
    worked = {shift.day_index for shift in result.assignments if shift.employee_id == "a"}
    assert 5 in worked
    assert 12 not in worked
    assert 13 not in worked


def test_no_weekend_wish_can_work_both():
    person = _person("Free", "free")
    draft = _draft(
        [person],
        [_posts("midi", WEEKDAYS, 10 * 60, 14 * 60, (1,))],
        closed_weekdays=frozenset(day for day in WEEKDAYS if day not in {"saturday", "sunday"}),
    )
    result, trace = generate_for("core-2.6", draft, SearchEffort.MINIMAL)
    worked = {shift.day_index for shift in result.assignments if shift.employee_id == "free"}
    assert {5, 6, 12, 13} <= worked
    assert trace.seeder == "empty"
    assert trace.seed_index == 0
    assert trace.n_locks == 0
    assert trace.seeds_infeasible == 0
    assert set(trace.calendars_by_seeder) == {"empty"}


def test_under_contract_beats_someone_already_at_contract():
    people = [_person("Ada", "ada", hours=4), _person("Bea", "bea", hours=35)]
    draft = _draft(people, [_posts("midi", {"monday", "tuesday"}, 10 * 60, 14 * 60, (1,))])
    assignments = core_2_6._fill_assignments(draft, {person.id: set() for person in people}, people)
    assert _holder(assignments, 1, 10 * 60).employee_id == "bea"


def test_only_eligible_person_over_contract_takes_the_post():
    person = _person("Ada", "ada", hours=3)
    draft = _draft([person], [_posts("midi", {"monday"}, 10 * 60, 14 * 60, (1,))])
    assignments = core_2_6._fill_assignments(draft, {"ada": set()}, [person])
    shift = _holder(assignments, 0, 10 * 60)
    assert shift.employee_id == "ada"
    assert shift.duration_hours > person.contractual_hours_per_week


def test_lower_ratio_wins_for_same_level_and_contract():
    people = [_person("Ada", "ada", hours=35), _person("Bea", "bea", hours=35)]
    draft = _draft(people, [_posts("midi", {"monday", "tuesday"}, 10 * 60, 14 * 60, (1,))])
    assignments = core_2_6._fill_assignments(draft, {person.id: set() for person in people}, people)
    assert _holder(assignments, 0, 10 * 60).employee_id == "ada"
    assert _holder(assignments, 1, 10 * 60).employee_id == "bea"


def test_transfer_reduces_gap_above_half_hour():
    people = [
        _person("Ada", "a", hours=35, min_shift=1),
        _person("Bea", "b", hours=35, min_shift=6),
    ]
    short_days = {"monday", "tuesday", "wednesday", "thursday"}
    draft = _draft(
        people,
        [
            _posts("short", short_days, 10 * 60, 13 * 60, (1,)),
            _posts("long", {"friday"}, 10 * 60, 16 * 60, (1,)),
        ],
    )
    assignments = core_2_6._fill_assignments(draft, {person.id: set() for person in people}, people)
    ada = _week_hours(assignments, "a", 0)
    bea = _week_hours(assignments, "b", 0)
    assert abs(ada - bea) <= 0.5
    assert bea <= ada + 1e-9
    assert bea > 6


def test_rest_goes_to_the_higher_surplus_day():
    people = [
        _person("A", "a"),
        _person("M1", "m1", forced_off=frozenset({1})),
        _person("M2", "m2", forced_off=frozenset({1})),
        _person("M3", "m3"),
    ]
    draft = _draft(
        people,
        [
            _posts("tue", {"tuesday"}, 10 * 60, 14 * 60, (1, 1, 1)),
            _posts("wed", {"wednesday"}, 10 * 60, 14 * 60, (1,)),
            _posts("other", {"monday", "thursday", "friday", "saturday", "sunday"}, 10 * 60, 14 * 60, (1, 1)),
        ],
    )
    off = core_2_6._surplus_rest_days(draft)
    assert 2 in off["a"]
    assert 1 not in off["a"]


def test_window_is_exact_when_someone_fits():
    people = [
        _person("Fit", "fit", min_shift=2),
        _person("Tall", "tall", min_shift=8),
    ]
    draft = _draft(people, [_posts("midi", {"monday"}, 10 * 60, 14 * 60, (1,))])
    assignments = core_2_6._fill_assignments(draft, {person.id: set() for person in people}, people)
    shift = _holder(assignments, 0, 10 * 60)
    assert shift.employee_id == "fit"
    assert shift.end_minutes == 14 * 60


def test_window_stays_exact_when_every_minimum_is_longer():
    people = [
        _person("Ada", "ada", min_shift=8),
        _person("Bea", "bea", min_shift=8),
    ]
    draft = _draft(people, [_span_posts()])
    assignments = core_2_6._fill_assignments(draft, {person.id: set() for person in people}, people)
    early = _holder(assignments, 0, 10 * 60)
    late = _holder(assignments, 0, 12 * 60)
    assert early.end_minutes == 14 * 60
    assert late.end_minutes == 18 * 60
    assert early.employee_id in {"ada", "bea"}
    assert late.employee_id in {"ada", "bea"}
    assert early.employee_id != late.employee_id


def test_mix0_does_not_include_core_2_6():
    assert "core-2.6" not in MIX0_EXPERTS


def test_registry_inserts_core_2_6_after_core_2_5():
    refs = list_engine_refs()
    assert refs[refs.index("core-2.5") + 1] == "core-2.6"
    assert refs[-1] == "mix-0"
