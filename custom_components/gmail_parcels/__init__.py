import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_URL, EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_LOG_LEVEL,
    DEFAULT_HOST,
    DEFAULT_LOG_LEVEL,
    DOMAIN,
    WS_ENDPOINT,
)
from .websocket_client import WebsocketClient

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Gmail Parcels component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Gmail Parcels from a config entry."""
    url = entry.options.get(
        CONF_URL, entry.data.get(CONF_URL, f"{DEFAULT_HOST}{WS_ENDPOINT}")
    )
    level_name = entry.options.get(
        CONF_LOG_LEVEL, entry.data.get(CONF_LOG_LEVEL, DEFAULT_LOG_LEVEL)
    ).upper()
    level = getattr(logging, level_name, logging.INFO)
    _LOGGER.setLevel(level)
    logging.getLogger(__package__).setLevel(level)

    client = WebsocketClient(url)
    await client.async_start()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {"client": client}

    async def _close(event: Any) -> None:
        await client.async_stop()

    # Register shutdown handler
    entry.async_on_unload(hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _close))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    data = hass.data[DOMAIN].get(entry.entry_id)
    if data:
        client = data["client"]
        await client.async_stop()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
