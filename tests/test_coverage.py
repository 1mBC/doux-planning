from doux_planning.coverage import PostWindow, derive_post_windows, derive_slices, stretch_to_min_shift
from doux_planning.matching import match_posts
from doux_planning.staff import Employee
from doux_planning.structures import ArrivalWave, DepartureWave, ServiceStructure
from doux_planning.types import ServiceName, Team
from tests.fixtures import cuisine_ladder, employee, kitchen_midday_structure, kitchen_staff


def test_kitchen_midday_slices():
    slices = derive_slices(kitchen_midday_structure())
    by_start = {item.start_minutes: item.post_levels for item in slices}
    assert by_start[10 * 60] == (4,)
    assert by_start[11 * 60] == (4, 2, 2)
    assert by_start[11 * 60 + 30] == (4, 2, 2, 1)
    assert by_start[14 * 60 + 30] == (4, 2)
    assert by_start[15 * 60] == (4,)


def test_second_chef_fills_sous_chef_cascade():
    posts = (4, 3, 2, 2, 1)
    staff = list(kitchen_staff())
    matched = match_posts(posts, staff)
    by_post = [(item.post_level, item.employee.name if item.employee else None) for item in matched]
    assert by_post[0] == (4, "ChefA")
    assert by_post[1] == (3, "ChefB")
    assert by_post[2] == (2, "Second")
    assert by_post[3] == (2, "Sam")
    assert by_post[4] == (1, None)


def test_sole_chef_stays_chef_not_plonge():
    posts = (4, 1)
    chef = employee("ChefA", "chef", employee_id="chef-a")
    matched = match_posts(posts, [chef])
    assert matched[0].post_level == 4
    assert matched[0].employee is chef
    empty = [item for item in matched if item.employee is None]
    assert len(empty) == 1
    assert empty[0].post_level == 1


def test_fifo_same_level_opener_leaves_first():
    structure = ServiceStructure(
        id="two-l1",
        team=Team.CUISINE,
        service_id=ServiceName.MIDDAY.value,
        weekdays=frozenset({"monday"}),
        arrivals=(ArrivalWave(10 * 60, (1,)), ArrivalWave(11 * 60, (1,))),
        departures=(DepartureWave(14 * 60, (1,)), DepartureWave(15 * 60, ())),
    )
    windows = {(item.start_minutes, item.end_minutes, item.level) for item in derive_post_windows(structure)}
    assert (10 * 60, 14 * 60, 1) in windows
    assert (11 * 60, 15 * 60, 1) in windows


def test_higher_skill_opener_stays_until_close():
    structure = ServiceStructure(
        id="eve-skill",
        team=Team.CUISINE,
        service_id=ServiceName.EVENING.value,
        weekdays=frozenset({"tuesday"}),
        arrivals=(
            ArrivalWave(18 * 60, (3,)),
            ArrivalWave(19 * 60, (1,)),
            ArrivalWave(19 * 60 + 30, (2, 1)),
        ),
        departures=(
            DepartureWave(22 * 60 + 30, (3, 2, 1)),
            DepartureWave(23 * 60, (3, 2)),
            DepartureWave(24 * 60, ()),
        ),
    )
    windows = derive_post_windows(structure)
    chef = [item for item in windows if item.level == 3]
    assert len(chef) == 1
    assert chef[0].start_minutes == 18 * 60
    assert chef[0].end_minutes == 24 * 60


def test_stretch_extends_end_then_start():
    structure = ServiceStructure(
        id="short-eve",
        team=Team.CUISINE,
        service_id=ServiceName.EVENING.value,
        weekdays=frozenset({"tuesday"}),
        arrivals=(ArrivalWave(19 * 60 + 30, (1,)),),
        departures=(DepartureWave(22 * 60 + 30, ()), DepartureWave(24 * 60, ())),
    )
    hole = PostWindow(level=1, start_minutes=19 * 60 + 30, end_minutes=22 * 60 + 30)
    stretched = stretch_to_min_shift(hole, 4.0, structure)
    assert stretched.start_minutes == 19 * 60 + 30
    assert stretched.end_minutes == 23 * 60 + 30
