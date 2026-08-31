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


class WellbeingPreference(str, Enum):
    TWO_CONSECUTIVE_REST_DAYS = "two_consecutive_rest_days"
    WEEKEND_OFF_EVERY_TWO_WEEKS = "weekend_off_every_two_weeks"
    AT_LEAST_ONE_WEEKEND_REST_DAY = "at_least_one_weekend_rest_day"
    NO_EVENING_SERVICE = "no_evening_service"
    NO_MORNING_SERVICE = "no_morning_service"
    MAX_TWO_COUPURES_PER_WEEK = "max_two_coupures_per_week"
    MAX_THREE_COUPURES_PER_WEEK = "max_three_coupures_per_week"


WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
QUANTUM_MINUTES = 15
CYCLE_DAYS = 14
MIN_REST_BETWEEN_DAYS_HOURS = 11
REST_DAYS_PER_WEEK = 2
MAX_COUPURE_HOURS = 5
MAX_DAILY_HOURS_CUISINE = 11.0
MAX_DAILY_HOURS_SALLE = 11.5
MAX_WEEKLY_HOURS = 48.0


def weekday_index(name: str) -> int:
    key = name.lower()
    if key not in WEEKDAYS:
        raise ValueError(f"Unknown weekday: {name}")
    return WEEKDAYS.index(key)


def validate_quantum(minutes: int) -> int:
    if minutes < 0 or minutes % QUANTUM_MINUTES != 0:
        raise ValueError("Time must be aligned to a 15-minute grid")
    return minutes
