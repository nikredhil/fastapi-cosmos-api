"""Domain enumerations for the rental-management app."""
from __future__ import annotations

from enum import Enum


class UnitStatus(str, Enum):
    """Occupancy state of a rentable unit/flat."""

    VACANT = "vacant"
    OCCUPIED = "occupied"


class TenantStatus(str, Enum):
    ACTIVE = "active"
    PAST = "past"


class LeaseStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ENDED = "ended"


class BillType(str, Enum):
    """Kinds of charges a landlord tracks, tuned for the Indian market."""

    RENT = "rent"
    WATER = "water"
    ELECTRICITY = "electricity"
    MAINTENANCE = "maintenance"
    OTHER = "other"


class BillStatus(str, Enum):
    UNPAID = "unpaid"
    PARTIAL = "partial"
    PAID = "paid"
    OVERDUE = "overdue"
