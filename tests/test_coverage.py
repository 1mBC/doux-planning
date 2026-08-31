from doux_planning.coverage import derive_slices
from doux_planning.matching import match_posts
from doux_planning.staff import Employee
from doux_planning.types import Team
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
