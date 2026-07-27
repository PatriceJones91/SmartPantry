"""Expiration-state helpers for recommendation candidate discovery.

Expiration is used to create the first candidate group. It does not calculate a
Smart Score and it cannot make an incomplete recipe eligible.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any, Optional


class ExpirationState(str, Enum):
    UNKNOWN = "unknown"
    FRESH = "fresh"
    EXPIRING = "expiring"
    EXPIRED = "expired"


@dataclass(frozen=True)
class ExpirationAssessment:
    state: ExpirationState
    expiration_date: Optional[str]
    days_until_expiration: Optional[int]

    @property
    def is_usable(self) -> bool:
        return self.state is not ExpirationState.EXPIRED

    @property
    def is_expiring(self) -> bool:
        return self.state is ExpirationState.EXPIRING


def _parse_date(value: Any) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    text = str(value).strip()
    if not text:
        return None

    # Supabase commonly returns YYYY-MM-DD or an ISO timestamp.
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def assess_expiration(
    expiration_value: Any,
    *,
    today: Optional[date] = None,
    expiry_window_days: int = 7,
) -> ExpirationAssessment:
    """Classify an item's expiration state using a bounded, explicit window."""
    reference_date = today or date.today()
    expiration_date = _parse_date(expiration_value)
    if expiration_date is None:
        return ExpirationAssessment(ExpirationState.UNKNOWN, None, None)

    days = (expiration_date - reference_date).days
    normalized_date = expiration_date.isoformat()
    if days < 0:
        return ExpirationAssessment(ExpirationState.EXPIRED, normalized_date, days)
    if days <= max(int(expiry_window_days), 0):
        return ExpirationAssessment(ExpirationState.EXPIRING, normalized_date, days)
    return ExpirationAssessment(ExpirationState.FRESH, normalized_date, days)
