# Gmail Parcels — Home Assistant integration

Custom component that connects to the [Gmail Parcels add-on](https://github.com/alex-savin/hassio-app-gmail-parcels)
over its WebSocket (`/ws`) and surfaces parcel **counts** in Home Assistant.
Example automations are in [AUTOMATIONS.md](AUTOMATIONS.md).

## Design

The addon is the source of truth: it owns the SQLite store, status history, and
proof-of-delivery photos, and serves rich detail through its REST API / WebUI.
The integration deliberately keeps HA lean — **count sensors only, no per-parcel
entities**, with a compact parcel list in attributes for the handful of sensors
that need it. This avoids entity sprawl and keeps the recorder small.

## Entities

All grouped under a single **Gmail Parcels** device. Entity IDs are stable
(they exist at count 0), so they're safe to hard-code on dashboards.

| Entity | Meaning | Has `parcels` list? |
|--------|---------|:---:|
| `sensor.parcels_upcoming` | All parcels not yet delivered | ✅ |
| `sensor.parcels_today` | Out-for-delivery or ETA today | ✅ |
| `sensor.parcels_delivered` | Delivered, still tracked (≤7 days) | ✅ |
| `sensor.parcels_<carrier>` | Active parcels for a carrier | ✅ |
| `sensor.parcels_<carrier>_upcoming` | Per-carrier upcoming count | — |
| `sensor.parcels_<carrier>_today` | Per-carrier today count | — |
| `sensor.parcels_<carrier>_delivered` | Per-carrier delivered count | — |

Carriers: `ups`, `fedex`, `usps`, `dhl`, and `other` (anything unmodeled).
`today` is always a subset of `upcoming`.

### `parcels` attribute shape

Lean by design — no `status_history`, no photo paths (browse those in the addon
WebUI):

```json
{"tracking": "1Z…", "carrier": "UPS", "status": "out for delivery",
 "eta": "2026-06-12", "sender": "Amazon.com", "updated": "2026-06-11T14:30:00Z"}
```

## Install

1. Copy `custom_components/gmail_parcels` into your HA `config/custom_components/`.
2. Restart Home Assistant.
3. Add the **Gmail Parcels** integration and point its URL at
   `http://<addon-host>:8080/ws`.

Example automations and a dashboard card are in [`../DOC.md`](../DOC.md).

## Tests

Pure classification/compaction helpers live in
`custom_components/gmail_parcels/parcels.py` (no HA imports) and are covered by
`tests/test_parcels.py`:

```bash
python -m pytest tests/          # or, without pytest:
python -c "import tests.test_parcels as t; [getattr(t,f)() for f in dir(t) if f.startswith('test_')]"
```
