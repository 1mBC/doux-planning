from __future__ import annotations

import secrets
from dataclasses import dataclass, field, replace


class InvalidInviteCode(ValueError):
    pass


class EmployeeCannotEditConstraints(PermissionError):
    pass


@dataclass(frozen=True)
class EmployeeAccount:
    id: str
    employee_id: str
    restaurant_id: str


@dataclass
class RestaurantIdentity:
    id: str
    invite_code: str = field(default_factory=lambda: secrets.token_urlsafe(8))

    def rotate_invite_code(self) -> RestaurantIdentity:
        return replace(self, invite_code=secrets.token_urlsafe(8))


def redeem_invite(restaurant: RestaurantIdentity, code: str, account_id: str, employee_id: str) -> EmployeeAccount:
    if code != restaurant.invite_code:
        raise InvalidInviteCode("Invalid invite code")
    return EmployeeAccount(id=account_id, employee_id=employee_id, restaurant_id=restaurant.id)


def assert_restaurateur_owns_constraints(actor: str) -> None:
    if actor != "restaurateur":
        raise EmployeeCannotEditConstraints("Staff constraints are restaurateur-owned in v1")
