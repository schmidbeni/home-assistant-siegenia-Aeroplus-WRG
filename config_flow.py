from __future__ import annotations

from typing import Any, Dict

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD, CONF_PORT, CONF_SSL

from .const import DOMAIN, DEFAULT_PORT, DEFAULT_USE_SSL
from .api import SiegeniaClient

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Optional(CONF_SSL, default=DEFAULT_USE_SSL): bool,
    }
)

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: Dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST]
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]
            port = user_input.get(CONF_PORT, DEFAULT_PORT)
            use_ssl = user_input.get(CONF_SSL, DEFAULT_USE_SSL)

            await self.async_set_unique_id(f"{host}:{port}")
            self._abort_if_unique_id_configured()

            client = SiegeniaClient(host, username, password, port=port, use_ssl=use_ssl)
            try:
                await client.connect()
                await client.get_device()
            except Exception:
                errors["base"] = "cannot_connect"
            finally:
                await client.close()

            if not errors:
                data = {
                    "host": host,
                    "username": username,
                    "password": password,
                    "port": port,
                    "use_ssl": use_ssl,
                }
                return self.async_create_entry(title=f"Siegenia {host}", data=data)

        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA, errors=errors)
