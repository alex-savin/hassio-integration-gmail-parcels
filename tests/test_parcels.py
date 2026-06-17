"""Unit tests for the pure parcel-classification helpers.

These deliberately avoid importing Home Assistant. The package __init__ pulls in
`homeassistant`, so we load const.py and parcels.py directly into a throwaway
package namespace and stub `dateutil` if it isn't installed.
"""

import datetime
import importlib.util
import os
import sys
import types

_CC = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "custom_components",
    "gmail_parcels",
)


def _ensure_dateutil():
    try:
        import dateutil  # noqa: F401
    except Exception:
        m = types.ModuleType("dateutil")
        p = types.ModuleType("dateutil.parser")
        p.parse = lambda s: datetime.datetime.fromisoformat(s)
        m.parser = p
        sys.modules["dateutil"] = m
        sys.modules["dateutil.parser"] = p


def _load():
    _ensure_dateutil()
    pkg = types.ModuleType("gp")
    pkg.__path__ = [_CC]
    sys.modules["gp"] = pkg

    def load(name):
        spec = importlib.util.spec_from_file_location(
            "gp." + name, os.path.join(_CC, name + ".py")
        )
        mod = importlib.util.module_from_spec(spec)
        sys.modules["gp." + name] = mod
        spec.loader.exec_module(mod)
        return mod

    load("const")
    return load("parcels")


P = _load()

DATA = [
    {"tracking_number": "1Z1", "carrier": "UPS", "status": "in transit", "estimated_delivery": "", "sender": "Amazon", "last_updated": "t"},
    {"tracking_number": "1Z2", "carrier": "UPS", "status": "out for delivery", "estimated_delivery": "", "sender": "Nike"},
    {"tracking_number": "F1", "carrier": "FedEx", "status": "delivered", "estimated_delivery": "", "sender": "Etsy"},
    {"tracking_number": "U1", "carrier": "USPS", "status": "Arriving today", "estimated_delivery": "today", "sender": "eBay"},
    {"tracking_number": "X1", "carrier": "OnTrac", "status": "in transit", "estimated_delivery": "", "sender": "Shop"},
]

TODAY = datetime.date.today()


def _n(**kw):
    return len(P.filter_parcels(DATA, today=TODAY, **kw))


def test_global_buckets():
    assert _n(bucket="upcoming") == 4  # everything not delivered
    assert _n(bucket="today") == 2     # out-for-delivery + "today" ETA
    assert _n(bucket="delivered") == 1


def test_today_is_subset_of_upcoming():
    today = P.filter_parcels(DATA, bucket="today", today=TODAY)
    upcoming = P.filter_parcels(DATA, bucket="upcoming", today=TODAY)
    today_tns = {p["tracking_number"] for p in today}
    upcoming_tns = {p["tracking_number"] for p in upcoming}
    assert today_tns <= upcoming_tns


def test_carrier_scoping():
    assert _n(slug="ups", bucket="upcoming") == 2
    assert _n(slug="ups", bucket="today") == 1
    assert _n(slug="fedex", bucket="delivered") == 1
    assert _n(slug="usps", bucket="today") == 1


def test_parsed_eta_today():
    iso_today = TODAY.isoformat()
    data = [{"tracking_number": "P1", "carrier": "UPS", "status": "in transit", "estimated_delivery": iso_today}]
    assert len(P.filter_parcels(data, bucket="today", today=TODAY)) == 1


def test_unknown_carrier_is_other():
    assert P.carrier_slug({"carrier": "OnTrac"}) == "other"
    assert _n(slug="other", bucket="upcoming") == 1


def test_carrier_slug_case_insensitive():
    assert P.carrier_slug({"carrier": "fedex"}) == "fedex"
    assert P.carrier_slug({"carrier": "FedEx"}) == "fedex"
    assert P.carrier_slug({"carrier": ""}) == "other"


def test_compact_is_lean():
    c = P.compact(DATA[0])
    assert set(c.keys()) == {"tracking", "carrier", "status", "eta", "sender", "updated"}
    # No heavy fields leak into recorder-backed attributes.
    assert "status_history" not in c
    assert "photo_proof" not in c
