"""Count-sensor matrix for Gmail Parcels.

The addon owns the rich data (history, photos, full browsing) and serves it over
REST / the WebUI. Home Assistant only gets *clean counts* plus a lean parcel list
in attributes — no per-parcel entities, no recorder-heavy payloads.

Entities created (all grouped under one "Gmail Parcels" device):

    parcels_upcoming / parcels_today / parcels_delivered     global counts (+ list)
    parcels_<carrier>                                        per-carrier active count (+ list)
    parcels_<carrier>_<bucket>                               per-carrier/bucket count
    parcels_other                                            unknown-carrier active count (+ list)
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import BUCKETS, CARRIERS, DOMAIN, OTHER_CARRIER_SLUG
from .parcels import compact, filter_parcels

# Per-bucket presentation (icon shown in HA). Buckets come from const.BUCKETS.
_BUCKET_ICON = {
    "upcoming": "mdi:package-variant",
    "today": "mdi:truck-delivery",
    "delivered": "mdi:package-variant-closed",
}
_BUCKET_LABEL = {
    "upcoming": "Upcoming",
    "today": "Arriving Today",
    "delivered": "Delivered",
}
_CARRIER_ICON = "mdi:truck-fast"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    client = data["client"]

    device = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="Gmail Parcels",
        manufacturer="Gmail Parcels",
        model="Parcel Tracker",
    )

    entities: List[SensorEntity] = []

    # Global counts (with a lean parcel list in attributes).
    for bucket in BUCKETS:
        entities.append(ParcelsSensor(client, entry, device, bucket=bucket, with_list=True))

    # Per-carrier: an active-count total (with list) plus one count per bucket.
    for name, slug in CARRIERS.items():
        entities.append(
            ParcelsSensor(client, entry, device, slug=slug, carrier_name=name, with_list=True)
        )
        for bucket in BUCKETS:
            entities.append(
                ParcelsSensor(client, entry, device, slug=slug, carrier_name=name, bucket=bucket)
            )

    # Catch-all for parcels whose carrier we don't model.
    entities.append(
        ParcelsSensor(
            client, entry, device, slug=OTHER_CARRIER_SLUG, carrier_name="Other", with_list=True
        )
    )

    async_add_entities(entities, True)


class ParcelsSensor(SensorEntity):
    """A single count in the matrix.

    A sensor is defined by an optional carrier slug and an optional bucket:
      - bucket only            → global bucket count
      - slug only              → carrier active (upcoming) count
      - slug + bucket          → carrier/bucket count
    """

    _attr_has_entity_name = False
    _attr_native_unit_of_measurement = "parcels"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_should_poll = False

    def __init__(
        self,
        client,
        entry: ConfigEntry,
        device: DeviceInfo,
        *,
        bucket: Optional[str] = None,
        slug: Optional[str] = None,
        carrier_name: Optional[str] = None,
        with_list: bool = False,
    ) -> None:
        self._client = client
        self._device = device
        # A carrier "total" sensor (slug, no bucket) counts active = upcoming.
        self._bucket = bucket
        self._effective_bucket = bucket or ("upcoming" if slug else None)
        self._slug = slug
        self._carrier_name = carrier_name
        self._with_list = with_list

        self._attr_device_info = device
        self._attr_name, key, self._attr_icon = self._describe()
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        # Stable, predictable entity_id: sensor.parcels_<key>
        self.entity_id = f"sensor.parcels_{key}"
        self._attr_native_value = 0
        self._attr_extra_state_attributes: Dict[str, Any] = {}

    def _describe(self) -> tuple[str, str, str]:
        """Return (friendly_name, entity_key, icon) for this sensor."""
        if self._slug and self._bucket:
            name = f"{self._carrier_name} {_BUCKET_LABEL[self._bucket]} Parcels"
            return name, f"{self._slug}_{self._bucket}", _BUCKET_ICON[self._bucket]
        if self._slug:
            return f"{self._carrier_name} Parcels", self._slug, _CARRIER_ICON
        # Global bucket sensor.
        return f"{_BUCKET_LABEL[self._bucket]} Parcels", self._bucket, _BUCKET_ICON[self._bucket]

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._client.subscribe(self._handle_update))
        # Render whatever the client already has.
        self._handle_update()

    @callback
    def _handle_update(self) -> None:
        data = self._client.data or {}
        parcels: List[Dict[str, Any]] = data.get("parcels", [])
        today = datetime.date.today()

        matched = filter_parcels(
            parcels, bucket=self._effective_bucket, slug=self._slug, today=today
        )

        self._attr_native_value = len(matched)
        attrs: Dict[str, Any] = {"last_update": data.get("fetched_at")}
        if self._with_list:
            attrs["parcels"] = [compact(p) for p in matched]
        self._attr_extra_state_attributes = attrs

        if self.hass is not None:
            self.schedule_update_ha_state()
