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
WEEKDAY_FR = {
    "monday": "lundi",
    "tuesday": "mardi",
    "wednesday": "mercredi",
    "thursday": "jeudi",
    "friday": "vendredi",
    "saturday": "samedi",
    "sunday": "dimanche",
}
SERVICE_FR = {
    ServiceName.MORNING.value: "petit-déjeuner",
    ServiceName.MIDDAY.value: "déjeuner",
    ServiceName.EVENING.value: "dîner",
}
QUANTUM_MINUTES = 15
CYCLE_DAYS = 14
MIN_REST_BETWEEN_DAYS_HOURS = 11
REST_DAYS_PER_WEEK = 2
MAX_COUPURE_HOURS = 5
MAX_DAILY_HOURS_CUISINE = 11.0
MAX_DAILY_HOURS_SALLE = 11.5
MAX_WEEKLY_HOURS = 48.0
DEFAULT_MIN_SHIFT_HOURS = 4.0


def week_label_scheme_from_weekends(weekends) -> str:
    for weekend in weekends:
        value = weekend.value if isinstance(weekend, WeekendChoice) else weekend
        if value in {WeekendChoice.EVEN.value, WeekendChoice.ODD.value}:
            return "parity"
    return "ab"


def week_label_for_day(day_index: int, scheme: str) -> str:
    first, second = ("Paire", "Impaire") if scheme == "parity" else ("A", "B")
    return first if day_index < 7 else second


def format_clock(minutes: int) -> str:
    total = ((minutes % 1440) + 1440) % 1440
    hours = total // 60
    mins = total % 60
    hour_label = "00h" if hours == 0 else f"{hours}h"
    if mins == 0:
        return hour_label
    return f"{hours}h{mins:02d}"


def weekday_index(name: str) -> int:
    key = name.lower()
    if key not in WEEKDAYS:
        raise ValueError(f"Unknown weekday: {name}")
    return WEEKDAYS.index(key)


def validate_quantum(minutes: int) -> int:
    if minutes < 0 or minutes % QUANTUM_MINUTES != 0:
        raise ValueError("Time must be aligned to a 15-minute grid")
    return minutes
