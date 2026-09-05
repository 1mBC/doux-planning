from __future__ import annotations

from enum import Enum


class Team(str, Enum):
    SALLE = "salle"
    CUISINE = "cuisine"


class ServiceName(str, Enum):
    CONTINUOUS = "continuous"
    MORNING = "morning"
    MIDDAY = "midday"
    EVENING = "evening"


class WarningSeverity(str, Enum):
    INTERDIT = "interdit"
    COUVERTURE = "couverture"
    SOUHAIT = "souhait"


class WeekendChoice(str, Enum):
    EVERY_TWO = "every_two"
    EVEN = "even"
    ODD = "odd"


class SearchEffort(str, Enum):
    """How many rest-calendar hypotheses generation tries before keeping the best."""

    MINIMAL = "minimal"
    OPTIMIZED = "optimized"
    MAXIMAL = "maximal"


WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
QUANTUM_MINUTES = 15
CYCLE_DAYS = 14
MIN_REST_BETWEEN_DAYS_HOURS = 11
REST_DAYS_PER_WEEK = 2
MAX_COUPURE_HOURS = 5
MAX_DAILY_HOURS_CUISINE = 11.0
MAX_DAILY_HOURS_SALLE = 11.5
MAX_WEEKLY_HOURS = 48.0
DEFAULT_MIN_SHIFT_HOURS = 4.0


def weekday_index(name: str) -> int:
    key = name.lower()
    if key not in WEEKDAYS:
        raise ValueError(f"Unknown weekday: {name}")
    return WEEKDAYS.index(key)


def validate_quantum(minutes: int) -> int:
    if minutes < 0 or minutes % QUANTUM_MINUTES != 0:
        raise ValueError("Time must be aligned to a 15-minute grid")
    return minutes
