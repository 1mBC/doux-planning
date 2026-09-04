from __future__ import annotations

from dataclasses import dataclass

from doux_planning.structures import ServiceStructure
from doux_planning.types import QUANTUM_MINUTES


@dataclass(frozen=True)
class CoverageSlice:
    start_minutes: int
    end_minutes: int
    post_levels: tuple[int, ...]


@dataclass(frozen=True)
class PostWindow:
    """A single exclusive post that exists from start to end."""

    level: int
    start_minutes: int
    end_minutes: int


def _drop_lowest(posts: list[int], remaining: tuple[int, ...]) -> list[int]:
    remaining_list = list(remaining)
    kept: list[int] = []
    # Keep a multiset matching remaining, preferring to keep higher levels (chef stays).
    current = sorted(posts, reverse=True)
    remaining_sorted = sorted(remaining_list, reverse=True)
    used = [False] * len(current)
    for need in remaining_sorted:
        found = None
        for i, level in enumerate(current):
            if not used[i] and level == need:
                found = i
                break
        if found is None:
            for i, level in enumerate(current):
                if not used[i] and level >= need:
                    found = i
                    break
        if found is None:
            continue
        used[found] = True
        kept.append(current[found])
    return kept


def structure_span(structure: ServiceStructure) -> tuple[int, int]:
    times = [wave.time_minutes for wave in (*structure.arrivals, *structure.departures)]
    return min(times), max(times)


def stretch_to_min_shift(window: PostWindow, min_hours: float, structure: ServiceStructure) -> PostWindow:
    """Keep the coverage window, then extend the shift to min_hours (end first, then start)."""
    need = int(min_hours * 60)
    duration = window.end_minutes - window.start_minutes
    if duration >= need:
        return window
    service_start, service_end = structure_span(structure)
    end = min(max(window.end_minutes, window.start_minutes + need), service_end)
    start = window.start_minutes
    if end - start < need:
        start = max(service_start, end - need)
    return PostWindow(level=window.level, start_minutes=start, end_minutes=end)


def derive_post_windows(structure: ServiceStructure) -> tuple[PostWindow, ...]:
    live: list[tuple[int, int]] = []  # (level, start)
    finished: list[PostWindow] = []
    events: list[tuple[int, str, object]] = []
    for wave in structure.arrivals:
        events.append((wave.time_minutes, "arrival", wave))
    for wave in structure.departures:
        events.append((wave.time_minutes, "departure", wave))
    events.sort(key=lambda item: (item[0], 0 if item[1] == "arrival" else 1))

    for time_minutes, kind, wave in events:
        if kind == "arrival":
            for level in wave.post_levels:  # type: ignore[attr-defined]
                live.append((level, time_minutes))
        else:
            remaining = wave.remaining_post_levels  # type: ignore[attr-defined]
            current_levels = [level for level, _ in live]
            kept_levels = _drop_lowest(current_levels, remaining)
            new_live: list[tuple[int, int]] = []
            kept_bag = list(kept_levels)
            # Higher skill stays for remaining posts; among equals, later arrivals stay
            # so the earliest arrival leaves first (FIFO) when coverage still allows it.
            for level, start in sorted(live, key=lambda item: (-item[0], -item[1])):
                if level in kept_bag:
                    kept_bag.remove(level)
                    new_live.append((level, start))
                else:
                    finished.append(PostWindow(level=level, start_minutes=start, end_minutes=time_minutes))
            live = new_live
    for level, start in live:
        finished.append(PostWindow(level=level, start_minutes=start, end_minutes=start))
    return tuple(finished)


def derive_slices(structure: ServiceStructure) -> tuple[CoverageSlice, ...]:
    times = sorted(
        {
            wave.time_minutes
            for wave in (*structure.arrivals, *structure.departures)
        }
    )
    if len(times) < 2:
        return ()
    windows = derive_post_windows(structure)
    slices: list[CoverageSlice] = []
    for start, end in zip(times, times[1:]):
        if end - start < QUANTUM_MINUTES and end != start:
            pass
        posts = tuple(
            sorted(
                (window.level for window in windows if window.start_minutes <= start < window.end_minutes),
                reverse=True,
            )
        )
        slices.append(CoverageSlice(start_minutes=start, end_minutes=end, post_levels=posts))
    return tuple(slices)
