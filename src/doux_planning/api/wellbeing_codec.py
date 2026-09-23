from __future__ import annotations

from typing import Any

from doux_planning.context import BoardWish
from doux_planning.staff import COMPANY_SERVICE_IDS, REMOVED_WELLBEING_KEYS, Unavailability, Wellbeing
from doux_planning.types import WEEKDAYS, WeekendChoice

_FICHE_MAX_KEYS = frozenset({"max_evenings_per_week", "max_mornings_per_week"})
_EVERY_FLAGS = frozenset({"every_morning", "every_evening"})
_STRIP_ON_READ = REMOVED_WELLBEING_KEYS | _FICHE_MAX_KEYS | _EVERY_FLAGS


def wellbeing_from_json(payload: Any) -> Wellbeing:
    if payload is None:
        return Wellbeing()
    if isinstance(payload, list):
        if not payload:
            return Wellbeing()
        raise ValueError("legacy wellbeing keys are not accepted")
    if not isinstance(payload, dict):
        raise ValueError("wellbeing must be an object")
    forbidden = REMOVED_WELLBEING_KEYS.intersection(payload)
    if forbidden:
        raise ValueError(f"legacy wellbeing keys are not accepted: {sorted(forbidden)}")
    weekend = payload.get("weekend")
    return Wellbeing(
        consecutive_rest=bool(payload.get("consecutive_rest", False)),
        weekend_rest_day=bool(payload.get("weekend_rest_day", False)),
        weekend=None if weekend is None else WeekendChoice(weekend),
        max_services=payload.get("max_services") or {},
        max_coupures_per_week=payload.get("max_coupures_per_week"),
    )


def wellbeing_to_json(wellbeing: Wellbeing) -> dict[str, Any]:
    return {
        "consecutive_rest": wellbeing.consecutive_rest,
        "weekend_rest_day": wellbeing.weekend_rest_day,
        "weekend": None if wellbeing.weekend is None else wellbeing.weekend.value,
        "max_services": dict(wellbeing.max_services),
        "max_coupures_per_week": wellbeing.max_coupures_per_week,
    }


def coerce_wellbeing(payload: Any) -> Wellbeing:
    if payload is None or payload == {} or payload == []:
        return Wellbeing()
    if isinstance(payload, list):
        return _apply_legacy_mapping(Wellbeing(), [item for item in payload if isinstance(item, str)], {})
    if not isinstance(payload, dict):
        raise ValueError("wellbeing must be an object")
    cleaned = {key: value for key, value in payload.items() if key not in _STRIP_ON_READ}
    base = wellbeing_from_json(cleaned)
    present_new = {
        "consecutive_rest": "consecutive_rest" in payload,
        "weekend_rest_day": "weekend_rest_day" in payload,
        "max_coupures_per_week": payload.get("max_coupures_per_week") is not None,
    }
    present_max = set(cleaned.get("max_services") or {}) if isinstance(cleaned.get("max_services"), dict) else set()
    return _apply_legacy_mapping(base, list(payload), payload, present_new=present_new, present_max=present_max)


def _apply_legacy_mapping(
    base: Wellbeing,
    keys: list[str],
    raw: dict[str, Any],
    *,
    present_new: dict[str, bool] | None = None,
    present_max: set[str] | None = None,
) -> Wellbeing:
    present_new = present_new or {}
    present_max = present_max or set()
    keyset = set(keys)
    consecutive = base.consecutive_rest
    if "two_consecutive_rest_days" in keyset and not present_new.get("consecutive_rest"):
        consecutive = True
    weekend = base.weekend
    if "weekend_off_every_two_weeks" in keyset and weekend is None:
        weekend = WeekendChoice.EVERY_TWO
    weekend_rest_day = base.weekend_rest_day
    if "at_least_one_weekend_rest_day" in keyset and not present_new.get("weekend_rest_day"):
        weekend_rest_day = True
    max_coupures = base.max_coupures_per_week
    if not present_new.get("max_coupures_per_week"):
        mapped: list[int] = []
        if "max_two_coupures_per_week" in keyset:
            mapped.append(2)
        if "max_three_coupures_per_week" in keyset:
            mapped.append(3)
        if mapped:
            max_coupures = min(mapped)
    max_services = dict(base.max_services)
    if "no_evening_service" in keyset and "evening" not in present_max:
        max_services["evening"] = 0
    if "no_morning_service" in keyset and "morning" not in present_max:
        max_services["morning"] = 0
    evenings = raw.get("max_evenings_per_week")
    if evenings is not None and "evening" not in present_max:
        max_services["evening"] = int(evenings)
    mornings = raw.get("max_mornings_per_week")
    if mornings is not None and "morning" not in present_max:
        max_services["morning"] = int(mornings)
    return Wellbeing(
        consecutive_rest=consecutive,
        weekend_rest_day=weekend_rest_day,
        weekend=weekend,
        max_services=max_services,
        max_coupures_per_week=max_coupures,
    )


def unavailability_from_json(raw: Any) -> Unavailability:
    if not isinstance(raw, dict):
        raise ValueError("invalid unavailability")
    if "every_morning" in raw or "every_evening" in raw:
        raise ValueError("legacy every_morning / every_evening are not accepted")
    weekday = raw.get("weekday")
    service_id = raw.get("service_id")
    if not weekday or not service_id:
        raise ValueError("unavailability requires weekday and service_id")
    return Unavailability(weekday=weekday, service_id=service_id)


def coerce_unavailabilities(raw_list: Any, company_services: list[str]) -> list[Unavailability]:
    if raw_list is None:
        return []
    if not isinstance(raw_list, list):
        raise ValueError("invalid unavailabilities")
    offered = [service_id for service_id in company_services if service_id in COMPANY_SERVICE_IDS]
    seen: set[tuple[str, str]] = set()
    out: list[Unavailability] = []

    def add(weekday: str, service_id: str) -> None:
        key = (weekday, service_id)
        if key in seen:
            return
        seen.add(key)
        out.append(Unavailability(weekday=weekday, service_id=service_id))

    for raw in raw_list:
        if not isinstance(raw, dict):
            raise ValueError("invalid unavailability")
        weekday = raw.get("weekday")
        if not weekday or not isinstance(weekday, str):
            continue
        weekday = weekday.lower()
        if weekday not in WEEKDAYS:
            continue
        every_morning = bool(raw.get("every_morning"))
        every_evening = bool(raw.get("every_evening"))
        if every_morning or every_evening:
            if every_morning and "morning" in offered:
                add(weekday, "morning")
            if every_evening and "evening" in offered:
                add(weekday, "evening")
            service_id = raw.get("service_id")
            if service_id in COMPANY_SERVICE_IDS:
                add(weekday, service_id)
            continue
        service_id = raw.get("service_id")
        if service_id is None or service_id == "":
            for offered_id in offered:
                add(weekday, offered_id)
            continue
        if service_id not in COMPANY_SERVICE_IDS:
            raise ValueError("invalid service")
        add(weekday, service_id)
    return out


def unavailability_to_json(item: Unavailability) -> dict[str, Any]:
    return {"weekday": item.weekday, "service_id": item.service_id}


def wish_to_json(wish: BoardWish) -> dict[str, Any]:
    payload: dict[str, Any] = {"kind": wish.kind, "held": wish.held}
    if wish.value is not None:
        payload["value"] = wish.value
    if wish.service_id is not None:
        payload["service_id"] = wish.service_id
    if wish.limit is not None:
        payload["limit"] = wish.limit
    return payload
