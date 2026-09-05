from __future__ import annotations

from typing import Any

from doux_planning.context import BoardWish
from doux_planning.staff import REMOVED_WELLBEING_KEYS, Unavailability, Wellbeing
from doux_planning.types import WeekendChoice


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
        weekend=None if weekend is None else WeekendChoice(weekend),
        max_services=payload.get("max_services") or {},
        max_coupures_per_week=payload.get("max_coupures_per_week"),
    )


def wellbeing_to_json(wellbeing: Wellbeing) -> dict[str, Any]:
    return {
        "consecutive_rest": wellbeing.consecutive_rest,
        "weekend": None if wellbeing.weekend is None else wellbeing.weekend.value,
        "max_services": dict(wellbeing.max_services),
        "max_coupures_per_week": wellbeing.max_coupures_per_week,
    }


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
