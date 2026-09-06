import pytest

from doux_planning.context import employee_board, empty_restaurant, upsert_employee, week_label_scheme
from doux_planning.engine import PlanningDraft, Shift, _has_weekday_consecutive_rest, evaluate
from doux_planning.planning import PlanningStore
from doux_planning.hydrate import _wellbeing, hydrate_delivered_cycle
from doux_planning.staff import REMOVED_WELLBEING_KEYS, Unavailability, Wellbeing
from doux_planning.structures import RestaurantHours
from doux_planning.types import ServiceName, Team, WarningSeverity, WeekendChoice
from tests.fixtures import employee, kitchen_midday_structure


def _shift(employee_id, day, start, end, post, service=ServiceName.MIDDAY.value) -> Shift:
    days = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
    return Shift(
        employee_id=employee_id,
        day_index=day,
        weekday=days[day % 7],
        service_id=service,
        team=Team.CUISINE,
        start_minutes=start,
        end_minutes=end,
        post_level=post,
    )


def test_sunday_closed_consecutive_rest_needs_sat_or_mon():
    hours = RestaurantHours.multi_service(ServiceName.MIDDAY.value, closed_weekdays={"sunday"})
    closed = {6}
    worked_except_sun = {0, 1, 2, 3, 4, 5}
    offs = {day for day in range(7) if day not in worked_except_sun}
    assert not _has_weekday_consecutive_rest(offs, 0, closed)
    offs_sat = offs | {5}
    assert _has_weekday_consecutive_rest(offs_sat, 0, closed)
    offs_mon = {day for day in range(7) if day not in {1, 2, 3, 4, 5}}
    assert _has_weekday_consecutive_rest(offs_mon, 0, closed)


def test_two_non_adjacent_closed_need_third_glued():
    closed = {2, 6}  # wednesday + sunday
    legal_only = closed
    assert not _has_weekday_consecutive_rest(legal_only, 0, closed)
    assert _has_weekday_consecutive_rest(legal_only | {1}, 0, closed)
    assert not _has_weekday_consecutive_rest(legal_only | {4}, 0, closed)


def test_weekend_even_odd_and_every_two_warnings():
    hours = RestaurantHours.multi_service(ServiceName.MIDDAY.value)
    staff = (
        employee("Ada", "commis", hours=20, employee_id="ada").with_wellbeing(Wellbeing(weekend=WeekendChoice.EVEN)),
        employee("Bea", "commis", hours=20, employee_id="bea").with_wellbeing(Wellbeing(weekend=WeekendChoice.ODD)),
        employee("Cal", "commis", hours=20, employee_id="cal").with_wellbeing(Wellbeing(weekend=WeekendChoice.EVERY_TWO)),
    )
    both_weekends = [_shift("ada", day, 11 * 60, 15 * 60, 2) for day in (5, 6, 12, 13)]
    both_weekends += [_shift("bea", day, 11 * 60, 15 * 60, 2) for day in (5, 6, 12, 13)]
    both_weekends += [_shift("cal", day, 11 * 60, 15 * 60, 2) for day in (5, 6, 12, 13)]
    result = evaluate(
        PlanningDraft(
            employees=staff,
            structures=(kitchen_midday_structure(),),
            hours=hours,
            assignments=tuple(both_weekends),
        )
    )
    assert "weekend_even_weeks" in result.codes()
    assert "weekend_odd_weeks" in result.codes()
    assert "weekend_every_two_weeks" in result.codes()


def test_week_label_scheme_parity_vs_ab():
    state = empty_restaurant("resto")
    even = employee("Ada", "commis", employee_id="ada").with_wellbeing(Wellbeing(weekend=WeekendChoice.EVEN))
    two = employee("Bea", "commis", employee_id="bea").with_wellbeing(Wellbeing(weekend=WeekendChoice.EVERY_TWO))
    upsert_employee(state, two)
    assert week_label_scheme(state) == "ab"
    upsert_employee(state, even)
    assert week_label_scheme(state) == "parity"


def test_max_evening_zero_and_coupure_zero_warn():
    person = employee("Emma", "sous-chef", hours=39, employee_id="emma").with_wellbeing(
        Wellbeing(max_services={ServiceName.EVENING.value: 0}, max_coupures_per_week=0)
    )
    assignments = [
        _shift("emma", 0, 11 * 60, 15 * 60, 3),
        _shift("emma", 0, 19 * 60, 23 * 60, 3, service=ServiceName.EVENING.value),
    ]
    hours = RestaurantHours.multi_service(ServiceName.MIDDAY.value, ServiceName.EVENING.value)
    result = evaluate(
        PlanningDraft(
            employees=(person,),
            structures=(kitchen_midday_structure(),),
            hours=hours,
            assignments=tuple(assignments),
        )
    )
    assert "max_evenings" in result.codes()
    assert "max_coupures" in result.codes()
    assert all(item.severity is WarningSeverity.SOUHAIT for item in result.warnings if item.code in {"max_evenings", "max_coupures"})
    evening = next(item for item in result.warnings if item.code == "max_evenings")
    assert evening.day_index == 0
    assert "lundi" in evening.message
    assert "max 0" in evening.message
    assert "dîner" in evening.message
    assert "sem. A" in evening.message
    coupure = next(item for item in result.warnings if item.code == "max_coupures")
    assert "1 coupures" in coupure.message
    assert "max 0" in coupure.message
    assert "sem. A" in coupure.message


def test_unavailability_is_only_day_service_pair():
    pattern = Unavailability(weekday="tuesday", service_id=ServiceName.MIDDAY.value)
    assert pattern.blocks("tuesday", ServiceName.MIDDAY.value)
    assert not pattern.blocks("tuesday", ServiceName.EVENING.value)
    assert not pattern.blocks("monday", ServiceName.MIDDAY.value)
    with pytest.raises(ValueError):
        Unavailability(weekday="tuesday", service_id="continuous")


def test_hydrate_saint_cloud_has_no_legacy_wellbeing_keys():
    state = hydrate_delivered_cycle(PlanningStore(), "saint-cloud")
    assert state.employees
    for person in state.employees:
        assert not isinstance(person.wellbeing, (list, set, frozenset))
        assert person.wellbeing.weekend is None or person.wellbeing.weekend in WeekendChoice
        for item in person.unavailabilities:
            assert item.weekday
            assert item.service_id
    raw = (state.cycle.draft.employees[0].wellbeing)
    assert raw.consecutive_rest in {True, False}


def test_removed_keys_are_listed():
    assert "at_least_one_weekend_rest_day" in REMOVED_WELLBEING_KEYS
    assert "no_evening_service" in REMOVED_WELLBEING_KEYS
    assert "max_two_coupures_per_week" in REMOVED_WELLBEING_KEYS


def test_hydrate_refuses_legacy_wellbeing():
    with pytest.raises(ValueError, match="legacy wellbeing"):
        _wellbeing({"wellbeing": ["two_consecutive_rest_days"]})
    with pytest.raises(ValueError, match="legacy"):
        _wellbeing({"max_evenings_per_week": 2, "wellbeing": {}})
    with pytest.raises(ValueError, match="legacy"):
        _wellbeing({"wellbeing": {"at_least_one_weekend_rest_day": True}})


def test_sunday_closed_weekend_rest_day_held_without_other_weekend_rest():
    hours = RestaurantHours.multi_service(ServiceName.MIDDAY.value, closed_weekdays={"sunday"})
    person = employee("Ada", "commis", hours=20, employee_id="ada").with_wellbeing(
        Wellbeing(weekend_rest_day=True)
    )
    assignments = [_shift("ada", day, 11 * 60, 15 * 60, 2) for day in (0, 1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12)]
    result = evaluate(
        PlanningDraft(
            employees=(person,),
            structures=(kitchen_midday_structure(),),
            hours=hours,
            assignments=tuple(assignments),
        )
    )
    assert "weekend_rest_day" not in result.codes()


def test_sunday_open_sat_and_sun_worked_warns_weekend_rest_day():
    hours = RestaurantHours.multi_service(ServiceName.MIDDAY.value)
    person = employee("Ada", "commis", hours=20, employee_id="ada").with_wellbeing(
        Wellbeing(weekend_rest_day=True)
    )
    assignments = [_shift("ada", day, 11 * 60, 15 * 60, 2) for day in (5, 6, 12, 13)]
    result = evaluate(
        PlanningDraft(
            employees=(person,),
            structures=(kitchen_midday_structure(),),
            hours=hours,
            assignments=tuple(assignments),
        )
    )
    assert "weekend_rest_day" in result.codes()
    assert all(
        item.severity is WarningSeverity.SOUHAIT
        for item in result.warnings
        if item.code == "weekend_rest_day"
    )


def test_weekend_rest_day_stacks_with_weekend_even():
    hours = RestaurantHours.multi_service(ServiceName.MIDDAY.value)
    person = employee("Ada", "commis", hours=20, employee_id="ada").with_wellbeing(
        Wellbeing(weekend_rest_day=True, weekend=WeekendChoice.EVEN)
    )
    assignments = [_shift("ada", day, 11 * 60, 15 * 60, 2) for day in (5, 6, 12, 13)]
    result = evaluate(
        PlanningDraft(
            employees=(person,),
            structures=(kitchen_midday_structure(),),
            hours=hours,
            assignments=tuple(assignments),
        )
    )
    assert "weekend_rest_day" in result.codes()
    assert "weekend_even_weeks" in result.codes()


def test_absent_weekend_rest_day_is_false_no_board_row():
    assert _wellbeing({"wellbeing": {}}).weekend_rest_day is False
    assert _wellbeing({"wellbeing": {"consecutive_rest": True}}).weekend_rest_day is False
    state = empty_restaurant("resto")
    posed = employee("Ada", "commis", employee_id="ada").with_wellbeing(Wellbeing(weekend_rest_day=True))
    upsert_employee(state, posed)
    board = employee_board(state, "ada")
    assert any(item.kind == "weekend_rest_day" for item in board.wishes)
    upsert_employee(state, employee("Bea", "commis", employee_id="bea"))
    absent = employee_board(state, "bea")
    assert all(item.kind != "weekend_rest_day" for item in absent.wishes)
