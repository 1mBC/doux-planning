from dataclasses import replace

from doux_planning.engine import (
    GENERATION_HORIZON_DAYS,
    MINIMAL_CALENDARS,
    OPTIMIZED_CALENDAR_MULTIPLIER,
    SEARCH_CALENDAR_LIMITS,
    SEQUENTIAL_WEEK_SOLVE,
    EngineResult,
    PlanningDraft,
    Shift,
    evaluate,
    generate_cycle,
    publish_allowed,
    rank_candidates,
    swap_shifts,
    _attempt_key,
    _coupure_count_in_week,
    _enumerate_rest_days,
    _pick_for_post,
    _plan_rest_days,
)
from doux_planning.staff import Unavailability
from doux_planning.structures import ArrivalWave, DepartureWave, RestaurantHours, ServiceStructure
from doux_planning.staff import Wellbeing
from doux_planning.types import SearchEffort, ServiceName, Team, WarningSeverity, WeekendChoice, WEEKDAYS
from tests.fixtures import employee, kitchen_midday_structure, kitchen_staff


def _draft(assignments=(), employees=None, extra_structures=None) -> PlanningDraft:
    structures = (kitchen_midday_structure(),)
    if extra_structures:
        structures = structures + extra_structures
    return PlanningDraft(
        employees=employees or kitchen_staff(),
        structures=structures,
        hours=RestaurantHours.multi_service(ServiceName.MIDDAY.value),
        assignments=tuple(assignments),
    )


def _shift(employee_id, day, start, end, post, weekday=None, service=ServiceName.MIDDAY.value) -> Shift:
    days = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
    return Shift(
        employee_id=employee_id,
        day_index=day,
        weekday=weekday or days[day % 7],
        service_id=service,
        team=Team.CUISINE,
        start_minutes=start,
        end_minutes=end,
        post_level=post,
    )


def test_empty_plonge_is_couverture_warning():
    assignments = [
        _shift("chef-a", 0, 10 * 60, 16 * 60, 4),
        _shift("chef-b", 0, 11 * 60, 15 * 60, 3),
        _shift("second", 0, 11 * 60, 14 * 60 + 30, 2),
        _shift("sam", 0, 11 * 60, 14 * 60 + 30, 2),
    ]
    result = evaluate(_draft(assignments))
    assert "empty_post" in result.codes()
    assert result.of_severity(WarningSeverity.COUVERTURE)


def test_chef_starting_late_leaves_morning_hole():
    assignments = [_shift("chef-a", 0, 11 * 60, 16 * 60, 4)]
    result = evaluate(_draft(assignments))
    hole = next(
        item
        for item in result.of_severity(WarningSeverity.COUVERTURE)
        if item.code == "empty_post" and "niveau 4" in item.message and "10h" in item.message
    )
    assert hole.day_index == 0
    assert "lundi" in hole.message
    assert "sem. A" in hole.message
    assert "déjeuner" in hole.message
    assert "10h–11h" in hole.message


def test_interdit_fixtures():
    short_rest = [
        _shift("chef-a", 0, 10 * 60, 23 * 60, 4, weekday="monday"),
        _shift("chef-a", 1, 8 * 60, 16 * 60, 4, weekday="tuesday"),
    ]
    rest = evaluate(_draft(short_rest, employees=(employee("ChefA", "chef", employee_id="chef-a"),)))
    assert "rest_between_days" in rest.codes()

    no_rest_days = [
        _shift("chef-a", day, 10 * 60, 16 * 60, 4) for day in range(7)
    ]
    weekly = evaluate(_draft(no_rest_days, employees=(employee("ChefA", "chef", employee_id="chef-a"),)))
    assert "weekly_rest_days" in weekly.codes()

    coupure = [
        _shift("chef-a", 0, 8 * 60, 11 * 60, 4, service=ServiceName.MORNING.value),
        _shift("chef-a", 0, 18 * 60, 22 * 60, 4, service=ServiceName.EVENING.value),
    ]
    hours = RestaurantHours.multi_service(ServiceName.MORNING.value, ServiceName.MIDDAY.value, ServiceName.EVENING.value)
    draft = PlanningDraft(
        employees=(employee("ChefA", "chef", employee_id="chef-a"),),
        structures=(kitchen_midday_structure(),),
        hours=hours,
        assignments=tuple(coupure),
    )
    assert "max_coupure" in evaluate(draft).codes()

    long_day = [_shift("chef-a", 0, 8 * 60, 21 * 60, 4)]
    assert "max_daily_hours" in evaluate(_draft(long_day, employees=(employee("ChefA", "chef", employee_id="chef-a"),))).codes()

    long_week = [_shift("chef-a", day, 8 * 60, 18 * 60, 4) for day in range(6)]
    assert "max_weekly_hours" in evaluate(
        _draft(long_week, employees=(employee("ChefA", "chef", employee_id="chef-a"),))
    ).codes()

    unavailable = employee("ChefA", "chef", employee_id="chef-a").with_unavailability(
        Unavailability(weekday="monday", service_id=ServiceName.MIDDAY.value)
    )
    assigned = [_shift("chef-a", 0, 10 * 60, 16 * 60, 4)]
    assert "unavailability" in evaluate(_draft(assigned, employees=(unavailable,))).codes()


def test_cycle_wrap_rest_is_interdit():
    person = employee("ChefA", "chef", employee_id="chef-a")
    assignments = [
        _shift("chef-a", 13, 14 * 60, 23 * 60, 4, weekday="sunday"),
        _shift("chef-a", 0, 8 * 60, 16 * 60, 4, weekday="monday"),
    ]
    result = evaluate(_draft(assignments, employees=(person,)))
    assert "rest_between_days" in result.codes()


def test_souhait_consecutive_rest_and_contract_hours():
    person = employee("Sam", "commis", hours=20, employee_id="sam").with_wellbeing(
        Wellbeing(consecutive_rest=True)
    )
    assignments = [
        _shift("sam", 0, 11 * 60, 15 * 60, 2),
        _shift("sam", 1, 11 * 60, 15 * 60, 2),
        _shift("sam", 3, 11 * 60, 15 * 60, 2),
        _shift("sam", 5, 11 * 60, 15 * 60, 2),
    ]
    result = evaluate(_draft(assignments, employees=(person,)))
    assert "consecutive_rest_days" in result.codes()
    assert "contract_hours" in result.codes()
    assert all(item.severity is WarningSeverity.SOUHAIT for item in result.warnings if item.code in {"consecutive_rest_days", "contract_hours"})


def test_publish_with_acknowledged_interdit():
    person = employee("ChefA", "chef", employee_id="chef-a")
    assignments = [
        _shift("chef-a", 0, 10 * 60, 23 * 60, 4),
        _shift("chef-a", 1, 8 * 60, 16 * 60, 4),
    ]
    result = evaluate(_draft(assignments, employees=(person,)))
    interdits = result.of_severity(WarningSeverity.INTERDIT)
    assert interdits
    assert not publish_allowed(result, frozenset())
    acked = frozenset(item.key() for item in interdits)
    assert publish_allowed(result, acked)


def test_rank_candidates_orders_by_warnings_then_fit():
    staff = kitchen_staff()
    draft = _draft()
    ranked = rank_candidates(draft, 0, "monday", ServiceName.MIDDAY.value, Team.CUISINE, 11 * 60 + 30, 15 * 60, 1)
    assert ranked
    assert ranked[0].employee.level >= 1
    assert ranked[0].interdit_count <= ranked[-1].interdit_count


def test_swap_matches_manual_reassign():
    a = _shift("chef-a", 0, 10 * 60, 16 * 60, 4)
    b = _shift("sam", 1, 11 * 60, 15 * 60, 2, weekday="tuesday")
    draft = _draft([a, b])
    swapped = swap_shifts(draft, a, b)
    remaining = [shift for shift in draft.assignments if shift not in (a, b)]
    manual = evaluate(
        draft.with_assignments(
            tuple(remaining)
            + (
                Shift(
                    employee_id="sam",
                    day_index=a.day_index,
                    weekday=a.weekday,
                    service_id=a.service_id,
                    team=a.team,
                    start_minutes=a.start_minutes,
                    end_minutes=a.end_minutes,
                    post_level=a.post_level,
                ),
                Shift(
                    employee_id="chef-a",
                    day_index=b.day_index,
                    weekday=b.weekday,
                    service_id=b.service_id,
                    team=b.team,
                    start_minutes=b.start_minutes,
                    end_minutes=b.end_minutes,
                    post_level=b.post_level,
                ),
            )
        )
    )
    assert swapped.codes() == manual.codes()


def test_generate_is_fourteen_day_single_solve():
    assert GENERATION_HORIZON_DAYS == 14
    assert SEQUENTIAL_WEEK_SOLVE is False
    person = employee("ChefA", "chef", hours=35, employee_id="chef-a").with_wellbeing(
        Wellbeing(weekend=WeekendChoice.EVERY_TWO)
    )
    draft = _draft(employees=(person,))
    result = generate_cycle(draft)
    by_day = {shift.day_index for shift in result.assignments}
    weekend_a = 5 in by_day or 6 in by_day
    weekend_b = 12 in by_day or 13 in by_day
    both_weekends_worked = (5 in by_day and 6 in by_day) and (12 in by_day and 13 in by_day)
    if both_weekends_worked:
        assert "weekend_every_two_weeks" in result.codes()
    else:
        assert not (weekend_a and weekend_b and not (5 in by_day or 6 in by_day))


def test_generate_skips_monday_unavailability():
    blocked = employee("ChefA", "chef", employee_id="chef-a").with_unavailability(
        Unavailability(weekday="monday", service_id=ServiceName.MIDDAY.value)
    )
    other = employee("ChefB", "chef", employee_id="chef-b")
    result = generate_cycle(_draft(employees=(blocked, other)))
    monday = [
        shift
        for shift in result.assignments
        if shift.employee_id == "chef-a" and shift.weekday == "monday"
    ]
    assert monday == []


def test_generate_skips_midday_can_work_evening():
    blocked = replace(
        employee("Sam", "commis", employee_id="sam").with_unavailability(
            Unavailability(weekday="monday", service_id=ServiceName.MIDDAY.value)
        ),
        forced_off_days=frozenset({1, 2, 8, 9}),
    )
    evening = ServiceStructure(
        id="cuisine-evening",
        team=Team.CUISINE,
        service_id=ServiceName.EVENING.value,
        weekdays=frozenset(WEEKDAYS),
        arrivals=(ArrivalWave(18 * 60, (1,)),),
        departures=(DepartureWave(22 * 60, ()),),
    )
    hours = RestaurantHours.multi_service(ServiceName.MIDDAY.value, ServiceName.EVENING.value)
    draft = PlanningDraft(
        employees=(blocked,),
        structures=(kitchen_midday_structure(), evening),
        hours=hours,
    )
    result = generate_cycle(draft)
    monday_midday = [
        shift
        for shift in result.assignments
        if shift.employee_id == "sam"
        and shift.weekday == "monday"
        and shift.service_id == ServiceName.MIDDAY.value
    ]
    monday_evening = [
        shift
        for shift in result.assignments
        if shift.employee_id == "sam"
        and shift.weekday == "monday"
        and shift.service_id == ServiceName.EVENING.value
    ]
    assert monday_midday == []
    assert monday_evening


def test_generate_prefers_exact_level_not_senior():
    senior = employee("ChefA", "chef", hours=39, employee_id="chef-a")
    junior = employee("Second", "sous-chef", hours=39, employee_id="second")
    structure = ServiceStructure(
        id="l3-only",
        team=Team.CUISINE,
        service_id=ServiceName.MIDDAY.value,
        weekdays=frozenset({"monday"}),
        arrivals=(ArrivalWave(11 * 60, (3,)),),
        departures=(DepartureWave(15 * 60, ()),),
    )
    hours = RestaurantHours.multi_service(ServiceName.MIDDAY.value, closed_weekdays=set(WEEKDAYS) - {"monday"})
    draft = PlanningDraft(employees=(senior, junior), structures=(structure,), hours=hours)
    result = generate_cycle(draft)
    l3 = [shift for shift in result.assignments if shift.post_level == 3]
    assert l3
    assert all(shift.employee_id == "second" for shift in l3)


def _two_open_days_structure(level: int) -> tuple[ServiceStructure, RestaurantHours]:
    structure = ServiceStructure(
        id=f"l{level}-only",
        team=Team.CUISINE,
        service_id=ServiceName.MIDDAY.value,
        weekdays=frozenset({"monday", "tuesday"}),
        arrivals=(ArrivalWave(11 * 60, (level,)),),
        departures=(DepartureWave(15 * 60, ()),),
    )
    hours = RestaurantHours.multi_service(
        ServiceName.MIDDAY.value,
        closed_weekdays=set(WEEKDAYS) - {"monday", "tuesday"},
    )
    return structure, hours


def test_generate_level4_takes_post_when_level3_at_hours():
    junior = employee("Second", "sous-chef", hours=4, employee_id="second")
    senior = employee("ChefA", "chef", hours=39, employee_id="chef-a")
    structure, hours = _two_open_days_structure(3)
    draft = PlanningDraft(employees=(senior, junior), structures=(structure,), hours=hours)
    result = generate_cycle(draft)
    week_a = [
        shift.employee_id
        for shift in result.assignments
        if shift.post_level == 3 and shift.day_index < 7
    ]
    junior_hours = sum(
        shift.duration_hours
        for shift in result.assignments
        if shift.employee_id == "second" and shift.day_index < 7
    )
    assert "second" in week_a
    assert "chef-a" in week_a
    assert junior_hours <= 4 + 1e-9


def test_generate_level3_takes_post_when_level2_at_hours():
    junior = employee("Sam", "commis", hours=4, employee_id="sam")
    mid = employee("Second", "sous-chef", hours=39, employee_id="second")
    structure, hours = _two_open_days_structure(2)
    draft = PlanningDraft(employees=(mid, junior), structures=(structure,), hours=hours)
    result = generate_cycle(draft)
    week_a = [
        shift.employee_id
        for shift in result.assignments
        if shift.post_level == 2 and shift.day_index < 7
    ]
    junior_hours = sum(
        shift.duration_hours
        for shift in result.assignments
        if shift.employee_id == "sam" and shift.day_index < 7
    )
    assert "sam" in week_a
    assert "second" in week_a
    assert junior_hours <= 4 + 1e-9


def test_generate_does_not_overfill_part_timer_while_teammate_under():
    part = employee("Lucie", "plongeur", hours=15, employee_id="lucie")
    full = employee("Vlad", "commis", hours=35, employee_id="vlad")
    evening = ServiceStructure(
        id="l1-eve",
        team=Team.CUISINE,
        service_id=ServiceName.EVENING.value,
        weekdays=frozenset({"monday", "tuesday", "wednesday", "thursday", "friday", "saturday"}),
        arrivals=(ArrivalWave(19 * 60, (1,)),),
        departures=(DepartureWave(23 * 60, ()),),
    )
    hours = RestaurantHours.multi_service(ServiceName.EVENING.value, closed_weekdays={"sunday"})
    result = generate_cycle(
        PlanningDraft(employees=(part, full), structures=(evening,), hours=hours)
    )
    lucie_week_a = sum(
        shift.duration_hours
        for shift in result.assignments
        if shift.employee_id == "lucie" and shift.day_index < 7
    )
    assert lucie_week_a <= 15 + 1e-9


def test_generate_caps_part_timer_shifts_to_hours_over_typical_post():
    part = employee("Lucie", "plongeur", hours=15, employee_id="lucie")
    full = employee("Vlad", "commis", hours=35, employee_id="vlad")
    evening = ServiceStructure(
        id="l1-eve-5h",
        team=Team.CUISINE,
        service_id=ServiceName.EVENING.value,
        weekdays=frozenset({"monday", "tuesday", "wednesday", "thursday", "friday", "saturday"}),
        arrivals=(ArrivalWave(19 * 60, (1,)),),
        departures=(DepartureWave(24 * 60, ()),),
    )
    hours = RestaurantHours.multi_service(ServiceName.EVENING.value, closed_weekdays={"sunday"})
    result = generate_cycle(
        PlanningDraft(employees=(part, full), structures=(evening,), hours=hours)
    )
    lucie_a = [
        shift for shift in result.assignments if shift.employee_id == "lucie" and shift.day_index < 7
    ]
    lucie_b = [
        shift for shift in result.assignments if shift.employee_id == "lucie" and shift.day_index >= 7
    ]
    assert len(lucie_a) <= 3
    assert len(lucie_b) <= 3


def test_generate_does_not_rest_the_only_people_who_can_cover():
    staff = (
        employee("A", "chef", employee_id="a"),
        employee("B", "sous-chef", employee_id="b"),
        employee("C", "commis", employee_id="c"),
        employee("D", "plongeur", employee_id="d"),
    )
    structure = ServiceStructure(
        id="four-monday",
        team=Team.CUISINE,
        service_id=ServiceName.MIDDAY.value,
        weekdays=frozenset({"monday"}),
        arrivals=(
            ArrivalWave(10 * 60, (4,)),
            ArrivalWave(11 * 60, (3,)),
            ArrivalWave(12 * 60, (2, 1)),
        ),
        departures=(DepartureWave(16 * 60, ()),),
    )
    hours = RestaurantHours.multi_service(
        ServiceName.MIDDAY.value, closed_weekdays=set(WEEKDAYS) - {"monday"}
    )
    result = generate_cycle(PlanningDraft(employees=staff, structures=(structure,), hours=hours))
    monday = [shift for shift in result.assignments if shift.day_index == 0]
    assert len(monday) == 4
    assert "empty_post" not in {
        warning.code for warning in result.warnings if warning.day_index == 0
    }


def test_weekend_off_counts_as_consecutive_rest():
    person = employee("Sam", "commis", hours=20, employee_id="sam").with_wellbeing(
        Wellbeing(consecutive_rest=True)
    )
    assignments = [_shift("sam", day, 11 * 60, 15 * 60, 2) for day in range(5)]
    result = evaluate(_draft(assignments, employees=(person,)))
    assert "consecutive_rest_days" not in result.codes()


def test_generate_consecutive_rest_still_works_saturday():
    theo = employee("Theo", "chef", hours=39, employee_id="theo").with_wellbeing(
        Wellbeing(consecutive_rest=True)
    )
    emma = employee("Emma", "sous-chef", hours=39, employee_id="emma")
    weekday = ServiceStructure(
        id="mid-week",
        team=Team.CUISINE,
        service_id=ServiceName.MIDDAY.value,
        weekdays=frozenset({"monday", "tuesday", "wednesday", "thursday", "friday"}),
        arrivals=(ArrivalWave(11 * 60, (3,)),),
        departures=(DepartureWave(15 * 60, ()),),
    )
    saturday = ServiceStructure(
        id="mid-sat",
        team=Team.CUISINE,
        service_id=ServiceName.MIDDAY.value,
        weekdays=frozenset({"saturday"}),
        arrivals=(ArrivalWave(10 * 60, (1,)),),
        departures=(DepartureWave(16 * 60, ()),),
    )
    hours = RestaurantHours.multi_service(ServiceName.MIDDAY.value, closed_weekdays={"sunday"})
    draft = PlanningDraft(employees=(theo, emma), structures=(weekday, saturday), hours=hours)
    off = _plan_rest_days(draft)
    assert off["theo"]
    result = generate_cycle(draft)
    saturday_posts = [
        shift for shift in result.assignments if shift.weekday == "saturday"
    ]
    assert saturday_posts


def test_generate_keeps_opener_for_earlier_level1():
    opener = employee("Aurore", "commis", hours=30, employee_id="aurore")
    later = employee("Vlad", "commis", hours=35, employee_id="vlad").with_unavailability(
        Unavailability(weekday="monday", service_id=ServiceName.MORNING.value)
    )
    chef = employee("Emma", "sous-chef", hours=39, employee_id="emma")
    structure = ServiceStructure(
        id="open-l1",
        team=Team.CUISINE,
        service_id=ServiceName.MIDDAY.value,
        weekdays=frozenset({"monday"}),
        arrivals=(
            ArrivalWave(10 * 60, (1,)),
            ArrivalWave(11 * 60, (3,)),
            ArrivalWave(12 * 60, (2,)),
        ),
        departures=(DepartureWave(16 * 60, ()),),
    )
    hours = RestaurantHours.multi_service(
        ServiceName.MIDDAY.value, closed_weekdays=set(WEEKDAYS) - {"monday"}
    )
    result = generate_cycle(
        PlanningDraft(employees=(opener, later, chef), structures=(structure,), hours=hours)
    )
    opening = [
        shift
        for shift in result.assignments
        if shift.start_minutes == 10 * 60 and shift.post_level == 1
    ]
    l2 = [shift for shift in result.assignments if shift.post_level == 2]
    assert opening
    assert opening[0].employee_id == "aurore"
    assert l2
    assert l2[0].employee_id == "vlad"


def test_prefer_completing_a_started_day():
    on_duty = employee("Aurore", "commis", hours=20, employee_id="aurore")
    idle = employee("Lucie", "plongeur", hours=15, employee_id="lucie")
    evening = ServiceStructure(
        id="eve-complete-day",
        team=Team.CUISINE,
        service_id=ServiceName.EVENING.value,
        weekdays=frozenset({"monday"}),
        arrivals=(ArrivalWave(18 * 60, (1,)),),
        departures=(DepartureWave(22 * 60, ()),),
    )
    draft = _draft(employees=(on_duty, idle), extra_structures=(evening,))
    assignments = [
        _shift("aurore", 0, 10 * 60, 14 * 60, 2),
        _shift("lucie", 1, 11 * 60, 14 * 60, 1),
    ]
    picked = _pick_for_post(
        draft,
        assignments,
        employee_pool=[on_duty, idle],
        window_level=1,
        day_index=0,
        weekday="monday",
        service_id=ServiceName.EVENING.value,
        team=Team.CUISINE,
        start_minutes=18 * 60,
        end_minutes=22 * 60,
        off_days={"aurore": set(), "lucie": set()},
    )
    assert picked is not None
    chosen, assigned = picked
    assert chosen.id == "aurore"
    assert assigned.end_minutes - assigned.start_minutes >= 4 * 60


def test_generate_does_not_exceed_weekly_coupure_cap():
    emma = employee("Emma", "sous-chef", hours=39, employee_id="emma").with_wellbeing(
        Wellbeing(max_coupures_per_week=2)
    )
    vlad = employee("Vlad", "commis", hours=39, employee_id="vlad")
    open_days = frozenset({"monday", "tuesday", "wednesday"})
    midday = ServiceStructure(
        id="mid-3d",
        team=Team.CUISINE,
        service_id=ServiceName.MIDDAY.value,
        weekdays=open_days,
        arrivals=(ArrivalWave(11 * 60, (1,)),),
        departures=(DepartureWave(15 * 60, ()),),
    )
    evening = ServiceStructure(
        id="eve-3d",
        team=Team.CUISINE,
        service_id=ServiceName.EVENING.value,
        weekdays=open_days,
        arrivals=(ArrivalWave(19 * 60, (1,)),),
        departures=(DepartureWave(23 * 60, ()),),
    )
    hours = RestaurantHours.multi_service(
        ServiceName.MIDDAY.value,
        ServiceName.EVENING.value,
        closed_weekdays=set(WEEKDAYS) - open_days,
    )
    result = generate_cycle(
        PlanningDraft(employees=(emma, vlad), structures=(midday, evening), hours=hours)
    )
    assert _coupure_count_in_week(result.assignments, "emma", 0) <= 2
    assert _coupure_count_in_week(result.assignments, "emma", 7) <= 2
    assert "max_coupures" not in result.codes()


def test_coupures_are_counted_per_week_not_per_cycle():
    person = employee("Emma", "sous-chef", hours=39, employee_id="emma").with_wellbeing(
        Wellbeing(max_coupures_per_week=2)
    )
    assignments = []
    for day in (0, 1, 2):
        assignments.append(_shift("emma", day, 11 * 60, 15 * 60, 3))
        assignments.append(
            _shift("emma", day, 19 * 60, 23 * 60, 3, service=ServiceName.EVENING.value)
        )
    for day in (7, 8):
        assignments.append(_shift("emma", day, 11 * 60, 15 * 60, 3))
        assignments.append(
            _shift("emma", day, 19 * 60, 23 * 60, 3, service=ServiceName.EVENING.value)
        )
    result = evaluate(_draft(assignments, employees=(person,)))
    coupures = [warning for warning in result.warnings if warning.code == "max_coupures"]
    assert len(coupures) == 1
    assert coupures[0].day_index == 0


def test_generate_cycle_is_deterministic():
    first = generate_cycle(_draft())
    second = generate_cycle(_draft())
    assert first.assignments == second.assignments


def test_enumerate_rest_days_returns_unique_covering_calendars():
    patterns = _enumerate_rest_days(_draft())
    assert patterns
    fingerprints = {
        tuple(sorted((employee_id, tuple(sorted(days))) for employee_id, days in pattern.items()))
        for pattern in patterns
    }
    assert len(fingerprints) == len(patterns)


def test_generate_skips_shift_shorter_than_employee_min():
    person = employee("Lucie", "plongeur", hours=15, employee_id="lucie")
    structure = ServiceStructure(
        id="short-eve",
        team=Team.CUISINE,
        service_id=ServiceName.EVENING.value,
        weekdays=frozenset({"monday"}),
        arrivals=(ArrivalWave(19 * 60, (1,)),),
        departures=(DepartureWave(22 * 60, ()),),
    )
    hours = RestaurantHours.multi_service(
        ServiceName.EVENING.value, closed_weekdays=set(WEEKDAYS) - {"monday"}
    )
    result = generate_cycle(
        PlanningDraft(employees=(person,), structures=(structure,), hours=hours)
    )
    assert all(shift.duration_hours >= 4 for shift in result.assignments)
    assert not any(shift.day_index == 0 for shift in result.assignments)


def test_generate_cycle_default_search_is_optimized():
    draft = _draft()
    assert draft.search_effort is SearchEffort.OPTIMIZED
    first = generate_cycle(draft)
    second = generate_cycle(draft, search=SearchEffort.OPTIMIZED)
    assert first.assignments == second.assignments


def test_search_effort_calendar_limits():
    assert SEARCH_CALENDAR_LIMITS[SearchEffort.MINIMAL] == MINIMAL_CALENDARS == 16
    assert SEARCH_CALENDAR_LIMITS[SearchEffort.OPTIMIZED] == 16 * OPTIMIZED_CALENDAR_MULTIPLIER
    assert SEARCH_CALENDAR_LIMITS[SearchEffort.MAXIMAL] is None


def test_attempt_prefers_fewer_shifts_below_role():
    chef = employee("Chef", "chef", hours=4, employee_id="chef-a")
    draft = _draft(employees=(chef,))
    exact = EngineResult(assignments=(_shift("chef-a", 0, 10 * 60, 14 * 60, 4),), warnings=())
    below = EngineResult(assignments=(_shift("chef-a", 0, 10 * 60, 14 * 60, 1),), warnings=())
    assert _attempt_key(draft, below) > _attempt_key(draft, exact)


def test_generate_reassigns_same_day_to_fill_a_hole():
    alex = employee("Alex", "commis", hours=4, employee_id="alex")
    blair = employee("Blair", "commis", hours=4, employee_id="blair").with_unavailability(
        Unavailability(weekday="monday", service_id=ServiceName.EVENING.value)
    )
    casey = replace(
        employee("Casey", "plongeur", hours=4, employee_id="casey").with_unavailability(
            Unavailability(weekday="monday", service_id=ServiceName.MIDDAY.value)
        ),
        forced_off_days=frozenset({0}),
    )
    midday = ServiceStructure(
        id="mid-mon",
        team=Team.CUISINE,
        service_id=ServiceName.MIDDAY.value,
        weekdays=frozenset({"monday"}),
        arrivals=(ArrivalWave(11 * 60, (2,)),),
        departures=(DepartureWave(15 * 60, ()),),
    )
    evening = ServiceStructure(
        id="eve-mon",
        team=Team.CUISINE,
        service_id=ServiceName.EVENING.value,
        weekdays=frozenset({"monday"}),
        arrivals=(ArrivalWave(19 * 60, (1,)),),
        departures=(DepartureWave(23 * 60, ()),),
    )
    hours = RestaurantHours.multi_service(
        ServiceName.MIDDAY.value,
        ServiceName.EVENING.value,
        closed_weekdays=set(WEEKDAYS) - {"monday"},
    )
    result = generate_cycle(
        PlanningDraft(employees=(alex, blair, casey), structures=(midday, evening), hours=hours)
    )
    monday = [shift for shift in result.assignments if shift.day_index == 0]
    assert any(shift.service_id == ServiceName.MIDDAY.value for shift in monday)
    assert any(shift.service_id == ServiceName.EVENING.value for shift in monday)
    assert "empty_post" not in {
        warning.code for warning in result.warnings if warning.day_index == 0
    }


def test_short_post_is_stretched_to_employee_min_shift():
    person = employee("Lucie", "plongeur", hours=20, employee_id="lucie")
    evening = ServiceStructure(
        id="short-closer",
        team=Team.CUISINE,
        service_id=ServiceName.EVENING.value,
        weekdays=frozenset({"monday"}),
        arrivals=(ArrivalWave(19 * 60 + 30, (1,)),),
        departures=(DepartureWave(22 * 60 + 30, ()), DepartureWave(24 * 60, ())),
    )
    hours = RestaurantHours.multi_service(
        ServiceName.EVENING.value, closed_weekdays=set(WEEKDAYS) - {"monday"}
    )
    result = generate_cycle(PlanningDraft(employees=(person,), structures=(evening,), hours=hours))
    monday = [shift for shift in result.assignments if shift.day_index == 0]
    assert monday
    assert monday[0].start_minutes == 19 * 60 + 30
    assert monday[0].end_minutes == 23 * 60 + 30
    assert "empty_post" not in {warning.code for warning in result.warnings if warning.day_index == 0}


def test_short_post_stays_empty_when_service_cannot_reach_min_shift():
    person = employee("Lucie", "plongeur", hours=20, employee_id="lucie")
    evening = ServiceStructure(
        id="too-short",
        team=Team.CUISINE,
        service_id=ServiceName.EVENING.value,
        weekdays=frozenset({"monday"}),
        arrivals=(ArrivalWave(19 * 60 + 30, (1,)),),
        departures=(DepartureWave(22 * 60 + 30, ()),),
    )
    hours = RestaurantHours.multi_service(
        ServiceName.EVENING.value, closed_weekdays=set(WEEKDAYS) - {"monday"}
    )
    result = generate_cycle(PlanningDraft(employees=(person,), structures=(evening,), hours=hours))
    assert not [shift for shift in result.assignments if shift.day_index == 0]
    assert "empty_post" in {warning.code for warning in result.warnings if warning.day_index == 0}


def test_lower_personal_min_shift_fills_a_short_post():
    person = replace(employee("Lucie", "plongeur", hours=20, employee_id="lucie"), min_shift_hours=3.0)
    evening = ServiceStructure(
        id="three-hour",
        team=Team.CUISINE,
        service_id=ServiceName.EVENING.value,
        weekdays=frozenset({"monday"}),
        arrivals=(ArrivalWave(19 * 60 + 30, (1,)),),
        departures=(DepartureWave(22 * 60 + 30, ()),),
    )
    hours = RestaurantHours.multi_service(
        ServiceName.EVENING.value, closed_weekdays=set(WEEKDAYS) - {"monday"}
    )
    result = generate_cycle(PlanningDraft(employees=(person,), structures=(evening,), hours=hours))
    monday = [shift for shift in result.assignments if shift.day_index == 0]
    assert monday
    assert monday[0].duration_hours == 3.0


def _first_message(result, code: str) -> str:
    return next(item.message for item in result.warnings if item.code == code)


def test_remaining_evaluate_messages_are_french():
    chef = employee("ChefA", "chef", employee_id="chef-a")
    long_day = evaluate(_draft([_shift("chef-a", 0, 8 * 60, 21 * 60, 4)], employees=(chef,)))
    assert "max 11h" in _first_message(long_day, "max_daily_hours")
    assert "lundi" in _first_message(long_day, "max_daily_hours")

    no_rest = evaluate(
        _draft([_shift("chef-a", day, 10 * 60, 16 * 60, 4) for day in range(7)], employees=(chef,))
    )
    assert "/ 2 j. de repos" in _first_message(no_rest, "weekly_rest_days")
    assert "sem. A" in _first_message(no_rest, "weekly_rest_days")

    coupure = evaluate(
        PlanningDraft(
            employees=(chef,),
            structures=(kitchen_midday_structure(),),
            hours=RestaurantHours.multi_service(
                ServiceName.MORNING.value, ServiceName.MIDDAY.value, ServiceName.EVENING.value
            ),
            assignments=(
                _shift("chef-a", 0, 8 * 60, 11 * 60, 4, service=ServiceName.MORNING.value),
                _shift("chef-a", 0, 18 * 60, 22 * 60, 4, service=ServiceName.EVENING.value),
            ),
        )
    )
    assert "coupure > 5h" in _first_message(coupure, "max_coupure")
    assert "lundi" in _first_message(coupure, "max_coupure")

    long_week = evaluate(
        _draft([_shift("chef-a", day, 8 * 60, 18 * 60, 4) for day in range(6)], employees=(chef,))
    )
    assert "/ max 48h" in _first_message(long_week, "max_weekly_hours")
    assert "sem. A" in _first_message(long_week, "max_weekly_hours")

    blocked = chef.with_unavailability(Unavailability(weekday="monday", service_id=ServiceName.MIDDAY.value))
    indispo = evaluate(_draft([_shift("chef-a", 0, 10 * 60, 16 * 60, 4)], employees=(blocked,)))
    assert "posé sur indispo" in _first_message(indispo, "unavailability")
    assert "lundi déjeuner" in _first_message(indispo, "unavailability")

    closed = evaluate(
        PlanningDraft(
            employees=(chef,),
            structures=(kitchen_midday_structure(),),
            hours=RestaurantHours.multi_service(ServiceName.MIDDAY.value, closed_weekdays={"sunday"}),
            assignments=(_shift("chef-a", 6, 11 * 60, 15 * 60, 4),),
        )
    )
    assert "shift sur fermeture" in _first_message(closed, "assigned_on_closure")
    assert "dimanche · déjeuner" in _first_message(closed, "assigned_on_closure")

    sam = employee("Sam", "commis", hours=20, employee_id="sam").with_wellbeing(Wellbeing(consecutive_rest=True))
    souhait = evaluate(
        _draft(
            [
                _shift("sam", 0, 11 * 60, 15 * 60, 2),
                _shift("sam", 1, 11 * 60, 15 * 60, 2),
                _shift("sam", 3, 11 * 60, 15 * 60, 2),
                _shift("sam", 5, 11 * 60, 15 * 60, 2),
            ],
            employees=(sam,),
        )
    )
    assert "pas deux repos consécutifs" in _first_message(souhait, "consecutive_rest_days")
    assert "contrat" in _first_message(souhait, "contract_hours")
    assert "sem. A" in _first_message(souhait, "contract_hours")
    assert all(
        item.severity is WarningSeverity.SOUHAIT
        for item in souhait.warnings
        if item.code == "contract_hours"
    )

    ada = employee("Ada", "commis", hours=20, employee_id="ada").with_wellbeing(
        Wellbeing(weekend_rest_day=True, weekend=WeekendChoice.EVEN)
    )
    bea = employee("Bea", "commis", hours=20, employee_id="bea").with_wellbeing(Wellbeing(weekend=WeekendChoice.ODD))
    cal = employee("Cal", "commis", hours=20, employee_id="cal").with_wellbeing(
        Wellbeing(weekend=WeekendChoice.EVERY_TWO)
    )
    both_weekends = [_shift("ada", day, 11 * 60, 15 * 60, 2) for day in (5, 6, 12, 13)]
    both_weekends += [_shift("bea", day, 11 * 60, 15 * 60, 2) for day in (5, 6, 12, 13)]
    both_weekends += [_shift("cal", day, 11 * 60, 15 * 60, 2) for day in (5, 6, 12, 13)]
    weekends = evaluate(
        PlanningDraft(
            employees=(ada, bea, cal),
            structures=(kitchen_midday_structure(),),
            hours=RestaurantHours.multi_service(ServiceName.MIDDAY.value),
            assignments=tuple(both_weekends),
        )
    )
    assert "pas de repos samedi ou dimanche" in _first_message(weekends, "weekend_rest_day")
    assert "week-end pair non tenu" in _first_message(weekends, "weekend_even_weeks")
    assert "week-end impair non tenu" in _first_message(weekends, "weekend_odd_weeks")
    assert "pas exactement un week-end off / 14 j." in _first_message(weekends, "weekend_every_two_weeks")
