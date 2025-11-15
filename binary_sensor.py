from __future__ import annotations
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import EntityCategory
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN, DATA_CLIENT, DATA_COORDINATOR

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    client = data[DATA_CLIENT]
    coordinator = data[DATA_COORDINATOR]
    async_add_entities([SiegeniaOnlineBinarySensor(client, coordinator, entry)], True)

class SiegeniaOnlineBinarySensor(CoordinatorEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    
    def __init__(self, client, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._client = client
        self._entry = entry
        system_name = self._get_system_name()
        self._attr_name = f"{system_name} Online" if system_name else "Siegenia Online"
        self._attr_unique_id = f"{entry.entry_id}-online"
    
    @property
    def device_info(self):
        """Return device information to link this entity with the device."""
        system_name = self._get_system_name()
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": system_name if system_name else "Siegenia Airoplus",
            "manufacturer": "Siegenia",
            "model": "Airoplus WRG Smart",
        }
        
    def _get_system_name(self) -> str | None:
        """Get the system name from device info."""
        data = self.coordinator.data or {}
        for part in ("state", "params", "info"):
            d = data.get(part) or {}
            if isinstance(d, dict):
                system_name = d.get("systemname") or d.get("device_name")
                if system_name:
                    return system_name
        return None
    
    @property
    def is_on(self) -> bool:
        try:
            return bool(getattr(self._client, "connected", False))
        except Exception:
            return False