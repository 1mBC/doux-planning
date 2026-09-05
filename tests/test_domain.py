from doux_planning.hydrate import hydrate_delivered_cycle
from doux_planning.invites import (
    InvalidInviteCode,
    InviteAlreadyRedeemed,
    RestaurantIdentity,
    UnknownInviteToken,
    assert_restaurateur_owns_constraints,
    redeem_invite,
    rotate_employee_invite_token,
)
from doux_planning.planning import PlanningStore
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
from doux_planning.staff import Wellbeing
from doux_planning.types import ServiceName, Team, WeekendChoice, validate_quantum
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
    assert person.min_shift_hours == 4


def test_unavailability_patterns_round_trip():
    tuesday = Unavailability(weekday="tuesday", service_id=ServiceName.MIDDAY.value)
    person = employee("Sam", "commis").with_unavailability(tuesday)
    assert tuesday.blocks("tuesday", ServiceName.MIDDAY.value)
    assert not tuesday.blocks("monday", ServiceName.MIDDAY.value)
    assert not tuesday.blocks("tuesday", ServiceName.EVENING.value)
    assert len(person.unavailabilities) == 1


def test_wellbeing_consecutive_rest_is_recorded():
    person = employee("Sam", "commis").with_wellbeing(Wellbeing(consecutive_rest=True))
    assert person.wellbeing.consecutive_rest is True
    assert person.wellbeing.weekend is None


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
    sam = employee("Sam", "commis")
    account, restaurant = redeem_invite(
        restaurant, (sam,), restaurant.invite_code, "acc-1", employee_id="sam"
    )
    assert account.restaurant_id == "resto-1"
    assert account.employee_id == "sam"
    assert "sam" in restaurant.linked_employee_ids
    try:
        redeem_invite(restaurant, (sam,), "nope", "acc-2", employee_id="sam")
        raise AssertionError("expected InvalidInviteCode")
    except InvalidInviteCode:
        pass
    assert_restaurateur_owns_constraints("restaurateur")
    try:
        assert_restaurateur_owns_constraints("employee")
        raise AssertionError("expected permission error")
    except PermissionError:
        pass


def test_employee_invite_token_generated_and_not_id():
    person = employee("Sam", "commis")
    assert person.invite_token
    assert person.invite_token != person.id


def test_redeem_manual_qr_rotate_and_bad_company_code():
    restaurant = RestaurantIdentity(id="resto-1", invite_code="join-me")
    first = employee("Ada", "commis", employee_id="ada")
    second = employee("Bea", "commis", employee_id="bea")
    staff = (first, second)
    account_a, restaurant = redeem_invite(
        restaurant, staff, "join-me", "acc-a", employee_id="ada"
    )
    assert account_a.employee_id == "ada"
    assert restaurant.linked_employee_ids == frozenset({"ada"})
    try:
        redeem_invite(restaurant, staff, "join-me", "acc-a2", employee_id="ada")
        raise AssertionError("expected InviteAlreadyRedeemed")
    except InviteAlreadyRedeemed:
        pass
    try:
        redeem_invite(restaurant, staff, "join-me", "acc-a3", employee_token=first.invite_token)
        raise AssertionError("expected InviteAlreadyRedeemed")
    except InviteAlreadyRedeemed:
        pass
    old_token = first.invite_token
    rotated = rotate_employee_invite_token(first)
    assert rotated.invite_token != old_token
    staff_rotated = (rotated, second)
    unlinked = RestaurantIdentity(id="resto-1", invite_code="join-me")
    try:
        redeem_invite(unlinked, staff_rotated, "join-me", "acc-old", employee_token=old_token)
        raise AssertionError("expected UnknownInviteToken")
    except UnknownInviteToken:
        pass
    account_rotated, linked = redeem_invite(
        unlinked, staff_rotated, "join-me", "acc-new", employee_token=rotated.invite_token
    )
    assert account_rotated.employee_id == "ada"
    assert "ada" in linked.linked_employee_ids
    account_b, after_b = redeem_invite(
        restaurant, staff, "join-me", "acc-b", employee_token=second.invite_token
    )
    assert account_b.employee_id == "bea"
    assert after_b.linked_employee_ids == frozenset({"ada", "bea"})
    try:
        redeem_invite(restaurant, staff, "wrong", "acc-x", employee_id="bea")
        raise AssertionError("expected InvalidInviteCode")
    except InvalidInviteCode:
        pass


def test_hydrate_saint_cloud_employees_have_invite_tokens():
    state = hydrate_delivered_cycle(PlanningStore(), "saint-cloud")
    assert state.employees
    assert all(person.invite_token and person.invite_token != person.id for person in state.employees)


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
