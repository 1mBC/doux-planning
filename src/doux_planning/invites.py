from __future__ import annotations

import secrets
from collections.abc import Sequence
from dataclasses import dataclass, field, replace

from doux_planning.staff import Employee


class InvalidInviteCode(ValueError):
    pass


class UnknownInviteToken(ValueError):
    pass


class UnknownEmployee(ValueError):
    pass


class InviteAlreadyRedeemed(ValueError):
    pass


class InviteTargetMismatch(ValueError):
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
    linked_employee_ids: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        self.linked_employee_ids = frozenset(self.linked_employee_ids)

    def rotate_invite_code(self) -> RestaurantIdentity:
        return replace(self, invite_code=secrets.token_urlsafe(8))


def rotate_employee_invite_token(employee: Employee) -> Employee:
    token = secrets.token_urlsafe(16)
    while token == employee.id or token == employee.invite_token:
        token = secrets.token_urlsafe(16)
    return replace(employee, invite_token=token)


def redeem_invite(
    restaurant: RestaurantIdentity,
    employees: Sequence[Employee],
    company_code: str,
    account_id: str,
    employee_id: str | None = None,
    employee_token: str | None = None,
) -> tuple[EmployeeAccount, RestaurantIdentity]:
    if company_code != restaurant.invite_code:
        raise InvalidInviteCode("Invalid invite code")
    if employee_token:
        match = next((person for person in employees if person.invite_token == employee_token), None)
        if match is None:
            raise UnknownInviteToken("Unknown invite token")
        if employee_id is not None and employee_id != match.id:
            raise InviteTargetMismatch("employee_id does not match token")
        target = match
    else:
        if not employee_id:
            raise ValueError("employee_id or employee_token is required")
        target = next((person for person in employees if person.id == employee_id), None)
        if target is None:
            raise UnknownEmployee("Unknown employee")
    if target.id in restaurant.linked_employee_ids:
        raise InviteAlreadyRedeemed("Employee fiche is already linked")
    account = EmployeeAccount(id=account_id, employee_id=target.id, restaurant_id=restaurant.id)
    updated = replace(restaurant, linked_employee_ids=frozenset({*restaurant.linked_employee_ids, target.id}))
    return account, updated


def assert_restaurateur_owns_constraints(actor: str) -> None:
    if actor != "restaurateur":
        raise EmployeeCannotEditConstraints("Staff constraints are restaurateur-owned in v1")
