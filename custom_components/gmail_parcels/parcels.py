"""Pure helpers for bucketing and compacting parcels.

Kept free of Home Assistant imports so the classification logic can be unit
tested in isolation and reused by every sensor without duplication.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional

from .const import CARRIERS, OTHER_CARRIER_SLUG


def _parse_date(value: Optional[str]) -> Optional[datetime.date]:
    if not value:
        return None
    # dateutil is a HA dependency; import lazily so this module stays import-light.
    try:
        from dateutil import parser

        return parser.parse(value).date()
    except Exception:
        return None


def in_bucket(parcel: Dict[str, Any], bucket: str, today: datetime.date) -> bool:
    """Return whether a parcel belongs to the given bucket.

    - delivered: status contains "delivered"
    - today:     ETA parses to today, OR status is out-for-delivery, OR the raw
                 ETA string says "today" (carriers/NER emit relative phrases)
    - upcoming:  anything not delivered (today is a subset of upcoming)
    """
    status = (parcel.get("status") or "").lower()
    eta_str = parcel.get("estimated_delivery") or ""
    delivered = "delivered" in status

    if bucket == "delivered":
        return delivered
    if bucket == "upcoming":
        return not delivered
    if bucket == "today":
        if delivered:
            return False
        if _parse_date(eta_str) == today:
            return True
        if "out for delivery" in status:
            return True
        if "today" in eta_str.lower():
            return True
        return False
    return False


def carrier_slug(parcel: Dict[str, Any]) -> str:
    """Map a parcel's carrier to its entity-id slug, or 'other' if unknown."""
    carrier = (parcel.get("carrier") or "").strip()
    if carrier in CARRIERS:
        return CARRIERS[carrier]
    # Case-insensitive fallback (e.g. "fedex" vs "FedEx").
    lower = carrier.lower()
    for name, slug in CARRIERS.items():
        if name.lower() == lower:
            return slug
    return OTHER_CARRIER_SLUG


def compact(parcel: Dict[str, Any]) -> Dict[str, Any]:
    """A lean, recorder-friendly view of a parcel for sensor attributes.

    Deliberately omits status_history and photo paths — those are large and are
    served by the addon's REST API / WebUI for detailed browsing.
    """
    return {
        "tracking": parcel.get("tracking_number"),
        "carrier": parcel.get("carrier"),
        "status": parcel.get("status"),
        "eta": parcel.get("estimated_delivery"),
        "sender": parcel.get("sender"),
        "updated": parcel.get("last_updated"),
    }


def filter_parcels(
    parcels: List[Dict[str, Any]],
    bucket: Optional[str] = None,
    slug: Optional[str] = None,
    today: Optional[datetime.date] = None,
) -> List[Dict[str, Any]]:
    """Filter parcels by bucket and/or carrier slug."""
    if today is None:
        today = datetime.date.today()
    out = []
    for p in parcels:
        if slug is not None and carrier_slug(p) != slug:
            continue
        if bucket is not None and not in_bucket(p, bucket, today):
            continue
        out.append(p)
    return out
