from doux_planning.invites import InvalidInviteCode, RestaurantIdentity, assert_restaurateur_owns_constraints, redeem_invite
from doux_planning.staff import (
    Employee,
    Role,
    RoleLadder,
    SubstitutionExplanationRequired,
    TeamMismatchError,
    Unavailability,
    default_legal_rules,
)
from doux_planning.structures import ArrivalWave, RestaurantHours, ServiceStructure
from doux_planning.types import ServiceName, Team, WellbeingPreference, validate_quantum
from tests.fixtures import cuisine_ladder, employee


def test_cuisine_employee_is_kitchen_only():
    person = employee("Sam", "commis")
    assert person.team is Team.CUISINE
    assert person.role.team is Team.CUISINE


def test_role_ladder_requires_explanation():
    roles = (Role("chef", 4, Team.CUISINE),)
    try:
        RoleLadder(Team.CUISINE, roles, substitution_explained=False)
        raise AssertionError("expected SubstitutionExplanationRequired")
    except SubstitutionExplanationRequired:
        pass
    ladder = cuisine_ladder()
    assert [role.name for role in ladder.roles] == ["chef", "sous-chef", "commis", "plongeur"]
    assert [role.level for role in ladder.roles] == [4, 3, 2, 1]


def test_employee_team_must_match_role():
    role = Role("chef de rang", 3, Team.SALLE)
    try:
        Employee(id="x", name="Ada", role=role, team=Team.CUISINE, contractual_hours_per_week=35)
        raise AssertionError("expected TeamMismatchError")
    except TeamMismatchError:
        pass


def test_employee_contract_profile():
    person = employee("Sam", "commis", hours=35)
    assert person.name == "Sam"
    assert person.role.name == "commis"
    assert person.level == 2
    assert person.team is Team.CUISINE
    assert person.contractual_hours_per_week == 35


def test_unavailability_patterns_round_trip():
    tuesday = Unavailability(weekday="tuesday")
    mornings = Unavailability(every_morning=True)
    midi = Unavailability(service_id=ServiceName.MIDDAY.value)
    person = employee("Sam", "commis").with_unavailability(tuesday).with_unavailability(mornings).with_unavailability(midi)
    assert tuesday.blocks("tuesday", ServiceName.MIDDAY.value, False, False)
    assert not tuesday.blocks("monday", ServiceName.MIDDAY.value, False, False)
    assert mornings.blocks("monday", ServiceName.MORNING.value, True, False)
    assert not mornings.blocks("monday", ServiceName.EVENING.value, False, True)
    assert midi.blocks("friday", ServiceName.MIDDAY.value, False, False)
    assert len(person.unavailabilities) == 3


def test_wellbeing_consecutive_rest_is_recorded():
    person = employee("Sam", "commis").with_wellbeing(WellbeingPreference.TWO_CONSECUTIVE_REST_DAYS)
    assert WellbeingPreference.TWO_CONSECUTIVE_REST_DAYS in person.wellbeing


def test_legal_rules_visible_without_generation():
    rules = default_legal_rules()
    assert len(rules) == 6
    ids = {rule.id for rule in rules}
    assert ids == {
        "rest_between_days",
        "weekly_rest_days",
        "max_coupure",
        "max_daily_cuisine",
        "max_daily_salle",
        "max_weekly_hours",
    }


def test_invite_code_links_account():
    restaurant = RestaurantIdentity(id="resto-1")
    account = redeem_invite(restaurant, restaurant.invite_code, "acc-1", "sam")
    assert account.restaurant_id == "resto-1"
    try:
        redeem_invite(restaurant, "nope", "acc-2", "sam")
        raise AssertionError("expected InvalidInviteCode")
    except InvalidInviteCode:
        pass
    assert_restaurateur_owns_constraints("restaurateur")
    try:
        assert_restaurateur_owns_constraints("employee")
        raise AssertionError("expected permission error")
    except PermissionError:
        pass


def test_continuous_vs_services_and_closures():
    continuous = RestaurantHours.continuous(closed_weekdays={"monday"})
    assert continuous.services == (ServiceName.CONTINUOUS.value,)
    assert continuous.is_closed("monday", ServiceName.CONTINUOUS.value)
    multi = RestaurantHours.multi_service(
        ServiceName.MORNING.value,
        ServiceName.MIDDAY.value,
        ServiceName.EVENING.value,
    )
    assert len(multi.services) == 3


def test_wave_time_must_be_quarter_hour():
    ArrivalWave(11 * 60 + 30, (2,))
    try:
        ArrivalWave(11 * 60 + 10, (2,))
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
    validate_quantum(15)
