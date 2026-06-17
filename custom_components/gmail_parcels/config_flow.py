from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_URL
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_LOG_LEVEL,
    DEFAULT_HOST,
    DEFAULT_LOG_LEVEL,
    DOMAIN,
    LOG_LEVEL_CHOICES,
    WS_ENDPOINT,
)

class GmailParcelsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Gmail Parcels."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "GmailParcelsOptionsFlowHandler":
        return GmailParcelsOptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: Dict[str, str] = {}
        if user_input is not None:
            # TODO: Validate the URL here by trying to connect?
            return self.async_create_entry(title="Gmail Parcels", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_URL, default=f"{DEFAULT_HOST}{WS_ENDPOINT}"): str,
                    vol.Optional(CONF_LOG_LEVEL, default=DEFAULT_LOG_LEVEL): vol.In(LOG_LEVEL_CHOICES),
                }
            ),
            errors=errors,
        )


class GmailParcelsOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self.entry = entry

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_URL,
                        default=self.entry.options.get(
                            CONF_URL,
                            self.entry.data.get(CONF_URL, f"{DEFAULT_HOST}{WS_ENDPOINT}"),
                        ),
                    ): str,
                    vol.Optional(
                        CONF_LOG_LEVEL,
                        default=self.entry.options.get(
                            CONF_LOG_LEVEL,
                            self.entry.data.get(CONF_LOG_LEVEL, DEFAULT_LOG_LEVEL),
                        ),
                    ): vol.In(LOG_LEVEL_CHOICES),
                }
            ),
        )
