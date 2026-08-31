from __future__ import annotations

from dataclasses import dataclass

from doux_planning.staff import Employee


@dataclass(frozen=True)
class MatchedPost:
    post_level: int
    employee: Employee | None


def match_posts(post_levels: tuple[int, ...], employees: list[Employee]) -> tuple[MatchedPost, ...]:
    """Assign highest remaining people to highest remaining posts (exclusive)."""
    remaining_people = sorted(employees, key=lambda employee: (-employee.level, employee.id))
    result: list[MatchedPost] = []
    for post_level in sorted(post_levels, reverse=True):
        chosen_index = None
        for index, employee in enumerate(remaining_people):
            if employee.level >= post_level:
                chosen_index = index
                break
        if chosen_index is None:
            result.append(MatchedPost(post_level=post_level, employee=None))
            continue
        employee = remaining_people.pop(chosen_index)
        result.append(MatchedPost(post_level=post_level, employee=employee))
    result.sort(key=lambda item: -item.post_level)
    return tuple(result)
