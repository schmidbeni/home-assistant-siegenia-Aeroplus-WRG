from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    DOMAIN,
    PLATFORMS,
    DATA_CLIENT,
    DATA_COORDINATOR,
    UPDATE_INTERVAL_SECONDS,
)
from .api import SiegeniaClient

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Siegenia from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    host = entry.data["host"]
    username = entry.data["username"]
    password = entry.data["password"]
    port = entry.data.get("port", 443)
    use_ssl = entry.data.get("use_ssl", True)

    client = SiegeniaClient(
        host=host,
        username=username,
        password=password,
        port=port,
        use_ssl=use_ssl,
    )
    await client.connect()

    async def _async_update():
        data: dict = {}
        try:
            if not client.connected:
                await client.connect()
            state = await client.get_device_state()
            params = await client.get_device_params()
            info = await client.get_device()
            data = {"state": state, "params": params, "info": info}
        except Exception as exc:
            # reconnect + retry once
            _LOGGER.debug("Update error, attempting reconnect: %s", exc)
            await client.connect()
            state = await client.get_device_state()
            params = await client.get_device_params()
            info = await client.get_device()
            data = {"state": state, "params": params, "info": info}
        return data

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="siegenia",
        update_method=_async_update,
        update_interval=timedelta(seconds=UPDATE_INTERVAL_SECONDS),
    )

    await coordinator.async_config_entry_first_refresh()

    # Push-triggered refresh when unsolicited WS messages arrive
    try:
        client.set_on_push(lambda _data: hass.async_create_task(coordinator.async_request_refresh()))
    except Exception:
        pass

    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CLIENT: client,
        DATA_COORDINATOR: coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id, None)
        if data:
            client: SiegeniaClient | None = data.get(DATA_CLIENT)
            if client:
                await client.close()
    return unload_ok
